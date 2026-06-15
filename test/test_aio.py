import asyncio

import pytest

from pysm import Event, State, StateMachineException
from pysm.aio import AsyncQueuedStateMachine


def test_async_machine_behaves_like_core_for_simple_transition():
    async def scenario():
        machine = AsyncQueuedStateMachine('m')
        off = State('off')
        on = State('on')

        machine.add_state(off, initial=True)
        machine.add_state(on)
        machine.add_transition(off, on, events=['turn_on'])
        machine.initialize()

        await machine.dispatch(Event('turn_on'))

        assert machine.state is on
        assert machine.leaf_state is on

    asyncio.run(scenario())


def test_async_internal_dispatch_from_enter_runs_after_transition_finishes():
    async def scenario():
        calls = []
        machine = AsyncQueuedStateMachine('m')
        a = State('a')
        b = State('b')
        c = State('c')

        async def enter_b(state, event):
            calls.append('enter_b')
            await machine.dispatch(Event('finish'))
            calls.append('enter_b_returned')

        async def after_go(state, event):
            calls.append('after_go')

        async def finish_action(state, event):
            calls.append('finish_action')

        b.handlers = {'enter': enter_b}
        machine.add_state(a, initial=True)
        machine.add_state(b)
        machine.add_state(c)
        machine.add_transition(a, b, events=['go'], after=after_go)
        machine.add_transition(b, c, events=['finish'], action=finish_action)
        machine.initialize()

        await machine.dispatch(Event('go'))

        assert calls == [
            'enter_b',
            'enter_b_returned',
            'after_go',
            'finish_action',
        ]
        assert machine.state is c

    asyncio.run(scenario())


def test_async_callbacks_are_awaited_in_core_lifecycle_order():
    async def scenario():
        calls = []
        machine = AsyncQueuedStateMachine('m')
        a = State('a')
        b = State('b')

        async def condition(state, event):
            await asyncio.sleep(0)
            calls.append('condition')
            return True

        async def before(state, event):
            await asyncio.sleep(0)
            calls.append('before')

        async def action(state, event):
            await asyncio.sleep(0)
            calls.append('action')

        async def enter_b(state, event):
            await asyncio.sleep(0)
            calls.append('enter')

        async def after(state, event):
            await asyncio.sleep(0)
            calls.append('after')

        b.handlers = {'enter': enter_b}
        machine.add_state(a, initial=True)
        machine.add_state(b)
        machine.add_transition(a, b, events=['go'], condition=condition,
                               before=before, action=action, after=after)
        machine.initialize()

        await machine.dispatch(Event('go'))

        assert calls == ['condition', 'before', 'action', 'enter', 'after']

    asyncio.run(scenario())


def test_async_multiple_internal_events_keep_fifo_order():
    async def scenario():
        calls = []
        machine = AsyncQueuedStateMachine('m')
        a = State('a')
        b = State('b')

        async def enter_b(state, event):
            await machine.dispatch(Event('validate'))
            await machine.dispatch(Event('metrics'))

        b.handlers = {'enter': enter_b}
        machine.add_state(a, initial=True)
        machine.add_state(b)
        machine.add_transition(a, b, events=['go'])
        machine.add_transition(b, None, events=['validate'],
                               action=lambda s, e: calls.append('validate'))
        machine.add_transition(b, None, events=['metrics'],
                               action=lambda s, e: calls.append('metrics'))
        machine.initialize()

        await machine.dispatch(Event('go'))

        assert calls == ['validate', 'metrics']

    asyncio.run(scenario())


def test_async_external_dispatch_waits_for_internal_queue_to_drain():
    async def scenario():
        calls = []
        external_tasks = []
        machine = AsyncQueuedStateMachine('m')
        a = State('a')
        b = State('b')

        async def enter_b(state, event):
            calls.append('enter_b')
            external_tasks.append(
                asyncio.create_task(machine.dispatch(Event('external'))))
            await asyncio.sleep(0)
            await machine.dispatch(Event('internal'))

        b.handlers = {'enter': enter_b}
        machine.add_state(a, initial=True)
        machine.add_state(b)
        machine.add_transition(a, b, events=['go'])
        machine.add_transition(b, None, events=['external'],
                               action=lambda s, e: calls.append('external'))
        machine.add_transition(b, None, events=['internal'],
                               action=lambda s, e: calls.append('internal'))
        machine.initialize()

        await machine.dispatch(Event('go'))
        await external_tasks[0]

        assert calls == ['enter_b', 'internal', 'external']

    asyncio.run(scenario())


def test_async_max_internal_steps_guard():
    async def scenario():
        machine = AsyncQueuedStateMachine('m', max_internal_steps=2)
        state = State('state')

        machine.add_state(state, initial=True)
        machine.add_transition(
            state, None, events=['loop'],
            action=lambda s, e: machine.dispatch(Event('loop')))
        machine.initialize()

        with pytest.raises(StateMachineException) as exc:
            await machine.dispatch(Event('loop'))

        assert 'max_internal_steps=2' in str(exc.value)

    asyncio.run(scenario())
