# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
import os

sys.path.insert(0, os.path.abspath('../src'))

project = 'Signal-Bot'
copyright = '2023, Sidneys1'
author = 'Sidneys1'
from signal_bot.version import VERSION  # pylint: disable=wrong-import-position
version = f'v{VERSION}'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', "sphinx_autodoc_typehints", 'sphinx_paramlinks', "myst_parser"]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_theme_options = {
    'navigation_depth': 3,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'style_external_links': True,
}

autodoc_default_options = {
    "members": True,
    # "inherited-members": True,
    "member-order": "bysource",
    "undoc-members": False,
    "autoclass_content": "both",
    "show-inheritance": True,
}

autodoc_typehints = 'description'
autodoc_typehints_description_target = 'documented_params'
typehints_use_signature_return = False
# typehints_defaults = 'braces-after'
myst_heading_anchors = 2
autodoc_typehints_format = 'short'
python_use_unqualified_type_names = True
