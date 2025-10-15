locals {
  cf_org_name   = "gsa-tts-benefits-studio"
  cf_space_name = "notify-production"
  env           = "production"
  app_name      = "notify-admin"
}

resource "null_resource" "prevent_destroy" {

  lifecycle {
    prevent_destroy = true # never destroy production
  }
}

module "redis-v70" {
  source = "github.com/GSA-TTS/terraform-cloudgov//redis?ref=v2.4.0"

  cf_space_id     = local.cf_space_name
  name            = "${local.app_name}-redis-v70-${local.env}"
  redis_plan_name = "redis-3node-large"
  json_params = jsonencode(
    {
      "engineVersion" : "7.0",
    }
  )
}

module "logo_upload_bucket" {
  source = "github.com/GSA-TTS/terraform-cloudgov//s3?ref=v2.4.0"

  cf_space_id = local.cf_space_name
  name        = "${local.app_name}-logo-upload-bucket-${local.env}"
}

module "api_network_route" {
  source = "../shared/container_networking"

  cf_org_name          = local.cf_org_name
  cf_space_name        = local.cf_space_name
  source_app_name      = "${local.app_name}-${local.env}"
  destination_app_name = "notify-api-${local.env}"
}

# ##########################################################################
# This governs the name of our main website. Because domain names are unique,
# it only lives here in this one location in production. Resulting problem:
# it is hard to test. Create a temporary, similar code block (with a different
# subdomain) in Sandbox, test your changes there, and bring them here.
#
# Dependencies:
# 1) an app named notify-admin-production in Cloud.gov
# 2) this route, manually created by an OrgManager:
#     `cf create-domain gsa-tts-benefits-studio beta.notify.gov`
# 3) the acme-challenge CNAME record
#       https://cloud.gov/docs/services/external-domain-service/#how-to-create-an-instance-of-this-service
###########################################################################
module "domain" {
  source = "github.com/GSA-TTS/terraform-cloudgov//domain?ref=v2.4.0"

  cf_org_name    = local.cf_org_name
  cf_space_name  = local.cf_space_name
  app_name_or_id = "${local.app_name}-${local.env}"
  name           = "${local.app_name}-domain-${local.env}"
  cdn_plan_name  = "domain"
  domain_name    = "beta.notify.gov"
}
