resource "aws_s3_bucket" "devops_take_home_demo_bucket" {
  bucket = var.bucket_name

  tags = var.tags
}

resource "aws_s3_bucket_policy" "secure_transport_https_only" {
  bucket = aws_s3_bucket.devops_take_home_demo_bucket.id
  policy = data.aws_iam_policy_document.secure_transport_https_only.json
}

data "aws_iam_policy_document" "secure_transport_https_only" {
  statement {
    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = [
      "s3:*"
    ]

    effect = "Deny"

    resources = [
      aws_s3_bucket.devops_take_home_demo_bucket.arn,
      "${aws_s3_bucket.devops_take_home_demo_bucket.arn}/*",
    ]

    condition {
      test     = "Bool"
      values   = ["false"]
      variable = "aws:SecureTransport"
    }
  }
}
