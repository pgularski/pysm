import threading

import pytest

from pysm import Event, State, StateMachine, StateMachineException
from pysm.queued import QueuedStateMachine, ThreadSafeQueuedStateMachine


class SchedulerAbort(BaseException):
    pass


def test_queued_machine_behaves_like_core_for_simple_transition():
    machine = QueuedStateMachine('m')
    off = State('off')
    on = State('on')

    machine.add_state(off, initial=True)
    machine.add_state(on)
    machine.add_transition(off, on, events=['turn_on'])
    machine.initialize()

    machine.dispatch(Event('turn_on'))

    assert machine.state is on
    assert machine.leaf_state is on


def test_internal_dispatch_from_enter_runs_after_current_transition_finishes():
    calls = []
    machine = QueuedStateMachine('m')
    a = State('a')
    b = State('b')
    c = State('c')

    def enter_b(state, event):
        calls.append('enter_b')
        machine.dispatch(Event('finish'))
        calls.append('enter_b_returned')

    def after_go(state, event):
        calls.append('after_go')

    def finish_action(state, event):
        calls.append('finish_action')

    b.handlers = {'enter': enter_b}
    machine.add_state(a, initial=True)
    machine.add_state(b)
    machine.add_state(c)
    machine.add_transition(a, b, events=['go'], after=after_go)
    machine.add_transition(b, c, events=['finish'], action=finish_action)
    machine.initialize()

    machine.dispatch(Event('go'))

    assert calls == [
        'enter_b',
        'enter_b_returned',
        'after_go',
        'finish_action',
    ]
    assert machine.state is c


def test_multiple_internal_events_keep_fifo_order():
    calls = []
    machine = QueuedStateMachine('m')
    a = State('a')
    b = State('b')

    def enter_b(state, event):
        machine.dispatch(Event('validate'))
        machine.dispatch(Event('metrics'))

    b.handlers = {'enter': enter_b}
    machine.add_state(a, initial=True)
    machine.add_state(b)
    machine.add_transition(a, b, events=['go'])
    machine.add_transition(b, None, events=['validate'],
                           action=lambda s, e: calls.append('validate'))
    machine.add_transition(b, None, events=['metrics'],
                           action=lambda s, e: calls.append('metrics'))
    machine.initialize()

    machine.dispatch(Event('go'))

    assert calls == ['validate', 'metrics']


def test_internal_queue_drains_before_external_queue():
    calls = []
    machine = QueuedStateMachine('m')
    a = State('a')
    b = State('b')

    def enter_b(state, event):
        machine._external_queue.append(Event('external'))
        machine.dispatch(Event('internal'))

    b.handlers = {'enter': enter_b}
    machine.add_state(a, initial=True)
    machine.add_state(b)
    machine.add_transition(a, b, events=['go'])
    machine.add_transition(b, None, events=['external'],
                           action=lambda s, e: calls.append('external'))
    machine.add_transition(b, None, events=['internal'],
                           action=lambda s, e: calls.append('internal'))
    machine.initialize()

    machine.dispatch(Event('go'))

    assert calls == ['internal', 'external']


def test_max_internal_steps_guard():
    machine = QueuedStateMachine('m', max_internal_steps=2)
    state = State('state')

    machine.add_state(state, initial=True)
    machine.add_transition(state, None, events=['loop'],
                           action=lambda s, e: machine.dispatch(Event('loop')))
    machine.initialize()

    try:
        machine.dispatch(Event('loop'))
    except StateMachineException as exc:
        assert 'max_internal_steps=2' in str(exc)
    else:
        assert False, 'Expected StateMachineException'


def test_internal_events_from_every_phase_keep_source_order():
    phases = ['handler', 'condition', 'before', 'exit', 'action',
              'enter', 'after']
    calls = []
    machine = QueuedStateMachine('m')
    a = State('a')
    b = State('b')

    def mark(phase):
        machine.dispatch(Event('mark', input=phase))

    def handler(state, event):
        mark('handler')

    def condition(state, event):
        mark('condition')
        return True

    def before(state, event):
        mark('before')

    def exit_a(state, event):
        mark('exit')

    def action(state, event):
        mark('action')

    def enter_b(state, event):
        mark('enter')

    def after(state, event):
        mark('after')

    def record(state, event):
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

    machine.dispatch(Event('go'))

    assert calls == phases


@pytest.mark.parametrize('phase', [
    'handler',
    'condition',
    'before',
    'exit',
    'action',
    'enter',
    'after',
])
def test_queued_callback_failure_clears_queued_work_from_each_phase(phase):
    calls = []
    machine = QueuedStateMachine('m')
    a = State('a')
    b = State('b')

    def fail(state, event):
        machine.dispatch(Event('stale'))
        raise RuntimeError(phase)

    def condition(state, event):
        if phase == 'condition':
            fail(state, event)
        return True

    def record_stale(state, event):
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
        machine.dispatch(Event('go'))

    assert machine._is_processing is False
    assert list(machine._internal_queue) == []
    assert list(machine._external_queue) == []

    machine.dispatch(Event('unknown'))
    assert calls == []


