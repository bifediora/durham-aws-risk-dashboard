# Durham Risk Intelligence Dashboard
# Terraform outputs

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

output "dashboard_instance_id" {
  description = "ID of the Terraform managed EC2 dashboard instance."
  value       = aws_instance.dashboard.id
}

output "dashboard_public_ip" {
  description = "Public IP address of the Terraform managed EC2 dashboard instance."
  value       = aws_instance.dashboard.public_ip
}

output "dashboard_public_dns" {
  description = "Public DNS name of the Terraform managed EC2 dashboard instance."
  value       = aws_instance.dashboard.public_dns
}

output "dashboard_security_group_id" {
  description = "ID of the dashboard EC2 security group."
  value       = aws_security_group.dashboard_ec2.id
}

output "dashboard_app_url" {
  description = "Public dashboard URL served through Nginx on HTTP port 80."
  value       = "http://${aws_instance.dashboard.public_ip}"
}

output "dashboard_internal_app_port" {
  description = "Internal FastAPI application port used behind Nginx."
  value       = var.app_port
}

output "dashboard_ssh_command" {
  description = "SSH command for connecting to the Terraform managed EC2 instance."
  value       = "ssh -i ~/.ssh/durham-risk-dashboard-key.pem ec2-user@${aws_instance.dashboard.public_ip}"
}
