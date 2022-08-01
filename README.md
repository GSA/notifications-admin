# US Notify Admin

Cloned from the brilliant work of the team at [GOV.UK Notify](https://github.com/alphagov/notifications-admin), cheers!

US Notify admin application - https://notifications-admin.app.cloud.gov (contact team for access)

 - Register and manage users
 - Create and manage services
 - Send batch emails and SMS by uploading a CSV
 - Show history of notifications

## QUICK START

NOTE: Set up the [notifications-api repo](https://github.com/18F/notifications-api) locally first, you'll need that docker network and a functioning api to make use of this repo.
```
# create .env file as instructed below

# download vscode and install the Remote-Containers plug-in from Microsoft

# make sure your docker daemon is running

# Using the command pallette (cmd+p), search "Remote Containers: Open folder in project" 
# choose devcontainer-admin folder, after reload, hit "show logs" in bottom-right
# logs should complete shortly after running gulp.js and compiling front-end files

# Check vscode panel > ports, await green dot, open a new terminal and run the web server
make run-flask
```

Visit [localhost:6012](http://localhost:6012)

NOTE: any .py code changes you make should be picked up automatically in development. If you're developing JavaScript code, open another vscode terminal and run `npm run watch` to achieve the same.

## To test the application
From a terminal within the running devcontainer:

```
# run all the tests
make test

# continuously run js tests
npm run test-watch
```

To run a specific JavaScript test, you'll need to copy the full command from `package.json`.

## Further docs [STILL UK DOCS]

- [Working with static assets](docs/static-assets.md)
- [JavaScript documentation](https://github.com/alphagov/notifications-manuals/wiki/JavaScript-Documentation)
- [Updating dependencies](https://github.com/alphagov/notifications-manuals/wiki/Dependencies)
