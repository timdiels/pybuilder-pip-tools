Developer documentation
=======================

Documentation for developers/contributors of the project.

Project decisions
-----------------
`python.distutils` plugin generates ``setup(dependency_links=...)`` from
``project.depends_on(url=...)``. `dependency_links` is deprecated and we do not
want urls to show up in `setup.py`, so we opt to add 2 properties ``*_urls``
instead of using ``depends_on(url=...)``.
