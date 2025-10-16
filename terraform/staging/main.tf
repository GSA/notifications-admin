locals {
  cf_org_name   = "gsa-tts-benefits-studio"
  cf_space_name = "notify-staging"
  env           = "staging"
  app_name      = "notify-admin"
}

resource "null_resource" "prevent_destroy" {

  lifecycle {
    prevent_destroy = false # destroying staging is allowed
  }
}

module "redis-v70" {
  source = "github.com/GSA-TTS/terraform-cloudgov//redis?ref=v2.4.0"

  cf_space_id     = local.cf_space_name
  name            = "${local.app_name}-redis-v70-${local.env}"
  redis_plan_name = "redis-dev"
  json_params = jsonencode(
    {
      "engineVersion" : "7.0",
    }
  )

  providers = {
    cloudfoundry-community = cloudfoundry-community.legacy
  }
}

module "logo_upload_bucket" {
  source = "github.com/GSA-TTS/terraform-cloudgov//s3?ref=v2.4.0"

  cf_space_id = local.cf_space_name
  name        = "${local.app_name}-logo-upload-bucket-${local.env}"
  providers = {
    cloudfoundry-community = cloudfoundry-community.legacy
  }
}

module "api_network_route" {
  source = "../shared/container_networking"

  cf_org_name          = local.cf_org_name
  cf_space_name        = local.cf_space_name
  source_app_name      = "${local.app_name}-${local.env}"
  destination_app_name = "notify-api-${local.env}"
}
