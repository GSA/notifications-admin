data "cloudfoundry_space" "space" {
  org  = var.cf_org_name
  name = var.cf_space_name
}

data "cloudfoundry_app" "source_app" {
  org_name   = var.cf_org_name
  name       = var.source_app_name
  space_name = data.cloudfoundry_space.space.id
}

data "cloudfoundry_app" "destination_app" {
  name       = var.destination_app_name
  space_name = data.cloudfoundry_space.space.id
}

resource "cloudfoundry_network_policy" "internal_route" {
  policies = [{
    source_app      = data.cloudfoundry_app.source_app.id
    destination_app = data.cloudfoundry_app.destination_app.id
    port            = var.destination_port
  }]
}
