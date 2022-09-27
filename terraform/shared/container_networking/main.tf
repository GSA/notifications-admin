data "cloudfoundry_space" "space" {
  org_name = var.cf_org_name
  name     = var.cf_space_name
}

data "cloudfoundry_app" "source_app" {
  name_or_id = var.source_app_name
  space      = data.cloudfoundry_space.space.id
}

data "cloudfoundry_app" "destination_app" {
  name_or_id = var.destination_app_name
  space      = data.cloudfoundry_space.space.id
}

resource "cloudfoundry_network_policy" "internal_route" {
  policy {
    source_app      = data.cloudfoundry_app.source_app.id
    destination_app = data.cloudfoundry_app.destination_app.id
    port            = var.destination_port
  }
}
