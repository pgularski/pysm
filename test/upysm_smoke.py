import sys

sys.path.insert(0, '.')

from pysm import Event, Stack, State, StateMachine


def test_simple_state_machine():
    machine = StateMachine('toggle')
    off = State('off')
    on = State('on')

    machine.add_state(off, initial=True)
    machine.add_state(on)
    machine.add_transition(off, on, events=['turn_on'])
    machine.add_transition(on, off, events=['turn_off'])
    machine.initialize()

    assert machine.state is off
    assert machine.leaf_state is off

    machine.dispatch(Event('turn_on'))
    assert machine.state is on
    assert machine.leaf_state is on

    machine.dispatch(Event('turn_off'))
    assert machine.state is off
    assert machine.leaf_state is off


def test_nested_state_machine():
    oven = StateMachine('oven')
    closed = StateMachine('closed')
    opened = State('opened')
    off = State('off')
    heating = StateMachine('heating')
    baking = State('baking')

    oven.add_state(closed, initial=True)
    oven.add_state(opened)
    closed.add_state(off, initial=True)
    closed.add_state(heating)
    heating.add_state(baking, initial=True)
    oven.add_transition(closed, baking, events=['bake'])
    oven.add_transition(closed, opened, events=['open'])
    oven.initialize()

    assert oven.state is closed
    assert closed.state is off
    assert oven.leaf_state is off

    oven.dispatch(Event('bake'))
    assert oven.state is closed
    assert closed.state is heating
    assert heating.state is baking
    assert oven.leaf_state is baking

    oven.dispatch(Event('open'))
    assert oven.state is opened
    assert oven.leaf_state is opened


def test_initial_enter_events():
    calls = []

    def on_enter(state, event):
        calls.append(state.name)
        assert event.name == 'enter'

    machine = StateMachine('root')
    child = StateMachine('child')
    leaf = State('leaf')
    child.handlers = {'enter': on_enter}
    leaf.handlers = {'enter': on_enter}

    machine.add_state(child, initial=True)
    child.add_state(leaf, initial=True)
    machine.initialize(fire_events_on_init=True)

    assert calls == ['child', 'leaf']


def test_history_and_stack_maxlen():
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
    assert [state.name for state in machine.leaf_state_stack.deque] == [
        'off',
        'on',
    ]

    stack = Stack(maxlen=2)
    stack.push(1)
    stack.push(2)
    stack.push(3)
    assert list(stack.deque) == [2, 3]
    assert stack.pop() == 3
    assert stack.pop() == 2


test_simple_state_machine()
test_nested_state_machine()
test_initial_enter_events()
test_history_and_stack_maxlen()
print('upysm smoke ok')
