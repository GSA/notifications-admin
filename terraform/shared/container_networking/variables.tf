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
  default = "61443"
}
