terraform {
  source = "../../modules/s3"
}

include "root" {
  path = find_in_parent_folders()
}

inputs = {
  bucket_name = "dev-bucket-devops-take-home-demo"
  tags = {
    "terraform_managed" = "true"
    "environment"       = "dev"
  }
}
