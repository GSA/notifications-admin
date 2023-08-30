#!/usr/bin/env bash

username=`whoami`
org="gsa-tts-benefits-studio"

usage="
$0: Reset terraform state so run.sh can be run again or for a new username

Usage:
  $0 -h
  $0 [-u <USER NAME>]

Options:
-h: show help and exit
-u <USER NAME>: your username. Default: $username

Notes:
* Requires cf-cli@8
"

while getopts ":hu:" opt; do
  case "$opt" in
    u)
      username=${OPTARG}
      ;;
    h)
      echo "$usage"
      exit 0
      ;;
  esac
done

read -p "Are you sure you want to import terraform state and remove existing service keys for $username (y/n)? " verify

if [[ $verify != "y" ]]; then
  exit 0
fi

# ensure we're in the correct directory
cd $(dirname $0)

service_account="$username-terraform"

if [[ ! -s "secrets.auto.tfvars" ]]; then
  # create user in notify-local-dev space to create s3 buckets
  ../create_service_account.sh -s notify-local-dev -u $service_account > secrets.auto.tfvars
fi

echo "Importing terraform state for $username"
terraform init

key_name=$username-admin-dev-key

cf t -s notify-local-dev
terraform import -var "username=$username" module.logo_upload_bucket.cloudfoundry_service_instance.bucket $(cf service --guid $username-csv-upload-bucket)
cf delete-service-key -f $username-logo-upload-bucket $key_name
cf delete-service-key -f $username-csv-upload-bucket $key_name

./run.sh -u $username
