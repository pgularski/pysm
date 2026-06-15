import asyncio

import pytest

from pysm import Event, State, StateMachine, StateMachineException, any_event
from pysm.aio import AsyncQueuedStateMachine
from pysm.serialization import restore, snapshot


class SchedulerAbort(BaseException):
    pass


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


def test_async_internal_events_from_every_phase_keep_source_order():
    async def scenario():
        phases = ['handler', 'condition', 'before', 'exit', 'action',
                  'enter', 'after']
        calls = []
        machine = AsyncQueuedStateMachine('m')
        a = State('a')
        b = State('b')

        async def mark(phase):
            await machine.dispatch(Event('mark', input=phase))

        async def handler(state, event):
            await mark('handler')

        async def condition(state, event):
            await mark('condition')
            return True

        async def before(state, event):
            await mark('before')

        async def exit_a(state, event):
            await mark('exit')

        async def action(state, event):
            await mark('action')

        async def enter_b(state, event):
            await mark('enter')

        async def after(state, event):
            await mark('after')

        async def record(state, event):
            calls.append(event.input)

        a.handlers = {'go': handler, 'exit': exit_a}
        b.handlers = {'enter': enter_b}
        machine.add_state(a, initial=True)
        machine.add_state(b)
        machine.add_transition(a, b, events=['go'], condition=condition,
                               before=before, action=action, after=after)
        machine.add_transition(b, None, events=['mark'], input=phases,
                               action=record)
        machine.initialize()

        await machine.dispatch(Event('go'))

        assert calls == phases

    asyncio.run(scenario())


@pytest.mark.parametrize('phase', [
    'handler',
    'condition',
    'before',
    'exit',
    'action',
    'enter',
    'after',
])
def test_async_callback_failure_clears_queued_work_from_each_phase(phase):
    async def scenario():
        calls = []
        machine = AsyncQueuedStateMachine('m')
        a = State('a')
        b = State('b')

        async def fail(state, event):
            await machine.dispatch(Event('stale'))
            raise RuntimeError(phase)

        async def condition(state, event):
            if phase == 'condition':
                await fail(state, event)
            return True

        async def record_stale(state, event):
            calls.append('stale')

        a.handlers = {'stale': record_stale}
        b.handlers = {'stale': record_stale}
        if phase == 'handler':
            a.handlers['go'] = fail
        if phase == 'exit':
            a.handlers['exit'] = fail
        if phase == 'enter':
            b.handlers['enter'] = fail

        machine.add_state(a, initial=True)
        machine.add_state(b)
        machine.add_transition(
            a, b, events=['go'],
            condition=condition,
            before=fail if phase == 'before' else None,
            action=fail if phase == 'action' else None,
            after=fail if phase == 'after' else None)
        machine.initialize()

        with pytest.raises(RuntimeError, match=phase):
            await machine.dispatch(Event('go'))

        assert machine._is_processing is False
        assert machine._processing_task is None
        assert list(machine._internal_queue) == []
        assert list(machine._external_queue) == []

        await machine.dispatch(Event('unknown'))
        assert calls == []

    asyncio.run(scenario())


def test_async_cancellation_clears_internal_queue_and_releases_lock():
    async def scenario():
        machine = AsyncQueuedStateMachine('m')
        a = State('a')
        b = State('b')
        entered = asyncio.Event()
        release = asyncio.Event()

        async def enter_b(state, event):
            await machine.dispatch(Event('stale'))
            entered.set()
            await release.wait()

        b.handlers = {'enter': enter_b}
        machine.add_state(a, initial=True)
        machine.add_state(b)
        machine.add_transition(a, b, events=['go'])
        machine.add_transition(b, None, events=['stale'])
        machine.initialize()

        task = asyncio.create_task(machine.dispatch(Event('go')))
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        assert machine._is_processing is False
        assert machine._processing_task is None
        assert list(machine._internal_queue) == []
        assert list(machine._external_queue) == []

        await asyncio.wait_for(machine.dispatch(Event('unknown')), 0.1)
        release.set()

    asyncio.run(scenario())


def test_async_base_exception_clears_queues_and_releases_processor():
    async def scenario():
        calls = []
        machine = AsyncQueuedStateMachine('m')
        state = State('state')

        async def aborting_action(state, event):
            await machine.dispatch(Event('stale'))
            raise SchedulerAbort()

        machine.add_state(state, initial=True)
        machine.add_transition(state, None, events=['go'],
                               action=aborting_action)
        machine.add_transition(state, None, events=['stale'],
                               action=lambda s, e: calls.append('stale'))
        machine.initialize()

        with pytest.raises(SchedulerAbort):
            await machine.dispatch(Event('go'))

        assert machine._is_processing is False
        assert machine._processing_task is None
        assert list(machine._internal_queue) == []
        assert list(machine._external_queue) == []

        await machine.dispatch(Event('unknown'))
        assert calls == []

    asyncio.run(scenario())


