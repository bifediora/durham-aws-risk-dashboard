# Durham Risk Intelligence Dashboard

## Project Overview

The Durham Risk Intelligence Dashboard is a cloud hosted FastAPI application built as part of an AWS cloud engineering portfolio project.

The project uses sample Durham, North Carolina public safety data to create a geospatial analytics dashboard. The application combines public safety records, spatial context, dashboard analytics, AWS deployment, monitoring, artifact storage, and load balanced application access.

The broader portfolio goal is to demonstrate three cloud engineering phases:

1. Build a production style AWS architecture
2. Convert the infrastructure to Terraform
3. Add CI/CD deployment automation

This repository currently represents the application workload and Phase 1 AWS architecture foundation.

## Portfolio Purpose

This project is designed to show the ability to:

- Build a real data driven web application
- Deploy a FastAPI app to AWS EC2
- Configure a persistent Linux service with systemd
- Place an application behind an Application Load Balancer
- Configure a Target Group with health checks
- Use AWS CloudWatch and SNS for basic monitoring
- Use S3 for private project artifact storage
- Structure a project for future Terraform automation
- Structure a project for future CI/CD deployment
- Connect cloud infrastructure to a meaningful geospatial analytics use case

## Current Project Status

Current status:

```text
Local dashboard: working
EC2 dashboard: working
Application Load Balancer: working
Target Group: healthy
Dashboard through ALB: working
Persistent EC2 service: working
CloudWatch monitoring: configured
SNS alerting: configured
Private S3 artifact bucket: created
Dashboard screenshots captured and uploaded to S3
Runtime dependencies: cleaned
Architecture notes: documented
Current architecture diagram: documented
Target architecture diagram: documented
ALB target group notes: documented
Project checkpoint: documented
Process log: documented
GitHub repository: created and pushed
```

## Current AWS Architecture

The current deployment uses a Phase 1 AWS architecture in progress.

The dashboard is deployed on an EC2 instance, served through a persistent `systemd` service, and accessed through an Application Load Balancer.

```text
User
  ↓
Application Load Balancer on port 80
  ↓
Target Group
  ↓
EC2 FastAPI application on port 8000
  ↓
Local CSV based sample data
```

Current preferred dashboard access pattern:

```text
http://<ALB-DNS-NAME>/dashboard
```

Current preferred health endpoint access pattern:

```text
http://<ALB-DNS-NAME>/health
```

Direct EC2 access on port `8000` may still be available temporarily for development and troubleshooting, but the preferred access path is now through the Application Load Balancer.

## Architecture Documentation

Supporting architecture documentation is stored in the `docs/` folder.

| Document | Purpose |
|---|---|
| `docs/current_architecture_diagram.md` | Mermaid based diagram of the current AWS deployment |
| `docs/target_architecture_diagram.md` | Mermaid based diagram and notes for the target Phase 1 production style AWS architecture |
| `docs/aws_architecture_notes.md` | Current architecture notes, target architecture, Terraform goals, and CI/CD goals |
| `docs/alb_target_group_notes.md` | Detailed ALB, Target Group, health check, security group, and troubleshooting notes |
| `docs/project_checkpoint.md` | Current project state, handoff notes, AWS resources, GitHub status, and next steps |
| `docs/ec2_deployment_notes.md` | EC2 setup and deployment notes |
| `docs/cloudwatch_monitoring_notes.md` | CloudWatch and SNS monitoring notes |
| `docs/process_log.md` | Step by step project build log |
| `docs/dashboard_enhancement_plan.md` | Dashboard improvement plan and feature notes |

The current architecture now follows this working deployment pattern:

```text
User
  ↓
Application Load Balancer on port 80
  ↓
Target Group
  ↓
EC2 FastAPI application on port 8000
  ↓
Local sample data, templates, static assets, GeoJSON layers, and charts
```

Supporting AWS services include:

- CloudWatch
- SNS
- S3
- GitHub
- EC2 security group controls
- ALB security group controls
- Target Group health checks

## Current AWS Services Used

