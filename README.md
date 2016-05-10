# pysm
Python State Machine

# Status
[![Build Status](https://travis-ci.org/pgularski/pysm.png?branch=master)](https://travis-ci.org/pgularski/pysm)
[![Coverage Status](https://coveralls.io/repos/github/pgularski/pysm/badge.svg?branch=master)](https://coveralls.io/github/pgularski/pysm?branch=master)

# Features
- Finite State Machine (FSM)
- Hierarchical State Machine (HSM) with Internal/External/Local transitions
- Pushdown Automaton (PDA)
- Transition hooks - enter, exit, action, before, after
- States history
- Conditional transitions (if/elif/else-like logic)
- An object may contain many state machines
- Easy to use
- Explicit behaviour (no method or attribute is added to the object containing a state machine)
- No need to extend a class with State Machine class (composition over inheritance), however, one can extend the Event class to always contain the entity object
- Entry and exit actions are associated with states, not transitions
- Fast (even with hundreds of transition rules)
- Not too many pythonisms, so that it's easily portable to other languages (ie. JavaScript)

# Installation
```
pip install pysm
```
or clone this repository and then
```
python setup.py install
```

# Rationale
There are a plethora of python state machine implementations out there. Some of them really powerful.
There's usually one problem with them, though - quite often they have too much magic under the hood. Specifically, they tend to add methods to a subject object, for instance. Using dynamic method creation seems apealing at first glance and it looks very well in simple demo examples. Yet the more mature the project gets the higher the risk someone is going to get bitten with this very feature. I have learned it the hard way. In most cases you don't want a dynamic property or method creation in your objects. And the further you get and more customers you have and APIs stabilise the more painful it gets when you realise you didn't want a certain item added to your instance in the first place. And then your dynamic code clashes with the API but it's too late to remove the dynamic code someone's relying on.

That said, explicit is better than implicit. And simple is better than complex. These are the main ideas behind this (yet another) state machine implementation. And also, debugging the state machine itself and code that uses it is a breeze.

# Examples

## Simple FSM (Finite State Machine)

![alt tag](https://cloud.githubusercontent.com/assets/3026621/15031178/bf5efb2a-124e-11e6-9748-0b5a5be60a30.png)

```python
from pysm import State, StateMachine, Event

on = State('on')
off = State('off')

sm = StateMachine('sm')
sm.add_state(on, initial=True)
sm.add_state(off)

sm.add_transition(on, off, events=['off'])
sm.add_transition(off, on, events=['on'])

sm.initialize()

assert sm.state == on
sm.dispatch(Event('off'))
assert sm.state == off
sm.dispatch(Event('on'))
assert sm.state == on
```

## HSM (Hierarchical State Machine)

![alt tag](https://cloud.githubusercontent.com/assets/3026621/15031148/ad955f06-124e-11e6-865e-c7e3340f14cb.png)

```python
# ... action functions go here

sm = StateMachine('sm')
s0 = StateMachine('s0')
s1 = StateMachine('s1')
s2 = StateMachine('s2')
s11 = State('s11')
s21 = StateMachine('s21')
s211 = State('s211')

sm.add_state(s0, initial=True)
s0.add_state(s1, initial=True)
s0.add_state(s2)
s1.add_state(s11, initial=True)
s2.add_state(s21, initial=True)
s21.add_state(s211, initial=True)

s0.add_transition(s1, None, events='j', action=action_j)
s0.add_transition(s1, s0, events='d')
s0.add_transition(s1, s11, events='b')
s0.add_transition(s1, s1, events='a')
s0.add_transition(s1, s211, events='f')
s0.add_transition(s1, s2, events='c')
s0.add_transition(s2, None, events='k', action=action_k)
s0.add_transition(s2, s11, events='f')
s0.add_transition(s2, s1, events='c')
s1.add_transition(s11, None, events='h', condition=is_foo, action=unset_foo)
s1.add_transition(s11, None, events='n', action=action_n)
s1.add_transition(s11, s211, events='g')
s21.add_transition(s211, None, events='m', action=action_m)
s21.add_transition(s211, s0, events='g')
s21.add_transition(s211, s21, events='d')
s2.add_transition(s21, None, events='l', condition=is_foo, action=action_l)
s2.add_transition(s21, s211, events='b')
s2.add_transition(s21, s21, events='h', condition=is_foo, action=set_foo)
sm.add_transition(s0, None, events='i', action=action_i)
sm.add_transition(s0, s211, events='e')

sm.initialize()

# See it working in UTs
```

## RPN (Reverse Polish Notation) Calculator

```python
'''
Test StateMachine can act as Pushdown Automaton.
'''

import string
from pysm import StateMachine, Event, State


class Calculator(object):
    def __init__(self):
        self.sm = self.get_state_machine()
        self.result = None

    def get_state_machine(self):
        sm = StateMachine('sm')
        initial = State('Initial')
        number = State('BuildingNumber')
        sm.add_state(initial, initial=True)
        sm.add_state(number)
        sm.add_transition(initial, number,
                          events=['parse'], input=string.digits,
                          action=self.start_building_number)
        sm.add_transition(number, None,
                          events=['parse'], input=string.digits,
                          action=self.build_number)
        sm.add_transition(number, initial,
                          events=['parse'], input=string.whitespace)
        sm.add_transition(initial, None,
                          events=['parse'], input='+-*/',
                          action=self.do_operation)
        sm.add_transition(initial, None,
                          events=['parse'], input='=',
                          action=self.do_equal)
        sm.initialize()
        return sm

    def parse(self, string):
        for char in string:
            self.sm.dispatch(Event('parse', input=char))

    def caluculate(self, string):
        self.parse(string)
        return self.result

    def start_building_number(self, event):
        digit = event.input
        self.sm.stack.push(int(digit))
        return True

    def build_number(self, event):
        digit = event.input
        number = str(self.sm.stack.pop())
        number += digit
        self.sm.stack.push(int(number))
        return True

    def do_operation(self, event):
        operation = event.input
        y = self.sm.stack.pop()
        x = self.sm.stack.pop()
        # eval is evil
        result = eval('float(x) %s float(y)' % operation)
        self.sm.stack.push(result)
        return True

    def do_equal(self, event):
        operation = event.input
        number = self.sm.stack.pop()
        self.result = number
        return True


def test_calc_callbacks():
    calc = Calculator()
    assert calc.caluculate(' 167 3 2 2 * * * 1 - =') == 2003
    assert calc.caluculate('    167 3 2 2 * * * 1 - 2 / =') == 1001.5
    assert calc.caluculate('    3   5 6 +  * =') == 33
    assert calc.caluculate('        3    4       +     =') == 7
    assert calc.caluculate('2 4 / 5 6 - * =') == -0.5
```


## Transition to historical states

![alt tag](https://cloud.githubusercontent.com/assets/3026621/15139510/6b29a642-168e-11e6-8338-ad6c950c2761.png)


```python
import threading
import time
from pysm import StateMachine, State, Event


# It's possible to encapsulate all state related behaviour in a state class
class HeatingState(StateMachine):
    def on_enter(self, event):
        oven = event.cargo['source_event'].cargo['oven']
        if not oven.timer.is_alive():
            oven.start_timer()
        print 'Heating on'

    def on_exit(self, event):
        print 'Heating off'

    def register_handlers(self):
        self.handlers = {
            'enter': self.on_enter,
            'exit': self.on_exit,
        }


class Oven(object):
    TIMEOUT = 1

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
        print 'Light on'

    def light_off(self):
        print 'Light off'

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
        print 'Timeout...'
        self.sm.dispatch(Event('timeout', oven=self))
        self.timer = threading.Timer(Oven.TIMEOUT, self.on_timeout)

    def on_open_enter(self, event):
        print 'Opening door'
        self.light_on()

    def on_open_exit(self, event):
        print 'Closing door'
        self.light_off()

    def on_door_close(self, event):
        # Transition to a history state
        self.sm.set_previous_leaf_state(event)
```

```python
>>> oven = Oven()
>>> print oven.state
Off
>>> oven.bake()
Heating on
>>> print oven.state
Baking
>>> oven.open_door()
Heating off
Opening door
Light on
>>> print oven.state
Door open
>>> oven.close_door()
Closing door
Light off
Heating on
>>> print oven.state
Baking
Timeout...
Heating off
>>> print oven.state
Off
```
