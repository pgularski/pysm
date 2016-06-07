from pysm import State, StateMachine, Event

foo = True

def on_enter(state, event):
    print('enter state {0}'.format(state.name))

def on_exit(state, event):
    print('exit state {0}'.format(state.name))

def set_foo(state, event):
    global foo
    print('set foo')
    foo = True

def unset_foo(state, event):
    global foo
    print('unset foo')
    foo = False

def action_i(state, event):
    print('action_i')

def action_j(state, event):
    print('action_j')

def action_k(state, event):
    print('action_k')

def action_l(state, event):
    print('action_l')

def action_m(state, event):
    print('action_m')

def action_n(state, event):
    print('action_n')

def is_foo(state, event):
    return foo is True

def is_not_foo(state, event):
    return foo is False


m = StateMachine('m')
s0 = StateMachine('s0')
s1 = StateMachine('s1')
s2 = StateMachine('s2')
s11 = State('s11')
s21 = StateMachine('s21')
s211 = State('s211')

m.add_state(s0, initial=True)
s0.add_state(s1, initial=True)
s0.add_state(s2)
s1.add_state(s11, initial=True)
s2.add_state(s21, initial=True)
s21.add_state(s211, initial=True)

# Internal transitions
m.add_transition(s0, None, events='i', action=action_i)
s0.add_transition(s1, None, events='j', action=action_j)
s0.add_transition(s2, None, events='k', action=action_k)
s1.add_transition(s11, None, events='h', condition=is_foo, action=unset_foo)
s1.add_transition(s11, None, events='n', action=action_n)
s21.add_transition(s211, None, events='m', action=action_m)
s2.add_transition(s21, None, events='l', condition=is_foo, action=action_l)

# External transition
m.add_transition(s0, s211, events='e')
s0.add_transition(s1, s0, events='d')
s0.add_transition(s1, s11, events='b')
s0.add_transition(s1, s1, events='a')
s0.add_transition(s1, s211, events='f')
s0.add_transition(s1, s2, events='c')
s0.add_transition(s2, s11, events='f')
s0.add_transition(s2, s1, events='c')
s1.add_transition(s11, s211, events='g')
s21.add_transition(s211, s0, events='g')
s21.add_transition(s211, s21, events='d')
s2.add_transition(s21, s211, events='b')
s2.add_transition(s21, s21, events='h', condition=is_not_foo, action=set_foo)

# Attach enter/exit handlers
states = [m, s0, s1, s11, s2, s21, s211]
for state in states:
    state.handlers = {'enter': on_enter, 'exit': on_exit}

m.initialize()


def test():
    assert m.leaf_state == s11
    m.dispatch(Event('a'))
    assert m.leaf_state == s11
    # This transition toggles state between s11 and s211
    m.dispatch(Event('c'))
    assert m.leaf_state == s211
    m.dispatch(Event('b'))
    assert m.leaf_state == s211
    m.dispatch(Event('i'))
    assert m.leaf_state == s211
    m.dispatch(Event('c'))
    assert m.leaf_state == s11
    assert foo is True
    m.dispatch(Event('h'))
    assert foo is False
    assert m.leaf_state == s11
    # Do nothing if foo is False
    m.dispatch(Event('h'))
    assert m.leaf_state == s11
    # This transition toggles state between s11 and s211
    m.dispatch(Event('c'))
    assert m.leaf_state == s211
    assert foo is False
    m.dispatch(Event('h'))
    assert foo is True
    assert m.leaf_state == s211
    m.dispatch(Event('h'))
    assert m.leaf_state == s211


if __name__ == '__main__':
    test()