def test_queued_base_exception_clears_queues_and_releases_processor():
    calls = []
    machine = QueuedStateMachine('m')
    a = State('a')

    def aborting_action(state, event):
        machine.dispatch(Event('stale'))
        raise SchedulerAbort()

    machine.add_state(a, initial=True)
    machine.add_transition(a, None, events=['go'], action=aborting_action)
    machine.add_transition(a, None, events=['stale'],
                           action=lambda s, e: calls.append('stale'))
    machine.initialize()

    try:
        machine.dispatch(Event('go'))
    except SchedulerAbort:
        pass
    else:
        assert False, 'Expected SchedulerAbort'

    assert machine._is_processing is False
    assert list(machine._internal_queue) == []
    assert list(machine._external_queue) == []

    machine.dispatch(Event('unknown'))
    assert calls == []


def test_queued_runtime_error_clears_pending_internal_events():
    calls = []
    machine = QueuedStateMachine('m')
    a = State('a')

    def aborting_action(state, event):
        machine.dispatch(Event('stale'))
        raise RuntimeError('boom')

    machine.add_state(a, initial=True)
    machine.add_transition(a, None, events=['go'], action=aborting_action)
    machine.add_transition(a, None, events=['stale'],
                           action=lambda s, e: calls.append('stale'))
    machine.initialize()

    try:
        machine.dispatch(Event('go'))
    except RuntimeError:
        pass
    else:
        assert False, 'Expected RuntimeError'

    assert list(machine._internal_queue) == []
    assert list(machine._external_queue) == []
    machine.dispatch(Event('unknown'))
    assert calls == []


def test_thread_safe_queued_machine_serializes_concurrent_dispatches():
    machine = ThreadSafeQueuedStateMachine('m')
    off = State('off')
    on = State('on')

    machine.add_state(off, initial=True)
    machine.add_state(on)
    machine.add_transition(off, on, events=['toggle'])
    machine.add_transition(on, off, events=['toggle'])
    machine.initialize()

    def toggle_many():
        for _ in range(10):
            machine.dispatch(Event('toggle'))

    threads = [threading.Thread(target=toggle_many) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert machine.state is off
    assert machine.leaf_state is off
    assert len(machine.leaf_state_stack.deque) <= machine.STACK_SIZE


def test_thread_safe_nested_machine_uses_root_scheduler_for_internal_event():
    calls = []
    machine = ThreadSafeQueuedStateMachine('root')
    child = StateMachine('child')
    a = State('a')
    b = State('b')

    def enter_b(state, event):
        calls.append('enter_b')
        machine.dispatch(Event('finish'))

    b.handlers = {'enter': enter_b}
    machine.add_state(child, initial=True)
    child.add_state(a, initial=True)
    child.add_state(b)
    child.add_transition(a, b, events=['go'])
    child.add_transition(b, None, events=['finish'],
                         action=lambda s, e: calls.append('finish'))
    machine.initialize()

    machine.dispatch(Event('go'))

    assert calls == ['enter_b', 'finish']
    assert machine.leaf_state is b


def test_thread_safe_queued_machine_survives_slow_handler_storm():
    machine = ThreadSafeQueuedStateMachine('m')
    off = State('off')
    on = State('on')

    def slow_action(state, event):
        import time
        time.sleep(0.001)

    machine.add_state(off, initial=True)
    machine.add_state(on)
    machine.add_transition(off, on, events=['toggle'], action=slow_action)
    machine.add_transition(on, off, events=['toggle'], action=slow_action)
    machine.initialize()

    threads = [
        threading.Thread(
            target=lambda: [machine.dispatch(Event('toggle'))
                            for _ in range(5)])
        for _ in range(20)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert machine.state is off
    assert machine.leaf_state is off
    assert list(machine._internal_queue) == []
    assert list(machine._external_queue) == []


def test_thread_safe_queued_machine_never_runs_two_handlers_at_once():
    active_handlers = [0]
    max_active_handlers = [0]
    guard = threading.Lock()
    machine = ThreadSafeQueuedStateMachine('m')
    off = State('off')
    on = State('on')

    def slow_action(state, event):
        import time
        with guard:
            active_handlers[0] += 1
            max_active_handlers[0] = max(
                max_active_handlers[0], active_handlers[0])
        time.sleep(0.001)
        with guard:
            active_handlers[0] -= 1

    machine.add_state(off, initial=True)
    machine.add_state(on)
    machine.add_transition(off, on, events=['toggle'], action=slow_action)
    machine.add_transition(on, off, events=['toggle'], action=slow_action)
    machine.initialize()

    start = threading.Barrier(11)

    def toggle_many():
        start.wait()
        for _ in range(5):
            machine.dispatch(Event('toggle'))

    threads = [threading.Thread(target=toggle_many) for _ in range(10)]
    for thread in threads:
        thread.start()
    start.wait()
    for thread in threads:
        thread.join()

    assert max_active_handlers[0] == 1
    assert active_handlers[0] == 0
