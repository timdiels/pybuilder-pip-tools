#!/usr/bin/env sh

# On master branch?
if [ `git rev-parse --abbrev-ref HEAD` = "master" ]; then
    # Commit is (version) tagged?
    if [ git name-rev --tags --no-undefined HEAD >/dev/null 2>&1 ]; then
        # Upload to Python index

        if [ "$TRAVIS_PULL_REQUEST" != "false" ]; then
            index=https://testpypi.python.org/pypi
        else
            index=https://pypi.python.org/pypi
        fi

        pyb upload_twine --exclude run_unit_tests --exclude run_integration_tests --exclude verify -P "distutils_upload_repositor=$index"
    fi
fi
