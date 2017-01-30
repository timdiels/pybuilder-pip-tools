# Copyright (C) 2016 VIB/BEG/UGent - Tim Diels <timdiels.m@gmail.com>
# 
# This file is part of PyBuilder Pip Tools.
# 
# PyBuilder Pip Tools is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# PyBuilder Pip Tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with PyBuilder Pip Tools.  If not, see <http://www.gnu.org/licenses/>.

'''
Test everything
'''

import pytest
import os
import sys
import plumbum as pb
from textwrap import dedent, indent

####################################
# pybuilder test lib for Python>=2.6. Same stability as plugin.

def pyb(init_body):
    '''
    Create build.py and call pyb
    '''
    content = (
        dedent(
            '''\
            from pybuilder.core import init, use_plugin
            
            use_plugin('python.core')
            use_plugin('pybuilder_pip_tools')
            
            @init
            def init(project):
            {}
            '''
        )
        .format(indent(dedent(init_body), '    '))
    )
    with open('build.py', 'w') as f:
        f.write(content)
    pb.local['vex']('--path', 'venv', '-m', 'pip', 'install', '-U', 'pip', 'setuptools', 'wheel', 'pybuilder', 'pytest-cov')   #TODO does this use `which python` or some other Python version for the venv? It should match
    pb.local['vex']('--path', 'venv', 'pyb', '-X', 'pip_sync')
    
def assert_pyb_fails(init_body, failure_message):
    with pytest.raises(pb.ProcessExecutionError) as ex:
        pyb(init_body)
    message = 'BUILD FAILED - ' + failure_message
    print(ex.value.stdout)
    print(ex.value.stderr, file=sys.stderr)
    assert message in ex.value.stdout, '\nExpected stdout to contain: {}'.format(message)
    
def create_project(name, version='1.0.0'):
    '''
    Create directory with a setup.py
    
    Returns absolute file:// url to it.
    '''
    os.mkdir(name)
    with open(os.path.join(name, 'setup.py'), 'w') as f:
        f.write(
            dedent('''\
                setup(name={name!r},
                  version={version!r},
                  description='Example description',
                  author='James Foobar',
                  author_email='foobar@example.com',
                  url='https://example.com/',
                  packages=[],
                )
            ''')
            .format(name=name, version=version)
        )
    return 'file://' + os.path.abspath(name)

@pytest.yield_fixture(autouse=True)
def use_temp_dir(tmpdir):  # Based on chicken_turtle_util.test.use_temp_dir
    '''
    pytest fixture that sets current working directory to a temporary directory
    '''
    original_cwd = os.getcwd()
    os.chdir(str(tmpdir))
    yield tmpdir
    os.chdir(str(original_cwd))
    
def assert_text_contains(whole, part):  # From chicken_turtle_util.test.assert_text_contains
    '''
    Assert long string contains given string
    '''
    assert part in whole, '\nActual:\n{}\n\nExpected to contain:\n{}'.format(whole, part)
    
####################################

