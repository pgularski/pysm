# -*- coding: utf-8 -*-
#
# pysm documentation build configuration file.

import os
import sys

# Make the project importable when building docs without installing the package.
sys.path.insert(0, os.path.abspath(os.pardir))


# -- General configuration ------------------------------------------------

needs_sphinx = '7.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx.ext.extlinks',
]

templates_path = ['_templates']

source_suffix = {
    '.rst': 'restructuredtext',
}

master_doc = 'index'

project = 'pysm'
copyright = '2026, Piotr Gularski'
author = 'Piotr Gularski'

try:
    from pysm import __version__

    version = '.'.join(__version__.split('.')[:2])
    release = __version__
except ImportError:
    version = release = 'dev'

language = 'en'

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

pygments_style = 'sphinx'

todo_include_todos = False


# -- Autodoc configuration ------------------------------------------------

autodoc_member_order = 'bysource'
autodoc_typehints = 'description'


# -- Intersphinx configuration --------------------------------------------

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
}


# -- External links -------------------------------------------------------

extlinks = {
    'issue': ('https://github.com/pgularski/pysm/issues/%s', '#%s'),
    'pull': ('https://github.com/pgularski/pysm/pull/%s', 'PR #%s'),
}


# -- Options for HTML output ----------------------------------------------

html_theme = 'sphinx_rtd_theme'

html_static_path = ['_static']

htmlhelp_basename = 'pysmdoc'


# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    # The paper size: 'letterpaper' or 'a4paper'.
    # 'papersize': 'letterpaper',

    # The font size: '10pt', '11pt' or '12pt'.
    # 'pointsize': '10pt',

    # Additional LaTeX preamble.
    # 'preamble': '',

    # LaTeX figure float alignment.
    # 'figure_align': 'htbp',
}

latex_documents = [
    (
        master_doc,
        'pysm.tex',
        'pysm Documentation',
        'Piotr Gularski',
        'manual',
    ),
]


# -- Options for manual page output ---------------------------------------

man_pages = [
    (
        master_doc,
        'pysm',
        'pysm Documentation',
        [author],
        1,
    ),
]


# -- Options for Texinfo output -------------------------------------------

texinfo_documents = [
    (
        master_doc,
        'pysm',
        'pysm Documentation',
        author,
        'pysm',
        'Python State Machine implementation.',
        'Miscellaneous',
    ),
]
