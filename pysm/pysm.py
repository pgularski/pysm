#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
from Queue import deque
import logging
import sys

log = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
log.addHandler(handler)
log.setLevel(logging.INFO)


class StateMachineException(Exception):
    pass


class Event(object):
    def __init__(self, name, input=None, propagate=True, **cargo):
        self.name = name
        self.input = input
        self.propagate = propagate
        self.cargo = cargo
        # This must be always the root machine
        self.state_machine = None

    def __repr__(self):
        return '<Event {0}, input={1}, cargo={2} ({3})>'.format(
            self.name, self.input, self.cargo, hex(id(self)))


class State(object):
    def __init__(self, name):
        self.parent = None
        self.name = name
        # self.id = 1
        self.handlers = {}
        self.initial = False
        self.register_handlers()

    def is_substate(self, state):
        if state is self:
            return True
        parent = self.parent
        while parent:
            if parent is state:
                return True
            parent = parent.parent
        return False

    def __repr__(self):
        return '<State {0} ({1})>'.format(self.name, hex(id(self)))

    def register_handlers(self):
        pass

    def on(self, event):
        if event.name in self.handlers:
            event.propagate = False
            self.handlers[event.name](event)
        # Never propagate exit/enter events, even if propagate is set to True
        if (self.parent and event.propagate and
                event.name not in ['exit', 'enter']):
            self.parent.on(event)

    def _nop(self, event):
        return True


class TransitionsContainer(object):
    def __init__(self, machine):
        self._machine = machine
        self._transitions = collections.defaultdict(list)

    def add(self, key, transition):
        self._transitions[key].append(transition)

    def get(self, event):
        key = (self._machine.state, event.name, event.input)
        return self._get_transition_matching_condition(key, event)

    def _get_transition_matching_condition(self, key, event):
        for transition in self._transitions[key]:
            if transition['condition'](event) is True:
                return transition


class Stack(object):
    def __init__(self, maxlen=None):
        self.deque = deque(maxlen=maxlen)

    def pop(self):
        return self.deque.pop()

    def push(self, value):
        self.deque.append(value)

    def peek(self):
        return self.deque[-1]

    def __repr__(self):
        return str(list(self.deque))


class StateMachine(State):
    def __init__(self, name):
        super(StateMachine, self).__init__(name)
        self.states = set()
        self.state = None
        self._transitions = TransitionsContainer(self)
        self.state_stack = Stack(maxlen=32)
        self.leaf_state_stack = Stack(maxlen=32)
        self.stack = Stack()
        self.validator = Validator(self)

    def add_state(self, state, initial=False):
        self.validator.validate_add_state(state, initial)
        state.initial = initial
        state.parent = self
        self.states.add(state)

    def add_states(self, *states):
        for state in states:
            self.add_state(state)

    def set_initial_state(self, state):
        self.validator.validate_set_initial(state)
        state.initial = True

    @property
    def initial_state(self):
        for state in self.states:
            if state.initial:
                return state
        return None

    @property
    def root_machine(self):
        machine = self
        while machine.parent:
            machine = machine.parent
        return machine

    def add_transition(
            self, from_state, to_state, events, input=None, action=None,
            condition=None, before=None, after=None):
        if input is None:
            input = [None]
        if action is None:
            action = self._nop
        if before is None:
            before = self._nop
        if after is None:
            after = self._nop
        if condition is None:
            condition = self._nop

        self.validator.validate_add_transition(
            from_state, to_state, events, input)

        for input_value in input:
            for event in events:
                key = (from_state, event, input_value)
                transition = {
                    'from_state': from_state,
                    'to_state': to_state,
                    'action': action,
                    'condition': condition,
                    'before': before,
                    'after': after,
                }
                self._transitions.add(key, transition)

    def get_transition(self, event):
        machine = self.leaf_state.parent
        while machine:
            transition = machine._transitions.get(event)
            if transition:
                return transition
            machine = machine.parent
        return None

    @property
    def leaf_state(self):
        return self._get_leaf_state(self)

    def _get_leaf_state(self, state):
        while hasattr(state, 'state') and state.state is not None:
            state = state.state
        return state

    def initialize(self):
        machines = deque()
        machines.append(self)
        while machines:
            machine = machines.popleft()
            self.validator.validate_initial_state(machine)
            machine.state = machine.initial_state
            for child_state in machine.states:
                if isinstance(child_state, StateMachine):
                    machines.append(child_state)

    def dispatch(self, event):
        event.state_machine = self
        self.leaf_state.on(event)
        transition = self.get_transition(event)
        if transition is None:
            return
        to_state = transition['to_state']
        from_state = transition['from_state']
        if to_state is None:
            transition['action'](event)
            return

        transition['before'](event)
        top_state = self._exit_states(event, from_state, to_state)
        transition['action'](event)
        self._enter_states(event, top_state, to_state)
        transition['after'](event)

    def _exit_states(self, event, from_state, to_state):
        # TODO: Either remove event argument or create it above
        self.leaf_state_stack.push(self.leaf_state)
        state = self.leaf_state
        while (state.parent and
                not (from_state.is_substate(state) and
                     to_state.is_substate(state))
                or (state == from_state == to_state)
        ):
            log.debug('exiting %s', state.name)
            exit_event = Event('exit', propagate=False, source_event=event)
            exit_event.state_machine = self
            state.on(exit_event)
            state.parent.state_stack.push(state)
            state.parent.state = state.parent.initial_state
            state = state.parent
        return state

    def _enter_states(self, event, top_state, to_state):
        path = []
        state = self._get_leaf_state(to_state)

        while state.parent and state != top_state:
            path.append(state)
            state = state.parent
        for state in reversed(path):
            log.debug('entering %s', state.name)
            enter_event = Event('enter', propagate=False, source_event=event)
            enter_event.state_machine = self
            state.on(enter_event)
            state.parent.state = state

    def set_previous_leaf_state(self, event=None):
        if event is not None:
            event.state_machine = self
        from_state = self.leaf_state
        try:
            to_state = self.leaf_state_stack.peek()
        except IndexError:
            return
        top_state = self._exit_states(event, from_state, to_state)
        self._enter_states(event, top_state, to_state)

    def revert_to_previous_leaf_state(self, event=None):
        self.set_previous_leaf_state(event)
        try:
            self.leaf_state_stack.pop()
        except IndexError:
            return


