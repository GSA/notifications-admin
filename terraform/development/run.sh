#!/usr/bin/env bash

username=`whoami`
org="gsa-tts-benefits-studio-prototyping"

usage="
$0: Create development infrastructure

Usage:
  $0 -h
  $0 [-u <USER NAME>] [-k]

Options:
-h: show help and exit
-u <USER NAME>: your username. Default: $username
-k: keep service user. Default is to remove them after run
-d: Destroy development resources. Default is to create them

Notes:
* Requires cf-cli@8
* Requires terraform/development to be run on API app first, with the same [-u <USER NAME>]
"

action="apply"
creds="remove"

while getopts ":hkdu:" opt; do
  case "$opt" in
    u)
      username=${OPTARG}
      ;;
    k)
      creds="keep"
      ;;
    d)
      action="destroy"
      ;;
    h)
      echo "$usage"
      exit 0
      ;;
  esac
done

set -e

service_account="$username-terraform"

if [[ ! -s "secrets.auto.tfvars" ]]; then
  # create user in notify-local-dev space to create s3 buckets
  ../create_service_account.sh -s notify-local-dev -u $service_account > secrets.auto.tfvars
fi

if [[ ! -f "../../.env" ]]; then
  cp ../../sample.env ../../.env
fi

set +e

terraform init
terraform $action -var="username=$username"

set -e

if [[ $creds = "remove" ]]; then
  ../destroy_service_account.sh -s notify-local-dev -u $service_account
  rm secrets.auto.tfvars
fi

exit 0
