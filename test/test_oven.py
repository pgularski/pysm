import threading
import time
from pysm import StateMachine, State, Event


# It's possible to encapsulate all state related behaviour in a state class.
class HeatingState(StateMachine):
    def on_enter(self, state, event):
        oven = event.cargo['source_event'].cargo['oven']
        if not oven.timer.is_alive():
            oven.start_timer()
        print('Heating on')

    def on_exit(self, state, event):
        print('Heating off')

    def register_handlers(self):
        self.handlers = {
            'enter': self.on_enter,
            'exit': self.on_exit,
        }


class Oven(object):
    TIMEOUT = 0.1

    def __init__(self):
        self.sm = self._get_state_machine()
        self.timer = threading.Timer(Oven.TIMEOUT, self.on_timeout)

    def _get_state_machine(self):
        oven = StateMachine('Oven')
        door_closed = StateMachine('Door closed')
        door_open = State('Door open')
        heating = HeatingState('Heating')
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

        # This time, a state behaviour is handled by Oven's methods.
        door_open.handlers = {
            'enter': self.on_open_enter,
            'exit': self.on_open_exit,
            'close': self.on_door_close
        }

        oven.initialize()
        return oven

    @property
    def state(self):
        return self.sm.leaf_state.name

    def light_on(self):
        print('Light on')

    def light_off(self):
        print('Light off')

    def start_timer(self):
        self.timer.start()

    def bake(self):
        self.sm.dispatch(Event('bake', oven=self))

    def toast(self):
        self.sm.dispatch(Event('toast', oven=self))

    def open_door(self):
        self.sm.dispatch(Event('open', oven=self))

    def close_door(self):
        self.sm.dispatch(Event('close', oven=self))

    def on_timeout(self):
        print('Timeout...')
        self.sm.dispatch(Event('timeout', oven=self))
        self.timer = threading.Timer(Oven.TIMEOUT, self.on_timeout)

    def on_open_enter(self, state, event):
        print('Opening door')
        self.light_on()

    def on_open_exit(self, state, event):
        print('Closing door')
        self.light_off()

    def on_door_close(self, state, event):
        # Transition to a history state
        self.sm.set_previous_leaf_state(event)


def test_oven():
    oven = Oven()
    print(oven.state)
    assert oven.state == 'Off'
    oven.bake()
    print(oven.state)
    assert oven.state == 'Baking'
    oven.open_door()
    print(oven.state)
    assert oven.state == 'Door open'
    oven.close_door()
    print(oven.state)
    assert oven.state == 'Baking'
    time.sleep(0.2)
    print(oven.state)
    assert oven.state == 'Off'


if __name__ == '__main__':
    test_oven()
