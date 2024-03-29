locals {
  cf_api_url      = "https://api.fr.cloud.gov"
  s3_service_name = "notify-terraform-state"
}

module "s3" {
  source = "github.com/18f/terraform-cloudgov//s3"

  cf_api_url      = local.cf_api_url
  cf_user         = var.cf_user
  cf_password     = var.cf_password
  cf_org_name     = "gsa-tts-benefits-studio"
  cf_space_name   = "notify-management"
  s3_service_name = local.s3_service_name
}

resource "cloudfoundry_service_key" "bucket_creds" {
  name             = "${local.s3_service_name}-access"
  service_instance = module.s3.bucket_id
}

output "bucket_credentials" {
  value = cloudfoundry_service_key.bucket_creds.credentials
}