@pytest.mark.parametrize('depends_on, pybuilder_pip_tools_urls, requirements, requirements_development, depends_on_text', (
    ('depends_on', 'pybuilder_pip_tools_urls', 'requirements.txt', 'requirements_development.txt', 'depends_on'),
    ('build_depends_on', 'pybuilder_pip_tools_build_urls', 'build_requirements.txt', 'build_requirements_development.txt', 'build_depends_on or plugin_depends_on'),
    ('plugin_depends_on', 'pybuilder_pip_tools_build_urls', 'build_requirements.txt', 'build_requirements_development.txt', 'build_depends_on or plugin_depends_on'),
))
class TestAll(object):
        
    def test_url_scheme_missing(self, depends_on, pybuilder_pip_tools_urls, requirements, requirements_development, depends_on_text):
        '''
        When url lacks scheme://, fail build
        '''
        name = 'pkg'
        assert_pyb_fails(
            init_body='''\
                project.{depends_on}({name!r})
                project.get_property({pybuilder_pip_tools_urls!r}).append({url!r})
            '''.format(
                depends_on=depends_on,
                pybuilder_pip_tools_urls=pybuilder_pip_tools_urls,
                name=name,
                url=name
            ),
            failure_message="Dependency url must start with '{{scheme}}://', got: {!r}".format(name)
        )
        
    @pytest.mark.parametrize('fragment', [False, True])
    def test_url_missing_egg_parameter(self, depends_on, pybuilder_pip_tools_urls, requirements, requirements_development, depends_on_text, fragment):
        '''
        When url lacks '#egg=name-version' entirely, fail build
        '''
        name = 'pkg'
        url = create_project(name)
        if fragment:
            url += '#other=meh'
        assert_pyb_fails(
            init_body='''\
                project.{depends_on}({name!r})
                project.get_property({pybuilder_pip_tools_urls!r}).append({url!r})
            '''.format(
                depends_on=depends_on,
                pybuilder_pip_tools_urls=pybuilder_pip_tools_urls,
                name=name,
                url=url
            ),
            failure_message="Missing '#egg=pkg-name-version' fragment in url {!r}".format(url)
        )
        
    def test_url_missing_version(self, depends_on, pybuilder_pip_tools_urls, requirements, requirements_development, depends_on_text):
        '''
        When url has egg=name instead of egg=name-version, fail build
        '''
        name = 'pkg'
        url = create_project(name)
        url += '#egg=' + name
        assert_pyb_fails(
            init_body='''\
                project.{depends_on}({name!r})
                project.get_property({pybuilder_pip_tools_urls!r}).append({url!r})
            '''.format(
                depends_on=depends_on,
                pybuilder_pip_tools_urls=pybuilder_pip_tools_urls,
                name=name,
                url=url
            ),
            failure_message=(
                "Missing version in 'egg' parameter of url {!r}. "
                "Please add version such that: 'egg={{pkg-name}}-{{version}}'."
                .format(url)
            )
        )
         
    def test_url_not_in_dependencies(self, depends_on, pybuilder_pip_tools_urls, requirements, requirements_development, depends_on_text):
        '''
        When url refers to package not listed in project dependencies, fail build
        '''
        name = 'pkg'
        url = create_project(name)
        url += '#egg={}-1.0.0'.format(name)
        assert_pyb_fails(
            init_body='''\
                project.get_property({pybuilder_pip_tools_urls!r}).append({url!r})
            '''.format(
                depends_on=depends_on,
                pybuilder_pip_tools_urls=pybuilder_pip_tools_urls,
                name=name,
                url=url
            ),
            failure_message=(
                "Dependency url references dependency {name!r}, but {name!r} is not registered "
                "as a dependency via {depends_on}. "
                "Possible causes: "
                "1) forgot to add with {depends_on}, "
                "2) meant to use the build/runtime counterpart or "
                "3) forgot to specify version in '#egg={{pkg-name}}-{{version}}' fragment."
                .format(name=name, depends_on=depends_on_text)
            )
        )
        
    def assert_basic(self, depends_on, pybuilder_pip_tools_urls, requirements_development, name, url):
        pyb(
            init_body='''\
                project.{depends_on}({name!r})
                project.get_property({pybuilder_pip_tools_urls!r}).append({url!r})
            '''.format(
                depends_on=depends_on,
                pybuilder_pip_tools_urls=pybuilder_pip_tools_urls,
                name=name,
                url=url
            )
        )
        
        # Check url appears in requirements_development
        with open(requirements_development) as f:
            content = [line.rstrip() for line in f.readlines()]
        assert '-e ' + url in content

    @pytest.mark.parametrize('fragment', ('#egg={}-0', '#egg={}-0&other=meh', '#other=meh&egg={}-0'))
    def test_valid_fragments(self, depends_on, pybuilder_pip_tools_urls, requirements, requirements_development, depends_on_text, fragment):
        '''
        When valid fragment, work fine
        '''
        name = 'pybuilder'
        url = 'git+https://github.com/pybuilder/pybuilder.git'
        url += fragment.format(name)
        self.assert_basic(depends_on, pybuilder_pip_tools_urls, requirements_development, name, url)
        
    def test_dashed_name(self, depends_on, pybuilder_pip_tools_urls, requirements, requirements_development, depends_on_text):
        '''
        When package name contains dashes, work fine
        '''
        name = 'cubicweb-celery'
        url = 'hg+https://hg.logilab.org/review/cubes/celery#egg=cubicweb-celery-0'
        self.assert_basic(depends_on, pybuilder_pip_tools_urls, requirements_development, name, url)
        
    def test_output_files(self, depends_on, pybuilder_pip_tools_urls, requirements, requirements_development, depends_on_text):
        '''
        When valid url, correct output files
        
        - requirements: no urls
        - requirements_development: urls when overridden
        
        In both cases, add version constraint if given.
        '''
        name = 'pybuilder'
        url = 'git+https://github.com/pybuilder/pybuilder.git#egg=pybuilder-0'
        version = '==0.11.5'
        pyb(
            init_body='''\
                project.{depends_on}('fpkg', '==0.1')
                project.{depends_on}({name!r}, {version!r})
                project.get_property({pybuilder_pip_tools_urls!r}).append({url!r})
            '''.format(
                depends_on=depends_on,
                pybuilder_pip_tools_urls=pybuilder_pip_tools_urls,
                name=name,
                url=url,
                version=version
            )
        )
        
        # Check requirements: no urls, but do include package with correct version
        with open(requirements) as f:
            lines = [line.strip() for line in f.readlines()]
        for line in lines:
            assert not line.startswith('-e')
        assert name + version in lines
        assert 'fpkg==0.1' in lines
        
        # Check requirements: overridden urls appear, non-overridden appear as non-url; with correct version 
        with open(requirements_development) as f:
            lines = [line.strip() for line in f.readlines()]
        assert '-e ' + url + version in lines
        assert name + version not in lines
        assert 'fpkg==0.1' in lines

