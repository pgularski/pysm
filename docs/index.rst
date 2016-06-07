Python State Machine
====================

`Github <https://github.com/pgularski/pysm/>`_ |
`PyPI <https://pypi.python.org/pypi/pysm/>`_


`The State Pattern <https://en.wikipedia.org/wiki/State_pattern>`_
solves many problems, untangles the code and saves one's sanity.
Yet.., it's a bit rigid and doesn't scale. The goal of this library is to give
you a close to the State Pattern simplicity with much more flexibility. And,
if needed, the full state machine functionality, including `FSM
<https://en.wikipedia.org/wiki/Finite-state_machine>`_, `HSM
<https://en.wikipedia.org/wiki/UML_state_machine
#Hierarchically_nested_states>`_, `PDA
<https://en.wikipedia.org/wiki/Pushdown_automaton>`_ and other tasty things.

Goals:
    - Provide a State Pattern-like behavior with more flexibility
    - Be explicit and don't add any code to objects
    - Handle directly any kind of event (not only strings) - parsing strings is
      cool again!
    - Keep it simple, even for someone who's not very familiar with the FSM
      terminology


.. toctree::
   :maxdepth: 2

   pysm_module
   installing
   quickstart
   examples
   user_guide
   cookbook
