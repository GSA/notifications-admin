### Setting Up Environment Variables for Local Development to the Staging API

When you’re working locally, you can point your local admin repo to the staging API and use that to help debug
issues with the staging data set.  To do this, you’ll need to modify your .env file for the admin project and
include the following new environment variables:

- `ADMIN_CLIENT_SECRET`
- `ADMIN_CLIENT_USERNAME`
- `DANGEROUS_SALT`
- `SECRET_KEY`

Additionally, update `API_HOST_NAME` and `NOTIFY_ENVIRONMENT`:

1. Change `API_HOST_NAME` to `API_HOST_NAME=https://notify-api-staging.app.cloud.gov`
2. Change `NOTIFY_ENVIRONMENT` to `NOTIFY_ENVIRONMENT=staging`

### Retrieving Environment Variables for Staging

You can retrieve the values needed for these by using the `cf` CLI (Cloud Foundry CLI tool) and making sure
you’re targeting the `notify-staging` space.

1. `cf login -a [api.fr.cloud.gov](http://api.fr.cloud.gov/) --sso`
2. select `notify-staging`
3. `cf env notify-admin-staging`

By pointing your local environment to staging, it should mirror what's in staging.
