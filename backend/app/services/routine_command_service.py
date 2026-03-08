from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from app.models.routine import Routine
from app.models.routine_runtime_state import RoutineRuntimeState, RuntimeStatus
from app.models.routine_task import RoutineTask
from app.models.task import Task
from app.schemas.socketio import ClientCommandPayload, CommandType
from app.socketio.bus import socketio_bus
from app.socketio.state import build_runtime_payload, get_or_create_runtime_state, routine_read_with_tasks
from sqlmodel import Session, select


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

        runtime.updated_at = datetime.utcnow()
        db.add(runtime)
        db.commit()
        db.refresh(runtime)

        applied_payload = {
            "command_id": command_payload.command_id,
            "type": command_payload.type.value,
            "runtime": build_runtime_payload(runtime).model_dump(),
            "effective_at": datetime.now(timezone.utc),
            "actor": actor,
        }

        await socketio_bus.emit_to_user(user_id, "server.command.applied", applied_payload)
        if started_payload:
            started_payload["runtime"] = build_runtime_payload(runtime).model_dump()
            await socketio_bus.emit_to_user(user_id, "server.routine.started", started_payload)

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

        routine = db.exec(select(Routine).where(Routine.id == command.routine_id, Routine.user_id == user_id)).first()
        if not routine:
            raise CommandValidationError("routine_not_found")
        if runtime.active_routine_id is not None:
            raise CommandValidationError("routine_already_active")

        first_task = db.exec(
            select(Task, RoutineTask.position)
            .join(RoutineTask, RoutineTask.task_id == Task.id)
            .where(RoutineTask.routine_id == command.routine_id)
            .order_by(RoutineTask.position.asc())
        ).first()
        if not first_task:
            raise CommandValidationError("routine_has_no_tasks")

        _, position = first_task
        runtime.active_routine_id = command.routine_id
        runtime.status = RuntimeStatus.RUNNING
        runtime.current_task_position = position
        runtime.task_started_at = datetime.utcnow()

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
        return runtime

    def _pause_routine(self, runtime: RoutineRuntimeState) -> RoutineRuntimeState:
        if runtime.active_routine_id is None:
            raise CommandValidationError("no_active_routine")
        if runtime.status != RuntimeStatus.RUNNING:
            raise CommandValidationError("routine_not_running")

        runtime.status = RuntimeStatus.PAUSED
        return runtime

    def _resume_routine(self, runtime: RoutineRuntimeState) -> RoutineRuntimeState:
        if runtime.active_routine_id is None:
            raise CommandValidationError("no_active_routine")
        if runtime.status != RuntimeStatus.PAUSED:
            raise CommandValidationError("routine_not_paused")

        now = datetime.utcnow()
        if runtime.task_started_at and runtime.updated_at:
            paused_delta = now - runtime.updated_at
            runtime.task_started_at = runtime.task_started_at + paused_delta
        elif runtime.task_started_at is None:
            runtime.task_started_at = now

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
        runtime.current_task_position = next_position
        runtime.task_started_at = datetime.utcnow() if runtime.status == RuntimeStatus.RUNNING else None
        return runtime


routine_command_service = RoutineCommandService()
