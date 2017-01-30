Developer documentation
=======================

Documentation for developers/contributors of the project.

Project decisions
-----------------
`python.distutils` plugin generates ``setup(dependency_links=...)`` from
``project.depends_on(url=...)``. `dependency_links` is deprecated and we do not
want urls to show up in `setup.py`, so we opt to add 2 properties ``*_urls``
instead of using ``depends_on(url=...)``.

No error is raised when plugin and build requirements conflict. No public
function exists to check whether the intersection of 2 specifier sets is empty.
Implementing such a function would take much effort judging by the length
of the specification of version specifiers, while the issue isn't too hard for
a human to figure out when pip-sync inevitably fails to find a matching
version.
