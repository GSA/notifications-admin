terraform {
  required_version = "~> 1.7"
  required_providers {
    cloudfoundry = {
      source  = "cloudfoundry/cloudfoundry"
      version = "1.9.0"
    }
  }
}

provider "cloudfoundry" {
  api_url      = "https://api.fr.cloud.gov"
  user         = var.cf_user
  password     = var.cf_password
  app_logs_max = 30
}
