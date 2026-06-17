Installation
============

``pysm`` supports Python 3.7 and newer. Install it from
`PyPI <https://pypi.python.org/pypi/pysm/>`_::

    python -m pip install pysm

Or clone the `Github pysm repository <https://github.com/pgularski/pysm/>`_
and install the checkout::

    git clone https://github.com/pgularski/pysm
    cd pysm
    python -m pip install .

The package includes ``py.typed`` and ``.pyi`` files, so type checkers and
editors can use the shipped type information without an extra stub package.
The classic ``from pysm import StateMachine, State, Event`` import remains
dependency-free; optional runtime helpers are imported from their own modules.


MicroPython
-----------

Use ``upysm`` when installing the library on MicroPython. ``upysm`` is the
MicroPython distribution channel for selected ``pysm`` releases; it is not a
fork and does not carry separate application code. The installed package still
imports as ``pysm``:

.. code-block:: python

    from pysm import Event, State, StateMachine

Modern MicroPython installations should use ``mip`` through ``mpremote``:

.. code-block:: console

    mpremote mip install https://pgularski.github.io/upysm/

Pin a specific release for repeatable device builds:

.. code-block:: console

    mpremote mip install https://pgularski.github.io/upysm/0.4.0/

You can also install from the MicroPython REPL:

.. code-block:: python

    import mip
    mip.install('https://pgularski.github.io/upysm/')

Older firmware that still uses ``upip`` can install the package from PyPI:

.. code-block:: python

    import upip
    upip.install('upysm')

The default ``upysm`` build is core-focused. Optional modules such as
``pysm.queued``, ``pysm.aio``, ``pysm.serialization``, and ``pysm.builder`` are
documented for regular Python and should only be added to constrained device
builds intentionally.


Building the documentation locally
----------------------------------

The documentation build uses Sphinx and the Read the Docs theme::

    python -m pip install -r docs/requirements.txt
    python -m sphinx -b html docs docs/_build/html
