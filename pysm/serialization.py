'''Optional snapshot/restore helpers for pysm state machines.'''
from collections import deque
from typing import Any, Deque, Dict, Iterable, List, Optional, Tuple, cast

from .pysm import Stack, State, StateMachine, StateMachineException


SNAPSHOT_VERSION = 1
Path = List[str]
PathKey = Tuple[str, ...]
SnapshotData = Dict[str, Any]
MachineData = Dict[str, Any]


def snapshot(machine: StateMachine,
             metadata: Optional[Any] = None) -> SnapshotData:
    '''Return a plain-data snapshot of a configured state machine graph.'''
    root = machine.root_machine
    _validate_unique_sibling_names(root)
    machines = _iter_machines(root)
    states_data = [_state_path(state) for state in _iter_states(root)]
    machines_data: List[MachineData] = []
    leaf_state = root._leaf_state
    leaf_state_stack = [
        _state_path(state)
        for state in cast(Iterable[State], root.leaf_state_stack.deque)
    ]
    data: SnapshotData = {
        'version': SNAPSHOT_VERSION,
        'root': _state_path(root),
        'states': states_data,
        'machines': machines_data,
        'leaf_state': _state_path(leaf_state)
        if leaf_state is not None else None,
        'leaf_state_stack': leaf_state_stack,
    }
    if metadata is not None:
        data['metadata'] = metadata

    for item in machines:
        machines_data.append({
            'path': _state_path(item),
            'state': _state_path(item.state) if item.state is not None else None,
            'state_stack': [
                _state_path(state)
                for state in cast(Iterable[State], item.state_stack.deque)
            ],
        })

    states_data.sort()
    machines_data.sort(key=lambda item: item['path'])
    return data


def restore(machine: StateMachine, data: SnapshotData) -> StateMachine:
    '''Restore ``machine`` from a snapshot created by :func:`snapshot`.

    The machine graph must already be constructed and initialized. Restore is
    strict about topology so stale snapshots fail loudly instead of silently
    restoring to the wrong state.
    '''
    root = machine.root_machine
    if data.get('version') != SNAPSHOT_VERSION:
        raise StateMachineException('Unsupported snapshot version: {0}'.format(
            data.get('version')))
    if data.get('root') != _state_path(root):
        raise StateMachineException('Snapshot root does not match machine root')

    _validate_topology(root, data)
    _validate_active_state_paths(root, data)

    for machine_data in cast(List[MachineData], data.get('machines', [])):
        item = _resolve_machine_path(root, machine_data['path'])
        state_path = cast(Optional[Path], machine_data.get('state'))
        item.state = (_resolve_state_path(root, state_path)
                      if state_path is not None else None)
        _replace_stack(
            item.state_stack,
            [_resolve_state_path(root, path)
             for path in cast(List[Path], machine_data.get('state_stack', []))])

    leaf_path = cast(Optional[Path], data.get('leaf_state'))
    root._leaf_state = (_resolve_state_path(root, leaf_path)
                        if leaf_path is not None else None)
    _replace_stack(
        root.leaf_state_stack,
        [_resolve_state_path(root, path)
         for path in cast(List[Path], data.get('leaf_state_stack', []))])
    return machine


def _iter_states(root: StateMachine) -> Iterable[State]:
    queue: Deque[State] = deque([root])
    while queue:
        state = queue.popleft()
        yield state
        if isinstance(state, StateMachine):
            children = sorted(
                cast(Iterable[State], state.states),
                key=lambda item: item.name)
            queue.extend(children)


def _iter_machines(root: StateMachine) -> List[StateMachine]:
    return [state for state in _iter_states(root)
            if isinstance(state, StateMachine)]


def _state_path(state: State) -> Path:
    path: Path = []
    item = state
    while item is not None:
        path.append(item.name)
        item = item.parent
    return list(reversed(path))


def _resolve_machine_path(root: StateMachine, path: Path) -> StateMachine:
    state = _resolve_state_path(root, path)
    if not isinstance(state, StateMachine):
        raise StateMachineException(
            'Path does not point to a state machine: {0}'.format(path))
    return state


