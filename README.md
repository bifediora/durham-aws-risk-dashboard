# Durham Risk Intelligence Dashboard

## Project Overview

The Durham Risk Intelligence Dashboard is a FastAPI based geospatial analytics application deployed on AWS as a cloud engineering portfolio project.

The dashboard combines Durham public safety event data, census tract analytics, ACS demographic context, municipal geography, neighborhood reference layers, and interactive map/chart views. It is framed as a public-facing risk intelligence, preparedness, and resilience interpretation prototype, not as an enforcement prediction tool.

The current final portfolio deployment is a Terraform managed single-instance AWS architecture:

```text
User browser
  -> EC2 public IP on HTTP port 80
  -> Nginx reverse proxy
  -> FastAPI app on localhost port 8000
  -> dashboard routes, static assets, templates, and local project data
```

Application deployment is automated through GitHub Actions using GitHub OIDC, AWS IAM, and AWS Systems Manager. Monitoring includes EC2 CloudWatch alarms, SNS email alerting, and a Route 53 HTTP health check for the public `/health` endpoint.

## Portfolio Purpose

This project demonstrates the ability to:

- Build a data-driven FastAPI web application.
- Design a public-facing geospatial dashboard with Leaflet and Chart.js.
- Deploy a Python application to AWS EC2.
- Use Nginx as a public reverse proxy in front of an internal FastAPI runtime.
- Manage cloud infrastructure with Terraform.
- Configure persistent application runtime with `systemd`.
- Add CloudWatch alarms and SNS email alerting.
- Add Route 53 application health monitoring for a public health endpoint.
- Use AWS Systems Manager for remote deployment command execution.
- Use GitHub Actions OIDC for keyless AWS deployment automation.
- Connect cloud infrastructure work to a meaningful geospatial analytics use case.

## Current Project Status

Current final portfolio status:

```text
Dashboard MVP: feature frozen
MVP Git tag: dashboard-mvp-v1
AWS deployment: active
Infrastructure management: Terraform
Compute: single Amazon Linux 2023 EC2 instance
Public web entry point: Nginx on HTTP port 80
FastAPI runtime: localhost port 8000
Service manager: systemd
Public dashboard URL: http://54.242.183.123
Health endpoint: http://54.242.183.123/health
Deployment automation: GitHub Actions + OIDC + AWS SSM
Monitoring: CloudWatch, SNS, Route 53 health check
Direct public FastAPI port 8000 access: closed
```

Earlier ALB, Target Group, Custom AMI, Launch Template, and Auto Scaling Group work is retained in `docs/` as exploratory AWS architecture documentation. Those components are not the current final deployment path for this portfolio version.

## Dashboard MVP Checkpoint

The dashboard MVP is feature frozen at the Git tag:

```text
dashboard-mvp-v1
```

This checkpoint captures Phase 5: Dashboard MVP Polish and Analytical Layer Expansion.

Current dashboard capabilities include:

- Interactive Leaflet map with point, cluster, density, and choropleth visualization modes.
- Durham municipal boundary geography and census tracts intersecting the municipal boundary.
- Full census tract geometries preserved for ACS and tract-level analytical consistency.
- Tract-level enrichment outputs combining ACS demographic indicators and event aggregates.
- Separate enriched arrest and shooting event outputs.
- Neighborhood context geography for public interpretation and local orientation.
- KPI cards, district and severity charts, top offense summaries, selected records, and a Temporal Activity Explorer.
- Start date and end date filtering intended to update the full dashboard.
- Refined tract popup behavior, choropleth legends, selected-feature highlighting, and spatial filtering interactions.

The dashboard should remain stable as a portfolio MVP. Current work has shifted from dashboard feature iteration to infrastructure, deployment automation, monitoring, and documentation.

## Current AWS Architecture

The current deployment uses a Terraform managed EC2 instance with Nginx as the public web entry point and FastAPI running internally.

```text
User browser
  ↓
EC2 public IP on HTTP port 80
  ↓
Nginx reverse proxy
  ↓
FastAPI application on localhost port 8000
  ↓
Dashboard routes, templates, static assets, GeoJSON layers, and local project data
```

Current public access:

```text
Dashboard: http://54.242.183.123
Health:    http://54.242.183.123/health
```

Confirmed runtime details:

| Item | Value |
|---|---|
| EC2 instance ID | `i-0998e40b915d53346` |
| Public HTTP port | `80` |
| Internal FastAPI port | `8000` |
| Service name | `durham-risk-dashboard.service` |
| EC2 deploy path | `/home/ec2-user/durham-aws-risk-dashboard` |
| GitHub repository | `bifediora/durham-aws-risk-dashboard` |
| AWS region | `us-east-1` |

## Terraform Managed Deployment

Terraform in `infra/terraform/` manages the current AWS infrastructure foundation:

- EC2 instance.
- Security group.
- IAM roles and instance profile for SSM.
- GitHub Actions OIDC deploy role.
- SNS topic.
- CloudWatch alarms.
- Route 53 application health check.
- Terraform outputs for public URL, instance details, and internal app port.

The EC2 instance uses a bootstrap script connected through Terraform `user_data`:

```text
infra/scripts/ec2_bootstrap.sh
```

The bootstrap process installs system dependencies, clones the repository, creates the Python virtual environment, installs `requirements.txt`, creates the `systemd` service, configures Nginx, and starts both services.

