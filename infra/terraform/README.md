# Terraform Workspace

## Durham Risk Intelligence Dashboard

## Purpose

This folder contains Terraform configuration for provisioning AWS infrastructure for the Durham Risk Intelligence Dashboard.

The dashboard application is a FastAPI based geospatial analytics project. This Terraform workspace is intended to support the infrastructure layer needed to host that application in AWS in a repeatable and documented way.

## Current Status

This is a starter Terraform workspace.

The AWS provider configuration, input variables, and placeholder outputs exist, but no AWS infrastructure resources are defined yet. At this stage, the workspace is ready for planning and incremental development, but it does not create EC2 instances, networking resources, load balancers, monitoring resources, or other AWS services.

## Terraform Strategy

The selected Terraform strategy is:

```text
Option 3: Hybrid Learning Approach
```

The manually created AWS deployment remains the working reference architecture while the Terraform managed version is built separately and incrementally.

The goal is to learn and document Infrastructure as Code without disrupting the stable dashboard. Terraform changes should be introduced carefully, reviewed through `terraform plan`, and kept separate from dashboard feature work.

## Planned First Implementation

The first Terraform implementation should stay small and reproducible.

Initial resources to add:

- EC2 instance
- Security group
- SSH access configuration
- HTTP or application port access
- Project tags
- Outputs for public IP and app URL

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
| `main.tf` | Defines the Terraform version constraint, AWS provider requirement, and provider region |
| `variables.tf` | Defines starter input variables such as AWS region, project name, environment, and owner |
| `outputs.tf` | Defines placeholder outputs for project name, environment, and AWS region |
| `terraform.tfvars.example` | Provides example variable values for future local Terraform runs |
| `.terraform.lock.hcl` | Locks provider dependency versions after `terraform init` |

## Future Usage Commands

These commands are for future use once infrastructure resources are defined:

```bash
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
```

Do not run `terraform apply` until resources have been intentionally added and the plan has been reviewed.

## Safety Notes

- Do not commit `terraform.tfvars` if it contains sensitive values.
- Do not commit AWS credentials.
- Keep Terraform changes separate from dashboard feature changes.
- Review `terraform plan` before applying changes.

## Next Step

The next step is adding the first Terraform resources:

- EC2 instance
- Security group
