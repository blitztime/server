"""Configuration file for the Sphinx documentation builder.

https://www.sphinx-doc.org/en/master/usage/configuration.html
"""
import os
import sys

import sphinx_rtd_theme    # noqa:F401


sys.path.insert(0, os.path.abspath('../..'))

project = 'Blitztime API Server'
copyright = '2021, Artemis'
author = 'Artemis'
release = '0.2.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx_rtd_theme',
]

html_theme = 'sphinx_rtd_theme'
