from threading import Lock
from time import monotonic
from typing import Callable, Generator
from uuid import uuid4

from backend.core.agent import Approval

PendingRun = Generator[Approval, bool, str]


class Approvals:
    """Keep a paused run until the user answers once or the approval expires."""

    def __init__(self) -> None:
        self._pending: dict[str, tuple[float, PendingRun]] = {}
        self._lock = Lock()

    def _expire(self) -> None:
        now = monotonic()
        expired = [key for key, (deadline, _) in self._pending.items() if deadline <= now]
        for key in expired:
            _, execution = self._pending.pop(key)
            execution.close()

    def advance(self, execution: PendingRun, resume: Callable) -> dict:
        try:
            approval = resume()
        except StopIteration as finished:
            return {"response": finished.value}
        except Exception:
            execution.close()
            raise

        with self._lock:
            self._expire()
            if len(self._pending) >= 16:
                execution.close()
                raise OverflowError("Há muitas aprovações pendentes.")
            token = uuid4().hex
            self._pending[token] = (monotonic() + 300, execution)

        return {"approval": {"id": token, "tool": approval.tool, "arguments": approval.arguments}}

    def take(self, key: str) -> PendingRun | None:
        with self._lock:
            self._expire()
            found = self._pending.pop(key, None)
            return found[1] if found else None

    def close(self) -> None:
        with self._lock:
            for _, execution in self._pending.values():
                execution.close()
            self._pending.clear()
