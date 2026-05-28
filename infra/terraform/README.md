# Terraform Workspace

## Durham Risk Intelligence Dashboard

## Purpose

This folder contains Terraform configuration for provisioning AWS infrastructure for the Durham Risk Intelligence Dashboard.

The dashboard application is a FastAPI based geospatial analytics project. This Terraform workspace is intended to support the infrastructure layer needed to host that application in AWS in a repeatable and documented way.

## Current Status

This is now an active Terraform infrastructure workspace.

The AWS provider configuration, input variables, EC2 resource, security group resource, and operational outputs are defined. Terraform currently provisions a clean Amazon Linux 2023 EC2 instance and a security group for SSH and dashboard web access.

This Terraform managed environment is separate from the original manually created AWS deployment, which remains the working reference architecture while the Infrastructure as Code version is built incrementally.

Terraform now passes a bootstrap script to the EC2 instance through `user_data`. The bootstrap process configures the application runtime, `systemd` service, and Nginx reverse proxy when a new instance is created. Terraform currently manages the infrastructure foundation, security group rules, EC2 bootstrap handoff, SSM instance access, GitHub Actions OIDC deployment role, SNS topic, CloudWatch alarms, and Route 53 application health check.

Public dashboard traffic enters through Nginx on HTTP port `80`. The FastAPI application runs internally on port `8000` behind Nginx, and port `8000` is no longer exposed publicly through the Terraform managed security group. This is a security hardening step that keeps direct application server access off the public internet.

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
- Public HTTP access through Nginx on port `80`
- Internal FastAPI application port behind Nginx
- SNS topic
- CloudWatch alarms
- Route 53 application health check
- SSM support for EC2 deployment commands
- GitHub Actions OIDC deployment role
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
http://54.242.183.123
```

Health check result:

```json
{"status":"healthy","service":"Durham Risk Intelligence Dashboard","version":"0.3.6"}
```

This manual deployment step is part of the hybrid learning approach. Future work may automate application setup with `user_data`, provisioning scripts, configuration management, or CI/CD.

## EC2 Bootstrap Automation Checkpoint

Terraform now connects an EC2 bootstrap script to the dashboard instance through `user_data`.

Bootstrap script:

```text
infra/scripts/ec2_bootstrap.sh
```

The bootstrap process now configures:

- System packages, including Git, Python 3.11, development dependencies, `gcc`, and Nginx.
- Project repository clone.
- Python virtual environment.
- Application dependency installation from `requirements.txt`.
- FastAPI dashboard `systemd` service.
- Nginx reverse proxy configuration.
- Startup and enablement for both the dashboard service and Nginx.

FastAPI is configured to run internally on port `8000`, while Nginx handles public web traffic on port `80`.

Terraform also uses `user_data_replace_on_change` so bootstrap script changes intentionally recreate the EC2 instance. This makes replacement behavior explicit and keeps the deployment recoverable.

This milestone reduced manual setup risk. If Terraform replaces the EC2 instance, the dashboard runtime can now be recreated automatically instead of relying on manual server configuration.

Current public dashboard URL:

```text
http://54.242.183.123
```

Current health check URL:

```text
http://54.242.183.123/health
```

Future improvements may include CI/CD, a dedicated deployment script, AMI baking, or SSM based management.

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

Terraform manages the security group rule that allows inbound HTTP traffic on port `80`. Public inbound access to port `8000` is intentionally closed; FastAPI remains reachable internally through `127.0.0.1:8000` behind Nginx.

Current health check URL:

```text
http://54.242.183.123/health
```

FastAPI app traffic should eventually be limited internally while Nginx handles public web traffic. Future work may automate Nginx setup through EC2 `user_data`, a provisioning script, Ansible, or CI/CD.

## CloudWatch and SNS Monitoring Checkpoint

Terraform now manages basic monitoring and alerting resources for the EC2 dashboard deployment.

Managed monitoring resources:

- SNS topic: `durham-risk-dashboard-dev-alerts`
- CloudWatch alarm: `durham-risk-dashboard-dev-ec2-high-cpu`
- CloudWatch alarm: `durham-risk-dashboard-dev-ec2-status-check-failed`

Current monitored signals:

- EC2 CPU utilization
- EC2 status check failure

The SNS email endpoint is configured through local Terraform variable values, such as `terraform.tfvars`, and should not be committed. The `terraform.tfvars` file remains ignored by Git to avoid exposing private notification endpoints or other local configuration values.

Current alarm states:

```text
CPUUtilization: OK
StatusCheckFailed: OK
```

Future monitoring improvements may include application health check monitoring, log forwarding, a CloudWatch dashboard, and notification refinement.

## Application Health Monitoring Checkpoint

Terraform now manages application-level health monitoring for the public dashboard endpoint.

Managed application health resources:

- Route 53 health check: `db6f0811-3d67-4773-80fa-4543012b273d`
- CloudWatch alarm: `durham-risk-dashboard-dev-app-health-check-failed`

Health check target:

```text
Type: HTTP
IP address: 54.242.183.123
Port: 80
Resource path: /health
```

CloudWatch alarms on the Route 53 `HealthCheckStatus` metric. Alert notifications reuse the existing Terraform managed dashboard SNS alerts topic.

Current application health alarm state:

```text
OK
```

The health check monitors the public Nginx endpoint on port `80`. FastAPI continues to run internally on port `8000` behind Nginx, and public users should not access the FastAPI port directly.

The EC2 instance resource also uses `lifecycle ignore_changes` for `ami` so changes to the latest Amazon Linux 2023 AMI do not unintentionally replace the dashboard instance.

## GitHub Actions Deployment Automation Checkpoint

Terraform now supports GitHub Actions deployment automation through AWS IAM OIDC and AWS Systems Manager.

Workflow file:

```text
.github/workflows/deploy.yml
```

Deployment flow:

```text
Push to main
  -> GitHub Actions starts
  -> GitHub OIDC assumes AWS IAM deploy role
  -> GitHub Actions sends AWS SSM command to EC2
  -> EC2 pulls latest code from GitHub
  -> Python requirements are checked
  -> systemd restarts durham-risk-dashboard.service
  -> local /health check passes
