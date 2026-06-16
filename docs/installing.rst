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


Building the documentation locally
----------------------------------

The documentation build uses Sphinx and the Read the Docs theme::

    python -m pip install -r docs/requirements.txt
    python -m sphinx -b html docs docs/_build/html