| AWS Service | Purpose |
|---|---|
| EC2 | Hosts the FastAPI dashboard application |
| Application Load Balancer | Provides the public HTTP entry point for the dashboard |
| Target Group | Routes ALB traffic to the EC2 FastAPI application on port `8000` |
| Security Groups | Control SSH access, ALB browser access, and ALB to EC2 application traffic |
| CloudWatch | Provides basic monitoring through a CPU alarm |
| SNS | Sends alert notifications from CloudWatch |
| S3 | Stores private project artifacts such as screenshots, reports, and diagrams |
| IAM | Supports AWS account and service access configuration |

## Application Load Balancer

Application Load Balancer name:

```text
durham-risk-dashboard-alb
```

Load balancer type:

```text
Application Load Balancer
```

Scheme:

```text
Internet-facing
```

Listener:

```text
HTTP : 80
```

Default action:

```text
Forward to durham-risk-dashboard-tg
```

Confirmed working ALB routes:

```text
/health
/dashboard
```

## Target Group

Target Group name:

```text
durham-risk-dashboard-tg
```

Target type:

```text
Instance
```

Protocol and port:

```text
HTTP : 8000
```

Health check path:

```text
/health
```

Success code:

```text
200
```

Registered target:

```text
durham-risk-dashboard-ec2
```

Target EC2 instance ID:

```text
i-07895b87a7d7eb25b
```

Final target health status:

```text
Healthy
```

## Health Check

The FastAPI health check endpoint is:

```text
/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "Durham Risk Intelligence Dashboard",
  "version": "0.2.3"
}
```

This endpoint is used by the Target Group to determine whether the EC2 application instance is healthy and available to receive traffic.

## Security Group Configuration

The current security group design separates public HTTP access from application traffic.

### ALB Security Group

ALB security group name:

```text
durham-risk-dashboard-alb-sg
```

ALB security group ID:

```text
sg-0039dbb4fe5326472
```

Current inbound rule:

| Type | Protocol | Port | Source | Purpose |
|---|---|---|---|---|
| HTTP | TCP | 80 | Current user IP | Allows browser access to the ALB during development |

Current outbound rule:

| Type | Protocol | Port | Destination | Purpose |
|---|---|---|---|---|
| Custom TCP | TCP | 8000 | 0.0.0.0/0 | Allows ALB outbound traffic to the FastAPI target on port `8000` |

### EC2 Security Group

EC2 security group name:

```text
launch-wizard-1
```

EC2 security group ID:

```text
sg-08614f1873385ef42
```

Relevant inbound rules:

| Type | Protocol | Port | Source | Purpose |
|---|---|---|---|---|
| SSH | TCP | 22 | Current user IP | Allows administrative SSH access |
| Custom TCP | TCP | 8000 | sg-0039dbb4fe5326472 | Allows FastAPI traffic from the ALB security group |

This means user traffic reaches the dashboard through the ALB on port `80`, while the EC2 application accepts application traffic on port `8000` from the ALB security group.

## S3 Artifact Bucket

A private S3 bucket has been created for project artifacts.

```text
durham-risk-dashboard-artifacts-byron-333973504198-us-east-1-an
```

The bucket is used for:

- Dashboard screenshots
- Architecture diagrams
- Exported reports
- Project documentation artifacts
- Future Terraform and CI/CD supporting files

The bucket is private and is not used for public website hosting.

## Screenshot Artifacts

Dashboard screenshots have been captured from the AWS deployment and uploaded to the private S3 artifacts bucket.

Local screenshot folder:

```text
artifacts/screenshots/
```

S3 screenshot folder:

```text
screenshots/
```

Current screenshot artifacts:

```text
dashboard_top_summary.png
dashboard_map_layers.png
dashboard_analytics_charts.png
```

These screenshots are intended for:

- GitHub portfolio documentation
- LinkedIn project summaries
- Architecture walkthroughs
- Future README visual updates
- Project presentation materials

The screenshot files are intentionally excluded from Git tracking through `.gitignore` because they are stored as private project artifacts in S3.

## Dashboard Features

