# VS Code && Docker installation

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