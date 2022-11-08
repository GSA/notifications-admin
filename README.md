# US Notify Admin

Cloned from the brilliant work of the team at [GOV.UK Notify](https://github.com/alphagov/notifications-admin), cheers!

US Notify admin application - https://notify-demo.app.cloud.gov (contact team for access)

 - Register and manage users
 - Create and manage services
 - Send batch emails and SMS by uploading a CSV
 - Show history of notifications

## QUICKSTART

---
**NOTE**: Set up the [notifications-api repo](https://github.com/18F/notifications-api) locally **FIRST**, you'll need both the docker network it provides and a functioning api to make use of the notifications-admin repo. It is expected as a byproduct of getting notifications-api running you will also be running VS Code and the Remote Containers extension, and that docker daemon is running and the API is as well.

Open the notifications-admin repo in VS Code (File->Open Folder, select notifications-admin folder)

create a .env file as detailed in the .env Setup section below

Using VS Code's command pallette (cmd+shift+p), search "Remote Containers: Open folder in Container..."

choose devcontainer-admin folder (note: this is a subfolder of notifications-admin/). This will open a new window, closing the current one in the process. After the new window loads, hit "show logs" link in the bottom-right. If this is the first build it will take a few minutes to create the image. The process completes shortly after running gulp.js and compiling front-end files.

Select View->Open View..., then search/select “ports”. Await a green dot on the port view, then open a new terminal and run the web server:
`make run-flask`

Visit [localhost:6012](http://localhost:6012)

NOTE: any .py code changes you make should be picked up automatically in development. If you're developing JavaScript code, open another vscode terminal and run `npm run watch` to achieve the same.

---
## .env Setup

create a .env file using sample.env as a template
`cp sample.env .env` (or via VS Code file browser)

from the notifications-api checkout, copy the values in that repo's .env file for `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` into this repo's .env file.

Change `BASIC_AUTH_USERNAME` and `BASIC_AUTH_PASSWORD` to what you'd like them to be for this deployment.

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

## Further docs [STILL UK DOCS]

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
