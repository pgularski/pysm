'''Optional fluent builder for pysm state machines.'''
from typing import Any, Hashable, Dict, Iterable, Optional, Tuple, Type, Union

from .pysm import State, StateMachine, StateMachineException


Path = Tuple[str, ...]
PathInput = Union[str, Iterable[str]]
ValueInput = Union[str, Iterable[Hashable]]


class StateMachineBuilder(object):
    '''Small opt-in helper that builds machines through the public core API.'''

    def __init__(
            self, name: str,
            machine_class: Type[StateMachine] = StateMachine,
            state_class: Type[State] = State) -> None:
        self.root = machine_class(name)
        self.machine_class = machine_class
        self.state_class = state_class
        self._states: Dict[Path, State] = {(name,): self.root}

    def state(
            self, name: str, initial: bool = False,
            parent_path: Optional[PathInput] = None) -> 'StateMachineBuilder':
        parent = self._resolve_machine(parent_path)
        path = self._child_path(parent, name)
        self._ensure_new_path(path)
        state = self.state_class(name)
        parent.add_state(state, initial=initial)
        self._states[path] = state
        return self

    def machine(
            self, name: str, initial: bool = False,
            parent_path: Optional[PathInput] = None) -> 'StateMachineBuilder':
        parent = self._resolve_machine(parent_path)
        path = self._child_path(parent, name)
        self._ensure_new_path(path)
        machine = self.machine_class(name)
        parent.add_state(machine, initial=initial)
        self._states[path] = machine
        return self

    def transition(
            self, from_path: PathInput, to_path: Optional[PathInput],
            events: ValueInput, input: Optional[ValueInput] = None,
            action: Any = None, condition: Any = None, before: Any = None,
            after: Any = None) -> 'StateMachineBuilder':
        from_state = self._resolve_state(from_path)
        to_state = None if to_path is None else self._resolve_state(to_path)
        events = self._normalize_values(events)
        if input is not None:
            input = self._normalize_values(input)
        machine = from_state.parent
        if machine is None:
            raise StateMachineException(
                'Cannot add a transition from the root machine')
        machine.add_transition(
            from_state, to_state, events, input=input, action=action,
            condition=condition, before=before, after=after)
        return self

    def build(self, initialize: bool = True) -> StateMachine:
        if initialize:
            self.root.initialize()
        return self.root

    def _resolve_machine(self, path: Optional[PathInput]) -> StateMachine:
        if path is None:
            return self.root
        state = self._resolve_state(path)
        if not isinstance(state, StateMachine):
            raise StateMachineException(
                'Path does not point to a state machine: {0}'.format(path))
        return state

    def _resolve_state(self, path: PathInput) -> State:
        parts = self._normalize_path(path)
        if parts in self._states:
            return self._states[parts]

        matches = [state for key, state in self._states.items()
                   if key[-len(parts):] == parts]
        if not matches:
            raise StateMachineException('Unknown state path: {0}'.format(path))
        if len(matches) > 1:
            raise StateMachineException('Ambiguous state path: {0}'.format(
                path))
        return matches[0]

    def _child_path(self, parent: StateMachine, name: str) -> Path:
        return self._path_for(parent) + (name,)

    def _path_for(self, state: State) -> Path:
        for path, item in self._states.items():
            if item is state:
                return path
        raise StateMachineException('Unknown state: {0}'.format(state.name))

    def _ensure_new_path(self, path: Path) -> None:
        if path in self._states:
            raise StateMachineException('State path already exists: {0}'.format(
                path))

    def _normalize_path(self, path: PathInput) -> Path:
        if isinstance(path, tuple):
            return path
        if isinstance(path, list):
            return tuple(path)
        if isinstance(path, str):
            if '/' in path:
                return tuple(part for part in path.split('/') if part)
            return (path,)
        raise StateMachineException('Unsupported state path: {0}'.format(path))

    def _normalize_values(self, values: ValueInput) -> Iterable[Hashable]:
        if isinstance(values, str):
            return [values]
        return values
