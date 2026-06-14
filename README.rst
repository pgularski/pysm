pysm - Python State Machine
===========================

``pysm`` is a tiny, explicit hierarchical state machine library for Python.
It keeps the original core small and dependency-free, while offering optional
modules for run-to-completion event scheduling, thread-safe dispatch,
serialization, and builder ergonomics.

The default import remains intentionally lean:

.. code-block:: python

   from pysm import StateMachine, State, Event

Optional features require explicit imports and are not pulled into the core.
That keeps the package suitable for memory-constrained MicroPython-style
deployments where only the classic runtime is wanted.


What It Is
----------

``pysm`` is built around explicit state objects and explicit transitions.
It does not inject methods or attributes into your domain objects.

Core features:

* Finite State Machine (FSM)
* Hierarchical State Machine (HSM)
* Pushdown-style stacks and history helpers
* Internal, external, and local transitions
* State ``enter`` / ``exit`` handlers
* Transition ``before`` / ``action`` / ``after`` callbacks
* Conditional transitions
* Hashable event names and inputs
* Zero required runtime dependencies


Core vs Optional Modules
------------------------

.. list-table::
   :header-rows: 1

   * - Module
     - Import
     - Purpose
     - MicroPython / ``upysm`` fit
   * - Core
     - ``from pysm import StateMachine, State, Event``
     - Classic tiny runtime
     - Yes
   * - Queued runtime
     - ``from pysm.queued import QueuedStateMachine``
     - Run-to-completion event scheduling
     - CPython-oriented optional module
   * - Thread-safe queued runtime
     - ``from pysm.queued import ThreadSafeQueuedStateMachine``
     - Queued dispatch protected by ``threading.RLock``
     - CPython-only
   * - Serialization
     - ``from pysm.serialization import snapshot, restore``
     - Snapshot active state and history using stable state paths
     - Optional utility
   * - Builder
     - ``from pysm.builder import StateMachineBuilder``
     - Reduce setup boilerplate without metaclasses or magic
     - Optional utility
   * - Type stubs
     - ``*.pyi`` files
     - IDE and type-checker help without runtime annotations
     - Development-time only


Basic Core FSM
--------------

.. code-block:: python

   from pysm import Event, State, StateMachine

   machine = StateMachine('toggle')
   off = State('off')
   on = State('on')

   machine.add_state(off, initial=True)
   machine.add_state(on)
   machine.add_transition(off, on, events=['turn_on'])
   machine.add_transition(on, off, events=['turn_off'])
   machine.initialize()

   machine.dispatch(Event('turn_on'))
   assert machine.state is on


Nested HSM
----------

.. code-block:: python

   oven = StateMachine('oven')
   door_closed = StateMachine('door_closed')
   door_open = State('door_open')
   off = State('off')
   heating = StateMachine('heating')
   baking = State('baking')

   oven.add_state(door_closed, initial=True)
   oven.add_state(door_open)
   door_closed.add_state(off, initial=True)
   door_closed.add_state(heating)
   heating.add_state(baking, initial=True)

   oven.add_transition(door_closed, baking, events=['bake'])
   oven.add_transition(door_closed, door_open, events=['open'])
   oven.initialize()

   oven.dispatch(Event('bake'))
   assert oven.leaf_state is baking


Queued Run-To-Completion Dispatch
---------------------------------

The classic ``StateMachine`` preserves historical behavior. If you need
deterministic event scheduling, use the opt-in queued runtime:

.. code-block:: python

   from pysm import Event, State
   from pysm.queued import QueuedStateMachine

   calls = []
   machine = QueuedStateMachine('m')
   start = State('start')
   ready = State('ready')

   def on_enter_ready(state, event):
       machine.dispatch(Event('validate'))
       machine.dispatch(Event('metrics'))

   ready.handlers = {'enter': on_enter_ready}

   machine.add_state(start, initial=True)
   machine.add_state(ready)
   machine.add_transition(start, ready, events=['go'])
   machine.add_transition(
       ready, None, events=['validate'],
       action=lambda state, event: calls.append('validate'))
   machine.add_transition(
       ready, None, events=['metrics'],
       action=lambda state, event: calls.append('metrics'))
   machine.initialize()

   machine.dispatch(Event('go'))
   assert calls == ['validate', 'metrics']

``QueuedStateMachine`` uses two FIFO queues. External events go to the external
queue. Events raised while the machine is already processing go to the internal
queue. Internal events are drained before the next external event is processed.
This gives deterministic run-to-completion behavior without changing the
classic core class.


Thread-Safe Queued Dispatch
---------------------------

For multi-threaded CPython programs, use the locked queued runtime:

.. code-block:: python

   from pysm.queued import ThreadSafeQueuedStateMachine

   machine = ThreadSafeQueuedStateMachine('m')

It uses ``threading.RLock`` and holds the lock for the whole
run-to-completion cycle. Long blocking handlers will therefore block other
threads from dispatching into the same machine. Async support is intentionally
not part of this class.


Snapshot And Restore
--------------------

Serialization returns plain Python primitives. It does not import ``json`` and
does not serialize callback code or domain objects.

.. code-block:: python

   from pysm.serialization import restore, snapshot

   data = snapshot(machine)
   # Store data with json.dumps(data), a database JSON column, Redis, etc.

   restored = build_the_same_machine_graph()
   restored.initialize()
   restore(restored, data)

Snapshots use full state paths, for example ``['oven', 'door_closed',
'heating', 'baking']``. Bare state names are not enough in a hierarchical
machine because different branches may contain states with the same name.
Restore is strict and raises if the saved topology does not match the machine
being restored.


Builder
-------

The builder is an optional setup helper. It does not change the core runtime
and does not add methods to your domain objects.

.. code-block:: python

   from pysm.builder import StateMachineBuilder

   machine = (StateMachineBuilder('toggle')
              .state('off', initial=True)
              .state('on')
              .transition('off', 'on', events=['turn_on'])
              .transition('on', 'off', events=['turn_off'])
              .build())

For nested machines, use paths when short names would be ambiguous.


MicroPython / upysm
-------------------

The MicroPython-oriented target should stay core-only:

.. code-block:: python

   from pysm import StateMachine, State, Event

Do not copy optional modules such as ``pysm.queued``, ``pysm.serialization``,
or ``pysm.builder`` into a constrained device build unless you explicitly need
them and have measured the memory cost.


Tests
-----

Run the test suite with:

.. code-block:: console

   pytest


Support
-------

If ``pysm`` saved you time, a small sponsorship or coffee is appreciated, but
not expected. The project is intentionally small and focused.


License
-------

MIT
