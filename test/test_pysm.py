import inspect
import mock
import pytest
import pysm
import logging
from pysm import Event, State, StateMachine, StateMachineException, Stack, log
_e = Event

# log.setLevel(logging.DEBUG)


def test_new_sm():
    run_call_mock = mock.Mock()
    stop_call_mock = mock.Mock()
    idling_mock = mock.Mock()
    running_mock = mock.Mock()
    action_mock = mock.Mock()

    class Idling(State):
        # @event('run')
        def run(self, event):
            run_call_mock(self, event.input, event.cargo)

        def do(self, event):
            entity = event.cargo['entity']
            entity.do()

        def on_enter(self, event):
            idling_mock(self, 'on_enter')

        def on_exit(self, event):
            idling_mock(self, 'on_exit')

        def register_handlers(self):
            self.handlers = {
                'run': self.run,
                'do': self.do,
                'enter': self.on_enter,
                'exit': self.on_exit,
            }

    def stop(event):
        stop_call_mock('stopping...', event.cargo)

    def do(event):
        entity = event.cargo['entity']
        entity.do()

    def enter(event):
        running_mock('running, enter')

    def exit(event):
        running_mock('running, exit')

    def update(event):
        print 'update', event

    def do_on_transition(event):
        action_mock('action on transition')

    class Entity(object):
        def do(self):
            print self, self.do

    idling = Idling('idling')
    running = State('running')
    running.handlers = {
        'stop': stop,
        'do': do,
        'update': update,
        'enter': enter,
        'exit': exit,
    }

    entity = Entity()

    sm = StateMachine('sm')
    sm.add_state(idling, initial=True)
    sm.add_state(running)
    sm.add_transition(idling, running, events=['run'], action=do_on_transition)
    sm.add_transition(running, idling, events=['stop'])
    sm.initialize()
    assert sm.state == idling
    sm.dispatch(_e('run'))
    assert sm.state == running
    assert run_call_mock.call_count == 1
    assert run_call_mock.call_args[0] == (idling, None, {})
    assert idling_mock.call_count == 1
    assert idling_mock.call_args[0] == (idling, 'on_exit')
    assert running_mock.call_count == 1
    assert running_mock.call_args[0] == ('running, enter',)
    assert action_mock.call_count == 1
    assert action_mock.call_args[0] == ('action on transition',)

    # Nothing should happen - running state has no 'run' handler
    sm.dispatch(_e('run'))
    assert sm.state == running
    assert run_call_mock.call_count == 1
    assert run_call_mock.call_args[0] == (idling, None, {})

    sm.dispatch(_e('stop'))
    assert sm.state == idling
    assert idling_mock.call_count == 2
    assert idling_mock.call_args[0] == (idling, 'on_enter')
    assert running_mock.call_count == 2
    assert running_mock.call_args[0] == ('running, exit',)
    assert stop_call_mock.call_count == 1
    assert stop_call_mock.call_args[0] == ('stopping...', {})

    # Unknown events must be ignored
    sm.dispatch(_e('blah'))
    sm.dispatch(_e('blah blah'))
    assert sm.state == idling


def test_conditions():
    class Bool(object):
        def __init__(self):
            self.value = True

        def get(self, event):
            return self.value

    bool_a = Bool()
    bool_b = Bool()

    def run(event):
        print 'runninng...'

    idling = State('idling')
    running = State('running')
    stopped = State('stopped')
    broken = State('broken')

    sm = StateMachine('sm')
    sm.add_state(idling, initial=True)
    sm.add_state(running)
    sm.add_state(stopped)
    sm.add_state(broken)
    sm.add_transition(idling, running, events=['run'], condition=bool_a.get)
    sm.add_transition(idling, stopped, events=['run'], condition=bool_b.get)
    sm.add_transition(running, idling, events=['idle'])
    sm.add_transition(stopped, idling, events=['idle'])
    sm.add_transition(broken, idling, events=['idle'])
    sm.initialize()

    # Expect no change
    bool_a.value = False
    bool_b.value = False
    assert sm.state == idling
    sm.dispatch(_e('run'))
    assert sm.state == idling
    sm.dispatch(_e('idle'))
    assert sm.state == idling

    # Expect first transition
    bool_a.value = True
    bool_b.value = False
    assert sm.state == idling
    sm.dispatch(_e('run'))
    assert sm.state == running
    sm.dispatch(_e('idle'))
    assert sm.state == idling

    # Expect first transition
    bool_a.value = True
    bool_b.value = True
    assert sm.state == idling
    sm.dispatch(_e('run'))
    assert sm.state == running
    sm.dispatch(_e('idle'))
    assert sm.state == idling

    # Expect second  transition
    bool_a.value = False
    bool_b.value = True
    assert sm.state == idling
    sm.dispatch(_e('run'))
    assert sm.state == stopped
    sm.dispatch(_e('idle'))
    assert sm.state == idling

    sm.add_transition(idling, broken, events=['run'])
    # Expect transition to state without condition
    bool_a.value = False
    bool_b.value = False
    assert sm.state == idling
    sm.dispatch(_e('run'))
    assert sm.state == broken
    sm.dispatch(_e('idle'))
    assert sm.state == idling


