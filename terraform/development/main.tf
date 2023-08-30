locals {
  cf_org_name      = "gsa-tts-benefits-studio"
  cf_space_name    = "notify-local-dev"
  recursive_delete = true
  key_name         = "${var.username}-admin-dev-key"
}

data "cloudfoundry_space" "dev" {
  org_name = local.cf_org_name
  name     = local.cf_space_name
}

module "logo_upload_bucket" {
  source = "github.com/18f/terraform-cloudgov//s3?ref=v0.2.0"

  cf_org_name      = local.cf_org_name
  cf_space_name    = local.cf_space_name
  recursive_delete = local.recursive_delete
  name             = "${var.username}-logo-upload-bucket"
}
resource "cloudfoundry_service_key" "logo_key" {
  name             = local.key_name
  service_instance = module.logo_upload_bucket.bucket_id
}

data "cloudfoundry_service_instance" "csv_bucket" {
  name_or_id = "${var.username}-csv-upload-bucket"
  space      = data.cloudfoundry_space.dev.id
}
resource "cloudfoundry_service_key" "csv_key" {
  name             = local.key_name
  service_instance = data.cloudfoundry_service_instance.csv_bucket.id
}

locals {
  credentials = <<EOM

#############################################################
# CSV_UPLOAD_BUCKET
CSV_BUCKET_NAME=${cloudfoundry_service_key.csv_key.credentials.bucket}
CSV_AWS_ACCESS_KEY_ID=${cloudfoundry_service_key.csv_key.credentials.access_key_id}
CSV_AWS_SECRET_ACCESS_KEY=${cloudfoundry_service_key.csv_key.credentials.secret_access_key}
CSV_AWS_REGION=${cloudfoundry_service_key.csv_key.credentials.region}
# LOGO_UPLOAD_BUCKET
LOGO_BUCKET_NAME=${cloudfoundry_service_key.logo_key.credentials.bucket}
LOGO_AWS_ACCESS_KEY_ID=${cloudfoundry_service_key.logo_key.credentials.access_key_id}
LOGO_AWS_SECRET_ACCESS_KEY=${cloudfoundry_service_key.logo_key.credentials.secret_access_key}
LOGO_AWS_REGION=${cloudfoundry_service_key.logo_key.credentials.region}
EOM
}

resource "null_resource" "output_creds_to_env" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    working_dir = "../.."
    command     = "echo \"${local.credentials}\" >> .env"
  }
}
