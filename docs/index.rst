Python State Machine
====================

`Github <https://github.com/pgularski/pysm/>`_ |
`PyPI <https://pypi.python.org/pypi/pysm/>`_


``pysm`` is a tiny, explicit hierarchical state machine library. The classic
core remains dependency-free and suitable for small runtimes, while optional
modules provide run-to-completion event scheduling, thread-safe dispatch,
async dispatch, serialization, builder ergonomics, and shipped type
information for editors and type checkers.

The core runtime still follows the original composition-first style: create
states, add them to a root machine, add transitions, initialize the machine,
and dispatch hashable events. Newer helpers are layered around that core
instead of changing the top-level import.

Core imports stay small:

.. code-block:: python

   from pysm import StateMachine, State, Event

Advanced behavior is opt-in:

.. code-block:: python

   from pysm.queued import QueuedStateMachine
   from pysm.queued import ThreadSafeQueuedStateMachine
   from pysm.aio import AsyncQueuedStateMachine
   from pysm.serialization import snapshot, restore
   from pysm.builder import StateMachineBuilder


.. toctree::
   :maxdepth: 2

   pysm_module
   optional_modules
   installing
   examples