def test_async_external_task_dispatched_inside_handler_does_not_deadlock():
    async def scenario():
        calls = []
        machine = AsyncQueuedStateMachine('m')
        a = State('a')
        b = State('b')

        async def enter_b(state, event):
            task = asyncio.create_task(machine.dispatch(Event('external')))
            await asyncio.wait_for(task, 0.1)
            await machine.dispatch(Event('internal'))
            calls.append('enter_returned')

        b.handlers = {'enter': enter_b}
        machine.add_state(a, initial=True)
        machine.add_state(b)
        machine.add_transition(a, b, events=['go'])
        machine.add_transition(b, None, events=['external'],
                               action=lambda s, e: calls.append('external'))
        machine.add_transition(b, None, events=['internal'],
                               action=lambda s, e: calls.append('internal'))
        machine.initialize()

        await asyncio.wait_for(machine.dispatch(Event('go')), 0.1)

        assert calls == ['enter_returned', 'internal', 'external']

    asyncio.run(scenario())


def test_async_external_task_dispatch_returns_before_processing_external_event():
    async def scenario():
        calls = []
        machine = AsyncQueuedStateMachine('m')
        a = State('a')
        b = State('b')

        async def enter_b(state, event):
            calls.append('enter')
            task = asyncio.create_task(machine.dispatch(Event('external')))
            await asyncio.wait_for(task, 0.1)
            calls.append('external_dispatch_returned')
            assert 'external' not in calls
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

        await asyncio.wait_for(machine.dispatch(Event('go')), 0.1)

        assert calls == [
            'enter',
            'external_dispatch_returned',
            'internal',
            'external',
        ]

    asyncio.run(scenario())


def test_async_sibling_task_external_event_is_cleared_after_active_failure():
    async def scenario():
        calls = []
        machine = AsyncQueuedStateMachine('m')
        a = State('a')
        b = State('b')

        async def enter_b(state, event):
            task = asyncio.create_task(machine.dispatch(Event('external')))
            await asyncio.wait_for(task, 0.1)
            await machine.dispatch(Event('internal'))
            raise RuntimeError('enter failed')

        b.handlers = {'enter': enter_b}
        machine.add_state(a, initial=True)
        machine.add_state(b)
        machine.add_transition(a, b, events=['go'])
        machine.add_transition(b, None, events=['external'],
                               action=lambda s, e: calls.append('external'))
        machine.add_transition(b, None, events=['internal'],
                               action=lambda s, e: calls.append('internal'))
        machine.initialize()

        with pytest.raises(RuntimeError, match='enter failed'):
            await machine.dispatch(Event('go'))

        assert list(machine._internal_queue) == []
        assert list(machine._external_queue) == []
        await machine.dispatch(Event('unknown'))
        assert calls == []

    asyncio.run(scenario())


def test_async_transition_condition_chain_stops_on_first_true_condition():
    async def scenario():
        calls = []
        machine = AsyncQueuedStateMachine('m')
        a = State('a')
        b = State('b')
        c = State('c')
        d = State('d')

        async def false_condition(state, event):
            await asyncio.sleep(0)
            calls.append('false')
            return False

        async def true_condition(state, event):
            await asyncio.sleep(0)
            calls.append('true')
            return True

        async def never_condition(state, event):
            calls.append('never')
            return True

        machine.add_state(a, initial=True)
        machine.add_state(b)
        machine.add_state(c)
        machine.add_state(d)
        machine.add_transition(a, b, events=['go'],
                               condition=false_condition)
        machine.add_transition(a, c, events=['go'],
                               condition=true_condition)
        machine.add_transition(a, d, events=['go'],
                               condition=never_condition)
        machine.initialize()

        await machine.dispatch(Event('go'))

        assert calls == ['false', 'true']
        assert machine.state is c

    asyncio.run(scenario())


