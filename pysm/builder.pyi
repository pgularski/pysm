from typing import Any, Callable, Hashable, Iterable, Optional

from .pysm import StateMachine

_Callback = Callable[[Any, Any], Any]

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
        action: Optional[_Callback] = ...,
        condition: Optional[_Callback] = ...,
        before: Optional[_Callback] = ...,
        after: Optional[_Callback] = ...,
    ) -> StateMachineBuilder: ...
    def build(self, initialize: bool = ...) -> StateMachine: ...
