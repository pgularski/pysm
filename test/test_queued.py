import threading

from pysm import Event, State, StateMachine, StateMachineException
from pysm.queued import QueuedStateMachine, ThreadSafeQueuedStateMachine


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
