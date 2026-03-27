from __future__ import annotations

from app.models.routine import Routine
from app.models.routine_access import AccessLevel, RoutineAccess, StartMode
from app.models.routine_runtime_state import (
    RoutineRuntimeState,
    RoutineRuntimeStateParticipant,
    RuntimeStatus,
)
from app.models.routine_task import RoutineTask
from app.models.task import Task
from app.schemas.runtime import (
    RuntimeActorRead,
    RuntimeCommandAccepted,
    RuntimeCommandRequest,
    RuntimeCommandType,
    RuntimeEventEnvelope,
    RuntimeEventType,
)
from app.services.runtime_event_bus import runtime_event_bus
from app.services.runtime_state import (
    build_runtime_active_read,
    build_runtime_sync_read,
    get_or_create_runtime_state,
    refresh_runtime_state,
)
from dataclasses import dataclass
from datetime import datetime
from sqlalchemy import delete, func
from sqlmodel import Session, select
from typing import Optional


class CommandValidationError(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass
class CommandContext:
    participant_user_ids: list[int]


@dataclass
class CommandResult:
    accepted: RuntimeCommandAccepted


class RoutineCommandService:
    async def execute(
        self,
        db: Session,
        user_id: int,
        command: dict | RuntimeCommandRequest,
        actor: dict[str, str],
    ) -> CommandResult:
        command_payload = (
            command
            if isinstance(command, RuntimeCommandRequest)
            else RuntimeCommandRequest.model_validate(command)
        )
        actor_payload = RuntimeActorRead.model_validate(actor)
        now = datetime.utcnow()

        runtime = refresh_runtime_state(db, get_or_create_runtime_state(db, user_id))
        context = self._apply_command(db, user_id, runtime, command_payload, now)

        runtime.updated_at = now
        db.add(runtime)
        db.commit()
        db.refresh(runtime)

        sync_payload = build_runtime_sync_read(db, runtime, server_time=now)
        active_payload = (
            build_runtime_active_read(db, runtime, server_time=now)
            if command_payload.type == RuntimeCommandType.ROUTINE_START
            else None
        )
        accepted = RuntimeCommandAccepted(
            command_id=command_payload.command_id,
            server_time=now,
            sync=sync_payload,
            active=active_payload,
        )

        await self._publish_runtime_event(
            runtime=runtime,
            command_type=command_payload.type,
            actor=actor_payload,
            context=context,
            sync_payload=sync_payload,
            active_payload=active_payload,
            server_time=now,
        )

        return CommandResult(accepted=accepted)

    async def stop_runtimes_for_routine(
        self,
        db: Session,
        routine_id: int,
    ) -> None:
        """
        Force stop any active runtime using the given routine and send events.
        Typically called before routine deletion.
        """
        now = datetime.utcnow()
        # Find all runtimes that have this routine active
        runtimes = db.exec(
            select(RoutineRuntimeState).where(RoutineRuntimeState.active_routine_id == routine_id)
        ).all()

        for runtime in runtimes:
            # Send STOP event
            sync_payload = build_runtime_sync_read(db, runtime, server_time=now)
            context = CommandContext(
                participant_user_ids=[p.user_id for p in (runtime.participants or [])]
            )
            actor_payload = RuntimeActorRead(type="server", id="system:routine-delete")

            await self._publish_runtime_event(
                runtime=runtime,
                command_type=RuntimeCommandType.ROUTINE_STOP,
                actor=actor_payload,
                context=context,
                sync_payload=sync_payload,
                active_payload=None,
                server_time=now,
            )
            db.delete(runtime)
            db.commit()


    def _apply_command(
        self,
        db: Session,
        user_id: int,
        runtime: RoutineRuntimeState,
        command: RuntimeCommandRequest,
        now: datetime,
    ) -> CommandContext:
        if command.type == RuntimeCommandType.ROUTINE_START:
            return self._start_routine(db, user_id, runtime, command, now)

        routine_id = runtime.active_routine_id
        self._assert_runtime_control_allowed(db, user_id, routine_id)

        if command.type == RuntimeCommandType.ROUTINE_STOP:
            self._stop_routine(runtime)
        elif command.type == RuntimeCommandType.ROUTINE_PAUSE:
            self._pause_routine(runtime, now)
        elif command.type == RuntimeCommandType.ROUTINE_RESUME:
            self._resume_routine(runtime, now)
        elif command.type == RuntimeCommandType.ROUTINE_SKIP:
            completed = self._skip_task(db, runtime, now)
            if completed:
                command.type = RuntimeCommandType.ROUTINE_COMPLETE
        elif command.type == RuntimeCommandType.ROUTINE_COMPLETE:
            self._complete_routine(runtime)
        else:
            raise CommandValidationError("unsupported_command")

        return CommandContext(
            participant_user_ids=[participant.user_id for participant in (runtime.participants or [])],
        )

    def _start_routine(
        self,
        db: Session,
        user_id: int,
        runtime: RoutineRuntimeState,
        command: RuntimeCommandRequest,
        now: datetime,
    ) -> CommandContext:
        if command.routine_id is None:
            raise CommandValidationError("missing_routine_id")

        access = db.exec(
            select(RoutineAccess).where(
                RoutineAccess.routine_id == command.routine_id,
                RoutineAccess.user_id == user_id,
            )
        ).first()
        if not access:
            raise CommandValidationError("routine_not_found")
        if access.access_level not in {AccessLevel.OWNER, AccessLevel.START}:
            raise CommandValidationError("insufficient_permissions")

        routine = db.get(Routine, command.routine_id)
        if not routine:
            raise CommandValidationError("routine_not_found")

        if runtime.active_routine_id is not None and runtime.status != RuntimeStatus.FINISHED:
            raise CommandValidationError("routine_already_active")

        first_row = db.exec(
            select(Task.id, RoutineTask.position)
            .join(RoutineTask, RoutineTask.task_id == Task.id)
            .where(RoutineTask.routine_id == command.routine_id)
            .order_by(RoutineTask.position.asc())
        ).first()
        if not first_row:
            raise CommandValidationError("routine_has_no_tasks")

        first_task_id, first_position = first_row
        accesses = db.exec(select(RoutineAccess).where(RoutineAccess.routine_id == routine.id)).all()
        starter_is_owner = access.access_level == AccessLevel.OWNER

        participant_ids = {user_id}
        for routine_access in accesses:
            if routine_access.user_id == user_id:
                continue
            if routine_access.start_mode == StartMode.FOLLOW_ANY:
                participant_ids.add(routine_access.user_id)
            elif routine_access.start_mode == StartMode.FOLLOW_OWNER and starter_is_owner:
                participant_ids.add(routine_access.user_id)

        involved_runtimes = set(
            db.exec(
                select(RoutineRuntimeStateParticipant.runtime_state_id).where(
                    RoutineRuntimeStateParticipant.user_id.in_(list(participant_ids))
                )
            ).all()
        )

        db.exec(
            delete(RoutineRuntimeStateParticipant).where(
                RoutineRuntimeStateParticipant.user_id.in_(list(participant_ids))
            )
        )
        for participant_id in participant_ids:
            db.add(
                RoutineRuntimeStateParticipant(
                    runtime_state_id=runtime.id,
                    user_id=participant_id,
                )
            )
        db.commit()

        for runtime_id in involved_runtimes:
            if runtime_id == runtime.id:
                continue
            count = db.exec(
                select(func.count(RoutineRuntimeStateParticipant.id)).where(
                    RoutineRuntimeStateParticipant.runtime_state_id == runtime_id
                )
            ).one()
            if count == 0:
                db.exec(delete(RoutineRuntimeState).where(RoutineRuntimeState.id == runtime_id))
        db.commit()
        db.refresh(runtime)

        del first_task_id
        runtime.active_routine_id = command.routine_id
        runtime.status = RuntimeStatus.RUNNING
        runtime.current_task_position = first_position
        runtime.task_started_at = now
        runtime.routine_started_at = now
        runtime.paused_at = None
        runtime.pause_duration = 0

        return CommandContext(
            participant_user_ids=[participant.user_id for participant in (runtime.participants or [])],
        )

    def _stop_routine(self, runtime: RoutineRuntimeState) -> None:
        if runtime.active_routine_id is None:
            raise CommandValidationError("no_active_routine")

        runtime.active_routine_id = None
        runtime.status = RuntimeStatus.IDLE
        runtime.current_task_position = None
        runtime.task_started_at = None
        runtime.routine_started_at = None
        runtime.paused_at = None
        runtime.pause_duration = 0

    def _complete_routine(self, runtime: RoutineRuntimeState) -> None:
        if runtime.active_routine_id is None:
            raise CommandValidationError("no_active_routine")

        runtime.active_routine_id = None
        runtime.status = RuntimeStatus.FINISHED
        runtime.current_task_position = None
        runtime.task_started_at = None
        runtime.routine_started_at = None
        runtime.paused_at = None
        runtime.pause_duration = 0

    def _pause_routine(self, runtime: RoutineRuntimeState, now: datetime) -> None:
        if runtime.active_routine_id is None:
            raise CommandValidationError("no_active_routine")
        if runtime.status != RuntimeStatus.RUNNING:
            raise CommandValidationError("routine_not_running")

        runtime.status = RuntimeStatus.PAUSED
        runtime.paused_at = now

    def _resume_routine(self, runtime: RoutineRuntimeState, now: datetime) -> None:
        if runtime.active_routine_id is None:
            raise CommandValidationError("no_active_routine")
        if runtime.status != RuntimeStatus.PAUSED:
            raise CommandValidationError("routine_not_paused")

        if runtime.paused_at is not None:
            pause_delta = now - runtime.paused_at
            runtime.pause_duration = max(0, int(runtime.pause_duration or 0)) + max(
                0, int(pause_delta.total_seconds())
            )
            if runtime.task_started_at is not None:
                runtime.task_started_at = runtime.task_started_at + pause_delta
        runtime.paused_at = None
        runtime.status = RuntimeStatus.RUNNING

    def _skip_task(self, db: Session, runtime: RoutineRuntimeState, now: datetime) -> bool:
        if runtime.active_routine_id is None:
            raise CommandValidationError("no_active_routine")
        if runtime.current_task_position is None:
            raise CommandValidationError("missing_current_task")

        next_row = db.exec(
            select(Task.id, RoutineTask.position)
            .join(RoutineTask, RoutineTask.task_id == Task.id)
            .where(
                RoutineTask.routine_id == runtime.active_routine_id,
                RoutineTask.position > runtime.current_task_position,
            )
            .order_by(RoutineTask.position.asc())
        ).first()

        if not next_row:
            self._complete_routine(runtime)
            return True

        _, next_position = next_row
        runtime.current_task_position = next_position
        runtime.task_started_at = now
        if runtime.status == RuntimeStatus.PAUSED:
            runtime.paused_at = now
        return False

    def _assert_runtime_control_allowed(
        self,
        db: Session,
        user_id: int,
        routine_id: Optional[int],
    ) -> None:
        if routine_id is None:
            raise CommandValidationError("no_active_routine")

        access = db.exec(
            select(RoutineAccess).where(
                RoutineAccess.routine_id == routine_id,
                RoutineAccess.user_id == user_id,
            )
        ).first()
        if not access:
            raise CommandValidationError("routine_not_found")
        if access.access_level not in {AccessLevel.OWNER, AccessLevel.START}:
            raise CommandValidationError("insufficient_permissions")

    def _runtime_event_type(self, command_type: RuntimeCommandType) -> RuntimeEventType:
        mapping = {
            RuntimeCommandType.ROUTINE_START: RuntimeEventType.RUNTIME_STARTED,
            RuntimeCommandType.ROUTINE_PAUSE: RuntimeEventType.RUNTIME_PAUSED,
            RuntimeCommandType.ROUTINE_RESUME: RuntimeEventType.RUNTIME_RESUMED,
            RuntimeCommandType.ROUTINE_SKIP: RuntimeEventType.RUNTIME_SKIPPED,
            RuntimeCommandType.ROUTINE_STOP: RuntimeEventType.RUNTIME_STOPPED,
            RuntimeCommandType.ROUTINE_COMPLETE: RuntimeEventType.RUNTIME_COMPLETED,
        }
        return mapping[command_type]

    async def _publish_runtime_event(
        self,
        *,
        runtime: RoutineRuntimeState,
        command_type: RuntimeCommandType,
        actor: RuntimeActorRead,
        context: CommandContext,
        sync_payload,
        active_payload,
        server_time: datetime,
    ) -> None:
        event_type = self._runtime_event_type(command_type)
        runtime_event = RuntimeEventEnvelope(
            event_id=self._event_id(runtime, event_type, server_time=server_time),
            event_type=event_type,
            server_time=server_time,
            actor=actor,
            sync=sync_payload,
            active=active_payload,
        )

        participant_user_ids = context.participant_user_ids or [
            participant.user_id for participant in (runtime.participants or [])
        ]
        for participant_user_id in participant_user_ids:
            await runtime_event_bus.publish(participant_user_id, runtime_event)

    def _event_id(
        self,
        runtime: RoutineRuntimeState,
        event_type: RuntimeEventType,
        *,
        server_time: datetime,
        suffix: str = "runtime",
    ) -> str:
        return f"{suffix}-{runtime.id}-{server_time.strftime('%Y%m%d%H%M%S%f')}-{event_type.value}"


routine_command_service = RoutineCommandService()
