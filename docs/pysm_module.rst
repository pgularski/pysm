Module documentation
====================

Public imports
--------------

The top-level package intentionally exports only the classic core runtime:
``StateMachine``, ``State``, ``Event``, ``StateMachineException``, ``Stack``,
``any_event``, ``AnyEvent``, ``logger``, ``__version__``, and
``__version_info__``.

Optional modules are documented below, but they are not imported by
``import pysm``. Import them explicitly when you need their behavior.


Core
----

.. automodule:: pysm.pysm
   :members:
   :inherited-members:
   :show-inheritance:


Queued runtime
--------------

.. automodule:: pysm.queued
   :members:
   :inherited-members:
   :show-inheritance:


Async runtime
-------------

.. automodule:: pysm.aio
   :members:
   :inherited-members:
   :show-inheritance:


Serialization
-------------

.. automodule:: pysm.serialization
   :members:
   :inherited-members:
   :show-inheritance:


Builder
-------

.. automodule:: pysm.builder
   :members:
   :inherited-members:
   :show-inheritance:
