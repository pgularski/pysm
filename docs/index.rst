Python State Machine
====================

`Github <https://github.com/pgularski/pysm/>`_ |
`PyPI <https://pypi.python.org/pypi/pysm/>`_


``pysm`` is a tiny, explicit hierarchical state machine library. The classic
core remains dependency-free and suitable for small runtimes, while optional
modules provide run-to-completion event scheduling, thread-safe dispatch,
serialization, and builder ergonomics.

Core imports stay small:

.. code-block:: python

   from pysm import StateMachine, State, Event

Advanced behavior is opt-in:

.. code-block:: python

   from pysm.queued import QueuedStateMachine
   from pysm.queued import ThreadSafeQueuedStateMachine
   from pysm.serialization import snapshot, restore
   from pysm.builder import StateMachineBuilder


.. toctree::
   :maxdepth: 2

   pysm_module
   installing
   examples
