# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys
sys.path.insert(0, os.path.abspath("../../izzy_heartbeat/"))

project = 'izzy-heartbeat'
copyright = '2025, Rich Dionne'
author = 'Rich Dionne'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
    'sphinx.ext.napoleon',
    'sphinx.ext.autosummary',
    'enum_tools.autoenum',
    'sphinx.ext.todo',
    'myst_parser'
]
autosummary_generate = True
autoclass_content = 'both'
todo_include_todos = True

templates_path = ['_templates']
exclude_patterns = []

myst_enable_extensions = [
    'colon_fence',
    'html_admonition'
]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
