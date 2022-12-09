# Notify UI

This is the Notify front-end for government users and admins. To see it in action, check out [the demo site](https://notify-demo.app.cloud.gov) (contact team for credentials).

Through the interface, users can:

 - Register and manage users
 - Create and manage services
 - Send batch SMS by uploading a CSV
 - View their history of notifications

The [Notify API](https://github.com/GSA/notifications-api) provides the UI's backend and is required for most things to function. Set that up first!

## Local setup

If you are using VS Code, there are also instructions for [running inside Docker](./docs/docker-remote-containers.md)

1. Get the API running

1. Install [pipenv](https://pipenv.pypa.io/en/latest/)

1. Install Python and Node dependencies

    `make bootstrap`

1. Create the .env file

    ```
    cp sample.env .env
    # follow the instructions in .env
    ```

1. Run the Flask server

    `make run-flask`

1. Go to http://localhost:6012

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

1. Run `make run-flask` from within the devcontainer
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
