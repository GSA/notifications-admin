locals {
  cf_org_name      = "gsa-tts-benefits-studio-prototyping"
  cf_space_name    = "notify-demo"
  env              = "demo"
  app_name         = "notify-admin"
  recursive_delete = false
}

module "redis" {
  source = "github.com/18f/terraform-cloudgov//redis"

  cf_user          = var.cf_user
  cf_password      = var.cf_password
  cf_org_name      = local.cf_org_name
  cf_space_name    = local.cf_space_name
  env              = local.env
  app_name         = local.app_name
  recursive_delete = local.recursive_delete
  redis_plan_name  = "redis-dev"
}

module "logo_upload_bucket" {
  source = "github.com/18f/terraform-cloudgov//s3"

  cf_user          = var.cf_user
  cf_password      = var.cf_password
  cf_org_name      = local.cf_org_name
  cf_space_name    = local.cf_space_name
  recursive_delete = local.recursive_delete
  s3_service_name  = "${local.app_name}-logo-upload-bucket-${local.env}"
}

# ##########################################################################
# The following lines need to be commented out for the initial `terraform apply`
# It can be re-enabled after:
# 1) the api app has first been deployed
# 2) the admin app has first been deployed
###########################################################################
module "api_network_route" {
  source = "../shared/container_networking"

  cf_user              = var.cf_user
  cf_password          = var.cf_password
  cf_org_name          = local.cf_org_name
  cf_space_name        = local.cf_space_name
  source_app_name      = "${local.app_name}-${local.env}"
  destination_app_name = "notify-api-${local.env}"
}
