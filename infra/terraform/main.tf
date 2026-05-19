# Durham Risk Intelligence Dashboard
# Terraform starter configuration
#
# Purpose:
# This file will eventually define the core AWS infrastructure for the dashboard.
#
# Current status:
# Terraform is not implemented yet.
#
# Current project strategy:
# Option 3 - Hybrid Learning Approach
#
# The current manually created AWS architecture will remain stable as the
# working reference architecture while a cleaner Terraform managed version
# is planned and built separately.
#
# Future resources may include:
# - VPC
# - Public subnets
# - Private subnets
# - Internet Gateway
# - Route tables
# - Security groups
# - Application Load Balancer
# - Target Group
# - Launch Template
# - Auto Scaling Group
# - S3 artifact bucket
# - CloudWatch alarms
# - SNS topic
# - IAM role and instance profile

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}