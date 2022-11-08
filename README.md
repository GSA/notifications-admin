# Notify UI

This is the Notify front-end for government users and admins. To see it in action, check out [the demo site](https://notify-demo.app.cloud.gov) (contact team for credentials).

Through the interface, users can:

 - Register and manage users
 - Create and manage services
 - Send batch SMS by uploading a CSV
 - View their history of notifications

The [Notify API](https://github.com/GSA/notifications-api) provides the UI's backend and is required for most things to function. Set that up first!

## Local setup

### Direct setup

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

### VS Code && Docker installation

If you're working in VS Code, you can also leverage Docker for a containerized dev environment

1. Get the API running, including the Docker network

1. Create the .env file

    ```
    cp sample.env .env
    # follow the instructions in .env
    ```

1. Install the Remote-Containers plug-in in VS Code

1. Using the command palette (shift+cmd+p) or green button thingy in the bottom left, search and select “Remote Containers: Open Folder in Container...” When prompted, choose **devcontainer-admin** folder (note: this is a *subfolder* of notifications-admin). This will start the container in a new window, replacing the current one.

1. Wait a few minutes while things happen 🍵

1. Open a VS Code terminal and run the Flask application:

    `make run-flask`

1. Go to http://localhost:6012

NOTE: when you change .env in the future, you'll need to rebuild the devcontainer for the change to take effect. VS Code _should_ detect the change and prompt you with a toast notification during a cached build. If not, you can find a manual rebuild in command pallette or just `docker rm` the notifications-api container.

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