def test_internal_transition():
    class Foo(object):
        def __init__(self):
            self.value = False
    foo = Foo()

    def on_enter(event):
        foo.value = True

    def on_exit(event):
        foo.value = True

    idling = State('idling')
    idling.handlers = {
        'enter': on_enter,
        'exit': on_exit,
    }

    sm = StateMachine('sm')
    sm.add_state(idling, initial=True)
    sm.add_transition(idling, None, events=['internal_transition'])
    sm.add_transition(idling, idling, events=['external_transition'])
    sm.initialize()
    sm.dispatch(_e('internal_transition'))
    assert foo.value is False
    sm.dispatch(_e('external_transition'))
    assert foo.value is True


def test_hsm_init():
    sm = StateMachine('sm')
    s0 = StateMachine('s0')
    s1 = StateMachine('s1')
    s2 = StateMachine('s2')
    s11 = State('s11')
    s12 = State('s12')
    sm.add_state(s0, initial=True)
    s0.add_state(s1, initial=True)
    s1.add_state(s11, initial=True)
    sm.initialize()
    assert sm.state == s0
    assert s0.state == s1
    assert s1.state == s11
    assert sm.leaf_state == s11


def test_hsm_get_transition():
    sm = StateMachine('sm')
    s0 = StateMachine('s0')
    s1 = StateMachine('s1')
    s2 = StateMachine('s2')
    s0.add_state(s1)
    s0.add_state(s2)
    s0.add_transition(s1, s2, events='a')
    s11 = State('s11')
    s12 = State('s12')
    sm.add_state(s0, initial=True)
    s0.add_state(s1, initial=True)
    s1.add_state(s11, initial=True)
    sm.initialize()
    transition = sm.get_transition(_e('a'))
    assert s1 == transition['from_state']
    assert s2 == transition['to_state']


def test_hsm_simple_hsm_transition():
    sm = StateMachine('sm')
    s0 = StateMachine('s0')
    s1 = StateMachine('s1')
    s2 = StateMachine('s2')
    s0.add_state(s1)
    s0.add_state(s2)
    s0.add_transition(s1, s2, events='a')
    s0.add_transition(s2, s1, events='a')
    s11 = State('s11')
    s12 = State('s12')
    sm.add_state(s0, initial=True)
    s0.add_state(s1, initial=True)
    s0.add_state(s2)
    s1.add_state(s11, initial=True)
    sm.initialize()
    assert sm.state == s0
    assert s0.state == s1
    assert s1.state == s11
    assert sm.leaf_state == s11

    sm.dispatch(_e('a'))
    assert sm.state == s0
    assert s0.state == s2
    assert sm.leaf_state == s2

    sm.dispatch(_e('a'))
    assert sm.state == s0
    assert s0.state == s1
    assert s1.state == s11
    assert sm.leaf_state == s11


