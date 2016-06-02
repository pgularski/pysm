'''
Explicit is better than implicit.
Gives similar to the State Pattern feeling but way more flexible.

Give a comparison between the State Pattern and this state machine.

Every state is is saved on the stack of states
A stack may be used in a PDA

May be used as a flat FSM.

Some terminology:
    leaf state
    previous leaf state

Some design decisions:
    :class:`pysm.StateMachine` is a subclass of :class:`pysm.State`

'''
# TODO: Separate in docstring - simple FSM case and HSM case?
# TODO: on changed to _on
# TODO: propagate shouldn't be an argument really but just a property

import collections
from collections import deque
import logging
import sys


logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class StateMachineException(Exception):
    '''All :class:`pysm.StateMachine` exceptions are of this type. '''
    pass


class Event(object):
    r''':class:`pysm.StateMachine` reacts to events. These have to be instances
    of this class.  Events are also used to control the flow of data propagated
    to states within the states hierarchy.

    :param name: Name of an event. It may be anything as long as it's hashable.
    :type name: :class:`collections.Hashable`
    :param input: Optional input. Anything hashable.
    :type input: :class:`collections.Hashable`
    :param \*\*cargo: Keyword arguments for an event, used to transport data to
        handlers.  It's added to an event as a `cargo` property of type `dict`.
        For `enter` and `exit` events, the original event that triggered a
        transition is passed in cargo as `source_event` entry.

    Event objects have the following attributes set once they've got
    instantiated:

        - `state_machine`: It's always set to the root
          :class:`pysm.StateMachine` instance in the states hierarchy. It
          allows getting useful information from within event handlers, like a
          current leaf state or a previous leaf state, the state machine's
          stack and the like.

        - `propagate`: It's `True` by default which means that an event will
          get propagated from a current leaf state up in the states hierarchy
          until it encounters a handler that can handle the event. Then it is
          set to `False`. It has to be explicitly set to `True` in a handler to
          re-propagate the event up in the hierarchy. It's similar to the class
          hierarchy in object oriented programming - `super` has to be invoked
          to call a method from a base class.

    .. note`:

        `enter` and `exit` events are never propagated, even if the `propagate`
        flag is set to `True` in a handler.

    .. code-block:: python

        state_machine.dispatch(Event('start'))
        state_machine.dispatch(Event('start', key='value'))
        state_machine.dispatch(Event('parse', input='#', entity=my_object))
        state_machine.dispatch(Event('%'))

    '''
    def __init__(self, name, input=None, **cargo):
        self.name = name
        self.input = input
        self.propagate = True
        self.cargo = cargo
        # This must be always the root machine
        self.state_machine = None

    def __repr__(self):
        return '<Event {0}, input={1}, cargo={2} ({3})>'.format(
            self.name, self.input, self.cargo, hex(id(self)))


