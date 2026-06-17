pysm - Python State Machine
---------------------------

Versatile and flexible Python State Machine library.


.. image:: https://github.com/pgularski/pysm/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/pgularski/pysm/actions/workflows/ci.yml
    :alt: CI

.. image:: https://readthedocs.org/projects/pysm/badge/?version=latest
    :target: http://pysm.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status


Implement simple and complex state machines
-------------------------------------------

It can do simple things like this:

.. image:: https://cloud.githubusercontent.com/assets/3026621/15031178/bf5efb2a-124e-11e6-9748-0b5a5be60a30.png

Or somewhat more complex like that:

.. image:: https://cloud.githubusercontent.com/assets/3026621/15031148/ad955f06-124e-11e6-865e-c7e3340f14cb.png


Python State Machine
--------------------

`The State Pattern <https://en.wikipedia.org/wiki/State_pattern>`_
solves many problems, untangles the code and saves one's sanity.
Yet.., it's a bit rigid and doesn't scale. The goal of this library is to give
you a close to the State Pattern simplicity with much more flexibility. And,
if needed, the full state machine functionality, including `FSM
<https://en.wikipedia.org/wiki/Finite-state_machine>`_, `HSM
<https://en.wikipedia.org/wiki/UML_state_machine
#Hierarchically_nested_states>`_, `PDA
<https://en.wikipedia.org/wiki/Pushdown_automaton>`_ and other tasty things.


Goals
-----

* Provide a State Pattern-like behavior with more flexibility (see
  `Documentation <http://pysm.readthedocs.io/en/latest/examples.html>`__ for
  examples)
* Be explicit and don't add any magic code to objects that use pysm
* Handle directly any kind of event or input (not only strings) - parsing
  strings is cool again!
* Keep it simple, even for someone who's not very familiar with the FSM
  terminology


Features
--------

* Finite State Machine (FSM)
* Hierarchical State Machine (HSM) with Internal/External/Local transitions
* Pushdown Automaton (PDA)
* Transition callbacks - action, before, after
* State hooks - enter, exit, and other event handlers
* Entry and exit actions are associated with states, not transitions
* Events may be anything as long as they're hashable
* States history and transition to previous states
* Conditional transitions (if/elif/else-like logic)
* Explicit behaviour (no method or attribute is added to the object containing a state machine)
* No need to extend a class with State Machine class (composition over inheritance)
* Fast (even with hundreds of transition rules)
* Not too many pythonisms, so that it's easily portable to other languages (ie. `JavaScript <https://github.com/pgularski/smjs>`_).
* MicroPython support
* Optional queued, thread-safe, async, serialization, builder, and typing helpers are available as explicit imports, so the core import stays small.


Installation
------------

Install pysm from `PyPI <https://pypi.python.org/pypi/pysm/>`_::

    pip install pysm

or clone the `Github pysm repository <https://github.com/pgularski/pysm/>`_::

    git clone https://github.com/pgularski/pysm
    cd pysm
    python setup.py install


Documentation
-------------

Read the docs for API documentation and examples - http://pysm.readthedocs.io/

The full documentation also covers the optional queued, thread-safe, async,
serialization, and builder modules.

See Unit Tests to see it working and extensively tested.


MicroPython support
-------------------

Use `upysm <https://github.com/pgularski/upysm>`_ when installing this library
on MicroPython. ``upysm`` is the MicroPython distribution channel for selected
``pysm`` releases; it is not a fork and does not carry separate application
code. The installed package still imports as ``pysm``::

   from pysm import Event, State, StateMachine

The default ``upysm`` package is core-focused for memory-constrained devices.
Optional CPython-oriented modules should stay out of device builds unless you
explicitly need them and have measured the memory cost.

Modern MicroPython installations should use ``mip`` through ``mpremote``::

   mpremote mip install https://pgularski.github.io/upysm/

Pin a specific release for repeatable device builds, replacing ``0.4.0`` with
the release you want::

   mpremote mip install https://pgularski.github.io/upysm/0.4.0/

You can also install from the MicroPython REPL::

   import mip
   mip.install('https://pgularski.github.io/upysm/')

Older firmware that still uses ``upip`` can install the package from PyPI::

   import upip
   upip.install('upysm')


Links
-----

* `Documentation <http://pysm.readthedocs.io>`__
* `Installation <http://pysm.readthedocs.io/en/latest/installing.html>`__
* `Github <https://github.com/pgularski/pysm>`_
* `Issues <https://github.com/pgularski/pysm/issues>`_
* `Examples <http://pysm.readthedocs.io/en/latest/examples.html>`_
