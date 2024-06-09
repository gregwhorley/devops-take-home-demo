variable "bucket_name" {
  type        = string
  description = "Name of the S3 bucket"
}
variable "tags" {
  type        = map(string)
  description = "The set of tags that will be applied to the S3 bucket"
}
