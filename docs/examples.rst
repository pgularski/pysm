.. |State| replace:: :class:`~pysm.pysm.State`

Examples
========

.. contents::
    :local:


Simple state machine
--------------------

This is a simple state machine with only two states - `on` and `off`.

.. include:: ../examples/simple_on_off.py
    :literal:


Complex hierarchical state machine
----------------------------------

A Hierarchical state machine similar to the one from Miro Samek's book [#f1]_,
page 95. *It is a state machine that contains all possible state transition
topologies up to four levels of state nesting* [#f2]_

.. image:: _static/img/complex_hsm.png

.. include:: ../examples/complex_hsm.py
    :literal:


Different ways to attach event handlers
---------------------------------------

A state machine and states may be created in many ways. The code below mixes
many styles to demonstrate it (In production code you'd rather keep your code
style consistent). One way is to subclass the |State| class and attach event
handlers to it. This resembles the State Pattern way of writing a state
machine. But handlers may live anywhere, really, and you can attach them
however you want. You're free to chose your own style of writing state machines
with pysm.
Also in this example a transition to a historical state is used.

.. image:: _static/img/oven_hsm.png

.. include:: ../examples/oven.py
    :literal:


Reverse Polish notation calculator
----------------------------------

A state machine is used in the `Reverse Polish notation (RPN)
<https://en.wikipedia.org/wiki/Reverse_Polish_notation>`_ calculator as a
parser. A single event name (`parse`) is used along with specific `inputs` (See
:func:`pysm.pysm.StateMachine.add_transition`).

This example also demonstrates how to use the stack of a state machine, so it
behaves as a `Pushdown Automaton (PDA)
<https://en.wikipedia.org/wiki/Pushdown_automaton>`_

.. include:: ../examples/rpn_calculator.py
    :literal:


----

.. rubric:: Footnotes

.. [#f1] `Miro Samek, Practical Statecharts in C/C++, CMP Books 2002.
        <http://www.amazon.com/Practical-Statecharts-Quantum-Programming-
        Embedded/dp/1578201101/ref=asap_bc?ie=UTF8>`_
.. [#f2] http://www.embedded.com/print/4008251 (visited on 07.06.2016)
