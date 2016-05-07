# pysm
Python State Machine

## Status
[![Build Status](https://travis-ci.org/pgularski/pysm.png?branch=master)](https://travis-ci.org/pgularski/pysm)


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
--
It can do this:

![alt tag](https://cloud.githubusercontent.com/assets/3026621/15031178/bf5efb2a-124e-11e6-9748-0b5a5be60a30.png)

Like that:
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

Or this:

![alt tag](https://cloud.githubusercontent.com/assets/3026621/15031148/ad955f06-124e-11e6-865e-c7e3340f14cb.png)

Like that:

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
