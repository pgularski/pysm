import asyncio
from typing import Any, Deque, Optional

from .pysm import Event, StateMachine

class AsyncQueuedStateMachine(StateMachine):
    max_internal_steps: Optional[int]
    _internal_queue: Deque[Event]
    _external_queue: Deque[Event]
    _is_processing: bool
    _processing_task: Optional[asyncio.Task[Any]]
    _execution_lock: asyncio.Lock
    def __init__(self, name: str,
                 max_internal_steps: Optional[int] = ...) -> None: ...
    async def dispatch(self, event: Event) -> None: ...  # type: ignore[override]
    async def set_previous_leaf_state(  # type: ignore[override]
        self, event: Optional[Event] = ...) -> None: ...
    async def revert_to_previous_leaf_state(  # type: ignore[override]
        self, event: Optional[Event] = ...) -> None: ...
