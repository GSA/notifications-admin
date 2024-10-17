#!/bin/bash

STAGING_APP_NAME="notify-admin-staging"

# Fetch the environment variables of the staging app
env_var_value=$(cf env "$STAGING_APP_NAME" | awk '/'"VCAP_SERVICES"':/,/^}/')


# Check if the environment variable was found"
if [ -z "$env_var_value" ]; then
  echo "Environment variable VCAP_SERVICES not found in the staging environment"
else
  env_var_json=$(echo "$env_var_value" | sed '1s/^[^:]*: //' | tr -d '\n')
  stringified_value=$(python3 -c "import json, sys; print(json.dumps(json.loads(sys.stdin.read())))" <<< "$env_var_json")
  echo "VCAP_SERVICES:"
  echo "$stringified_value"
fi
