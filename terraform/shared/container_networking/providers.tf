terraform {
  required_version = "~> 1.7"
  required_providers {
    cloudfoundry = {
      source  = "cloudfoundry/cloudfoundry"
      version = "1.9.0"
    }
  }
}
