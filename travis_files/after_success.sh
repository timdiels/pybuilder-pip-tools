#!/usr/bin/env sh
set -x

# Only run if all jobs succeeded and we are designated to run the after_success
# (i.e. we ensure it's run only once)
#
# This is a workaround, replace it once this has been released: https://github.com/travis-ci/travis-ci/issues/929
# Workaround: https://github.com/alrra/travis-after-all
npm install travis-after-all
travis-after-all
exit_code=$?
if [ $exit_code = 2 ]; then
    # A different runner will do the after_success
    exit 0
elif [ $exit_code != 0 ]; then
    # A job failed or travis-after-all had an internal error
    exit 1
fi

# Targetting master branch?
if [ "$TRAVIS_BRANCH" = "master" ]; then
    echo master
    # Commit is (version) tagged?
    if [ ! -z "$TRAVIS_TAG" ]; then
        echo tagged
        # Upload to Python index

        if [ "$TRAVIS_PULL_REQUEST" != "false" ]; then
            index=https://testpypi.python.org/pypi
        else
            index=https://pypi.python.org/pypi
        fi

        echo $index

        pyb upload_twine --exclude run_unit_tests --exclude run_integration_tests --exclude verify -P "distutils_upload_repositor=$index"
    fi
fi