def test_enter_exit_on_transitions():
    test_list = []

    def on_enter(event):
        state = inspect.currentframe().f_back.f_locals['self']
        # print 'entering', state
        test_list.append(('enter', state))

    def on_exit(event):
        state = inspect.currentframe().f_back.f_locals['self']
        # print 'exiting', state
        test_list.append(('exit', state))

    m = StateMachine('m')
    # exit = m.add_state('exit', terminal=True)
    s0 = StateMachine('s0')
    s1 = StateMachine('s1')
    s2 = StateMachine('s2')

    s11 = State('s11')
    s21 = StateMachine('s21')
    s211 = State('s211')
    s212 = State('s212')

    m.add_state(s0, initial=True)
    s0.add_state(s1, initial=True)
    s0.add_state(s2)
    s1.add_state(s11, initial=True)
    s2.add_state(s21, initial=True)
    s21.add_state(s211, initial=True)
    s21.add_state(s212)

    states = [m, s0, s1, s11, s2, s21, s211, s212]
    for state in states:
        state.handlers = {'enter': on_enter, 'exit': on_exit}

    s0.add_transition(s1, s1, events='a')
    s0.add_transition(s1, s11, events='b')
    s2.add_transition(s21, s211, events='b')
    s0.add_transition(s1, s2, events='c')
    s0.add_transition(s2, s1, events='c')
    s0.add_transition(s1, s0, events='d')
    s21.add_transition(s211, s21, events='d')
    m.add_transition(s0, s211, events='e')
    m.add_transition(s0, s212, events='z')
    s0.add_transition(s2, s11, events='f')
    s0.add_transition(s1, s211, events='f')
    s1.add_transition(s11, s211, events='g')
    s21.add_transition(s211, s0, events='g')

    m.initialize()

    test_list[:] = []
    m.dispatch(_e('a'))
    assert test_list == [('exit', s11), ('exit', s1), ('enter', s1), ('enter', s11)]

    test_list[:] = []
    m.dispatch(_e('b'))
    assert test_list == [('exit', s11), ('enter', s11)]
    m.dispatch(_e('c'))
    test_list[:] = []
    m.dispatch(_e('b'))
    assert test_list == [('exit', s211), ('enter', s211)]
    m.dispatch(_e('c'))

    test_list[:] = []
    m.dispatch(_e('c'))
    assert test_list == [('exit', s11), ('exit', s1), ('enter', s2), ('enter', s21), ('enter', s211)]
    test_list[:] = []
    m.dispatch(_e('c'))
    assert test_list == [('exit', s211), ('exit', s21),  ('exit', s2), ('enter', s1), ('enter', s11)]

    test_list[:] = []
    m.dispatch(_e('d'))
    assert test_list == [('exit', s11), ('exit', s1),  ('enter', s1), ('enter', s11)]
    m.dispatch(_e('c'))
    test_list[:] = []
    m.dispatch(_e('d'))
    assert test_list == [('exit', s211), ('enter', s211)]
    m.dispatch(_e('c'))

    test_list[:] = []
    m.dispatch(_e('e'))
    assert test_list == [('exit', s11), ('exit', s1),  ('enter', s2), ('enter', s21), ('enter', s211)]
    test_list[:] = []
    m.dispatch(_e('e'))
    assert test_list == [('exit', s211), ('exit', s21),  ('exit', s2), ('enter', s2), ('enter', s21), ('enter', s211)]

    test_list[:] = []
    m.dispatch(_e('f'))
    assert test_list == [('exit', s211), ('exit', s21),  ('exit', s2), ('enter', s1), ('enter', s11)]
    test_list[:] = []
    m.dispatch(_e('f'))
    assert test_list == [('exit', s11), ('exit', s1),  ('enter', s2), ('enter', s21), ('enter', s211)]

    test_list[:] = []
    m.dispatch(_e('g'))
    assert test_list == [('exit', s211), ('exit', s21),  ('exit', s2), ('enter', s1), ('enter', s11)]
    test_list[:] = []
    m.dispatch(_e('g'))
    assert test_list == [('exit', s11), ('exit', s1),  ('enter', s2), ('enter', s21), ('enter', s211)]

    test_list[:] = []
    m.dispatch(_e('z'))
    assert test_list == [('exit', s211), ('exit', s21), ('exit', s2), ('enter', s2), ('enter', s21), ('enter', s212)]
    assert m.leaf_state == s212

    test_list[:] = []
    m.dispatch(_e('c'))
    assert test_list == [('exit', s212), ('exit', s21), ('exit', s2), ('enter', s1), ('enter', s11)]
    assert m.leaf_state == s11

    test_list[:] = []
    m.dispatch(_e('g'))
    assert m.leaf_state == s211
    assert test_list == [('exit', s11), ('exit', s1),  ('enter', s2), ('enter', s21), ('enter', s211)]
    assert m.leaf_state == s211