The Terraform security group allows public HTTP traffic on port `80`. Public inbound access to FastAPI port `8000` has been removed; port `8000` remains an internal application runtime port behind Nginx.

## Deployment Automation

Deployment is automated with GitHub Actions:

```text
.github/workflows/deploy.yml
```

Deployment flow:

```text
Developer pushes to main
  ↓
GitHub Actions starts
  ↓
GitHub OIDC assumes AWS IAM deploy role
  ↓
GitHub Actions sends AWS SSM command
  ↓
EC2 pulls latest code
  ↓
Python requirements are checked
  ↓
systemd restarts durham-risk-dashboard.service
  ↓
local /health endpoint is validated
```

GitHub Actions does not SSH into EC2, and no SSH access was opened for GitHub hosted runners. The workflow uses GitHub OIDC instead of long-lived AWS access keys in GitHub.

GitHub Actions deploy role:

```text
arn:aws:iam::333973504198:role/durham-risk-dashboard-dev-github-actions-deploy-role
```

## Monitoring and Alerting

The current deployment monitors both infrastructure health and application health.

Infrastructure monitoring:

- EC2 CPU utilization CloudWatch alarm.
- EC2 status check failure CloudWatch alarm.

Application monitoring:

- Route 53 HTTP health check against `http://54.242.183.123/health`.
- CloudWatch alarm on the Route 53 `HealthCheckStatus` metric.
- SNS email alert path through the dashboard alerts topic.

The Route 53 health check reaches the application through the public Nginx endpoint on port `80`. FastAPI remains internal on port `8000`.

## Screenshots

Screenshot artifacts are stored outside Git tracking and may be used for portfolio presentation material.

Local screenshot folder:

```text
artifacts/screenshots/
```

Example screenshot artifact names:

```text
dashboard_top_summary.png
dashboard_map_layers.png
dashboard_analytics_charts.png
```

## Repository Structure

```text
durham-aws-risk-dashboard/
  app/
    main.py
    templates/
    static/
      css/
      js/
      geojson/
  data/
    processed/
    raw_geo/
  docs/
    current_architecture_diagram.md
    dashboard_mvp_summary.md
    process_log.md
    ...
  infra/
    scripts/
      ec2_bootstrap.sh
    terraform/
      main.tf
      variables.tf
      outputs.tf
      README.md
      terraform.tfvars.example
  scripts/
    build_event_tract_enrichment.py
    build_neighborhood_context.py
    build_tract_join.py
    extract_durham_acs_tracts.py
  .github/
    workflows/
      deploy.yml
  requirements.txt
  README.md
```

## Technical Skills Demonstrated

- Python web application development with FastAPI.
- Geospatial dashboard development with Leaflet.
- Analytical charting with Chart.js.
- Census/ACS enrichment and tract-level geospatial processing.
- AWS EC2 application hosting.
- Nginx reverse proxy configuration.
- Linux service management with `systemd`.
- Terraform infrastructure management.
- IAM role design for EC2, SSM, and GitHub OIDC.
- AWS Systems Manager command execution.
- GitHub Actions deployment automation.
- CloudWatch alarms, SNS alerting, and Route 53 health checks.
- Security group hardening and public/private runtime separation.

## Current Limitations

This is a portfolio-ready single-instance deployment, not a multi-AZ production system.

Current limitations:

- No HTTPS certificate or custom domain yet.
- No Route 53 DNS record for a named dashboard URL yet.
- No CloudWatch log forwarding yet.
- No managed database layer; the dashboard uses local project data files.
- No blue/green or rolling deployment strategy.
- No multi-instance load balancing in the current final deployment.

## Future Improvements

Potential future improvements include:

- Add HTTPS with a managed certificate.
- Add a Route 53 DNS record for a stable dashboard domain.
- Add CloudWatch log forwarding for application and Nginx logs.
- Add deployment notifications for GitHub Actions runs.
- Add broader automated test gates before deployment.
- Explore AMI baking or a more formal release process.
- Evaluate whether a future ALB or multi-instance design is needed for a later production-style version.

## Documentation

Supporting documentation is stored in the `docs/` folder.

| Document | Purpose |
|---|---|
| `docs/current_architecture_diagram.md` | Final current AWS architecture diagram and deployment flow |
| `docs/dashboard_mvp_summary.md` | Dashboard MVP technical summary and Phase 6 operations update |
| `docs/process_log.md` | Chronological project build and milestone log |
| `infra/terraform/README.md` | Terraform workspace documentation |
| `docs/aws_architecture_notes.md` | Earlier AWS architecture notes and exploratory work |
| `docs/alb_target_group_notes.md` | Earlier ALB and Target Group exploration notes |
| `docs/auto_scaling_group_notes.md` | Earlier Auto Scaling Group exploration notes |

## Portfolio Narrative

This project demonstrates the ability to take a meaningful geospatial analytics application from local development to an AWS-hosted, Terraform-managed deployment with automated updates and operational monitoring.

The final portfolio architecture emphasizes a practical cloud engineering path: FastAPI application development, EC2 hosting, Nginx reverse proxying, security group hardening, Terraform infrastructure, SSM-based deployment automation, GitHub Actions OIDC federation, CloudWatch/SNS alerting, and Route 53 application health monitoring.
