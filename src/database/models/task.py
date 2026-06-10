from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base


class TaskModel(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_task_list_id_status_priority", "task_list_id", "status", "priority"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_list_id: Mapped[int] = mapped_column(
        ForeignKey("task_lists.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    task_list: Mapped["TaskListModel"] = relationship(  # noqa: F821
        "TaskListModel", back_populates="tasks"
    )