def test_internal_vs_external_transitions():
    test_list = []

    class Foo(object):
        value = True

    def on_enter(event):
        state = inspect.currentframe().f_back.f_locals['self']
        test_list.append(('enter', state))

    def on_exit(event):
        state = inspect.currentframe().f_back.f_locals['self']
        test_list.append(('exit', state))

    def set_foo(event):
        Foo.value = True
        test_list.append('set_foo')

    def unset_foo(event):
        Foo.value = False
        test_list.append('unset_foo')

    def action_i(event):
        test_list.append('action_i')
        return True

    def action_j(event):
        test_list.append('action_j')
        return True

    def action_k(event):
        test_list.append('action_k')
        return True

    def action_l(event):
        test_list.append('action_l')

    def action_m(event):
        test_list.append('action_m')

    def action_n(event):
        test_list.append('action_n')
        return True

    m = StateMachine('m')
    # exit = m.add_state('exit', terminal=True)
    s0 = StateMachine('s0')
    s1 = StateMachine('s1')
    s2 = StateMachine('s2')

    s11 = State('s11')
    s21 = StateMachine('s21')
    s211 = State('s211')
    s212 = State('s212')

    m.add_state(s0, initial=True)
    s0.add_state(s1, initial=True)
    s0.add_state(s2)
    s1.add_state(s11, initial=True)
    s2.add_state(s21, initial=True)
    s21.add_state(s211, initial=True)
    s21.add_state(s212)

    states = [m, s0, s1, s11, s2, s21, s211, s212]
    for state in states:
        state.handlers = {'enter': on_enter, 'exit': on_exit}

    s0.add_transition(s1, s1, events='a')
    s0.add_transition(s1, s11, events='b')
    s2.add_transition(s21, s211, events='b')
    s0.add_transition(s1, s2, events='c')
    s0.add_transition(s2, s1, events='c')
    s0.add_transition(s1, s0, events='d')
    s21.add_transition(s211, s21, events='d')
    m.add_transition(s0, s211, events='e')
    m.add_transition(s0, s212, events='z')
    s0.add_transition(s2, s11, events='f')
    s0.add_transition(s1, s211, events='f')
    s1.add_transition(s11, s211, events='g')
    s21.add_transition(s211, s0, events='g')

    m.initialize()

    # Internal transitions
    m.add_transition(s0, None, events='i', action=action_i)
    s0.add_transition(s1, None, events='j', action=action_j)
    s0.add_transition(s2, None, events='k', action=action_k)
    s1.add_transition(s11, None, events='n', action=action_n)
    s1.add_transition(s11, None, events='h',
                      condition=lambda e: Foo.value is True, action=unset_foo)
    s2.add_transition(s21, None, events='l',
                      condition=lambda e: Foo.value is True, action=action_l)
    s21.add_transition(s211, None, events='m', action=action_m)
    # External transition
    s2.add_transition(s21, s21, events='h',
                      condition=lambda e: Foo.value is False, action=set_foo)

    m.initialize()

    test_list[:] = []
    m.dispatch(_e('i'))
    assert test_list == ['action_i']
    assert m.leaf_state == s11

    test_list[:] = []
    m.dispatch(_e('j'))
    assert test_list == ['action_j']
    assert m.leaf_state == s11

    test_list[:] = []
    m.dispatch(_e('n'))
    assert test_list == ['action_n']
    assert m.leaf_state == s11

    # This transition toggles state between s11 and s211
    m.dispatch(_e('c'))
    assert m.leaf_state == s211

    test_list[:] = []
    m.dispatch(_e('i'))
    assert test_list == ['action_i']
    assert m.leaf_state == s211

    test_list[:] = []
    m.dispatch(_e('k'))
    assert test_list == ['action_k']
    assert m.leaf_state == s211

    test_list[:] = []
    m.dispatch(_e('m'))
    assert test_list == ['action_m']
    assert m.leaf_state == s211

    test_list[:] = []
    m.dispatch(_e('n'))
    assert test_list == []
    assert m.leaf_state == s211

    # This transition toggles state between s11 and s211
    m.dispatch(_e('c'))
    assert m.leaf_state == s11

    test_list[:] = []
    assert Foo.value is True
    m.dispatch(_e('h'))
    assert Foo.value is False
    assert test_list == ['unset_foo']
    assert m.leaf_state == s11

    test_list[:] = []
    m.dispatch(_e('h'))
    assert test_list == []  # Do nothing if foo is False
    assert m.leaf_state == s11

    # This transition toggles state between s11 and s211
    m.dispatch(_e('c'))
    assert m.leaf_state == s211

    test_list[:] = []
    assert Foo.value is False
    m.dispatch(_e('h'))
    assert test_list == [('exit', s211), ('exit', s21), 'set_foo', ('enter', s21), ('enter', s211)]
    assert Foo.value is True
    assert m.leaf_state == s211

    test_list[:] = []
    m.dispatch(_e('h'))
    assert test_list == []
    assert m.leaf_state == s211


def test_add_transition_unknown_state():
    sm = StateMachine('sm')
    s1 = State('s1')
    s2 = State('s2')  # This state isn't added to sm
    s3 = StateMachine('s3')
    s31 = State('s31')
    s32 = State('s32')  # This state isn't added to s3

    sm.add_state(s1)
    sm.add_state(s3)
    s3.add_state(s31)

    with pytest.raises(StateMachineException) as exc:
        sm.add_transition(s1, s2, events='a')
    expected = (
        'Machine "sm" error: Unable to add transition to unknown state "s2"')
    assert expected in str(exc.value)

    with pytest.raises(StateMachineException) as exc:
        sm.add_transition(s2, s1, events='a')
    expected = (
        'Machine "sm" error: Unable to add transition from unknown state "s2"')
    assert expected in str(exc.value)

    with pytest.raises(StateMachineException) as exc:
        sm.add_transition(s1, s32, events='a')
    expected = (
        'Machine "sm" error: Unable to add transition to unknown state "s32"')
    assert expected in str(exc.value)

    with pytest.raises(StateMachineException) as exc:
        sm.add_transition(s32, s1, events='a')
    expected = (
        'Machine "sm" error: Unable to add transition from unknown state "s32"')
    assert expected in str(exc.value)


