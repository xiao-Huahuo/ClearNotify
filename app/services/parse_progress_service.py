import threading
import time
import uuid
from typing import Any


_LOCK = threading.Lock()
_TASKS: dict[str, dict[str, Any]] = {}
_TTL_SECONDS = 30 * 60


def _now() -> float:
    return time.time()


def _cleanup() -> None:
    now = _now()
    expired: list[str] = []
    for task_id, task in _TASKS.items():
        ts = float(task.get("updated_at") or task.get("created_at") or now)
        if now - ts > _TTL_SECONDS:
            expired.append(task_id)
    for task_id in expired:
        _TASKS.pop(task_id, None)


def create_task(user_id: int) -> str:
    with _LOCK:
        _cleanup()
        task_id = uuid.uuid4().hex
        now = _now()
        _TASKS[task_id] = {
            "task_id": task_id,
            "user_id": int(user_id),
            "status": "pending",
            "progress": 0,
            "stage": "任务已创建",
            "message": "",
            "created_at": now,
            "updated_at": now,
        }
        return task_id


def update_task(
    task_id: str,
    user_id: int,
    *,
    status: str | None = None,
    progress: int | None = None,
    stage: str | None = None,
    message: str | None = None,
) -> dict[str, Any] | None:
    with _LOCK:
        task = _TASKS.get(task_id)
        if not task or int(task.get("user_id", -1)) != int(user_id):
            return None
        if status:
            task["status"] = status
        if progress is not None:
            task["progress"] = max(0, min(100, int(progress)))
        if stage is not None:
            task["stage"] = str(stage)
        if message is not None:
            task["message"] = str(message)
        task["updated_at"] = _now()
        return dict(task)


def fail_task(task_id: str, user_id: int, message: str) -> dict[str, Any] | None:
    return update_task(
        task_id,
        user_id,
        status="failed",
        progress=100,
        stage="解析失败",
        message=message,
    )


def complete_task(task_id: str, user_id: int, message: str = "解析完成") -> dict[str, Any] | None:
    return update_task(
        task_id,
        user_id,
        status="completed",
        progress=100,
        stage="已完成",
        message=message,
    )


def get_task(task_id: str, user_id: int) -> dict[str, Any] | None:
    with _LOCK:
        task = _TASKS.get(task_id)
        if not task or int(task.get("user_id", -1)) != int(user_id):
            return None
        return dict(task)

