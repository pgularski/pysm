import pytest

from pysm import Event, StateMachineException
from pysm.builder import StateMachineBuilder


def test_builder_constructs_flat_machine():
    machine = (StateMachineBuilder('toggle')
               .state('off', initial=True)
               .state('on')
               .transition('off', 'on', events=['turn_on'])
               .transition('on', 'off', events=['turn_off'])
               .build())

    machine.dispatch(Event('turn_on'))
    assert machine.leaf_state.name == 'on'
    machine.dispatch(Event('turn_off'))
    assert machine.leaf_state.name == 'off'


def test_builder_uses_paths_to_resolve_nested_states():
    machine = (StateMachineBuilder('oven')
               .machine('door_closed', initial=True)
               .state('off', initial=True, parent_path='door_closed')
               .machine('heating', parent_path='door_closed')
               .state('baking', initial=True, parent_path='heating')
               .transition('off', 'baking', events=['bake'])
               .build())

    machine.dispatch(Event('bake'))

    assert machine.leaf_state.name == 'baking'
    assert machine.leaf_state.parent.name == 'heating'


def test_builder_rejects_ambiguous_short_paths():
    builder = (StateMachineBuilder('root')
               .machine('left', initial=True)
               .state('leaf', initial=True, parent_path='left')
               .machine('right')
               .state('leaf', initial=True, parent_path='right'))

    with pytest.raises(StateMachineException):
        builder.transition('leaf', 'right/leaf', events=['go'])
