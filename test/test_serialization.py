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


def test_restore_fails_on_topology_mismatch():
    machine = _duplicate_name_machine()
    data = snapshot(machine)

    changed = StateMachine('root')
    only = State('branch')
    changed.add_state(only, initial=True)
    changed.initialize()

    with pytest.raises(StateMachineException):
        restore(changed, data)
