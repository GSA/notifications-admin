![notify-logo](https://github.com/GSA/notifications-admin/assets/4156602/31b74039-4d87-4f89-a35e-71e9f3152342)

# Notify.gov Admin UI

This is the Notify front-end for government users and admins. To see it in
action, check out [the demo site](https://notify-demo.app.cloud.gov)
(contact team for credentials).

Through the interface, users can:

- Register and manage users
- Create and manage services
- Send batch SMS by uploading a CSV
- View their history of notifications

The [Notify.gov API](https://github.com/GSA/notifications-api) provides the
UI's backend and is required for most things to function. Set that up first!

Our other repositories are:

- [notifications-admin](https://github.com/GSA/notifications-admin)
- [us-notify-compliance](https://github.com/GSA/us-notify-compliance/)
- [notify-python-demo](https://github.com/GSA/notify-python-demo)

## Before You Start

### Pre-requisites

Before setting up the Admin UI, you must complete the following:

1. **Set up the Notify.gov API first** - [Follow the complete API setup instructions here](https://github.com/GSA/notifications-api#before-you-start). The API is required for the Admin UI to run and handles most of the system dependencies (Homebrew, Python, Poetry, Terraform, etc.).

2. **Cloud.gov account** - An active cloud.gov account with access to the `notify-local-dev` and `notify-staging` spaces. Contact your onboarding buddy for help with [setting up an account](https://cloud.gov/sign-up/) (requires a `.mil`, `.gov`, or `.fed.us` email address).

3. **Admin privileges** - Admin privileges and SSH access on your machine. Work with your organization's IT support staff if you need help with this.

## Local Environment Setup

This project is set up to work with
[nvm (Node Version Manager)](https://github.com/nvm-sh/nvm#installing-and-updating)
for managing and using Node.js (version 22.3.0) and the `npm` package manager.

### Docker installation

If you are using VS Code, there are also instructions for
[running inside Docker](./docs/docker-remote-containers.md).

### Node.js and npm Installation

The project will manage most of the Node.js pieces for you, but you will need to
install [nvm (Node Version Manager)](https://github.com/nvm-sh/nvm#installing-and-updating).

Follow the [nvm installation instructions](https://github.com/nvm-sh/nvm#installing-and-updating)
to install it with the provided script. The installation will automatically set up
your shell configuration.

### First-Time Project Setup

Once all of pre-requisites for the project are installed and you have a
cloud.gov account, you can now set up the admin project and get things running
locally!

First, clone the repository in the directory of your choosing on your machine:

```sh
git clone git@github.com:GSA/notifications-admin.git
```

Now go into the project directory (`notifications-admin` by default), create a
virtual environment, and set the local Python version to point to the virtual
environment (assumes version Python `3.13.2` is what is installed on your
machine):

```sh
cd notifications-admin
pyenv virtualenv 3.13.2 notify-admin
pyenv local notify-admin
```

_NOTE: If you're not sure which version of Python was installed with `pyenv`, you can check by running `pyenv versions` and it'll list everything available currently._

Now [log into cloud.gov](https://cloud.gov/docs/getting-started/setup/#set-up-the-command-line)
in the command line by using this command:

```sh
cf login -a api.fr.cloud.gov --sso
```

_REMINDER: Ensure you have access to the `notify-local-dev` and `notify-staging` spaces in cloud.gov_

Now run the development Terraform setup by navigating to the development
folder and running the script in it:

```sh
cd terraform/development
./run.sh
```

In addition to some infrastructure setup, this will also create a local `.env`
file for you in the project's root directory, which will include a handful of
project-specific environment variables.

#### Upgrading Python in existing projects

If you're upgrading an existing project to a newer version of Python, you can
follow these steps to get yourself up-to-date.

First, use `pyenv` to install the newer version of Python you'd like to use;
we'll use `3.13` in our example here since we recently upgraded to this version:

```sh
pyenv install 3.13
```

Next, delete the virtual environment you previously had set up. If you followed
the instructions above with the first-time set up, you can do this with `pyenv`:

```sh
pyenv virtualenv-delete notify-admin
```

Now, make sure you are in your project directory and recreate the same virtual
environment with the newer version of Python you just installed:

```sh
cd notifications-admin
pyenv virtualenv 3.13.2 notify-admin
pyenv local notify-admin
```

At this point, proceed with the rest of the instructions here in the README and
you'll be set with an upgraded version of Python.

_NOTE: If you're not sure about the details of your current virtual environment, you can run `poetry env info` to get more information. If you've been using `pyenv` for everything, you can also see all available virtual environments with `pyenv virtualenvs`._


#### Poetry upgrades ####

If you are doing a new project setup, then after you install poetry you need to install the export plugin

```sh
poetry self add poetry-plugin-export
```

If you are upgrading from poetry 1.8.5, you need to do this:

```sh
curl -sSL https://install.python-poetry.org | python3 - --version 2.1.3
poetry self add poetry-export-plugin
```

#### Updating the .env file for Login.gov

To configure the application for Login.gov, you will need to update the following environment variables in the .env file:

```
COMMIT_HASH=”--------”
```

Reach out to someone on the team to get the most recent Login.gov key.

```
LOGIN_PEM="INSERT_LOGIN_GOV_KEY_HERE"
```

#### Updating the .env file for E2E tests

With the newly created `.env` file in place, you'll need to make one more
adjustment in it for things to run properly for the E2E tests.

Open the `.env` file and look for the `NODE_EXTRA_CA_CERTS` environment variable
toward the top. You will need to modify its value to be the path to Homebrew's
CA certificate file.

Run `brew --prefix` to see Homebrew's root directory, and use that value to
update the `NODE_EXTRA_CA_CERTS` environment variable with the path. For
example, if `brew --prefix` gave `/opt/homebrew` as output, then the line would
look like this:

```
NODE_EXTRA_CA_CERTS=/opt/homebrew/etc/ca-certificates/cert.pem
```

Save this change to the `.env` file and you'll be squared away.

## Running the Project and Routine Maintenance

The first time you run the project you'll need to run the project setup from the
root project directory:

```sh
make bootstrap
```

This command is handled by the `Makefile` file in the root project directory, as
are a few others.

_NOTE: Run `make bootstrap` again whenever you pull new changes that include dependency updates or when you encounter issues with your development environment. This ensures your project stays up-to-date._

Now you can run the web server and background workers for asynchronous jobs:

```sh
make run-flask
```

This will run the local development web server and make the admin site
available at http://localhost:6012; remember to make sure that the Notify.gov
API is running as well!

## Creating a 'First User' in the database

To login as a user in the database, first create that user with the `create-test-user`
command. There will then be a user to link to your login.gov account.

Open a terminal pointing to the api project and then run this command.

```poetry run flask command create-test-user --admin=True```

Supply your name, email address, mobile number, and password when prompted. Make sure the email address
is the same one you are using in login.gov and make sure your phone number is in the format 5555555555.

If for any reason in the course of development it is necessary for your to delete your db
via the `dropdb` command, you will need to repeat these steps when you recreate your db.

## Git Hooks

We're using [`pre-commit`](https://pre-commit.com/) to manage hooks in order to
automate common tasks or easily-missed cleanup. It's installed as part of
`make bootstrap` and is limited to this project's virtualenv.

To run the hooks in advance of a `git` operation, use
`poetry run pre-commit run`. For running across the whole codebase (useful after
adding a new hook), use `poetry run pre-commit run --all-files`.

The configuration is stored in `.pre-commit-config.yaml`. In that config, there
are links to the repos from which the hooks are pulled, so hop through there if
you want a detailed description of what each one is doing.

We do not maintain any hooks in this repository.

## Python Dependency Management

We're using [`Poetry`](https://python-poetry.org/) for managing our Python
dependencies and local virtual environments.

This project has two key dependency files that must be managed together:

- `pyproject.toml` - Contains the dependency specifications
- `poetry.lock` - Contains the exact versions of all dependencies (including transitive ones)

### Managing Dependencies

There are two approaches for updating dependencies:

#### 1. Manual manipulation of `pyproject.toml`

If you manually edit the `pyproject.toml` file, you should use the `make py-lock` command to sync the `poetry.lock` file. This will
ensure that you don't inadvertently bring in other transitive dependency updates
that have not been fully tested with the project yet.

#### 2. Using Poetry to update dependencies (recommended)

If you're updating a dependency to a newer (or the latest) version,
let Poetry handle it by running:

```sh
poetry update <dependency> [<dependency>...]
```

You can specify more than one dependency together. With this command, Poetry
will do the following for you:

- Find the latest compatible version(s) of the specified dependency/dependencies
- Install the new versions
- Update and sync the `poetry.lock` file

In either situation, once you are finished and have verified the dependency
changes are working, please be sure to commit both the `pyproject.toml` and
`poetry.lock` files.

## Known Installation Issues

### Python Installation Errors

On M1 Macs, if you get a `fatal error: 'Python.h' file not found` message, try a
different method of installing Python. The recommended approach is to use
[`pyenv`](https://github.com/pyenv/pyenv), as noted above in the installation
instructions.

If you're using PyCharm for Python development, we've noticed some quirkiness
with the IDE and the interaction between Poetry and virtual environment
management that could cause a variety of problems to come up during project
setup and dependency management. Other tools, such as Visual Studio Code, have
proven to be a smoother experience for folks.

## To test the application

From a terminal within the running devcontainer:

```
# run all the tests
make test

# continuously run js tests
npm run test-watch
```

To run a specific JavaScript test, you'll need to copy the full command from
`package.json`.

## Running a11y-scans locally

Unlike most of the tests and scans, pa11y-ci cannot currently be run from within
the VSCode dev container.

1. `make run-flask` from within the devcontainer
2. Run `make a11y-scan` from your host computer.

## Further documentation

- [Working with static assets](docs/static-assets.md)
- [JavaScript documentation](https://github.com/alphagov/notifications-manuals/wiki/JavaScript-Documentation)
- [Updating dependencies](https://github.com/alphagov/notifications-manuals/wiki/Dependencies)

## License & public domain

Work through
[commit `543be77`](https://github.com/GSA/notifications-admin/commit/543be77776b64fddb6ba70fbb015ecd81a372478)
is licensed by the UK government under the MIT license. Work after that commit
is in the worldwide public domain. See [LICENSE.md](./LICENSE.md) for more
information.

## Contributing

As stated in [CONTRIBUTING.md](CONTRIBUTING.md), all contributions to this
project will be released under the CC0 dedication. By submitting a pull request,
you are agreeing to comply with this waiver of copyright interest.

## About the TTS Public Benefits Studio

The Public Benefits Studio is a team inside of
[GSA’s Technology Transformation Services](https://www.gsa.gov/about-us/organization/federal-acquisition-service/technology-transformation-services)
(TTS), home to innovative programs like [18F](https://18f.gsa.gov/) and
[Login.gov](https://login.gov). We collaborate with benefits programs to develop
shared technology tools and best practices that reduce the burden of navigating
government programs for low income individuals and families.

We’re a cross-functional team of technologists with specialized experience
working across public benefits programs like Medicaid, SNAP, and unemployment
insurance.

For more information on what we're working on, the Notify tool, and how to get
involved with our team,
[see our flyer.](https://github.com/GSA/notifications-admin/blob/main/docs/notify-pilot-flyer.md)

## Updating secrets for the E2E tests

At some point, E2E tests will fail because the secrets held in VCAP_SERVICES have expired.  To refresh
them, you will need to do the following:

1. Log in the normal way to access cloudfoundry command line options
2. In your terminal, run `chmod +x print_vcap.sh`
3. In your terminal, run `./print_vcap.sh`
4. Copy the value in your terminal and paste it into the VCAP_SERVICES secret in Github on the staging tier.