```

GitHub Actions does not SSH into the EC2 instance. No EC2 SSH port access was opened for GitHub runners. GitHub OIDC is used instead of long-lived AWS access keys in GitHub, and AWS Systems Manager is used for deployment command execution.

Terraform resources for SSM support:

```text
aws_iam_role.dashboard_ec2_ssm_role
aws_iam_role_policy_attachment.dashboard_ec2_ssm_core
aws_iam_instance_profile.dashboard_ec2_ssm_profile
iam_instance_profile attached to aws_instance.dashboard
```

Terraform resources for GitHub Actions OIDC:

```text
aws_iam_openid_connect_provider.github_actions
aws_iam_role.github_actions_deploy_role
aws_iam_role_policy.github_actions_ssm_deploy_policy
```

Confirmed deployment details:

```text
EC2 instance ID: i-0998e40b915d53346
EC2 service name: durham-risk-dashboard.service
EC2 deploy path: /home/ec2-user/durham-aws-risk-dashboard
GitHub repo: bifediora/durham-aws-risk-dashboard
AWS region: us-east-1
GitHub Actions deploy role: arn:aws:iam::333973504198:role/durham-risk-dashboard-dev-github-actions-deploy-role
```

The SSM managed instance was confirmed online, the SSM deployment test succeeded, and the GitHub Actions deployment workflow succeeded.

## Current Terraform Outputs

The workspace currently exposes these outputs:

- `dashboard_instance_id`
- `dashboard_public_ip`
- `dashboard_public_dns`
- `dashboard_security_group_id`
- `dashboard_app_url`: public Nginx URL without `:8000`
- `dashboard_internal_app_port`: internal FastAPI port behind Nginx
- `dashboard_ssh_command`

## Security Hardening Checkpoint

Terraform now manages the security group rule that allows public HTTP traffic on port `80`.

Terraform no longer exposes port `8000` publicly. The `app_port` variable remains defined because FastAPI still uses port `8000` internally behind Nginx.

The public dashboard output now points to the Nginx URL:

```text
dashboard_app_url = "http://54.242.183.123"
```

The internal FastAPI port is documented separately:

```text
dashboard_internal_app_port = 8000
```

This is a security hardening step. Public users should access the dashboard through Nginx on port `80`; direct public access to the FastAPI runtime should remain closed.

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
- Application health check monitoring
- CloudWatch log forwarding
- CloudWatch dashboard
- Notification refinement
- IAM role and instance profile
- EC2 `user_data` for application bootstrap
- Provisioning scripts for repeatable app setup
- Automated Nginx reverse proxy setup
- Internal-only FastAPI application access behind Nginx
- Dedicated deployment script
- AMI baking
- SSM based management
- GitHub Actions deployment integration
- Deployment notifications
- Workflow status reporting

## Current Files

| File | Purpose |
|---|---|
| `main.tf` | Defines the Terraform version constraint, AWS provider requirement, provider region, EC2 instance, security group, and AMI lookup |
| `variables.tf` | Defines input variables for AWS region, project metadata, EC2 configuration, key pair, SSH CIDR, application port, and application health monitoring |
| `outputs.tf` | Defines outputs for instance ID, public IP, public DNS, security group ID, dashboard URL, and SSH command |
| `terraform.tfvars.example` | Provides example variable values for future local Terraform runs |
| `.terraform.lock.hcl` | Locks provider dependency versions after `terraform init` |
| `../scripts/ec2_bootstrap.sh` | Bootstraps the EC2 application runtime, `systemd` service, and Nginx reverse proxy through Terraform `user_data` |
| `../../.github/workflows/deploy.yml` | Runs GitHub Actions deployment through OIDC-authenticated SSM command execution |

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

The next likely improvements are deployment notifications, workflow status reporting, log forwarding, HTTPS, or domain setup for the Terraform managed deployment. Future work should build on the current `user_data` bootstrap and GitHub Actions SSM deployment foundation.
