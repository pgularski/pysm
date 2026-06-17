import importlib
import os
from contextlib import contextmanager
import sys
import types

from pysm import Event, State, StateMachine
import pysm.pysm as core


class _StrictMicropythonDeque(object):
    def __init__(self, iterable, maxlen):
        self.q = list(iterable)
        self.maxlen = maxlen

    def append(self, item):
        if self.maxlen > 0 and len(self.q) >= self.maxlen:
            self.q.pop(0)
        self.q.append(item)

    def pop(self):
        return self.q.pop()

    def popleft(self):
        if not self.q:
            raise IndexError('pop from an empty deque')
        return self.q.pop(0)

    def __len__(self):
        return len(self.q)

    def __iter__(self):
        return iter(self.q)

    def __getitem__(self, key):
        return self.q[key]


class _StrictMicropythonDequeModule(object):
    deque = _StrictMicropythonDeque


@contextmanager
def _optional_module_with_core_deque(module_filename, deque_impl):
    original_deque = core.deque
    module_name = 'pysm._micropython_optional_{0}'.format(
        os.path.splitext(module_filename)[0])
    module_path = os.path.join(os.path.dirname(core.__file__), module_filename)
    core.deque = deque_impl
    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        yield module
    finally:
        core.deque = original_deque
        sys.modules.pop(module_name, None)


def _strict_compat_deque():
    return core.patch_deque(_StrictMicropythonDequeModule)


def test_queued_machine_uses_core_deque_compatibility_wrapper():
    compat_deque = _strict_compat_deque()

    with _optional_module_with_core_deque('queued.py', compat_deque) as queued:
        assert queued.deque is compat_deque

        machine = queued.QueuedStateMachine('m')
        machine._internal_queue.append(Event('queued'))

        assert machine._internal_queue.popleft().name == 'queued'


def test_async_machine_uses_core_deque_compatibility_wrapper():
    compat_deque = _strict_compat_deque()

    with _optional_module_with_core_deque('aio.py', compat_deque) as aio:
        assert aio.deque is compat_deque

        machine = aio.AsyncQueuedStateMachine('m')
        machine._external_queue.append(Event('queued'))

        assert machine._external_queue.popleft().name == 'queued'


def test_serialization_uses_core_deque_compatibility_wrapper():
    compat_deque = _strict_compat_deque()

    with _optional_module_with_core_deque(
            'serialization.py', compat_deque) as serialization:
        assert serialization.deque is compat_deque

        machine = StateMachine('m')
        off = State('off')
        on = State('on')
        machine.add_state(off, initial=True)
        machine.add_state(on)
        machine.add_transition(off, on, events=['on'])
        machine.initialize()
        machine.dispatch(Event('on'))

        data = serialization.snapshot(machine)
        restored = StateMachine('m')
        restored_off = State('off')
        restored_on = State('on')
        restored.add_state(restored_off, initial=True)
        restored.add_state(restored_on)
        restored.add_transition(restored_off, restored_on, events=['on'])
        restored.initialize()

        serialization.restore(restored, data)

        assert restored.leaf_state is restored_on


def test_async_awaitable_detection_does_not_require_inspect():
    import pysm.aio as aio

    async def native_coroutine():
        return 'native'

    @types.coroutine
    def generator_coroutine():
        if False:
            yield None
        return 'generator'

    native = native_coroutine()
    generator = generator_coroutine()
    try:
        assert aio._is_awaitable(native) is True
        assert aio._is_awaitable(generator) is True
        assert aio._is_awaitable('plain result') is False
    finally:
        native.close()
        generator.close()


def test_async_awaitable_detection_allows_micropython_coroutine_shape():
    import pysm.aio as aio

    class MicroPythonCoroutineShape(object):
        def send(self, value):
            return value

        def throw(self, *args):
            raise StopIteration

    old_value = aio._IS_MICROPYTHON
    aio._IS_MICROPYTHON = True
    try:
        assert aio._is_awaitable(MicroPythonCoroutineShape()) is True
    finally:
        aio._IS_MICROPYTHON = old_value