The current dashboard includes:

- Styled homepage
- Dashboard route
- Health check route
- KPI cards
- Top district summary
- Top arrest type summary
- Most common offense description
- Interactive Leaflet map
- Durham County boundary overlay
- Police beats overlay
- Arrest point overlay
- Gray, dark, and OpenStreetMap basemap options
- Layer controls
- Arrests by district chart
- Felony versus misdemeanor chart
- Top 10 offense descriptions chart
- Arrests by hour chart

## Current API Endpoints

| Endpoint | Purpose |
|---|---|
| `/` | Homepage |
| `/health` | Service health check |
| `/dashboard` | HTML dashboard |
| `/api/summary` | Summary metrics as JSON |
| `/api/records` | Sample records as JSON |
| `/api/map-points` | Converted arrest coordinates for map display |
| `/api/by-district` | Arrest counts by district |
| `/api/by-severity` | Felony versus misdemeanor counts |
| `/api/top-offenses` | Top offense descriptions |
| `/api/by-hour` | Arrest counts by hour of day |

## Geospatial Processing

The dashboard uses sample arrest data with projected `X` and `Y` coordinate fields.

The application converts coordinates from:

```text
EPSG:2264
```

to:

```text
EPSG:4326
```

This allows the records to be displayed correctly on a web map using Leaflet.

The app also filters out coordinate outliers using a Durham area bounding box before rendering map points.

## Project Structure

```text
durham-aws-risk-dashboard/
  app/
    main.py
    templates/
      index.html
      dashboard.html
    static/
      css/
        styles.css
      js/
        dashboard.js
      geojson/
        durham_county_boundary.geojson
        police_beats.geojson
  artifacts/
    screenshots/
    diagrams/
    reports/
  data/
    sample_arrests.csv
    raw_geo/
  docs/
    alb_target_group_notes.md
    aws_architecture_notes.md
    cloudwatch_monitoring_notes.md
    current_architecture_diagram.md
    dashboard_enhancement_plan.md
    ec2_deployment_notes.md
    process_log.md
    project_checkpoint.md
    target_architecture_diagram.md
  scripts/
    convert_geo_layers.py
    run_local.sh
    run_production.sh
  requirements.txt
  README.md
```

## Runtime Dependencies

The deployed app uses a cleaned runtime dependency file:

```text
fastapi==0.136.1
uvicorn==0.46.0
pandas==3.0.2
Jinja2==3.1.6
python-multipart==0.0.27
pyproj==3.7.2
```

Local geospatial processing tools such as `geopandas`, `pyogrio`, and `shapely` may be used for preparing GeoJSON layers, but they are not required for the current EC2 runtime app.

## Running Locally

From the project root:

```bash
cd /Users/byron/Documents/Projects/durham-aws-risk-dashboard
source durham-risk-aws-env/bin/activate
./scripts/run_local.sh
```

Then open:

```text
http://127.0.0.1:8000/dashboard
```

Health check:

```text
http://127.0.0.1:8000/health
```

## EC2 Deployment Notes

The application is deployed on an Ubuntu EC2 instance.

Current EC2 project path:

```text
/home/ubuntu/durham-aws-risk-dashboard
```

Current service name:

```text
durham-risk-dashboard
```

Useful EC2 service commands:

```bash
sudo systemctl status durham-risk-dashboard --no-pager
sudo systemctl restart durham-risk-dashboard
```

The app runs through a persistent systemd service so it continues running after the SSH session is closed.

## GitHub Repository

The project has been initialized as a Git repository and pushed to GitHub.

Repository:

```text
https://github.com/bifediora/durham-aws-risk-dashboard
```

Current branch:

```text
main
```

Git tracking has been configured with a `.gitignore` that excludes:

- Python virtual environments
- Private keys
- Environment files
- AWS credentials
- Python cache files
- macOS system files
- Raw geospatial files
- Local artifact outputs
- Local databases
- Logs

The repository is intended to show source code, documentation, application structure, and deployment readiness while avoiding sensitive files and large raw data artifacts.

## Target Phase 1 Architecture