def test_events_not_iterable():
    sm = StateMachine('sm')
    s1 = State('s1')
    sm.add_state(s1)

    with pytest.raises(StateMachineException) as exc:
        sm.add_transition(s1, None, events=1)
    expected = (
        'Machine "sm" error: Unable to add transition, '
        'events is not iterable: 1')
    assert expected in str(exc.value)


def test_input_not_iterable():
    sm = StateMachine('sm')
    s1 = State('s1')
    sm.add_state(s1)

    with pytest.raises(StateMachineException) as exc:
        sm.add_transition(s1, None, events=[1], input=2)
    expected = (
        'Machine "sm" error: Unable to add transition, '
        'input is not iterable: 2')
    assert expected in str(exc.value)


def test_add_not_a_state_instance():
    class NotState(object):
        pass

    sm = StateMachine('sm')
    s1 = NotState()

    with pytest.raises(StateMachineException) as exc:
        sm.add_state(s1)
    expected = (
        'Machine "sm" error: Unable to add state of '
        'type <class \'test_pysm.NotState\'>')
    assert expected in str(exc.value)


def test_no_initial_state():
    sm = StateMachine('sm')
    s1 = State('s1')
    s2 = State('s2')
    try:
        sm.initialize()
    except StateMachineException as exc:
        assert not exc

    sm.add_state(s1)
    sm.add_state(s2)
    with pytest.raises(StateMachineException) as exc:
        sm.initialize()
    expected = ('Machine "sm" error: Machine "sm" has no initial state')
    assert expected in str(exc.value)


def test_many_initial_states():
    sm = StateMachine('sm')
    s1 = State('s1')
    s2 = State('s2')

    sm.add_state(s1, initial=True)
    with pytest.raises(StateMachineException) as exc:
        sm.add_state(s2, initial=True)
    expected = ('Machine "sm" error: Unable to set initial state to "s2". '
                'Initial state is already set to "s1"')
    assert expected in str(exc.value)


def test_add_state_that_is_already_added_anywhere_in_the_hsm():
    sm = StateMachine('sm')
    s1 = State('s1')
    s2 = State('s2')
    s3 = StateMachine('s3')
    s31 = State('s31')
    s32 = State('s32')

    sm.add_state(s1)
    sm.add_state(s2)
    sm.add_state(s3)
    s3.add_state(s31)
    s3.add_state(s32)

    with pytest.raises(StateMachineException) as exc:
        s3.add_state(s2)
    expected = ('Machine "s3" error: State "s2" is already added '
                'to machine "sm"')
    assert expected in str(exc.value)


def test_state_stack():
    sm = StateMachine('sm')
    s1 = State('s1')
    s2 = State('s2')
    s3 = StateMachine('s3')
    s31 = State('s31')
    s32 = State('s32')

    sm.add_state(s1, initial=True)
    sm.add_state(s2)
    sm.add_state(s3)
    s3.add_state(s31, initial=True)
    s3.add_state(s32)

    sm.add_transition(s1, s2, events=['s1->s2'])
    sm.add_transition(s2, s1, events=['s2->s1'])
    sm.add_transition(s1, s3, events=['a'])
    s3.add_transition(s31, s32, events=['b'])
    sm.initialize()

    assert sm.state == s1
    assert sm.leaf_state == s1

    sm.dispatch(_e('s1->s2'))
    assert sm.state == s2
    assert sm.leaf_state == s2
    assert list(sm.state_stack.deque) == [s1]

    sm.dispatch(_e('s2->s1'))
    assert sm.state == s1
    assert sm.leaf_state == s1
    assert list(sm.state_stack.deque) == [s1, s2]

    sm.dispatch(_e('a'))
    assert sm.state == s3
    assert sm.leaf_state == s31
    assert s3.leaf_state == s31
    assert list(sm.state_stack.deque) == [s1, s2, s1]
    assert list(s3.state_stack.deque) == []

    sm.dispatch(_e('b'))
    assert sm.state == s3
    assert sm.leaf_state == s32
    assert s3.state == s32
    assert s3.leaf_state == s32
    assert list(sm.state_stack.deque) == [s1, s2, s1]
    assert list(s3.state_stack.deque) == [s31]

    # Brute force rollback of the previous state
    s3.state = s3.state_stack.pop()
    sm.state = sm.state_stack.pop()
    assert sm.state == s1
    assert sm.leaf_state == s1
    assert s3.state == s31
    assert s3.leaf_state == s31
    assert list(sm.state_stack.deque) == [s1, s2]
    assert list(s3.state_stack.deque) == []


