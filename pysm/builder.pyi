from typing import Any, Hashable, Iterable, Optional

from .pysm import Callback, StateMachine

class StateMachineBuilder(object):
    root: StateMachine
    def __init__(self, name: str, machine_class: Any = ...,
                 state_class: Any = ...) -> None: ...
    def state(self, name: str, initial: bool = ...,
              parent_path: Optional[Any] = ...) -> StateMachineBuilder: ...
    def machine(self, name: str, initial: bool = ...,
                parent_path: Optional[Any] = ...) -> StateMachineBuilder: ...
    def transition(
        self,
        from_path: Any,
        to_path: Optional[Any],
        events: Iterable[Hashable],
        input: Optional[Iterable[Hashable]] = ...,
        action: Optional[Callback] = ...,
        condition: Optional[Callback] = ...,
        before: Optional[Callback] = ...,
        after: Optional[Callback] = ...,
    ) -> StateMachineBuilder: ...
    def build(self, initialize: bool = ...) -> StateMachine: ...
