'''Python State Machine

The goal of this library is to give you a close to the State Pattern
simplicity with much more flexibility. And, if needed, the full state machine
functionality, including `FSM
<https://en.wikipedia.org/wiki/Finite-state_machine>`_, `HSM
<https://en.wikipedia.org/wiki/UML_state_machine
#Hierarchically_nested_states>`_, `PDA
<https://en.wikipedia.org/wiki/Pushdown_automaton>`_ and other tasty things.

Goals:
    - Provide a State Pattern-like behavior with more flexibility
    - Be explicit and don't add any code to objects
    - Handle directly any kind of event (not only strings) - parsing strings is
      cool again!
    - Keep it simple, even for someone who's not very familiar with the FSM
      terminology

----

.. |StateMachine| replace:: :class:`~.StateMachine`
.. |State| replace:: :class:`~.State`
.. |Hashable| replace:: :class:`~collections.Hashable`
.. |Iterable| replace:: :class:`~collections.Iterable`
.. |Callable| replace:: :class:`~collections.Callable`

'''
import collections
from collections import deque
import logging
import sys


logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class StateMachineException(Exception):
    '''All |StateMachine| exceptions are of this type. '''
    pass


class Event(object):
    r'''Triggers actions and transition in |StateMachine|.

    Events are also used to control the flow of data propagated to states
    within the states hierarchy.

    Event objects have the following attributes set after an event has been
    dispatched:

    **Attributes:**

        .. attribute:: state_machine

            A |StateMachine| instance that is handling the event (the one whose
            :func:`.StateMachine.dispatch` method is called)

        .. attribute:: propagate

            An event is propagated from a current leaf state up in the states
            hierarchy until it encounters a handler that can handle the event.
            To propagate it further, it has to be set to `True` in a handler.

    :param name: Name of an event. It may be anything as long as it's hashable.
    :type name: |Hashable|
    :param input: Optional input. Anything hashable.
    :type input: |Hashable|
    :param \*\*cargo: Keyword arguments for an event, used to transport data to
        handlers.  It's added to an event as a `cargo` property of type `dict`.
        For `enter` and `exit` events, the original event that triggered a
        transition is passed in cargo as `source_event` entry.

    .. note`:

        `enter` and `exit` events are never propagated, even if the `propagate`
        flag is set to `True` in a handler.

    **Example Usage:**

    .. code-block:: python

        state_machine.dispatch(Event('start'))
        state_machine.dispatch(Event('start', key='value'))
        state_machine.dispatch(Event('parse', input='#', entity=my_object))
        state_machine.dispatch(Event('%'))
        state_machine.dispatch(Event(frozenset([1, 2])))

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
    '''Represents a state in a state machine.

    `enter` and `exit` handlers are called whenever a state is entered or
    exited respectively. These action names are reserved only for this purpose.

    It is encouraged to extend this class to encapsulate a state behavior,
    similarly to the State Pattern.

    Once it's extended, the preferred way of adding an event handlers is
    through the :func:`~.State.register_handlers` hook. Usually,
    there's no need to create the :func:`__init__` in a subclass.

    :param name: Human readable state name
    :type name: str

    **Example Usage:**

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
        '''Hook method to register event handlers.

        It is used to easily extend |State| class. The hook is called from
        within the base :func:`.State__init__`. Usually, the
        :func:`__init__` doesn't have to be created in a subclass.

        Event handlers are kept in a `dict`, with events' names as keys,
        therefore registered events may be of any hashable type.

        Handlers take two arguments:

        - **state**: The current state that is handling an event. The same
              handler function may be attached to many states, therefore it
              is helpful to get the handling state's instance.
        - **event**: An event that triggered the handler call. If it is an
              `enter` or `exit` event, then the source event (the one that
              triggered the transition) is passed in `event`'s cargo
              property as `cargo.source_event`.

        **Example Usage:**

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
        '''Check whether the `state` is a substate of `self`.

        Also `self` is considered a substate of `self`.

        :param state: State to verify
        :type state: |State|
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
    '''State machine controls actions and transitions.

    To provide the State Pattern-like behavior, the formal state machine rules
    may be slightly broken, and instead of creating an `internal transition
    <https://en.wikipedia.org/wiki/UML_state_machine #Internal_transitions>`_
    for every action that doesn't require a state change, event handlers may be
    added to states. These are handled first when an event occurs. After that
    the actual transition is called, calling `enter`/`exit` actions and other
    transition actions. Nevertheless, internal transitions are also supported.

    So the order of calls on an event is as follows:

        1. State's event handler
        2. `condition` callback
        3. `before` callback
        4. `exit` handlers
        5. `action` callback
        6. `enter` handlers
        7. `after` callback

    If there's no handler in states or transition for an event, it is silently
    ignored.

    If using nested state machines, all events should be sent to the root state
    machine.

    **Attributes:**

        .. attribute:: state

            Current, local state (instance of |State|) in a state machine.

        .. attribute:: stack

            Stack that can be used if the `Pushdown Automaton (PDA)
            <https://en.wikipedia.org/wiki/Pushdown_automaton>`_ functionality
            is needed.

        .. attribute:: state_stack

            Stack of previous local states in a state machine. With every
            transition, a previous state (instance of |State|) is pushed to the
            `state_stack`. Only :attr:`.StateMachine.STACK_SIZE` (32
            by default) are stored and old values are removed from the stack.

        .. attribute:: leaf_state_stack

            Stack of previous leaf states in a state machine. With every
            transition, a previous leaf state (instance of |State|) is pushed
            to the `leaf_state_stack`. Only
            :attr:`.StateMachine.STACK_SIZE` (32 by default) are
            stored and old values are removed from the stack.

        **leaf_state**
            See the :attr:`~.StateMachine.leaf_state` property.

        **root_machine**
            See the :attr:`~.StateMachine.root_machine` property.

    :param name: Human readable state machine name
    :type name: str

    .. note ::

        |StateMachine| extends |State| and therefore it is possible to always
        use a |StateMachine| instance instead of the |State|. This wouldn't
        be a good practice though, as the |State| class is designed to be as
        small as possible memory-wise and thus it's more memory efficient. It
        is valid to replace a |State| with a |StateMachine| later on if there's
        a need to extend a state with internal states.

    .. note::

        For the sake of speed thread safety isn't guaranteed.

    **Example Usage:**

    .. code-block:: python

        state_machine = StateMachine('root_machine')
        state_on = State('On')
        state_off = State('Off')
        state_machine.add_state('Off', initial=True)
        state_machine.add_state('On')
        state_machine.add_transition(state_on, state_off, events=['off'])
        state_machine.add_transition(state_off, state_on, events=['on'])
        state_machine.initialize()
        state_machine.dispatch(Event('on'))

    '''
    STACK_SIZE = 32

    def __init__(self, name):
        super(StateMachine, self).__init__(name)
        self.states = set()
        self.state = None
        self._transitions = TransitionsContainer(self)
        self.state_stack = Stack(maxlen=StateMachine.STACK_SIZE)
        self.leaf_state_stack = Stack(maxlen=StateMachine.STACK_SIZE)
        self.stack = Stack()

    def add_state(self, state, initial=False):
        '''Add a state to a state machine.

        If states are added, one (and only one) of them has to be declared as
        `initial`.

        :param state: State to be added. It may be an another |StateMachine|
        :type state: |State|
        :param initial: Declare a state as initial
        :type initial: bool

        '''
        Validator(self).validate_add_state(state, initial)
        state.initial = initial
        state.parent = self
        self.states.add(state)

    def add_states(self, *states):
        '''Add `states` to the |StateMachine|.

        To set the initial state use
        :func:`~.StateMachine.set_initial_state`.

        :param states: A list of states to be added
        :type states: |State|

        '''
        for state in states:
            self.add_state(state)

    def set_initial_state(self, state):
        '''Set an initial state in a state machine.

        :param state: Set this state as initial in a state machine
        :type state: |State|

        '''
        Validator(self).validate_set_initial(state)
        state.initial = True

    @property
    def initial_state(self):
        '''Get the initial state in a state machine.

        :returns: Initial state in a state machine
        :rtype: |State|

        '''
        for state in self.states:
            if state.initial:
                return state
        return None

    @property
    def root_machine(self):
        '''Get the root state machine in a states hierarchy.

        :returns: Root state in the states hierarchy
        :rtype: |StateMachine|

        '''
        machine = self
        while machine.parent:
            machine = machine.parent
        return machine

    def add_transition(
            self, from_state, to_state, events, input=None, action=None,
            condition=None, before=None, after=None):
        '''Add a transition to a state machine.

        All callbacks take two arguments - `state` and `event`. See parameters
        description for details.

        It is possible to create conditional if/elif/else-like logic for
        transitions. To do so, add many same transition rules with different
        condition callbacks. First met condition will trigger a transition, if
        no condition is met, no transition is performed.

        :param from_state: Source state
        :type from_state: |State|
        :param to_state: Target state. If `None`, then it's an `internal
            transition <https://en.wikipedia.org/wiki/UML_state_machine
            #Internal_transitions>`_
        :type to_state: |State|, `None`
        :param events: List of events that trigger the transition
        :type events: |Iterable| of |Hashable|
        :param input: List of inputs that trigger the transition. A transition
            event may be associated with a specific input. i.e.: An event may
            be ``parse`` and an input associated with it may be ``$``. May be
            `None` (default), then every matched event name triggers a
            transition.
        :type input: `None`, |Iterable| of |Hashable|
        :param action: Action callback that is called during the transition
            after all states have been left but before the new one is entered.

            `action` callback takes two arguments:

                - state: Leaf state before transition
                - event: Event that triggered the transition

        :type action: |Callable|
        :param condition: Condition callback - if returns `True` transition may
            be initiated.

            `condition` callback takes two arguments:

                - state: Leaf state before transition
                - event: Event that triggered the transition

        :type condition: |Callable|
        :param before: Action callback that is called right before the
            transition.

            `before` callback takes two arguments:

                - state: Leaf state before transition
                - event: Event that triggered the transition

        :type before: |Callable|
        :param after: Action callback that is called just after the transition

            `after` callback takes two arguments:

                - state: Leaf state after transition
                - event: Event that triggered the transition

        :type after: |Callable|

        '''
        # Rather than adding some if statements later on, let's just declare a
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
        '''Get the current leaf state.

        The :attr:`~.StateMachine.state` property gives the current,
        local state in a state machine. The `leaf_state` goes to the bottom in
        a hierarchy of states. In most cases, this is the property that should
        be used to get the current state in a state machine, even in a flat
        FSM, to keep the consistency in the code and to avoid confusion.

        :returns: Leaf state in a hierarchical state machine
        :rtype: |State|

        '''
        return self._get_leaf_state(self)

    def _get_leaf_state(self, state):
        while hasattr(state, 'state') and state.state is not None:
            state = state.state
        return state

    def initialize(self):
        '''Initialize states in the state machine.

        After a state machine has been created and all states are added to it,
        :func:`~.StateMachine.initialize` has to be called.

        If using nested state machines (HSM),
        :func:`~.StateMachine.initialize` has to be called on a root
        state machine in the hierarchy.

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

        If using nested state machines (HSM), it has to be called on a root
        state machine in the hierarchy.

        :param event: Event to be dispatched
        :type event: :class:`.Event`

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
        :type event: :class:`.Event`

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
        '''Similar to :func:`.StateMachine.set_previous_leaf_state`
        but the current leaf_state is not saved on the stack of states. It
        allows to perform transitions further in the history of states.

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