def test_state_stack_high_tree():
    sm = StateMachine('sm')
    s0 = StateMachine('s0')
    s01 = StateMachine('s01')
    s011 = StateMachine('s011')
    s0111 = State('s0111')
    s0112 = State('s0112')
    s0113 = StateMachine('s0113')
    s01131 = State('s01131')

    sm.add_state(s0, initial=True)
    s0.add_state(s01, initial=True)
    s01.add_state(s011, initial=True)
    s011.add_state(s0111, initial=True)
    s011.add_state(s0112)
    s011.add_state(s0113)
    s0113.add_state(s01131, initial=True)

    s011.add_transition(s0111, s0113, events=['a'])
    sm.initialize()

    assert sm.leaf_state == s0111
    sm.dispatch(_e('a'))
    assert list(sm.state_stack.deque) == []
    assert list(s0.state_stack.deque) == []
    assert list(s01.state_stack.deque) == []
    assert list(s011.state_stack.deque) == [s0111]
    assert list(s011.leaf_state_stack.deque) == []
    assert list(s0113.state_stack.deque) == []
    assert list(sm.leaf_state_stack.deque) == [s0111]


def test_stack():
    stack = Stack()
    stack.push(1)
    stack.push(2)
    stack.push(3)
    assert repr(stack) == '[1, 2, 3]'
    assert stack.peek() == 3
    assert repr(stack) == '[1, 2, 3]'
    assert stack.pop() == 3
    assert repr(stack) == '[1, 2]'
    assert stack.pop() == 2
    assert repr(stack) == '[1]'
    assert stack.pop() == 1
    assert repr(stack) == '[]'
    with pytest.raises(IndexError) as exc:
        stack.pop()
    expected = ('pop from an empty deque')
    assert expected in str(exc.value)

    tiny_stack = Stack(maxlen=2)
    tiny_stack.push(1)
    assert repr(tiny_stack) == '[1]'
    tiny_stack.push(2)
    assert repr(tiny_stack) == '[1, 2]'
    tiny_stack.push(3)
    assert repr(tiny_stack) == '[2, 3]'


def test_transition_from_and_to_machine_itself():
    sm = StateMachine('sm')
    s1 = State('s1')
    s2 = State('s2')
    sm.add_state(s1, initial=True)
    sm.add_state(s2)

    with pytest.raises(StateMachineException) as exc:
        sm.add_transition(sm, s1, events=['sm->s1'])
    expected = (
        'Machine "sm" error: Unable to add transition from unknown state "sm"')
    assert expected in str(exc.value)
    sm.add_transition(s1, sm, events=['s1->sm'])
    sm.initialize()

    assert sm.state == s1
    sm.dispatch(_e('sm->s1'))
    assert sm.state == s1
    assert list(sm.state_stack.deque) == []
    sm.dispatch(_e('s1->sm'))
    assert sm.state == s1
    assert list(sm.state_stack.deque) == [s1]
    sm.dispatch(_e('sm->s1'))
    assert sm.state == s1
    assert list(sm.state_stack.deque) == [s1]
    sm.dispatch(_e('s1->sm'))
    assert sm.state == s1
    assert list(sm.state_stack.deque) == [s1, s1]


def test_add_transition_event_with_input():
    sm = StateMachine('sm')
    s1 = State('s1')
    s2 = State('s2')
    s3 = State('s3')
    sm.add_state(s1, initial=True)
    sm.add_state(s2)
    sm.add_state(s3)

    sm.add_transition(s1, s2, events=['a'], input=['go_to_s2'])
    sm.add_transition(s1, s3, events=['a'], input=['go_to_s3'])
    sm.add_transition(s2, s1, events=['a'])
    sm.add_transition(s3, s1, events=['a'])
    sm.initialize()

    assert sm.state == s1
    sm.dispatch(_e('a', input='go_to_s2'))
    assert sm.state == s2
    sm.dispatch(_e('a'))
    assert sm.state == s1
    sm.dispatch(_e('a', input='go_to_s3'))
    assert sm.state == s3
    sm.dispatch(_e('a'))
    assert sm.state == s1


def test_event_repr():
    data = {'data_key': 'data_value'}
    event = _e('test_event', input='test_input', key='value', data=data)
    # WARNING: This may fail if Python implementation changes the ordering of
    # items in the dictionary. CPython should be fine though.
    expected = ("<Event test_event, input=test_input, cargo={'data':"
                " {'data_key': 'data_value'}, 'key': 'value'}")
    assert expected in repr(event)


