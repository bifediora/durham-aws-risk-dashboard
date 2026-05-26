# Terraform Workspace

## Durham Risk Intelligence Dashboard

## Purpose

This folder contains Terraform configuration for provisioning AWS infrastructure for the Durham Risk Intelligence Dashboard.

The dashboard application is a FastAPI based geospatial analytics project. This Terraform workspace is intended to support the infrastructure layer needed to host that application in AWS in a repeatable and documented way.

## Current Status

This is now an active Terraform infrastructure workspace.

The AWS provider configuration, input variables, EC2 resource, security group resource, and operational outputs are defined. Terraform currently provisions a clean Amazon Linux 2023 EC2 instance and a security group for SSH and dashboard application access.

This Terraform managed environment is separate from the original manually created AWS deployment, which remains the working reference architecture while the Infrastructure as Code version is built incrementally.

## Terraform Strategy

The selected Terraform strategy is:

```text
Option 3: Hybrid Learning Approach
```

The manually created AWS deployment remains the working reference architecture while the Terraform managed version is built separately and incrementally.

The goal is to learn and document Infrastructure as Code without disrupting the stable dashboard. Terraform changes should be introduced carefully, reviewed through `terraform plan`, and kept separate from dashboard feature work.

## Completed First Implementation

The first Terraform implementation is intentionally small and reproducible.

Implemented resources and configuration:

- EC2 instance
- Security group
- SSH access configuration
- HTTP or application port access
- Project tags
- Outputs for public IP and app URL

## Current Terraform Outputs

The workspace currently exposes these outputs:

- `dashboard_instance_id`
- `dashboard_public_ip`
- `dashboard_public_dns`
- `dashboard_security_group_id`
- `dashboard_app_url`
- `dashboard_ssh_command`

## Future Expansion

Future Terraform expansion may include:

- VPC
- Public subnets
- Private subnets
- Internet Gateway
- Route tables
- Application Load Balancer
- Target Group
- Launch Template
- Auto Scaling Group
- S3 artifact bucket
- CloudWatch alarms
- SNS topic
- IAM role and instance profile
- GitHub Actions deployment integration

## Current Files

| File | Purpose |
|---|---|
| `main.tf` | Defines the Terraform version constraint, AWS provider requirement, provider region, EC2 instance, security group, and AMI lookup |
| `variables.tf` | Defines input variables for AWS region, project metadata, EC2 configuration, key pair, SSH CIDR, and application port |
| `outputs.tf` | Defines outputs for instance ID, public IP, public DNS, security group ID, dashboard URL, and SSH command |
| `terraform.tfvars.example` | Provides example variable values for future local Terraform runs |
| `.terraform.lock.hcl` | Locks provider dependency versions after `terraform init` |

## Usage Commands

Use these commands when reviewing or applying Terraform changes:

```bash
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
```

Review `terraform plan` before running `terraform apply`.

## Safety Notes

- Do not commit `terraform.tfvars` if it contains sensitive values.
- Do not commit AWS credentials.
- Keep Terraform changes separate from dashboard feature changes.
- Review `terraform plan` before applying changes.

## Next Step

The next step is installing and configuring the dashboard application on the Terraform managed EC2 instance in a later phase. Application installation and `systemd` setup have not been started in this Terraform checkpoint.
