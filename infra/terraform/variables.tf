# Durham Risk Intelligence Dashboard
# Terraform input variables

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

variable "instance_type" {
  description = "EC2 instance type for the Terraform managed dashboard server."
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "Existing AWS EC2 key pair name used for SSH access."
  type        = string
  default     = "durham-risk-dashboard-key"
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to connect to the EC2 instance over SSH."
  type        = string
  default     = "136.47.213.3/32"
}

variable "allowed_app_cidr" {
  description = "CIDR block allowed to access the public dashboard application."
  type        = string
  default     = "0.0.0.0/0"
}

variable "http_port" {
  description = "HTTP port used by the Nginx reverse proxy."
  type        = number
  default     = 80
}

variable "app_port" {
  description = "Application port used internally by the FastAPI dashboard."
  type        = number
  default     = 8000
}