# Reenable if we implement conflict detection
# class TestPluginBuildConflicts(object):
#     
#     '''
#     When a dependency appears as build and plugin dependency, test whether it
#     conflicts in the right cases
#     '''
#     
#     def test_no_version(self):
#         '''
#         When both having no version, no conflict 
#         '''
#         pyb(
#             init_body='''\
#                 project.plugin_depends_on('click')
#                 project.build_depends_on('click')
#             '''
#         )
#         
#     def test_compatible_version(self):
#         '''
#         When compatible versions, no conflict
#         '''
#         pyb(
#             init_body='''\
#                 project.plugin_depends_on('click', '>6.0')
#                 project.build_depends_on('click', '>6.4')
#             '''
#         )
#         
#         
#     def test_options_ignored(self):
#         '''
#         When having different options, not necessarily a conflict 
#         '''
#         pyb(
#             init_body='''\
#                 project.plugin_depends_on('chicken_turtle_util[click]', '==4.0.1')
#                 project.build_depends_on('chicken_turtle_util[debug]', '==4.0.1')
#             '''
#         )
#                 
#     def test_incompatible_version(self):
#         '''
#         When incompatible versions, conflict
#         '''
#         assert_pyb_fails(
#             init_body='''\
#                 project.plugin_depends_on('click', '>6.4')
#                 project.build_depends_on('click', '<6.4')
#             ''',
#             failure_message='TODOTODO8798789789799' #TODO
#         )
        
def test_sync():
    '''
    `*requirements_development.txt` get synced
    '''
    pyb(
        init_body='''\
            project.depends_on('cubicweb-celery')
            project.get_property('pybuilder_pip_tools_urls').append('hg+https://hg.logilab.org/review/cubes/celery@163a41551c67#egg=cubicweb-celery-0')
            project.build_depends_on('pybuilder')
            project.get_property('pybuilder_pip_tools_build_urls').append('git+https://github.com/pybuilder/pybuilder.git@1cb3723f95fcf5aab4d65b0524e16d2c6bb59a87#egg=pybuilder-0')
        '''
    )
    
    # Assert installed `*_development.txt`, i.e. urls were used.
    lines = pb.local['vex']('--path', 'venv', 'pip', 'freeze').splitlines()
    print(lines)
    assert any(line.startswith('PyBuilder==0.11.10.dev') for line in lines)
    assert 'cubicweb-celery==0.1' in lines
