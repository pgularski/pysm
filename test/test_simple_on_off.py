from pysm import State, StateMachine, Event

on = State('on')
off = State('off')

sm = StateMachine('sm')
sm.add_state(on, initial=True)
sm.add_state(off)

sm.add_transition(on, off, events=['off'])
sm.add_transition(off, on, events=['on'])

sm.initialize()

def test():
    assert sm.state == on
    sm.dispatch(Event('off'))
    assert sm.state == off
    sm.dispatch(Event('on'))
    assert sm.state == on


if __name__ == '__main__':
    test()
