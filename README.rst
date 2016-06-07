pysm
====

.. image:: https://travis-ci.org/pgularski/pysm.svg?branch=master
    :target: https://travis-ci.org/pgularski/pysm

.. image:: https://coveralls.io/repos/github/pgularski/pysm/badge.svg?branch=master
    :target: https://coveralls.io/github/pgularski/pysm?branch=master

.. image:: https://landscape.io/github/pgularski/pysm/master/landscape.svg?style=flat
    :target: https://landscape.io/github/pgularski/pysm/master
    :alt: Code Health

.. image:: https://readthedocs.org/projects/pysm/badge/?version=latest
    :target: http://pysm.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status


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

* Provide a State Pattern-like behavior with more flexibility
* Be explicit and don't add any code to objects
* Handle directly any kind of event (not only strings) - parsing strings is
  cool again!
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

Read the docs - http://pysm.readthedocs.io/


Links
-----
* `Documentation <http://pysm.readthedocs.io>`_
* `Installation <http://pysm.readthedocs.io/en/latest/installing.html>`_
* `Github <https://github.com/pgularski/pysm>`_
* `Issues <https://github.com/pgularski/pysm/issues>`_
* `Examples <http://pysm.readthedocs.io/en/latest/examples.html>`_
