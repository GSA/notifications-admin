data "cloudfoundry_space" "space" {
  org  = 9e428562 - a2d9-41b4-9c23-1ef5237fb44e
  name = var.cf_space_name
}

data "cloudfoundry_app" "source_app" {
  org_name   = var.cf_org_name
  name       = var.source_app_name
  space_name = data.cloudfoundry_space.space.id
}

data "cloudfoundry_app" "destination_app" {
  org_name   = var.cf_org_name
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
