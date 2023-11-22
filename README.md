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
- [notifications-utils](https://github.com/GSA/notifications-utils)
- [us-notify-compliance](https://github.com/GSA/us-notify-compliance/)
- [notify-python-demo](https://github.com/GSA/notify-python-demo)

## Before You Start

You will need the following items:

- An active cloud.gov account with the correct permissions - speak with your
  onboarding buddy for help with
  [setting up an account](https://cloud.gov/sign-up/) (requires a `.mil`,
  `.gov`, or `.fed.us` email address) and getting access to the
  `notify-local-dev` and `notify-staging` spaces.
- Admin priviliges and SSH access on your machine; you may need to work with
  your organization's IT support staff if you're not sure or don't currently
  have this access.

**In addition, you should set up the Notify.gov API first!**

[Follow the instructions here to set up the Notify.gov API.](https://github.com/GSA/notifications-api#before-you-start)

The Notify.gov API is required in order for the Notify.gov Admin UI to run, and
it will also take care of many of the steps that are listed here.  The sections
that are a repeat from the API setup are flagged with an **[API Step]** label
in front of them.

## Local Environment Setup

This project is set up to work with
[nvm (Node Version Manager)](https://github.com/nvm-sh/nvm#installing-and-updating)
for managing and using Node.js (version 16.15.1) and the `npm` package manager.

These instructions will walk you through how to set your machine up with all of
the required tools for this project.

### Docker installation

If you are using VS Code, there are also instructions for
[running inside Docker](./docs/docker-remote-containers.md).

### [API Step] Project Pre-Requisite Setup

On MacOS, using [Homebrew](https://brew.sh/) for package management is highly
recommended. This helps avoid some known installation issues. Start by following
the installation instructions on the Homebrew homepage.

**Note:** You will also need Xcode or the Xcode Command Line Tools installed. The
quickest way to do this is is by installing the command line tools in the shell:

```sh
xcode-select –-install
```

#### [API Step] Homebrew Setup

If this is your first time installing Homebrew on your machine, you may need to
add its binaries to your system's `$PATH` environment variable so that you can
use the `brew` command. Try running `brew help` to see if Homebrew is
recognized and runs properly. If that fails, then you'll need to add a
configuration line to wherever your `$PATH` environment variable is set.

Your system `$PATH` environment variable is likely set in one of these
locations:

For BASH shells:
- `~/.bashrc`
- `~/.bash_profile`
- `~/.profile`

For ZSH shells:
- `~/.zshrc`
- `~/.zprofile`

There may be different files that you need to modify for other shell
environments.

Which file you need to modify depends on whether or not you are running an
interactive shell or a login shell
(see [this Stack Overflow post](https://stackoverflow.com/questions/18186929/what-are-the-differences-between-a-login-shell-and-interactive-shell)
for an explanation of the differences).  If you're still not sure, please ask
the team for help!

Once you determine which file you'll need to modify, add these lines before any
lines that add or modify the `$PATH` environment variable; near or at the top
of the file is appropriate:

```sh
# Homebrew setup
eval "$(/opt/homebrew/bin/brew shellenv)"
```

This will make sure Homebrew gets setup correctly. Once you make these changes,
either start a new shell session or source the file
(`source ~/.FILE-YOU-MODIFIED`) you modified to have your system recognize the
changes.

Verify that Homebrew is now working by trying to run `brew help` again.

### [API Step] System-Level Package Installation

There are several packages you will need to install for your system in order to
get the app running (and these are good to have in general for any software
development).

Start off with these packages since they're quick and don't require additional
configuration after installation to get working out of the box:

- [jq](https://stedolan.github.io/jq/) - for working with JSON in the command
  line
- [git](https://git-scm.com/) - for version control management
- [tfenv](https://github.com/tfutils/tfenv) - for managing
  [Terraform](https://www.terraform.io/) installations
- [cf-cli@8](https://docs.cloudfoundry.org/cf-cli/install-go-cli.html) - for
  working with a Cloud Foundry platform (e.g., cloud.gov)
- [vim](https://www.vim.org/) - for editing files more easily in the command
  line
- [wget](https://www.gnu.org/software/wget/) - for retrieving files in the
  command line

You can install them by running the following:

```sh
brew install jq git tfenv cloudfoundry/tap/cf-cli@8 vim wget
```

#### [API Step] Terraform Installation

As a part of the installation above, you just installed `tfenv` to manage
Terraform installations. This is great, but you still need to install Terraform
itself, which can be done with this command:

```sh
tfenv install latest:^1.4.0
```

_NOTE: This project currently uses the latest `1.4.x release of Terraform._

#### [API Step] Python Installation

Now we're going to install a tool to help us manage Python versions and
virtual environments on our system.  First, we'll install
[pyenv](https://github.com/pyenv/pyenv) and one of its plugins,
[pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv), with Homebrew:

```sh
brew install pyenv pyenv-virtualenv
```

When these finish installing, you'll need to make another adjustment in the
file that you adjusted for your `$PATH` environment variable and Homebrew's
setup. Open the file, and add these lines to it:

```
# pyenv setup
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

Once again, start a new shell session or source the file in your current shell
session to make the changes take effect.

Now we're ready to install the Python version we need with `pyenv`, like so:

```sh
pyenv install 3.9
```

This will install the latest version of Python 3.9.

_NOTE: This project currently runs on Python 3.9.x._

#### [API Step] Python Dependency Installation

Lastly, we need to install the tool we use to manage Python dependencies within
the project, which is [poetry](https://python-poetry.org/).

Visit the
[official installer instructions page](https://python-poetry.org/docs/#installing-with-the-official-installer)
and follow the steps to install Poetry directly with the script.

This will ensure `poetry` doesn't conflict with any project virtual environments
and can update itself properly.

#### Node.js and npm Installation

The project will manage most of the Node.js pieces for you, but you will need to
install
[nvm (Node Version Manager)](https://github.com/nvm-sh/nvm#installing-and-updating)
in order for things to work.

Follow the steps in the installation instructions to get `nvm` installed with
the install script they provide, and double check that the file that you
adjusted for your `$PATH` environment variable and Homebrew's setup is properly
updated with the `nvm` setup as well.

Open the file and check for the `nvm` setup lines; if they're not there, then
add the lines found in the
[nvm installation instructions](https://github.com/nvm-sh/nvm#install--update-script)
to to the file after the `pyenv` section you created, e.g.:

```
# nvm setup
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
```

### First-Time Project Setup

Once all of pre-requisites for the project are installed and you have a
cloud.gov account, you can now set up the admin project and get things running
locally!

First, clone the respository in the directory of your choosing on your machine:

```sh
git clone git@github.com:GSA/notifications-admin.git
```

Now go into the project directory (`notifications-admin` by default), create a
virtual environment, and set the local Python version to point to the virtual
environment (assumes version Python `3.9.18` is what is installed on your
machine):

```sh
cd notifications-admin
pyenv virtualenv 3.9.18 notify-admin
pyenv local notify-admin
```

_If you're not sure which version of Python was installed with `pyenv`, you can check by running `pyenv versions` and it'll list everything available currently._

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

_NOTE: You'll want to occasionally run `make bootstrap` to keep your project up-to-date, especially when there are dependency updates._

Now you can run the web server and background workers for asynchronous jobs:

```sh
make run-flask
```

This will run the local development web server and make the admin site
available at http://localhost:6012; remember to make sure that the Notify.gov
API is running as well!

## Git Hooks

We're using [`pre-commit`](https://pre-commit.com/) to manage hooks in order to
automate common tasks or easily-missed cleanup. It's installed as part of
`make bootstrap` and is limited to this project's virtualenv.

To run the hooks in advance of a `git` operation, use
`poetry run pre-commit run`. For running across the whole codebase (useful after
adding a new hook), use `poetry run pre-commit run --all-files`.

The configuration is stored in `.pre-commit-config.yaml`. In that config, there
are links to the repos from which the hooks are pulled, so hop through there if
ou want a detailed description of what each one is doing.

We do not maintain any hooks in this repository.

## Python Dependency Management

We're using [`Poetry`](https://python-poetry.org/) for managing our Python
dependencies and local virtual environments. When it comes to managing the
Python dependencies, there are a couple of things to bear in mind.

For situations where you manually manipulate the `pyproject.toml` file, you
should use the `make py-lock` command to sync the `poetry.lock` file. This will
ensure that you don't inadvertently bring in other transitive dependency updates
that have not been fully tested with the project yet.

If you're just trying to update a dependency to a newer (or the latest) version,
you should let Poetry take care of that for you by running the following:

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

### Keeping the notification-utils Dependency Up-to-Date

The `notifications-utils` dependency references the other repository we have at
https://github.com/GSA/notifications-utils - this dependency requires a bit of
extra legwork to ensure it stays up-to-date.

Whenever a PR is merged in the `notifications-utils` repository, we need to make
sure the changes are pulled in here and committed to this repository as well.
You can do this by going through these steps:

- Make sure your local `main` branch is up-to-date
- Create a new branch to work in
- Run `make update-utils`
- Commit the updated `poetry.lock` file and push the changes
- Make a new PR with the change
- Have the PR get reviewed and merged

### Python dependency management

We're using [`Poetry`](https://python-poetry.org/) for managing our Python
dependencies and local virtual environments.  When it comes to managing the
Python dependencies, there are a couple of things to bear in mind.

For situations where you manually manipulate the `pyproject.toml` file, you
should use the `make py-lock` command to sync the `poetry.lock` file.  This will
ensure that you don't inadvertently bring in other transitive dependency updates
that have not been fully tested with the project yet.

If you're just trying to update a dependency to a newer (or the latest) version,
you should let Poetry take care of that for you by running the following:

```sh
poetry update <dependency> [<dependency>...]
```

You can specify more than one dependency together.  With this command, Poetry
will do the following for you:

- Find the latest compatible version(s) of the specified dependency/dependencies
- Install the new versions
- Update and sync the `poetry.lock` file

In either situation, once you are finished and have verified the dependency
changes are working, please be sure to commit both the `pyproject.toml` and
`poetry.lock` files.

### Keeping the notification-utils dependency up-to-date

The `notifications-utils` dependency references the other repository we have at
https://github.com/GSA/notifications-utils - this dependency requires a bit of
extra legwork to ensure it stays up-to-date.

Whenever a PR is merged in the `notifications-utils` repository, we need to make
sure the changes are pulled in here and committed to this repository as well.
You can do this by going through these steps:

- Make sure your local `main` branch is up-to-date
- Create a new branch to work in
- Run `make update-utils`
- Commit the updated `poetry.lock` file and push the changes
- Make a new PR with the change
- Have the PR get reviewed and merged

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

## Further docs from UK

- [Working with static assets](docs/static-assets.md)
- [JavaScript documentation](https://github.com/alphagov/notifications-manuals/wiki/JavaScript-Documentation)
- [Updating dependencies](https://github.com/alphagov/notifications-manuals/wiki/Dependencies)

## License && public domain

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
