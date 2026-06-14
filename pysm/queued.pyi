from typing import Optional

from .pysm import Event, StateMachine

class QueuedStateMachine(StateMachine):
    max_internal_steps: Optional[int]
    def __init__(self, name: str,
                 max_internal_steps: Optional[int] = ...) -> None: ...
    def dispatch(self, event: Event) -> None: ...

class ThreadSafeQueuedStateMachine(QueuedStateMachine):
    def __init__(self, name: str,
                 max_internal_steps: Optional[int] = ...) -> None: ...
    def dispatch(self, event: Event) -> None: ...
