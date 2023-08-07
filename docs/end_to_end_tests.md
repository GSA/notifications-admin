# Working with End-to-End Tests

End-to-End (E2E) tests are an important part of a assessing the overall
integrity and stability of a system.  They are a part of the overall
test suite and serve the function of simulating a user working through
the application.  By having comprehensive E2E tests in place, we can
instill higher confidence that future changes and refactorings won't
negatively impact any user experience or break existing functionality.

The US Notify project leverages [`pytest`](https://pytest.org/) for its
existing test suite (at least on the Python side of things) and is now
leveraging [Playwright for Python](https://playwright.dev/python/)
along with its `pytest` plugin for the E2E tests.


## Getting Started

To work with the E2E tests in US Notify, you need to make sure you have
all of the necessary components installed.  The quick and easy way to do
this is to use the Makefile as you did for the initial project setup. In
fact, if you've already done this, you are already set to go!  If not,
then run the bootstrap command in your shell:

```sh
make bootstrap
```

This takes care of installing all of your dependencies, including those
now needed for Playwright.

If you run into certificate errors at the `playwright install` step, try
doing this:

1. Run `brew --prefix` to see Homebrew's root directory

1. Create or modify the local `.env` file in the project and add this line:

   `NODE_EXTRA_CA_CERTS=/CHANGE-TO-HOMEBREW-INSTALL-PATH/etc/ca-certificates/cert.pem`

   Make sure to change `CHANGE-TO-HOMEBREW-INSTALL-PATH` to the path
   given by `brew --prefix` in the step above.  For example, if `brew --prefix`
   gave `/opt/homebrew` as output, then the line would look like this:

   `NODE_EXTRA_CA_CERTS=/opt/homebrew/etc/ca-certificates/cert.pem`

1. Save the changes to the `.env` file

1. Run `make bootstrap` again


### Manual Installation

If you need to install things separately, you'll still need to make sure
your environment is set up and configured as outlined in the README.

At your shell in the project root folder, run the following commands:

```sh
pipenv install pytest-playwright
pipenv run playwright install --with-deps
```

This will install Playwright and its `pytest` plugin, then the
additional dependencies that Playwright requires.

See more details on the [Playwright for Python Installation page](https://playwright.dev/python/docs/intro).


## Local Configuration

In order to run the E2E tests successfully on your local machine, you'll also
need to make sure you have a `.env` file in the root project folder, and that it
has at least these environment variables set in it:

```
NOTIFY_STAGING_URI
NOTIFY_STAGING_HTTP_AUTH_USER
NOTIFY_STAGING_HTTP_AUTH_PASSWORD
```

This file is **not** checked into source control and is configured to be
ignored in the project's `.gitignore` file; please be careful that it is
not committed to the repo and pushed!


## Running E2E Tests Locally

To run the E2E tests on your local machine, type this command in your
shell at the project root directory:

```sh
make e2e-test
```

You should see `pytest` start producing output and the existing E2E
tests run in multiple headless browsers.


## How to Create and Maintain E2E Tests

All of the E2E tests are found in the `tests/end_to_end` folder and are
written as `pytest` scripts using [Playwright's Python Framework](https://playwright.dev/python/docs/writing-tests).


## Maintaining E2E Tests with GitHub

The E2E tests are configured to run as a separate GitHub action as a
part of our other checks found in `.github/workflows/checks.yml`.

The E2E tests are not run as a part of the regular unit test suite; if
you look at the `Makefile` you'll see that the tests are two separate
commands, with the E2E tests configured separately.

This is done for a couple of reasons:

- Keeps unit tests isolated from the E2E tests
- Allows us to configure E2E tests separately

The environment variables are managed as a part of the GitHub
repository settings.
