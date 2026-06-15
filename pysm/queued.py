'''Optional queued execution layers for pysm.

The classes in this module deliberately live outside ``pysm.__init__`` so the
classic core import remains tiny and suitable for MicroPython-oriented builds.
'''
from collections import deque
from typing import Any, Deque, Optional

from .pysm import Event, StateMachine, StateMachineException


class QueuedStateMachine(StateMachine):
    '''State machine with run-to-completion event scheduling.

    External events enter an external FIFO queue. Events dispatched while the
    machine is already processing enter a separate internal FIFO queue. The
    internal queue is always drained before the next external event is handled.
    '''

    def __init__(self, name: str,
                 max_internal_steps: Optional[int] = None) -> None:
        super(QueuedStateMachine, self).__init__(name)
        self.max_internal_steps: Optional[int] = max_internal_steps
        self._internal_queue: Deque[Event] = deque()
        self._external_queue: Deque[Event] = deque()
        self._is_processing: bool = False

    def dispatch(self, event: Event) -> None:
        '''Enqueue ``event`` and process pending work to completion.'''
        if self._is_processing:
            self._internal_queue.append(event)
            return

        self._external_queue.append(event)
        self._is_processing = True
        internal_steps = 0

        try:
            while self._internal_queue or self._external_queue:
                if self._internal_queue:
                    internal_steps += 1
                    if (self.max_internal_steps is not None and
                            internal_steps > self.max_internal_steps):
                        raise StateMachineException(
                            'QueuedStateMachine "{0}" exceeded '
                            'max_internal_steps={1}'.format(
                                self.name, self.max_internal_steps))
                    next_event = self._internal_queue.popleft()
                else:
                    internal_steps = 0
                    next_event = self._external_queue.popleft()

                StateMachine.dispatch(self, next_event)
        except BaseException:
            self._clear_queues()
            raise
        finally:
            self._is_processing = False

    def _clear_queues(self) -> None:
        while self._internal_queue:
            self._internal_queue.popleft()
        while self._external_queue:
            self._external_queue.popleft()


class ThreadSafeQueuedStateMachine(QueuedStateMachine):
    '''Queued state machine protected by a reentrant execution lock.

    Long-running or blocking handlers hold the lock until the current
    run-to-completion cycle finishes. Async execution is intentionally kept out
    of this class.
    '''

    def __init__(self, name: str,
                 max_internal_steps: Optional[int] = None) -> None:
        super(ThreadSafeQueuedStateMachine, self).__init__(
            name, max_internal_steps=max_internal_steps)
        import threading
        self._execution_lock: Any = threading.RLock()

    def dispatch(self, event: Event) -> None:
        with self._execution_lock:
            return QueuedStateMachine.dispatch(self, event)