def test_async_condition_must_return_literal_true_not_truthy_value():
    async def scenario():
        calls = []
        machine = AsyncQueuedStateMachine('m')
        a = State('a')
        b = State('b')
        c = State('c')

        async def truthy_condition(state, event):
            await asyncio.sleep(0)
            calls.append('truthy')
            return 1

        async def literal_true_condition(state, event):
            await asyncio.sleep(0)
            calls.append('literal')
            return True

        machine.add_state(a, initial=True)
        machine.add_state(b)
        machine.add_state(c)
        machine.add_transition(a, b, events=['go'],
                               condition=truthy_condition)
        machine.add_transition(a, c, events=['go'],
                               condition=literal_true_condition)
        machine.initialize()

        await machine.dispatch(Event('go'))

        assert calls == ['truthy', 'literal']
        assert machine.state is c

    asyncio.run(scenario())


def test_async_any_event_fallback_and_input_matching():
    async def scenario():
        machine = AsyncQueuedStateMachine('m')
        a = State('a')
        b = State('b')
        c = State('c')

        machine.add_state(a, initial=True)
        machine.add_state(b)
        machine.add_state(c)
        machine.add_transition(a, b, events=['parse'], input=['expected'])
        machine.add_transition(a, c, events=[any_event], input=['fallback'])
        machine.initialize()

        await machine.dispatch(Event('parse', input='fallback'))
        assert machine.state is c

    asyncio.run(scenario())


def test_async_propagation_can_continue_to_parent_after_await():
    async def scenario():
        calls = []
        machine = AsyncQueuedStateMachine('root')
        child = StateMachine('child')
        leaf = State('leaf')

        async def leaf_handler(state, event):
            await asyncio.sleep(0)
            calls.append('leaf')
            event.propagate = True

        async def child_handler(state, event):
            await asyncio.sleep(0)
            calls.append('child')

        leaf.handlers = {'bubble': leaf_handler}
        child.handlers = {'bubble': child_handler}
        machine.add_state(child, initial=True)
        child.add_state(leaf, initial=True)
        machine.initialize()

        await machine.dispatch(Event('bubble'))

        assert calls == ['leaf', 'child']

    asyncio.run(scenario())


def test_async_enter_event_does_not_propagate_even_if_handler_requests_it():
    async def scenario():
        calls = []
        machine = AsyncQueuedStateMachine('root')
        child = StateMachine('child')
        a = State('a')
        b = State('b')

        async def enter_b(state, event):
            calls.append('b')
            event.propagate = True

        child.handlers = {'enter': lambda s, e: calls.append('child')}
        b.handlers = {'enter': enter_b}
        machine.add_state(child, initial=True)
        child.add_state(a, initial=True)
        child.add_state(b)
        child.add_transition(a, b, events=['go'])
        machine.initialize()

        await machine.dispatch(Event('go'))

        assert calls == ['b']

    asyncio.run(scenario())


def test_async_concurrent_external_dispatch_storm_preserves_internal_followups():
    async def scenario():
        calls = []
        machine = AsyncQueuedStateMachine('m')
        off = State('off')
        on = State('on')

        async def mark_on(state, event):
            await machine.dispatch(Event('mark'))

        machine.add_state(off, initial=True)
        machine.add_state(on)
        machine.add_transition(off, on, events=['toggle'], action=mark_on)
        machine.add_transition(on, off, events=['toggle'])
        machine.add_transition(on, None, events=['mark'],
                               action=lambda s, e: calls.append('mark'))
        machine.initialize()

        await asyncio.gather(*[
            machine.dispatch(Event('toggle')) for _ in range(100)
        ])

        assert machine.state is off
        assert len(calls) == 50
        assert list(machine._internal_queue) == []
        assert list(machine._external_queue) == []

    asyncio.run(scenario())


def test_async_snapshot_restore_after_history_changes():
    async def scenario():
        machine = AsyncQueuedStateMachine('m')
        off = State('off')
        on = State('on')
        machine.add_state(off, initial=True)
        machine.add_state(on)
        machine.add_transition(off, on, events=['on'])
        machine.add_transition(on, off, events=['off'])
        machine.initialize()

        await machine.dispatch(Event('on'))
        await machine.dispatch(Event('off'))
        data = snapshot(machine)

        restored = AsyncQueuedStateMachine('m')
        restored_off = State('off')
        restored_on = State('on')
        restored.add_state(restored_off, initial=True)
        restored.add_state(restored_on)
        restored.add_transition(restored_off, restored_on, events=['on'])
        restored.add_transition(restored_on, restored_off, events=['off'])
        restored.initialize()
        restore(restored, data)

        assert restored.leaf_state is restored_off
        assert [state.name for state in restored.leaf_state_stack.deque] == [
            'off',
            'on',
        ]
        await restored.dispatch(Event('on'))
        assert restored.leaf_state is restored_on

    asyncio.run(scenario())
