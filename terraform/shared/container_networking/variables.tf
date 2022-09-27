variable "cf_password" {
  type      = string
  sensitive = true
}
variable "cf_user" {}
variable "cf_org_name" {}
variable "cf_space_name" {}
variable "source_app_name" {}
variable "destination_app_name" {}
variable "destination_port" {
  type    = string
  # 61443 is the port to use to enable automatic TLS termination as specified at
  # https://cloud.gov/docs/management/container-to-container/#configuring-secure-container-to-container-networking
  default = "61443"
}
