# pyright: reportIncompatibleMethodOverride=false
'''Optional asyncio execution layer for pysm.

This module is intentionally not imported from ``pysm.__init__``. It requires
CPython's ``asyncio`` runtime and keeps the classic core import untouched.
'''
import asyncio
import inspect
from collections import deque
from typing import Any, Callable, Deque, Dict, Hashable, List, Optional, Tuple, cast

from .pysm import Event, State, StateMachine, StateMachineException, any_event, logger


Callback = Callable[[State, Event], Any]
Transition = Dict[str, Any]
TransitionKey = Tuple[Optional[State], object, Optional[Hashable]]


class AsyncQueuedStateMachine(StateMachine):
    '''Async state machine with run-to-completion event scheduling.

    The machine is intended to be used from one asyncio event loop. External
    idle dispatches are serialized with an ``asyncio.Lock``. Events dispatched
    from the currently running transition task are queued as internal events.
    Events dispatched by other tasks while the machine is already processing
    are queued as external events and return after enqueueing.
    '''

    def __init__(self, name: str,
                 max_internal_steps: Optional[int] = None) -> None:
        super(AsyncQueuedStateMachine, self).__init__(name)
        self.max_internal_steps: Optional[int] = max_internal_steps
        self._internal_queue: Deque[Event] = deque()
        self._external_queue: Deque[Event] = deque()
        self._is_processing: bool = False
        self._processing_task: Optional[asyncio.Task[Any]] = None
        self._execution_lock: asyncio.Lock = asyncio.Lock()

    async def dispatch(self, event: Event) -> None:
        '''Enqueue and process ``event`` using async RTC semantics.'''
        current_task = asyncio.current_task()
        if self._is_processing:
            if current_task is self._processing_task:
                self._internal_queue.append(event)
            else:
                self._external_queue.append(event)
            return

        async with self._execution_lock:
            self._external_queue.append(event)
            self._is_processing = True
            self._processing_task = current_task
            internal_steps = 0

            try:
                while self._internal_queue or self._external_queue:
                    if self._internal_queue:
                        internal_steps += 1
                        if (self.max_internal_steps is not None and
                                internal_steps > self.max_internal_steps):
                            raise StateMachineException(
                                'AsyncQueuedStateMachine "{0}" exceeded '
                                'max_internal_steps={1}'.format(
                                    self.name, self.max_internal_steps))
                        next_event = self._internal_queue.popleft()
                    else:
                        internal_steps = 0
                        next_event = self._external_queue.popleft()

                    await self._dispatch_one(next_event)
            except BaseException:
                self._clear_queues()
                raise
            finally:
                self._is_processing = False
                self._processing_task = None

    async def _dispatch_one(self, event: Event) -> None:
        event.state_machine = self
        leaf_state_before = self.leaf_state
        await self._on(leaf_state_before, event)
        transition = await self._get_transition(event)
        if transition is None:
            return
        to_state = cast(Optional[State], transition['to_state'])
        from_state = cast(State, transition['from_state'])

        await self._call(transition['before'], leaf_state_before, event)
        top_state = await self._exit_states(event, from_state, to_state)
        await self._call(transition['action'], leaf_state_before, event)
        await self._enter_states(event, top_state, to_state)
        await self._call(transition['after'], self.leaf_state, event)

    async def _on(self, state: State, event: Event) -> None:
        if event.name in state.handlers:
            event.propagate = False
            await self._call(state.handlers[event.name], state, event)
        if (state.parent and event.propagate and
                event.name not in ('exit', 'enter')):
            await self._on(state.parent, event)

    async def _get_transition(self, event: Event) -> Optional[Transition]:
        machine = self.leaf_state.parent
        while machine:
            transition = await self._get_machine_transition(machine, event)
            if transition:
                return transition
            machine = machine.parent
        return None

    async def _get_machine_transition(
            self, machine: StateMachine,
            event: Event) -> Optional[Transition]:
        key: TransitionKey = (machine.state, event.name, event.input)
        transition = await self._get_transition_matching_condition(
            machine, key, event)
        if transition:
            return transition
        key = (machine.state, any_event, event.input)
        return await self._get_transition_matching_condition(
            machine, key, event)

    async def _get_transition_matching_condition(
            self, machine: StateMachine, key: TransitionKey,
            event: Event) -> Optional[Transition]:
        from_state = self.leaf_state
        for transition in machine._transitions._transitions[key]:
            result = await self._call(
                transition['condition'], from_state, event)
            if result is True:
                return transition
        return None

    async def _exit_states(
            self, event: Optional[Event], from_state: State,
            to_state: Optional[State]) -> Optional[State]:
        if to_state is None:
            return None
        state = self.leaf_state
        self.leaf_state_stack.push(state)
        while ((state.parent and
                not (from_state.is_substate(state) and
                     to_state.is_substate(state))) or
               (state == from_state == to_state)):
            logger.debug('exiting %s', state.name)
            exit_event = Event('exit', propagate=False, source_event=event)
            exit_event.state_machine = self
            self.root_machine._leaf_state = state
            await self._on(state, exit_event)
            parent = state.parent
            assert parent is not None
            parent.state_stack.push(state)
            parent.state = parent.initial_state
            state = parent
        return state

    async def _enter_states(
            self, event: Optional[Event], top_state: Optional[State],
            to_state: Optional[State]) -> None:
        if to_state is None:
            return
        path: List[State] = []
        state = self._get_leaf_state(to_state)

        while state.parent is not None and state != top_state:
            path.append(state)
            state = state.parent
        for state in reversed(path):
            logger.debug('entering %s', state.name)
            enter_event = Event('enter', propagate=False, source_event=event)
            enter_event.state_machine = self
            self.root_machine._leaf_state = state
            await self._on(state, enter_event)
            parent = state.parent
            assert parent is not None
            parent.state = state

    async def set_previous_leaf_state(
            self, event: Optional[Event] = None) -> None:
        '''Async version of ``StateMachine.set_previous_leaf_state``.'''
        if event is not None:
            event.state_machine = self
        from_state = self.leaf_state
        try:
            to_state = self.leaf_state_stack.peek()
        except IndexError:
            return
        top_state = await self._exit_states(event, from_state, to_state)
        await self._enter_states(event, top_state, to_state)

    async def revert_to_previous_leaf_state(
            self, event: Optional[Event] = None) -> None:
        '''Async version of ``StateMachine.revert_to_previous_leaf_state``.'''
        await self.set_previous_leaf_state(event)
        try:
            self.leaf_state_stack.pop()
            self.leaf_state_stack.pop()
        except IndexError:
            return

    async def _call(self, callback: Callback, state: State,
                    event: Event) -> Any:
        result = callback(state, event)
        if inspect.isawaitable(result):
            return await result
        return result

    def _clear_queues(self) -> None:
        while self._internal_queue:
            self._internal_queue.popleft()
        while self._external_queue:
            self._external_queue.popleft()
