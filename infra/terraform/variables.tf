# Durham Risk Intelligence Dashboard
# Terraform input variables
#
# Purpose:
# This file will eventually define reusable input variables for the Terraform
# configuration.
#
# Current status:
# Starter variables only.

variable "aws_region" {
  description = "AWS region where the Durham Risk Intelligence Dashboard infrastructure will be deployed."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for naming and tagging AWS resources."
  type        = string
  default     = "durham-risk-dashboard"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "dev"
}

variable "owner" {
  description = "Resource owner for tagging."
  type        = string
  default     = "Byron Ifediora"
}