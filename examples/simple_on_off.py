#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
