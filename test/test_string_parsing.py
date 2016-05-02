#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Test based on the code from:
# http://code.activestate.com/recipes/\
#        578344-simple-finite-state-machine-class-v2/

import string

from pysm import State, StateMachine, Event


def char(event):
    return event.cargo['char']


# Simple storage object for each token
class token(object):
    def __init__(self, type):
        self.tokenType = type
        self.tokenText = ""

    def addCharacter(self, char):
        self.tokenText += char

    def __repr__(self):
        return "{0}<{1}>".format(self.tokenType, self.tokenText)


# Token list object - demonstrating the definition of state machine callbacks
class tokenList(object):
    def __init__(self):
        self.fss = None
        self.tokenList = []
        self.currentToken = None

    def StartToken(self, event):
        value = event.name
        self.currentToken = token(self.fss.state.name)
        self.currentToken.addCharacter(value)

    def addCharacter(self, event):
        value = event.name
        self.currentToken.addCharacter(value)

    def EndToken(self, event):
        value = event.name
        self.tokenList.append(self.currentToken)
        self.currentToken = None


class Parser(object):
    def __init__(self, t):
        self.t = t
        self.sm = None
        self.init_sm()

    def init_sm(self):
        start = State('Start')
        identifier = State('Identifier')
        operator = State('Operator')
        number = State('Number')
        start_quote = State('StartQuote')
        string_st = State('String')
        end_quote = State('EndQuote')

        sm = StateMachine(self)
        sm.add_states(
            start, identifier, operator, number, start_quote, string_st,
            end_quote)
        sm.set_initial_state(start)

        # # This works also after a minor tweak in callback functions
        # transitions = [
        #     (start, start, lambda e: char(e).isspace()),
        #     (start, identifier,
        #         lambda e: char(e).isalpha(), self.t.StartToken),
        #     (start, operator,
        #         lambda e: char(e) in "=+*/-()", self.t.StartToken),
        #     (start, number, lambda e: char(e).isdigit(), self.t.StartToken),
        #     (start, start_quote, lambda e: char(e) == "\'"),
        #     (start_quote, string,
        #         lambda e: char(e) != "\'", self.t.StartToken),
        #     (identifier, identifier,
        #         lambda e: char(e).isalnum(), self.t.addCharacter ),
        #     (identifier, start,
        #         lambda e: not char(e).isalnum(), self.t.EndToken ),
        #     (operator, start, lambda e: True, self.t.EndToken),
        #     (number, number,
        #         lambda e: char(e).isdigit() or char(e) == ".",
        #         self.t.addCharacter),
        #     (number, start,
        #         lambda e: not char(e).isdigit() and char(e) != ".",
        #         self.t.EndToken ),
        #     (string, string, lambda e: char(e) != "\'", self.t.addCharacter),
        #     (string, end_quote, lambda e: char(e) == "\'", self.t.EndToken ),
        #     (end_quote, start, lambda e: True)
        # ]

        # for transition in transitions:
        #     from_state = transition[0]
        #     to_state = transition[1]
        #     condition = transition[2]
        #     action = transition[3] if len(transition) == 4 else None
        #     events = ['on_char']

        #     sm.add_transition(from_state, to_state, events=events,
        #             condition=condition, action=action)

        alnum = string.letters + string.digits
        not_alnum = ''.join(set(string.printable)
                            - set(string.letters + string.digits))
        not_quote = ''.join(set(string.printable) - set(["'"]))
        not_digit_or_dot = ''.join(set(string.printable)
                                   - set(string.digits) - set(['.']))
        digits_and_dot = string.digits + '.'

        at = sm.add_transition
        at(start, start, events=string.whitespace)
        at(start, identifier, events=string.letters, after=self.t.StartToken)
        at(start, operator, events='=+*/-()', after=self.t.StartToken)
        at(start, number, events=string.digits, after=self.t.StartToken)
        at(start, start_quote, events="'", after=self.t.StartToken)
        at(identifier, identifier, events=alnum, action=self.t.addCharacter)
        at(identifier, start, events=not_alnum, action=self.t.EndToken)
        at(start_quote, string_st, events=not_quote, after=self.t.StartToken)
        at(operator, start, events=string.printable, action=self.t.EndToken)
        at(number, number, events=digits_and_dot, action=self.t.addCharacter)
        at(number, start, events=not_digit_or_dot, action=self.t.EndToken)
        at(string_st, string_st, events=not_quote, action=self.t.addCharacter)
        at(string_st, end_quote, events="'", action=self.t.EndToken)
        at(end_quote, start, events=string.printable)

        sm.initialize()
        self.sm = sm

    def on_char(self, char):
        self.sm.dispatch(Event(char))

    def parse(self, text):
        for char in text:
            self.on_char(char)


def test():
    text = "    x123 = MyString + 123.65 - 'hello' * value "
    t = tokenList()
    parser = Parser(t)
    t.fss = parser.sm
    parser.parse(text)
    expected = ('[Identifier<x123>, Operator<=>, Identifier<MyString>, '
                'Operator<+>, Number<123.65>, Operator<->, String<hello>, '
                'Operator<*>, Identifier<value>]')
    assert str(t.tokenList) == expected
