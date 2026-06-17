import pytest

from pysm import Event, State, StateMachine, StateMachineException
from pysm.serialization import restore, snapshot


def _duplicate_name_machine():
    machine = StateMachine('root')
    left = StateMachine('branch')
    right = StateMachine('other')
    left_leaf = State('leaf')
    right_leaf = State('leaf')

    machine.add_state(left, initial=True)
    machine.add_state(right)
    left.add_state(left_leaf, initial=True)
    right.add_state(right_leaf, initial=True)
    machine.add_transition(left, right_leaf, events=['right'])
    machine.initialize()
    return machine


def test_snapshot_restore_uses_paths_for_duplicate_names_in_different_branches():
    machine = _duplicate_name_machine()
    machine.dispatch(Event('right'))
    data = snapshot(machine)

    restored = _duplicate_name_machine()
    restore(restored, data)

    assert restored.leaf_state.name == 'leaf'
    assert restored.leaf_state.parent.name == 'other'


def test_snapshot_restore_restores_history_stack():
    machine = StateMachine('m')
    off = State('off')
    on = State('on')
    machine.add_state(off, initial=True)
    machine.add_state(on)
    machine.add_transition(off, on, events=['on'])
    machine.add_transition(on, off, events=['off'])
    machine.initialize()
    machine.dispatch(Event('on'))
    machine.dispatch(Event('off'))

    data = snapshot(machine)
    restored = StateMachine('m')
    restored_off = State('off')
    restored_on = State('on')
    restored.add_state(restored_off, initial=True)
    restored.add_state(restored_on)
    restored.add_transition(restored_off, restored_on, events=['on'])
    restored.add_transition(restored_on, restored_off, events=['off'])
    restored.initialize()

    restore(restored, data)

    assert restored.leaf_state is restored_off
    assert [state.name for state in restored.leaf_state_stack.deque] == [
        'off',
        'on',
    ]


def test_snapshot_restore_does_not_serialize_user_pda_stack():
    machine = StateMachine('root')
    child = StateMachine('child')
    leaf = State('leaf')
    machine.add_state(child, initial=True)
    child.add_state(leaf, initial=True)
    machine.initialize()
    machine.stack.push({'domain': 'root'})
    child.stack.push({'domain': 'child'})

    data = snapshot(machine)

    assert 'stack' not in data
    assert all('stack' not in item for item in data['machines'])

    restored = StateMachine('root')
    restored_child = StateMachine('child')
    restored_leaf = State('leaf')
    restored.add_state(restored_child, initial=True)
    restored_child.add_state(restored_leaf, initial=True)
    restored.initialize()
    restored.stack.push('keep root stack')
    restored_child.stack.push('keep child stack')

    restore(restored, data)

    assert list(restored.stack.deque) == ['keep root stack']
    assert list(restored_child.stack.deque) == ['keep child stack']


def _issue_8_machine():
    machine = StateMachine('device')
    active = StateMachine('active')
    asleep = State('asleep')
    idle = State('idle')
    running = State('running')

    machine.add_state(active, initial=True)
    machine.add_state(asleep)
    active.add_state(idle, initial=True)
    active.add_state(running)
    active.add_transition(idle, running, events=['start'])
    machine.add_transition(active, asleep, events=['sleep'])
    machine.initialize()

    return machine, {
        'active': active,
        'asleep': asleep,
        'idle': idle,
        'running': running,
    }


def test_issue_8_snapshot_restore_recovers_state_history_after_rebuild():
    machine, _ = _issue_8_machine()
    machine.dispatch(Event('start'))
    machine.dispatch(Event('sleep'))

    data = snapshot(machine)

    restored, restored_states = _issue_8_machine()
    restore(restored, data)

    assert restored.leaf_state is restored_states['asleep']
    assert restored.state is restored_states['asleep']
    assert restored_states['active'].state is restored_states['idle']
    assert [state.name for state in restored.state_stack.deque] == ['active']
    assert [state.name for state in
            restored_states['active'].state_stack.deque] == [
                'idle',
                'running',
            ]
    assert [state.name for state in restored.leaf_state_stack.deque] == [
        'idle',
        'running',
    ]

    restored.set_previous_leaf_state(Event('wake'))

    assert restored.leaf_state is restored_states['running']
    assert restored.state is restored_states['active']
    assert restored_states['active'].state is restored_states['running']
    assert [state.name for state in restored.leaf_state_stack.deque] == [
        'idle',
        'running',
        'asleep',
    ]


def test_restore_fails_on_topology_mismatch():
    machine = _duplicate_name_machine()
    data = snapshot(machine)

    changed = StateMachine('root')
    only = State('branch')
    changed.add_state(only, initial=True)
    changed.initialize()

    with pytest.raises(StateMachineException):
        restore(changed, data)


def test_snapshot_fails_on_duplicate_sibling_names():
    machine = StateMachine('root')
    first = State('duplicate')
    second = State('duplicate')
    machine.add_state(first, initial=True)
    machine.add_state(second)
    machine.initialize()

    with pytest.raises(StateMachineException, match='Ambiguous sibling'):
        snapshot(machine)


def test_restore_fails_when_machine_state_is_not_a_direct_child():
    machine = StateMachine('root')
    child = StateMachine('child')
    leaf = State('leaf')
    outsider = State('outsider')
    machine.add_state(child, initial=True)
    machine.add_state(outsider)
    child.add_state(leaf, initial=True)
    machine.initialize()

    data = snapshot(machine)
    for item in data['machines']:
        if item['path'] == ['root', 'child']:
            item['state'] = ['root', 'outsider']
            break

    restored = StateMachine('root')
    restored_child = StateMachine('child')
    restored_leaf = State('leaf')
    restored_outsider = State('outsider')
    restored.add_state(restored_child, initial=True)
    restored.add_state(restored_outsider)
    restored_child.add_state(restored_leaf, initial=True)
    restored.initialize()

    with pytest.raises(StateMachineException, match='not a child'):
        restore(restored, data)


def test_restore_fails_when_leaf_state_contradicts_machine_states():
    machine = StateMachine('root')
    child = StateMachine('child')
    leaf = State('leaf')
    outsider = State('outsider')
    machine.add_state(child, initial=True)
    machine.add_state(outsider)
    child.add_state(leaf, initial=True)
    machine.initialize()

    data = snapshot(machine)
    data['leaf_state'] = ['root', 'outsider']

    restored = StateMachine('root')
    restored_child = StateMachine('child')
    restored_leaf = State('leaf')
    restored_outsider = State('outsider')
    restored.add_state(restored_child, initial=True)
    restored.add_state(restored_outsider)
    restored_child.add_state(restored_leaf, initial=True)
    restored.initialize()

    with pytest.raises(StateMachineException, match='leaf state'):
        restore(restored, data)