def _resolve_state_path(root: StateMachine, path: Path) -> State:
    if not path:
        raise StateMachineException('State path cannot be empty')
    if path[0] != root.name:
        raise StateMachineException(
            'State path {0} does not start at root {1}'.format(
                path, root.name))

    state = root
    for name in path[1:]:
        if not isinstance(state, StateMachine):
            raise StateMachineException(
                'State path descends through non-machine state: {0}'.format(
                    path))
        matches = [
            child for child in cast(Iterable[State], state.states)
            if child.name == name
        ]
        if not matches:
            raise StateMachineException('Unknown state path: {0}'.format(path))
        if len(matches) > 1:
            raise StateMachineException('Ambiguous state path: {0}'.format(
                path))
        state = matches[0]
    return state


def _replace_stack(stack: Stack, states: Iterable[State]) -> None:
    maxlen = getattr(stack.deque, 'maxlen', StateMachine.STACK_SIZE)
    stack.deque = deque(maxlen=maxlen)
    for state in states:
        stack.push(state)


def _validate_topology(root: StateMachine, data: SnapshotData) -> None:
    expected_states = sorted(cast(List[Path], data.get('states', [])))
    actual_states = sorted(_state_path(state) for state in _iter_states(root))
    if expected_states != actual_states:
        raise StateMachineException('Snapshot topology does not match machine')

    expected_machines = sorted(
        cast(Path, item['path'])
        for item in cast(List[MachineData], data.get('machines', [])))
    actual_machines = sorted(_state_path(item) for item in _iter_machines(root))
    if expected_machines != actual_machines:
        raise StateMachineException('Snapshot machines do not match machine')

    _validate_unique_sibling_names(root)


def _validate_active_state_paths(
        root: StateMachine, data: SnapshotData) -> None:
    machines: Dict[PathKey, MachineData] = {}
    for machine_data in cast(List[MachineData], data.get('machines', [])):
        path = tuple(cast(Path, machine_data['path']))
        machine = _resolve_machine_path(root, machine_data['path'])
        machines[path] = machine_data

        state_path = cast(Optional[Path], machine_data.get('state'))
        if state_path is not None:
            state = _resolve_state_path(root, state_path)
            if state.parent is not machine:
                raise StateMachineException(
                    'Snapshot state is not a child of machine: {0}'.format(
                        state_path))

        for stack_path in cast(List[Path], machine_data.get('state_stack', [])):
            state = _resolve_state_path(root, stack_path)
            if state.parent is not machine:
                raise StateMachineException(
                    'Snapshot stack state is not a child of machine: {0}'
                    .format(stack_path))

    expected_leaf = _expected_leaf_path_from_machine_states(
        tuple(cast(Path, data['root'])), machines)
    actual_leaf = cast(Optional[Path], data.get('leaf_state'))
    if ((actual_leaf is None and expected_leaf is not None) or
            (actual_leaf is not None and tuple(actual_leaf) != expected_leaf)):
        raise StateMachineException(
            'Snapshot leaf state does not match active machine states')


def _expected_leaf_path_from_machine_states(
        root_path: PathKey,
        machines: Dict[PathKey, MachineData]) -> Optional[PathKey]:
    machine_data = machines[root_path]
    state_path = cast(Optional[Path], machine_data.get('state'))
    if state_path is None:
        return None

    leaf_path = tuple(state_path)
    while leaf_path in machines:
        child_data = machines[leaf_path]
        child_state_path = cast(Optional[Path], child_data.get('state'))
        if child_state_path is None:
            break
        leaf_path = tuple(child_state_path)
    return leaf_path


def _validate_unique_sibling_names(root: StateMachine) -> None:
    for state in _iter_states(root):
        if not isinstance(state, StateMachine):
            continue
        names: Dict[str, int] = {}
        for child in cast(Iterable[State], state.states):
            names.setdefault(child.name, 0)
            names[child.name] += 1
        duplicates = [name for name, count in names.items() if count > 1]
        if duplicates:
            raise StateMachineException(
                'Ambiguous sibling state names under {0}: {1}'.format(
                    _state_path(state), duplicates))