def test_state_repr():
    state = State('test_state')
    expected = "State test_state (0x"
    assert expected in repr(state)


def test_transition_to_history():
    oven = StateMachine('Oven')
    door_closed = StateMachine('DoorClosed')
    door_open = State('DoorOpen')
    heating = StateMachine('Heating')
    toasting = State('Toasting')
    baking = State('Baking')
    off = State('Off')

    oven.add_state(door_closed, initial=True)
    oven.add_state(door_open)
    door_closed.add_state(off, initial=True)
    door_closed.add_state(heating)
    heating.add_state(baking, initial=True)
    heating.add_state(toasting)

    oven.add_transition(door_closed, toasting, events=['toast'])
    oven.add_transition(door_closed, baking, events=['bake'])
    oven.add_transition(door_closed, off, events=['off', 'timeout'])
    oven.add_transition(door_closed, door_open, events=['open'])

    door_open.handlers = {'close': lambda e: oven.set_previous_leaf_state()}

    oven.initialize()

    assert oven.leaf_state == off
    oven.dispatch(_e('open'))
    assert oven.leaf_state == door_open
    try:
        oven.dispatch(_e('close'))
    except Exception as exc:
        assert not exc
    assert oven.leaf_state == off
    assert list(oven.leaf_state_stack.deque) == [off, door_open]

    oven.dispatch(_e('bake'))
    assert oven.leaf_state == baking
    oven.dispatch(_e('open'))
    assert oven.leaf_state == door_open
    try:
        oven.dispatch(_e('close'))
    except Exception as exc:
        assert not exc
    assert oven.leaf_state == baking
    expected = [off, door_open, off, baking, door_open]
    assert list(oven.leaf_state_stack.deque) == expected


def test_set_previous_state_no_history():
    m = StateMachine('m')
    off = State('Off')
    m.add_state(off, initial=True)
    m.initialize()
    off.handlers = {'test_no_history': lambda e: m.set_previous_leaf_state()}

    assert m.leaf_state == off
    try:
        m.dispatch(_e('test_no_history'))
    except Exception as exc:
        assert not exc
    assert m.leaf_state == off
    assert list(m.leaf_state_stack.deque) == []


def test_revert_to_previous_state():
    m = StateMachine('m')
    off = State('Off')
    on = State('On')
    m.add_state(off, initial=True)
    m.add_state(on)
    m.add_transition(on, off, events=['off'])
    m.add_transition(off, on, events=['on'])
    m.initialize()
    off.handlers = {
        'test_no_history': lambda e: m.revert_to_previous_leaf_state()
    }

    assert m.leaf_state == off
    try:
        m.dispatch(_e('test_no_history'))
    except Exception as exc:
        assert not exc
    assert m.leaf_state == off
    assert list(m.leaf_state_stack.deque) == []

    m.dispatch(_e('on'))
    assert m.leaf_state == on
    assert list(m.leaf_state_stack.deque) == [off]
    m.dispatch(_e('off'))
    assert m.leaf_state == off
    assert list(m.leaf_state_stack.deque) == [off, on]

    try:
        m.dispatch(_e('test_no_history'))
    except Exception as exc:
        assert not exc
    assert m.leaf_state == on
    assert list(m.leaf_state_stack.deque) == [off, on]


def test_event_propagate():
    data = []

    def do(event):
        state = inspect.currentframe().f_back.f_locals['self']
        event.cargo['data'].append(state)

    def do_with_propagate(event):
        state = inspect.currentframe().f_back.f_locals['self']
        event.cargo['data'].append(state)
        event.propagate = True

    m = StateMachine('m')
    s0 = StateMachine('s0')
    s1 = StateMachine('s1')
    s2 = StateMachine('s2')
    s3 = StateMachine('s3')
    s4 = State('s4')

    m.add_state(s0, initial=True)
    s0.add_state(s1, initial=True)
    s1.add_state(s2, initial=True)
    s2.add_state(s3, initial=True)
    s3.add_state(s4, initial=True)

    for state in s0, s1, s2, s3, s4:
        state.handlers = {'do': do}

    m.initialize()

    # No propagate by default
    m.dispatch(_e('do', data=data))
    assert data == [s4]

    # Should propagate only to the next state that can handle the event
    data = []
    s4.handlers = {'do': do_with_propagate}
    m.dispatch(_e('do', data=data))
    assert data == [s4, s3]

    data = []
    s4.handlers = {'do': do_with_propagate}
    s3.handlers = {}
    m.dispatch(_e('do', data=data))
    assert data == [s4, s2]

    data = []
    s4.handlers = {'do': do_with_propagate}
    s3.handlers = {'do': do}
    m.dispatch(_e('do', data=data))
    assert data == [s4, s3]

    data = []
    s4.handlers = {}
    s3.handlers = {}
    m.dispatch(_e('do', data=data))
    assert data == [s2]

    data = []
    s4.handlers = {}
    s3.handlers = {}
    s2.handlers = {'do': do_with_propagate}
    m.dispatch(_e('do', data=data))
    assert data == [s2, s1]


