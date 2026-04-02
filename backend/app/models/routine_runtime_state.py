from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List, Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.routine import Routine
    from app.models.user import User


class RuntimeStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"


class RoutineRuntimeStateParticipant(BaseModel, table=True):
    __tablename__ = "routine_runtime_state_participants"

    runtime_state_id: int = Field(foreign_key="routine_runtime_states.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True, unique=True)

    runtime_state: "RoutineRuntimeState" = Relationship(back_populates="participants")
    user: "User" = Relationship()


class RoutineRuntimeState(BaseModel, table=True):
    __tablename__ = "routine_runtime_states"

    active_routine_id: Optional[int] = Field(default=None, foreign_key="routines.id")
    status: RuntimeStatus = Field(default=RuntimeStatus.IDLE)
    current_task_position: Optional[int] = None
    task_started_at: Optional[datetime] = None
    routine_started_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    pause_duration: int = 0
    active_routine: Optional["Routine"] = Relationship(
        back_populates="runtime_states",
        sa_relationship_kwargs={"foreign_keys": "RoutineRuntimeState.active_routine_id"}
    )
    participants: List[RoutineRuntimeStateParticipant] = Relationship(
        back_populates="runtime_state",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    def recalculate(self, now: Optional[datetime] = None) -> bool:
        """
        Recalculate current task position and task start timestamp from routine start.
        Returns True when any field changed.
        """
        changed = False
        if self.active_routine_id is None or self.status != RuntimeStatus.RUNNING:
            return changed

        current_now = now or datetime.now(timezone.utc)

        started_at = self.routine_started_at
        if started_at is None:
            return changed
        elapsed_total_seconds = max(
            0,
            int((current_now - started_at).total_seconds()) - max(0, int(self.pause_duration or 0)),
        )

        routine = self.active_routine

        task_durations = sorted(
            [(rt.position, rt.task.duration if rt.task else 0) for rt in routine.routine_tasks],
            key=lambda item: item[0],
        )

        consumed = 0
        for position, duration in task_durations:
            task_duration = max(0, int(duration))
            if elapsed_total_seconds < consumed + task_duration:
                task_offset_seconds = elapsed_total_seconds - consumed
                next_task_started_at = current_now - timedelta(seconds=task_offset_seconds)
                changed = changed or (
                    self.current_task_position != position
                    or self.task_started_at != next_task_started_at
                )
                self.current_task_position = position
                self.task_started_at = next_task_started_at
                return changed
            consumed += task_duration

        changed = (
            self.status != RuntimeStatus.FINISHED
            or self.active_routine_id is not None
            or self.current_task_position is not None
            or self.task_started_at is not None
            or self.routine_started_at is not None
            or self.paused_at is not None
            or self.pause_duration != 0
        )
        self.status = RuntimeStatus.FINISHED
        self.active_routine_id = None
        self.current_task_position = None
        self.task_started_at = None
        self.routine_started_at = None
        self.paused_at = None
        self.pause_duration = 0
        return changed
