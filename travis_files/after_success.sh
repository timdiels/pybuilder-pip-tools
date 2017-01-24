#!/usr/bin/env sh

# Commit is (version) tagged?
if [ ! -z "$TRAVIS_TAG" ]; then
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

    # Upload to Python index
    pyb upload_twine --exclude run_unit_tests --exclude run_integration_tests --exclude verify
fi