class State(object):
    '''Represents a state within a state machine. All states are kept as
    instances of this class. It is encouraged to extend this class to
    encapsulate a state behavior, similarly to the State Pattern.

    :param name: Human readable name of a state
    :type name: str

    :func:`pysm.State.register_handlers` hook to faciliate exteneding the
    :class:`pysm.State`.

    .. code-block:: python

        # Extending State to encapsulate state-related behavior. Similar to the
        # State Pattern.
        class Running(State):
            def on_enter(self, state, event):
                print('Running state entered')

            def on_jump(self, state, event):
                print('Jumping')

            def on_dollar(self, state, event):
                print('Dollar found!')

            def register_handlers(self):
                self.handlers = {
                    'enter': self.on_enter,
                    'jump': self.on_jump,
                    '$': self.on_dollar
                }

    .. code-block:: python

        # Different way of attaching handlers. A handler may be any function as
        # long as it takes `state` and `event` args.
        def another_handler(state, event):
            print('Another handler')

        running = State('running')
        running.handlers = {
            'another_event': another_handler
        }


    .. note::

        @staticmethod could be use when overwriting
        Calling a state's handler from other state is possible (hence the
        `state` argument) although it would be considered a bad coding
        practice.

    '''
    def __init__(self, name):
        self.parent = None
        self.name = name
        # self.id = 1
        self.handlers = {}
        self.initial = False
        self.register_handlers()

    def __repr__(self):
        return '<State {0} ({1})>'.format(self.name, hex(id(self)))

    def register_handlers(self):
        '''Hook method to register event handlers. It is used to easily extend
        :class:`pysm.State` class - :func:`__init__` doesn't have to be created
        in a subclass, as the base one creates all that is required and then
        calls this hook method. As handlers are kept in a `dict`, registered
        events may be of any hashable type.

        Handlers take two arguments:

        - state: The current state that is handling an event. The same
              handler function may be attached to many states, therefore it
              is helpful to get the handling state's instance.
        - event: An event that triggered the handler call. If it is an
              `enter` or `exit` event, then the source event (the one that
              triggered the transition) is passed in `event`'s cargo
              property as `cargo.source_event`.


        .. code-block:: python

            class On(State):
                def handle_my_event(self, state, event):
                    print('Handling an event')

                def register_handlers(self):
                    self.handlers = {
                        'my_event': self.handle_my_event,
                        '&': self.handle_my_event,
                        frozenset([1, 2]): self.handle_my_event
                    }

        '''
        pass

    def is_substate(self, state):
        '''Check whether the `state` is a substate of `self`. Also `self` is
        considered a substate of `self`.

        :param state: State to verify
        :type state: :class:`pysm.State`
        :returns: `True` if `state` is a substate of `self`, `False` otherwise
        :rtype: bool

        '''
        if state is self:
            return True
        parent = self.parent
        while parent:
            if parent is state:
                return True
            parent = parent.parent
        return False

    def _on(self, event):
        if event.name in self.handlers:
            event.propagate = False
            self.handlers[event.name](self, event)
        # Never propagate exit/enter events, even if propagate is set to True
        if (self.parent and event.propagate and
                event.name not in ['exit', 'enter']):
            self.parent._on(event)

    def _nop(self, state, event):
        del state  # Unused (silence pylint)
        del event  # Unused (silence pylint)
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
        from_state = self._machine.leaf_state
        for transition in self._transitions[key]:
            if transition['condition'](from_state, event) is True:
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
    '''
    StateMachine may be empty (with no states added to it), then it acts as a
    simple State.

    :class:`pysm.StateMachine` extends :class:`pysm.State`

    '''
    def __init__(self, name):
        super(StateMachine, self).__init__(name)
        self.states = set()
        self.state = None
        self._transitions = TransitionsContainer(self)
        self.state_stack = Stack(maxlen=32)
        self.leaf_state_stack = Stack(maxlen=32)
        self.stack = Stack()

    def add_state(self, state, initial=False):
        '''Add a state to a state machine. If states are added, one (and only
        one) of them has to be declared as `initial`.

        :param state: State to be added. It may be an another
            :class:`pysm.StateMachine`
        :type state: :class:`pysm.State`
        :param initial: Declare a state as initial
        :type initial: bool

        '''
        Validator(self).validate_add_state(state, initial)
        state.initial = initial
        state.parent = self
        self.states.add(state)

    def add_states(self, *states):
        '''Add all `states` to the :class:`pysm.StateMachine`. In order to set
        the initial state use :func:`pysm.StateMachine.set_initial_state`.

        :param states: A list of states to be added
        :type states: :class:`pysm.State`

        '''
        for state in states:
            self.add_state(state)

    def set_initial_state(self, state):
        '''Set an initial state in a state machine. '''
        Validator(self).validate_set_initial(state)
        state.initial = True

    @property
    def initial_state(self):
        '''Get the initial state in a state machine.

        :returns: Initial state in a state machine
        :rtype: :class:`pysm.State`

        '''
        for state in self.states:
            if state.initial:
                return state
        return None

    @property
    def root_machine(self):
        '''Get the root state machine in a states hierarchy.

        :returns: Root state in the states hierarchy
        :rtype: :class:`pysm.StateMachine`

        '''
        machine = self
        while machine.parent:
            machine = machine.parent
        return machine

    def add_transition(
            self, from_state, to_state, events, input=None, action=None,
            condition=None, before=None, after=None):
        # Rather than adding some if statements later on let's just declare a
        # neutral items that will do nothing if called. It simplifies the logic
        # a lot.
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

        Validator(self).validate_add_transition(
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

    def _get_transition(self, event):
        machine = self.leaf_state.parent
        while machine:
            transition = machine._transitions.get(event)
            if transition:
                return transition
            machine = machine.parent
        return None

    @property
    def leaf_state(self):
        '''Get the leaf state in a hierarchical state machine. In order to be
        explicit leaf_state property is there. A `state` property gives the
        current state in a state machine the state is in, the leaf_state goes
        to the bottom in a hierarchy of states. In most cases, this is the
        property that should be used to get the current state in a state
        machine, even in a flat FSM, to keep the consistency in the code and to
        avoid confusion.

        :returns: Leaf state in a hierarchical state machine
        :rtype: :class:`pysm.State`

        '''
        return self._get_leaf_state(self)

    def _get_leaf_state(self, state):
        while hasattr(state, 'state') and state.state is not None:
            state = state.state
        return state

    def initialize(self):
        '''Initialize states in the state machine. After a state machine has
        been created and all states are added to it,
        :func:`pysm.StateMachine.initialize` has to be called on the root state
        machine in the hierarchy.

        '''
        machines = deque()
        machines.append(self)
        while machines:
            machine = machines.popleft()
            Validator(self).validate_initial_state(machine)
            machine.state = machine.initial_state
            for child_state in machine.states:
                if isinstance(child_state, StateMachine):
                    machines.append(child_state)

    def dispatch(self, event):
        '''Dispatch an event to a state machine.

        If using nested state machines (HSM):
        It has to be called on a root state machine in a hierarchy.

        :param event: Event to be dispatched
        :type event: :class:`pysm.Event`

        '''
        event.state_machine = self
        leaf_state_before = self.leaf_state
        leaf_state_before._on(event)
        transition = self._get_transition(event)
        if transition is None:
            return
        to_state = transition['to_state']
        from_state = transition['from_state']

        transition['before'](leaf_state_before, event)
        top_state = self._exit_states(event, from_state, to_state)
        transition['action'](leaf_state_before, event)
        self._enter_states(event, top_state, to_state)
        transition['after'](self.leaf_state, event)

    def _exit_states(self, event, from_state, to_state):
        if to_state is None:
            return
        state = self.leaf_state
        self.leaf_state_stack.push(state)
        while (state.parent and
                not (from_state.is_substate(state) and
                     to_state.is_substate(state)) or
                (state == from_state == to_state)):
            logger.debug('exiting %s', state.name)
            exit_event = Event('exit', propagate=False, source_event=event)
            exit_event.state_machine = self
            state._on(exit_event)
            state.parent.state_stack.push(state)
            state.parent.state = state.parent.initial_state
            state = state.parent
        return state

    def _enter_states(self, event, top_state, to_state):
        if to_state is None:
            return
        path = []
        state = self._get_leaf_state(to_state)

        while state.parent and state != top_state:
            path.append(state)
            state = state.parent
        for state in reversed(path):
            logger.debug('entering %s', state.name)
            enter_event = Event('enter', propagate=False, source_event=event)
            enter_event.state_machine = self
            state._on(enter_event)
            state.parent.state = state

    def set_previous_leaf_state(self, event=None):
        '''Transition to a previous leaf state. This makes a dynamic transition
        to a historical state. The current `leaf_state` is saved on the stack
        of historical leaf states when calling this method.

        :param event: (Optional) event that is passed to states involved in the
            transition
        :type event: :class:`pysm.Event`

        '''
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
        '''Similar to :func:`pysm.StateMachine.set_previous_leaf_state` but the
        current leaf_state is not saved on the stack of states. It allows to
        perform transitions further in the history of states.

        '''
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
