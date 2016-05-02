import inspect
import mock
import pytest
from pysm import Event, State, StateMachine, StateMachineException
_e = Event


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
    pass


def test_add_state_that_is_already_added_anywhere_in_the_hsm():
    pass
