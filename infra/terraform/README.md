# Terraform Workspace

## Durham Risk Intelligence Dashboard

## Purpose

This folder contains Terraform configuration for provisioning AWS infrastructure for the Durham Risk Intelligence Dashboard.

The dashboard application is a FastAPI based geospatial analytics project. This Terraform workspace is intended to support the infrastructure layer needed to host that application in AWS in a repeatable and documented way.

## Current Status

This is now an active Terraform infrastructure workspace.

The AWS provider configuration, input variables, EC2 resource, security group resource, and operational outputs are defined. Terraform currently provisions a clean Amazon Linux 2023 EC2 instance and a security group for SSH and dashboard web access.

This Terraform managed environment is separate from the original manually created AWS deployment, which remains the working reference architecture while the Infrastructure as Code version is built incrementally.

After provisioning, the dashboard application was installed manually on the Terraform managed EC2 instance and configured as a persistent `systemd` service. Nginx was also configured manually as a reverse proxy. Terraform currently manages the infrastructure foundation and security group rules only; it does not yet automate application installation, dependency setup, service creation, Nginx setup, or deployment updates.

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

## Manual Application Deployment Checkpoint

The FastAPI dashboard has been successfully deployed on the Terraform managed EC2 instance after provisioning.

Manual setup completed after Terraform apply:

- Confirmed SSH access to the EC2 instance.
- Confirmed Amazon Linux 2023 runtime.
- Installed base packages including Git, Python, build tooling, and Nginx.
- Cloned the project repository to `/home/ec2-user/durham-aws-risk-dashboard`.
- Created the project virtual environment with Python 3.11.
- Installed application dependencies.
- Added the missing runtime dependency `shapely` to `requirements.txt`.
- Started the dashboard with Uvicorn.
- Created and enabled `/etc/systemd/system/durham-risk-dashboard.service`.
- Confirmed the service is active and running.

Current public application URL:

```text
http://98.93.40.196
```

Health check result:

```json
{"status":"healthy","service":"Durham Risk Intelligence Dashboard","version":"0.3.6"}
```

This manual deployment step is part of the hybrid learning approach. Future work may automate application setup with `user_data`, provisioning scripts, configuration management, or CI/CD.

## Nginx Reverse Proxy Checkpoint

Nginx has been configured manually on the Terraform managed EC2 instance as a reverse proxy.

Current request routing:

```text
Public user
  -> port 80
  -> Nginx
  -> 127.0.0.1:8000
  -> FastAPI app
```

Nginx configuration path on the EC2 instance:

```text
/etc/nginx/conf.d/durham-risk-dashboard.conf
```

Terraform now manages the security group rule that allows inbound HTTP traffic on port `80`. The reverse proxy configuration itself was performed manually as part of the hybrid learning approach.

Current health check URL:

```text
http://98.93.40.196/health
```

FastAPI app traffic should eventually be limited internally while Nginx handles public web traffic. Future work may automate Nginx setup through EC2 `user_data`, a provisioning script, Ansible, or CI/CD.

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
- EC2 `user_data` for application bootstrap
- Provisioning scripts for repeatable app setup
- Automated Nginx reverse proxy setup
- Internal-only FastAPI application access behind Nginx
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

The next likely infrastructure improvement is CloudWatch monitoring, deployment automation, HTTPS, or domain setup for the Terraform managed deployment. Future Terraform work may automate the manual application and Nginx setup after the current deployment path is reviewed.
