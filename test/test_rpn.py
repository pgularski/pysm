#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
