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

Different ways to attach event handlers
---------------------------------------

A state machine and states may be created in many ways. The code below mixes
many styles to demonstrate it (In production code you'd rather keep your code
style consistent). One way is to subclass the |State| class and attach event
handlers to it. This resembles the State Pattern way of writing a state
machine. But handlers may live anywhere, really, and you can attach them
however you want. You're free to chose your own style of writing state machines
with pysm.

.. include:: ../examples/oven.py
    :literal:
