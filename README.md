# Notify UI

This is the Notify front-end for government users and admins. To see it in action, check out [the demo site](https://notify-demo.app.cloud.gov) (contact team for credentials).

Through the interface, users can:

- Register and manage users
- Create and manage services
- Send batch SMS by uploading a CSV
- View their history of notifications

The [Notify API](https://github.com/GSA/notifications-api) provides the UI's backend and is required for most things to function. Set that up first!

## Local setup

### Common steps

1.  Install pre-requisites for setup (on a Mac):
    - Install XCode or at least the XCode Command Line Tools
    - [Homebrew](https://brew.sh/) (follow instructions on page)
    - [jq](https://stedolan.github.io/jq/): `brew install jq`
    - [terraform](https://www.terraform.io/): `brew install terraform` or `brew install tfenv` and use `tfenv` to install `terraform ~> 1.4.0`
    - [cf-cli@8](https://docs.cloudfoundry.org/cf-cli/install-go-cli.html): `brew install cloudfoundry/tap/cf-cli@8`
1.  [Log into cloud.gov](https://cloud.gov/docs/getting-started/setup/#set-up-the-command-line): `cf login -a api.fr.cloud.gov --sso`
1.  Ensure you have access to the `notify-local-dev` and `notify-staging` spaces in cloud.gov
1.  Run the API setup steps
1.  Run the development terraform with:

        ```
        $ cd terraform/development
        $ ./run.sh
        ```

1.  If you want to send data to New Relic from your local develpment environment, set `NEW_RELIC_LICENSE_KEY` within `.env`
1.  Follow the instructions for either `Direct installation` or `Docker installation` below

### Direct installation

1. Get the API running

1. Install [poetry](https://python-poetry.org/docs/#installation)

1. Install [nvm (Node Version Manager)](https://github.com/nvm-sh/nvm#installing-and-updating)

1. Install Python and Node dependencies

   `make bootstrap`

   If you run into certificate errors at the `playwright install` step, try doing this:

   1. Run `brew --prefix` to see Homebrew's root directory

   1. Create or modify the local `.env` file in the project and add this line:

      `NODE_EXTRA_CA_CERTS=/CHANGE-TO-HOMEBREW-INSTALL-PATH/etc/ca-certificates/cert.pem`

      Make sure to change `CHANGE-TO-HOMEBREW-INSTALL-PATH` to the path given by `brew --prefix` in the step above.
      For example, if `brew --prefix` gave `/opt/homebrew` as output, then the line would look like this:

      `NODE_EXTRA_CA_CERTS=/opt/homebrew/etc/ca-certificates/cert.pem`

   1. Save the changes to the `.env` file

   1. Run `make bootstrap` again

1. Run the Flask server

   `make run-flask`

1. Go to http://localhost:6012

### Docker installation

If you are using VS Code, there are also instructions for [running inside Docker](./docs/docker-remote-containers.md)

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

```
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

## To test the application

From a terminal within the running devcontainer:

```
# run all the tests
make test

# continuously run js tests
npm run test-watch
```

To run a specific JavaScript test, you'll need to copy the full command from `package.json`.

## Running a11y-scans locally

Unlike most of the tests and scans, pa11y-ci cannot currently be run from within the VSCode dev container.

1. `make run-flask` from within the devcontainer
2. Run `make a11y-scan` from your host computer.

## Further docs from UK

- [Working with static assets](docs/static-assets.md)
- [JavaScript documentation](https://github.com/alphagov/notifications-manuals/wiki/JavaScript-Documentation)
- [Updating dependencies](https://github.com/alphagov/notifications-manuals/wiki/Dependencies)

## License && public domain

Work through [commit `543be77`](https://github.com/GSA/notifications-admin/commit/543be77776b64fddb6ba70fbb015ecd81a372478) is licensed by the UK government under the MIT license. Work after that commit is in the worldwide public domain. See [LICENSE.md](./LICENSE.md) for more information.

## Contributing

As stated in [CONTRIBUTING.md](CONTRIBUTING.md), all contributions to this project will be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.

## About the TTS Public Benefits Studio

The Public Benefits Studio is a team inside of [GSA’s Technology Transformation Services](https://www.gsa.gov/about-us/organization/federal-acquisition-service/technology-transformation-services) (TTS), home to innovative programs like [18F](https://18f.gsa.gov/) and [Login.gov](https://login.gov). We collaborate with benefits programs to develop shared technology tools and best practices that reduce the burden of navigating government programs for low income individuals and families.

We’re a cross-functional team of technologists with specialized experience working across public benefits programs like Medicaid, SNAP, and unemployment insurance.

For more information on what we're working on, the Notify tool, and how to get involved with our team, [see our flyer.](https://github.com/GSA/notifications-admin/blob/main/docs/notify-pilot-flyer.md)
