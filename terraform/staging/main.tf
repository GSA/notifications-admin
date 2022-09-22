locals {
  cf_org_name      = "gsa-10x-prototyping"
  cf_space_name    = "10x-notifications"
  env              = "staging"
  app_name         = "notifications-admin"
  recursive_delete = true
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
