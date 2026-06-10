from src.entities.task import TaskPriority, TaskStatus


def test_task_status_values():
    assert TaskStatus.pending == "pending"
    assert TaskStatus.in_progress == "in_progress"
    assert TaskStatus.completed == "completed"


def test_task_priority_values():
    assert TaskPriority.low == "low"
    assert TaskPriority.medium == "medium"
    assert TaskPriority.high == "high"


def test_task_status_is_str_enum():
    assert isinstance(TaskStatus.pending, str)
    assert isinstance(TaskStatus.in_progress, str)
    assert isinstance(TaskStatus.completed, str)


def test_task_priority_is_str_enum():
    assert isinstance(TaskPriority.low, str)
    assert isinstance(TaskPriority.medium, str)
    assert isinstance(TaskPriority.high, str)


def test_task_status_all_values():
    values = {s.value for s in TaskStatus}
    assert values == {"pending", "in_progress", "completed"}


def test_task_priority_all_values():
    values = {p.value for p in TaskPriority}
    assert values == {"low", "medium", "high"}
