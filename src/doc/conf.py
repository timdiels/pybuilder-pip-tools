# Generated by pyb, do not edit, edit _conf.py instead.

# Before committing after changing this file, first run ``pyb prepare`` such that conf.py is up to date
version = '1.0.1'
author = 'VIB/BEG/UGent, Tim Diels'
project = 'PyBuilder Pip Tools'
copyright = '2016, ' + author

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'sphinx.ext.mathjax',
    'numpydoc',
    'sphinx.ext.doctest',
    'sphinx.ext.coverage',
    'sphinx.ext.autosummary',
]

#--- rarely need to change anything below ------
numpydoc_show_class_members = False  # setting this to True breaks autosummary and not having autosummary breaks numpydoc

release = version
language = 'en'
pygments_style = 'sphinx'
templates_path = ['_templates']
source_suffix = '.rst'
todo_include_todos = True
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
master_doc = 'index'

# html
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# epub
epub_title = project
epub_publisher = author
epub_author = author
epub_copyright = copyright
epub_exclude_files = ['search.html']

# latex
latex_documents = [(master_doc, 'pybuilder-pip-tools.tex', project + ' Documentation', author, 'manual')]
latex_elements = {}

# texinfo
texinfo_documents = [(master_doc, 'pybuilder-pip-tools', project + ' Documentation', author, project, 'PyBuilder plugin to generate and install requirements.txt files from project (build) dependencies', 'Miscellaneous')]