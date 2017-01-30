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

__version__ = '$version'

from pybuilder.core import init, task, depends
from pybuilder.errors import BuildFailedException
from tempfile import NamedTemporaryFile
from glob import glob
import re
import os
import sys
from urllib.parse import urlparse, parse_qs

# Assumptions
# - when referring to extras, a user does so in `name`, e.g. depends_on('pkg[opt1,opt2]')

@init()
def init(project):
    project.plugin_depends_on('pip-tools', '>=1.7.0')
    project.plugin_depends_on('plumbum')
    project.plugin_depends_on('attrs')
    project.set_property_if_unset('pybuilder_pip_tools_urls', [])  
    project.set_property_if_unset('pybuilder_pip_tools_build_urls', [])

@task(description='Update `*requirements*.txt` with pip-compile and pip-sync `*requirements_development.txt`')
@depends('prepare')  # Note: plugin dependencies are installed during 'prepare'
def pip_sync(project):
    import plumbum as pb
    _pip_compile(project.dependencies, project.get_property('pybuilder_pip_tools_urls'), 'requirements', 'depends_on')
    _pip_compile(_merged_dependencies(project), project.get_property('pybuilder_pip_tools_build_urls'), 'build_requirements', 'build_depends_on or plugin_depends_on')
    pb.local['pip-sync'](*glob('*requirements_development.txt'))
    
def _merged_dependencies(project):
    '''
    Get plugin and build dependencies, merged together
    
    Compatible version constraints are merged through intersection.
    '''
    plugin_dependencies = {dependency.name : dependency for dependency in project.plugin_dependencies}
    build_dependency_names = set(dependency.name for dependency in project.build_dependencies)
    plugin_dependency_only_names = plugin_dependencies.keys() - build_dependency_names
    return project.build_dependencies + [plugin_dependencies[name] for name in plugin_dependency_only_names]
    
def _pip_compile(dependencies, urls, requirements_stem, depends_on):
    import attr
    
    # Validate dependencies
    for dependency in dependencies:
        if dependency.url is not None:
            raise BuildFailedException(
                'Dependency url set on {!r}. '
                '{depends_on}(url=...) should be '
                'considered deprecated as it uses '
                'setuptools.setup(dependency_links=...), which is deprecated. '
                'Instead, you have to release the dependency to a Python '
                'index.'
                .format(dependency.name, depends_on=depends_on)
            )
    
    # Merge urls and dependencies
    Dependency = attr.make_class('Dependency', ('name', 'options', 'version', 'url'))
    def split_dependency(dependency):
        match = re.fullmatch(r'([^[]*)(\[.*\])?', dependency.name)
        if not match:
            raise BuildFailedException( 
                'Invalid dependency name {!r}. '
                'Examples of valid names: pkg, pkg[extra1,extra2].'
                .format(dependency.name)
            )
        name, options = match.groups()
        return Dependency(name, options, dependency.version, url=None)
    dependencies = [split_dependency(dependency) for dependency in dependencies]
    dependencies = {dependency.name: dependency for dependency in dependencies}
    for url in urls:
        url = url.strip()
        
        # Prepend -e if missing. pip-compile only supports -e urls
        if url.startswith('-e'):
            url = url[3:].strip()
        
        # Split url
        url_parts = urlparse(url)
        if not url_parts.scheme:
            raise BuildFailedException( 
                "Dependency url must start with '{{scheme}}://', got: {!r}."
                .format(url)
            )
            
        # Get egg parameter from fragment
        query_parameters = parse_qs(url_parts.fragment)
        if not 'egg' in query_parameters:
            raise BuildFailedException( 
                "Missing '#egg=pkg-name-version' fragment in url {!r}."
                .format(url)
            )
        egg = query_parameters['egg'][0]
        
        # Get name from egg parameter
        parts = egg.split('-')
        if len(parts) == 1:
            raise BuildFailedException( 
                "Missing version in 'egg' parameter of url {!r}. "
                "Please add version such that: 'egg={{pkg-name}}-{{version}}'."
                .format(url)
            )
        name = '-'.join(parts[:-1])
        
        # Raise if package is not a dependency
        if name not in dependencies:
            raise BuildFailedException( 
                "Dependency url references dependency {name!r}, but {name!r} is not registered "
                "as a dependency via {depends_on}. "
                "Possible causes: "
                "1) forgot to add with {depends_on}, "
                "2) meant to use the build/runtime counterpart or "
                "3) forgot to specify version in '#egg={{pkg-name}}-{{version}}' fragment."
                .format(name=name, depends_on=depends_on)
            )
        
        # Append options, version and update dependency with url
        dependency = dependencies[name]
        if dependency.options:
            url += dependency.options
        if dependency.version:
            url += dependency.version
        dependency.url = url
    
    # Compile requirements.txt with a temporary requirements.in file
    _write_requirements_txt(dependencies, requirements_stem + '_development.txt', use_urls=True)
    _write_requirements_txt(dependencies, requirements_stem + '.txt', use_urls=False)
    
def _write_requirements_txt(dependencies, requirements_file, use_urls):
    import plumbum as pb
    requirements_in = NamedTemporaryFile('w', delete=False)
    try:
        # Write a requirements.in file
        with requirements_in:
            for dependency in dependencies.values():
                if dependency.url is not None and use_urls:
                    line = dependency.url
                    if not line.startswith('-e'):  # pip-compile only supports -e urls, so prefix -e if missing
                        line = '-e ' + line
                else:
                    line = dependency.name
                    if dependency.options:
                        line += dependency.options
                    if dependency.version:
                        line += dependency.version
                requirements_in.write(line + '\n')
                
        # Compile it to .txt
        pb.local['pip-compile'](requirements_in.name, '-o', requirements_file,
            '--no-header', '--no-annotate'  # make output more deterministic, handy when file is tracked (changes less often)
        )
        
    finally:
        os.unlink(requirements_in.name)
        