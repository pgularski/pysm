from typing import Any, Deque, Optional

from .pysm import Event, StateMachine

class QueuedStateMachine(StateMachine):
    max_internal_steps: Optional[int]
    _internal_queue: Deque[Event]
    _external_queue: Deque[Event]
    _is_processing: bool
    def __init__(self, name: str,
                 max_internal_steps: Optional[int] = ...) -> None: ...
    def initialize(self, fire_events_on_init: bool = ...) -> None: ...
    def dispatch(self, event: Event) -> None: ...

class ThreadSafeQueuedStateMachine(QueuedStateMachine):
    _execution_lock: Any
    def __init__(self, name: str,
                 max_internal_steps: Optional[int] = ...) -> None: ...
    def initialize(self, fire_events_on_init: bool = ...) -> None: ...
    def dispatch(self, event: Event) -> None: ...
