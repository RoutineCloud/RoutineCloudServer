from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import delete, func
from sqlmodel import Session, select

from app.models.routine import Routine
from app.models.routine_access import AccessLevel, RoutineAccess, StartMode
from app.models.routine_runtime_state import (
    RoutineRuntimeState,
    RoutineRuntimeStateParticipant,
    RuntimeStatus,
)
from app.models.routine_task import RoutineTask
from app.models.task import Task
from app.schemas.socketio import ClientCommandPayload, CommandType
from app.socketio.bus import socketio_bus
from app.socketio.state import (
    build_runtime_payload,
    get_or_create_runtime_state,
    routine_read_with_tasks,
)


class CommandValidationError(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass
class CommandResult:
    applied_payload: dict[str, Any]
    started_payload: Optional[dict[str, Any]] = None


class RoutineCommandService:
    async def execute(
        self,
        db: Session,
        user_id: int,
        command: dict[str, Any] | ClientCommandPayload,
        actor: dict[str, str],
    ) -> CommandResult:
        command_payload = command if isinstance(command, ClientCommandPayload) else ClientCommandPayload.model_validate(command)

        runtime = get_or_create_runtime_state(db, user_id)
        if runtime.recalculate():
            db.add(runtime)
            db.commit()
            db.refresh(runtime)
        started_payload: Optional[dict[str, Any]] = None

        if command_payload.type == CommandType.ROUTINE_START:
            runtime, started_payload = self._start_routine(db, user_id, runtime, command_payload)
        elif command_payload.type == CommandType.ROUTINE_END:
            runtime = self._end_routine(runtime)
        elif command_payload.type == CommandType.ROUTINE_PAUSE:
            runtime = self._pause_routine(runtime)
        elif command_payload.type == CommandType.ROUTINE_RESUME:
            runtime = self._resume_routine(runtime)
        elif command_payload.type == CommandType.TASK_SKIP:
            runtime = self._skip_task(db, runtime)

        if runtime.recalculate():
            db.add(runtime)
            db.commit()
            db.refresh(runtime)

        runtime.updated_at = datetime.utcnow()
        db.add(runtime)
        db.commit()
        db.refresh(runtime)

        applied_payload = {
            "command_id": command_payload.command_id,
            "type": command_payload.type.value,
            "runtime": build_runtime_payload(runtime).model_dump(),
            "effective_at": datetime.utcnow(),
            "actor": actor,
        }

        target_users = [p.user_id for p in (runtime.participants or [])]
        if not target_users:
            target_users = [user_id]
        for tid in target_users:
            await socketio_bus.emit_to_user(tid, "server.command.applied", applied_payload)
            if started_payload:
                # Refresh started_payload runtime for each user if it contains user-specific info
                # But here it's shared.
                started_payload["runtime"] = build_runtime_payload(runtime).model_dump()
                await socketio_bus.emit_to_user(tid, "server.routine.started", started_payload)

        return CommandResult(applied_payload=applied_payload, started_payload=started_payload)

    def _start_routine(
        self,
        db: Session,
        user_id: int,
        runtime: RoutineRuntimeState,
        command: ClientCommandPayload,
    ) -> tuple[RoutineRuntimeState, dict[str, Any]]:
        if command.routine_id is None:
            raise CommandValidationError("missing_routine_id")

        routine = db.exec(
            select(Routine)
            .join(RoutineAccess)
            .where(Routine.id == command.routine_id, RoutineAccess.user_id == user_id)
        ).first()
        if not routine:
            raise CommandValidationError("routine_not_found")
        if runtime.active_routine_id is not None:
            if runtime.status != RuntimeStatus.FINISHED:
                raise CommandValidationError("routine_already_active")

        first_task = db.exec(
            select(Task.id)
            .join(RoutineTask, RoutineTask.task_id == Task.id)
            .where(RoutineTask.routine_id == command.routine_id)
            .order_by(RoutineTask.position.asc())
        ).first()
        if not first_task:
            raise CommandValidationError("routine_has_no_tasks")

        # Discover participants based on start_mode
        accesses = db.exec(select(RoutineAccess).where(RoutineAccess.routine_id == routine.id)).all()
        starter_acc = next((a for a in accesses if a.user_id == user_id), None)
        is_owner = starter_acc.access_level == AccessLevel.OWNER if starter_acc else False

        participant_ids = {user_id}
        for acc in accesses:
            if acc.user_id == user_id:
                continue
            if acc.start_mode == StartMode.FOLLOW_ANY or (
                acc.start_mode == StartMode.FOLLOW_OWNER and is_owner
            ):
                participant_ids.add(acc.user_id)

        # Remove participants from ANY other runtime states and move them to this one
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
        for pid in participant_ids:
            db.add(RoutineRuntimeStateParticipant(runtime_state_id=runtime.id, user_id=pid))

        db.commit()

        # Cleanup empty runtimes
        for rid in involved_runtimes:
            if rid == runtime.id:
                continue
            count = db.exec(
                select(func.count(RoutineRuntimeStateParticipant.id)).where(
                    RoutineRuntimeStateParticipant.runtime_state_id == rid
                )
            ).one()
            if count == 0:
                db.exec(delete(RoutineRuntimeState).where(RoutineRuntimeState.id == rid))

        db.commit()
        db.refresh(runtime)

        now = datetime.utcnow()
        runtime.active_routine_id = command.routine_id
        runtime.status = RuntimeStatus.RUNNING
        runtime.current_task_position = 0
        runtime.task_started_at = now
        runtime.routine_started_at = now
        runtime.paused_at = None
        runtime.pause_duration = 0

        routine_payload = routine_read_with_tasks(db, user_id, command.routine_id)
        if not routine_payload:
            raise CommandValidationError("routine_not_found")

        return runtime, {
            "command_id": command.command_id,
            "routine": routine_payload.model_dump(),
            "runtime": build_runtime_payload(runtime).model_dump(),
        }

    def _end_routine(self, runtime: RoutineRuntimeState) -> RoutineRuntimeState:
        if runtime.active_routine_id is None:
            raise CommandValidationError("no_active_routine")

        runtime.active_routine_id = None
        runtime.status = RuntimeStatus.IDLE
        runtime.current_task_position = None
        runtime.task_started_at = None
        runtime.routine_started_at = None
        runtime.paused_at = None
        runtime.pause_duration = 0
        return runtime

    def _pause_routine(self, runtime: RoutineRuntimeState) -> RoutineRuntimeState:
        if runtime.active_routine_id is None:
            raise CommandValidationError("no_active_routine")
        if runtime.status != RuntimeStatus.RUNNING:
            raise CommandValidationError("routine_not_running")

        runtime.status = RuntimeStatus.PAUSED
        runtime.paused_at = datetime.utcnow()
        return runtime

    def _resume_routine(self, runtime: RoutineRuntimeState) -> RoutineRuntimeState:
        if runtime.active_routine_id is None:
            raise CommandValidationError("no_active_routine")
        if runtime.status != RuntimeStatus.PAUSED:
            raise CommandValidationError("routine_not_paused")

        now = datetime.utcnow()
        if runtime.paused_at is not None:
            paused_seconds = max(0, int((now - runtime.paused_at).total_seconds()))
            runtime.pause_duration = max(0, int(runtime.pause_duration or 0)) + paused_seconds
            if runtime.task_started_at is not None:
                runtime.task_started_at = runtime.task_started_at + (now - runtime.paused_at)
        runtime.paused_at = None

        runtime.status = RuntimeStatus.RUNNING
        return runtime

    def _skip_task(self, db: Session, runtime: RoutineRuntimeState) -> RoutineRuntimeState:
        if runtime.active_routine_id is None:
            raise CommandValidationError("no_active_routine")
        if runtime.current_task_position is None:
            raise CommandValidationError("missing_current_task")

        next_row = db.exec(
            select(Task, RoutineTask.position)
            .join(RoutineTask, RoutineTask.task_id == Task.id)
            .where(
                RoutineTask.routine_id == runtime.active_routine_id,
                RoutineTask.position > runtime.current_task_position,
            )
            .order_by(RoutineTask.position.asc())
        ).first()

        if not next_row:
            return self._end_routine(runtime)

        _, next_position = next_row
        now = datetime.utcnow()
        runtime.current_task_position = next_position
        runtime.task_started_at = now
        if runtime.status == RuntimeStatus.PAUSED:
            runtime.paused_at = now
        return runtime


routine_command_service = RoutineCommandService()