The target production style AWS architecture includes:

| Component | Purpose |
|---|---|
| VPC | Isolated cloud network |
| Public subnets | Internet facing resources |
| Private subnets | Application instances and private resources |
| Internet Gateway | Public internet routing |
| NAT Gateway | Outbound internet access for private instances |
| EC2 | Application compute |
| Application Load Balancer | Public traffic routing and health checks |
| Target Group | Registers EC2 instances and performs health checks |
| Launch Template | Defines reusable EC2 configuration |
| Auto Scaling Group | Instance recovery and scaling |
| RDS | Future private database layer |
| S3 | Artifact and export storage |
| CloudWatch | Logs, metrics, and alarms |
| SNS | Alert notifications |
| IAM | Secure service permissions |

Target request flow:

```text
User
  ↓
Application Load Balancer
  ↓
Target Group
  ↓
EC2 FastAPI instances
  ↓
Private data layer or local application data
  ↓
S3 artifact and export storage
```

## Current Versus Target Architecture

| Component | Current State | Target State |
|---|---|---|
| Compute | Single EC2 instance | EC2 instances managed by launch template and Auto Scaling Group |
| Public Access | Application Load Balancer on port `80` | Application Load Balancer with HTTPS and production DNS |
| Application Port | EC2 receives app traffic on port `8000` from ALB | Private EC2 app traffic from ALB only |
| Network | Default VPC | Custom VPC with public and private subnets |
| Scaling | Manual single instance | Auto Scaling Group |
| Data Layer | Local CSV file | Future RDS or structured storage |
| Artifacts | Private S3 bucket | Private S3 bucket managed by Terraform |
| Monitoring | CloudWatch CPU alarm, SNS, and Target Group health check | Expanded metrics, logs, health checks, and alarms |
| Deployment | Manual file copy, Git updates, and service restart | CI/CD pipeline |
| Infrastructure | Manually created AWS resources | Terraform managed infrastructure |

## Phase 2 Terraform Goal

After the Phase 1 architecture is stable, the project will be converted to Terraform.

Terraform should eventually manage:

- VPC
- Subnets
- Internet Gateway
- Route tables
- Security groups
- EC2
- IAM roles
- S3 bucket
- CloudWatch alarms
- SNS topic
- Application Load Balancer
- Target Group
- Launch Template
- Auto Scaling Group

## Phase 3 CI/CD Goal

After Terraform is introduced, the project will add CI/CD deployment automation.

Target CI/CD components:

- GitHub repository
- AWS CodePipeline
- AWS CodeBuild
- Deployment script or CodeDeploy
- Health check validation
- Rollback strategy
- Deployment documentation

## Current Roadmap

Near term:

1. Keep dashboard functionality frozen for now
2. Maintain screenshot artifacts in S3
3. Maintain current architecture documentation
4. Keep the Application Load Balancer as the preferred public access path
5. Maintain EC2 port `8000` access as restricted to the ALB security group
6. Create a launch template
7. Move toward Auto Scaling Group
8. Prepare for Terraform conversion

Future:

1. Convert infrastructure to Terraform
2. Add CI/CD deployment pipeline
3. Add structured data storage option
4. Add additional dashboard filters
5. Add ML readiness endpoints or baseline modeling workflow

## Portfolio Narrative

This project demonstrates the ability to take a meaningful data application from local development to cloud deployment and progressively mature the cloud architecture.

The project story:

```text
I built a geospatial risk intelligence dashboard using FastAPI and Durham public safety data, deployed it to AWS EC2, added persistent service management, configured CloudWatch and SNS monitoring, created private S3 artifact storage, captured dashboard screenshots as S3 artifacts, pushed the project to GitHub, documented the current and target AWS architectures, placed the application behind an Application Load Balancer with Target Group health checks, and tightened the security group path so public dashboard access flows through the ALB while the EC2 application port only accepts traffic from the ALB security group.
```

The application workload gives the AWS architecture practical meaning by connecting cloud infrastructure to public sector analytics, geospatial intelligence, and future applied ML readiness.