class Validator(object):
    def __init__(self, state_machine):
        self.state_machine = state_machine
        self.template = 'Machine "{0}" error: {1}'.format(
            self.state_machine.name, '{0}')

    def _raise(self, msg):
        raise StateMachineException(self.template.format(msg))

    def validate_add_state(self, state, initial):
        if not isinstance(state, State):
            msg = 'Unable to add state of type {0}'.format(type(state))
            self._raise(msg)
        self._validate_state_already_added(state)
        if initial is True:
            self.validate_set_initial(state)

    def _validate_state_already_added(self, state):
        root_machine = self.state_machine.root_machine
        machines = deque()
        machines.append(root_machine)
        while machines:
            machine = machines.popleft()
            if state in machine.states and machine is not self.state_machine:
                msg = ('Machine "{0}" error: State "{1}" is already added '
                       'to machine "{2}"'.format(
                       self.state_machine.name, state.name, machine.name))
                self._raise(msg)
            for child_state in machine.states:
                if isinstance(child_state, StateMachine):
                    machines.append(child_state)

    def validate_set_initial(self, state):
        for added_state in self.state_machine.states:
            if added_state.initial is True and added_state is not state:
                msg = ('Unable to set initial state to "{0}". '
                       'Initial state is already set to "{1}"'
                       .format(state.name, added_state.name))
                self._raise(msg)

    def validate_add_transition(self, from_state, to_state, events, input):
        self._validate_from_state(from_state)
        self._validate_to_state(to_state)
        self._validate_events(events)
        self._validate_input(input)

    def _validate_from_state(self, from_state):
        if from_state not in self.state_machine.states:
            msg = 'Unable to add transition from unknown state "{0}"'.format(
                from_state.name)
            self._raise(msg)

    def _validate_to_state(self, to_state):
        root_machine = self.state_machine.root_machine
        if to_state is None:
            return
        elif to_state is root_machine:
            return
        elif not to_state.is_substate(root_machine):
            msg = 'Unable to add transition to unknown state "{0}"'.format(
                to_state.name)
            self._raise(msg)

    def _validate_events(self, events):
        if not isinstance(events, collections.Iterable):
            msg = ('Unable to add transition, events is not iterable: {0}'
                   .format(events))
            self._raise(msg)

    def _validate_input(self, input):
        if not isinstance(input, collections.Iterable):
            msg = ('Unable to add transition, input is not iterable: {0}'
                   .format(input))
            self._raise(msg)

    def validate_initial_state(self, machine):
        if machine.states and not machine.initial_state:
            msg = 'Machine "{0}" has no initial state'.format(machine.name)
            self._raise(msg)