def test_event_propagate_enter_exit():
    data = []

    def do(event):
        state = inspect.currentframe().f_back.f_locals['self']
        event.cargo['source_event'].cargo['data'].append(state)

    def do_with_propagate(event):
        state = inspect.currentframe().f_back.f_locals['self']
        event.cargo['source_event'].cargo['data'].append(state)
        event.propagate = True

    m = StateMachine('m')
    s0 = StateMachine('s0')
    s1 = StateMachine('s1')
    s2 = StateMachine('s2')
    s3 = StateMachine('s3')
    s4 = State('s4')

    m.add_state(s0, initial=True)
    s0.add_state(s1, initial=True)
    s1.add_state(s2, initial=True)
    s2.add_state(s3, initial=True)
    s3.add_state(s4, initial=True)

    m.add_transition(s0, s0, events='a')

    for state in s0, s1, s2, s3, s4:
        state.handlers = {'enter': do, 'exit': do}

    m.initialize()

    m.dispatch(_e('a', data=data))
    assert data == [s4, s3, s2, s1, s0, s0, s1, s2, s3, s4]

    data = []
    s1.handlers = {}
    s3.handlers = {}
    m.dispatch(_e('a', data=data))
    assert data == [s4, s2, s0, s0, s2, s4]

    # Never propagate exit/enter events, even if propagate is set to True
    data = []
    s4.handlers = {'enter': do_with_propagate, 'exit': do_with_propagate}
    m.dispatch(_e('a', data=data))
    assert data == [s4, s2, s0, s0, s2, s4]


def test_previous_state_with_source_event():
    def do(event):
        state = inspect.currentframe().f_back.f_locals['self']
        event.cargo['source_event'].cargo['data'].append(state)

    def do_with_propagate(event):
        state = inspect.currentframe().f_back.f_locals['self']
        event.cargo['source_event'].cargo['data'].append(state)
        event.propagate = True

    m = StateMachine('m')
    s0 = StateMachine('s0')
    s1 = StateMachine('s1')
    s11 = State('s11')
    s12 = State('s12')

    m.add_state(s0, initial=True)
    s0.add_state(s1, initial=True)
    s1.add_state(s11, initial=True)
    s1.add_state(s12)

    for state in s0, s1, s11, s12:
        state.handlers = {'enter': do, 'exit': do}

    m.add_transition(s0, s12, events='a')

    m.initialize()

    data = []
    assert list(m.leaf_state_stack.deque) == []
    m.dispatch(_e('a', data=data))
    assert list(m.leaf_state_stack.deque) == [s11]

    data = []
    m.set_previous_leaf_state(event=_e('a', data=data))
    assert list(m.leaf_state_stack.deque) == [s11, s12]
    assert data == [s12, s11]


def test_previous_state_event_none():
    m = StateMachine('m')
    s0 = StateMachine('s0')
    s1 = StateMachine('s1')
    s11 = State('s11')
    s12 = State('s12')

    m.add_state(s0, initial=True)
    s0.add_state(s1, initial=True)
    s1.add_state(s11, initial=True)
    s1.add_state(s12)

    m.add_transition(s0, s12, events='a')

    m.initialize()

    assert list(m.leaf_state_stack.deque) == []
    m.dispatch(_e('a'))
    assert list(m.leaf_state_stack.deque) == [s11]

    try:
        m.set_previous_leaf_state(event=None)
    except Exception as exc:
        assert not exc
    assert list(m.leaf_state_stack.deque) == [s11, s12]


def test_state_machine_reference_present_in_event_with_nested_machines():
    m = StateMachine('m')
    s0 = StateMachine('s0')
    s1 = StateMachine('s1')
    s2 = State('s2')

    m.add_state(s0, initial=True)
    s0.add_state(s1, initial=True)
    s1.add_state(s2, initial=True)

    def do(event):
        assert event.state_machine == m

    for state in s0, s1, s2:
        state.handlers = {'enter': do, 'exit': do, 'do': do}

    m.add_transition(s0, s2, events=['do'])
    m.initialize()
    m.dispatch(_e('do'))


def test_add_states():
    # TODO Implement
    pass


def test_set_initial_state():
    # TODO Implement
    pass
