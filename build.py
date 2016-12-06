from pybuilder.core import use_plugin, init, Author, task, before, depends
from pybuilder.errors import BuildFailedException

@task
def tmp_stuff(project):
    for name, value in project.properties.items():
        if 'src' in str(value):
            print(name, value)
            
# plugin imports
import re
import os

use_plugin('python.core')
use_plugin('python.install_dependencies')
use_plugin('python.distutils')
use_plugin('python.sphinx')
use_plugin('copy_resources')
use_plugin('filter_resources')
use_plugin('source_distribution')

default_task = ['clean', 'package']

name = 'pybuilder-pip-tools'
version = '1.0.0'
summary = 'PyBuilder plugin to generate and install requirements.txt files from project (build) dependencies'
url = 'https://github.com/timdiels/pybuilder-pip-tools'  # Project home page
license = 'LGPLv3'
authors = [
    Author('VIB/BEG/UGent', 'info@psb.ugent.be'),  # Note: an email is required
    Author('Tim Diels', 'timdiels.m@gmail.com'),
]

@init()
def plugin_initialize(project, logger):
    # Validate project name: pybuilder_validate_name, _mode=strict|lenient. No off, that's what #use_plugin is for
    if re.search('\s', project.name):
        raise BuildFailedException('Project name may not contain whitespace, use dashes instead')
    if re.search('_', project.name): #TODO also raise on underscores and upper case unless project.set_property('pybuilder_chicken_turtle_name_validation', 'lenient') # default = 'strict'. When lenient, do not even warn; either raise or don't. This also means the name check needs to happen after init, so user can set this property
        raise BuildFailedException('Project name contains underscores, use dashes instead')
    if project.name.lower() != project.name:
        raise BuildFailedException('Project name contains upper case characters, use lower case instead')
    
    # Assert required files exist
    for file in ['LICENSE.txt', 'README.rst']:
        if not os.path.exists(file):
            raise BuildFailedException('Missing required file: {}'.format(file))
        
    # Files not to include in source distribution 
    project.get_property('source_dist_ignore_patterns').extend([
        '.project',
        '.pydevproject',
        '.settings'
    ])

    # Files to copy to dist root
    project.set_property('copy_resources_target', '$dir_dist')
    project.get_property('copy_resources_glob').extend([
        'README.rst',
        'LICENSE.txt',
    ])
    
    # setup.py
    with open('README.rst') as f:
        project.description = f.read()
    project.set_property('distutils_readme_file', 'README.rst')  # readme file name, should be at the root (like build.py). Defaults to README.md

################################
# pybuilder_pytest
#

'''
PyBuilder plugin which runs pytest on ``$dir_source_unittest_python``.

At task `run_unit_tests`, runs pytest on ``$dir_source_unittest_python``. The
latter defaults to ``src/unittest/python``. (`PYTHONPATH` is set to include
``$dir_source_main_python`` and ``$dir_source_unittest_python``)

To configure pytest, `write a pytest.ini or setup.cfg file`__ as usual.

.. __: http://doc.pytest.org/en/latest/customize.html
'''

import os

# python: 2.6 (because py.test and plumbum)

@init
def pytest_init(project):  #TODO rm prefix
    project.plugin_depends_on('plumbum')
    project.plugin_depends_on('pytest')
    project.set_property_if_unset('dir_source_unittest_python', 'src/unittest/python')
    
@task('run_unit_tests')
def pytest_run_unit_tests(project, logger):  #TODO rm prefix
    import plumbum as pb
    
    # PYTHONPATH
    path_parts = []
    if 'PYTHONPATH' in pb.local.env:
        path_parts.append(pb.local.env['PYTHONPATH'])
    path_parts.append(project.expand_path('$dir_source_main_python'))
    dir_source_unittest_python = project.expand_path('$dir_source_unittest_python')
    path_parts.append(dir_source_unittest_python)
    PYTHONPATH = os.pathsep.join(path_parts)
    
    # Run
    with pb.local.env(PYTHONPATH=PYTHONPATH):
        try:
            pb.local['py.test']['--maxfail', '1', '-v', '--lf', dir_source_unittest_python] & pb.FG #TODO rm --maxfail 1 -v --lf when final, add a property instead: pybuilder_pytest_args
        except pb.ProcessExecutionError as ex:
            raise BuildFailedException('py.test failed') from ex


################################

@init()
def build_dependencies(project):
    # PyBuilder
    project.build_depends_on('pybuilder') #TODO >=0.11.10 < 1.0.0 once available. There are 0.11.10.dev* releases though, maybe we could set directly to that
#     project.get_property('pybuilder_pip_tools_build_urls').extend([
#         'git+https://github.com/pybuilder/pybuilder.git#egg=pybuilder-0'
#     ])
    
    # Testing
    project.build_depends_on('pytest-env')
    project.build_depends_on('pytest-timeout')
    project.build_depends_on('pytest-mock')
    
    # pybuilder test lib (TODO)
    project.build_depends_on('plumbum')
    project.build_depends_on('vex')
    
    # Sphinx doc (sphinx already imported by python.sphinx plugin)
    project.build_depends_on('numpydoc')
    project.build_depends_on('sphinx-rtd-theme')
    
@init()
def initialize(project):
    # Package data
    # E.g. project.include_file('the.pkg', 'relative/to/pkg/some_file')

    # Files in which to replace placeholders like ${version}
    project.get_property('filter_resources_glob').extend([
        '**/pybuilder_pip_tools/__init__.py',
    ])

    # setup.py
    project.set_property('distutils_console_scripts', [  # entry points
    ])
    project.set_property('distutils_setup_keywords', 'pybuilder plugin pip-tools requirements.txt')
    project.set_property('distutils_classifiers', [  # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Build Tools',
    ])
    
    # doc: sphinx
    project.set_property('sphinx_project_name', 'PyBuilder Pip Tools')
    project.set_property('sphinx_run_apidoc', False)
    project.set_property('sphinx_source_dir', 'src/doc/sphinx')
    project.set_property('sphinx_config_path', 'src/doc/sphinx')
    project.set_property('sphinx_output_dir', '$dir_target/doc/sphinx')
