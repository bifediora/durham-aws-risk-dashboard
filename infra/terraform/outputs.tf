# Durham Risk Intelligence Dashboard
# Terraform outputs
#
# Purpose:
# This file will eventually define useful values Terraform should print after
# infrastructure is created.
#
# Current status:
# Placeholder outputs only.

output "project_name" {
  description = "Project name used by the Terraform configuration."
  value       = var.project_name
}

output "environment" {
  description = "Deployment environment."
  value       = var.environment
}

output "aws_region" {
  description = "AWS region for this Terraform workspace."
  value       = var.aws_region
}