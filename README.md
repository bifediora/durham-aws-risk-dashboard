# Durham Risk Intelligence Dashboard

## Project Overview

The Durham Risk Intelligence Dashboard is a cloud hosted FastAPI application built as part of an AWS cloud engineering portfolio project.

The project uses sample Durham, North Carolina public safety data to create a geospatial analytics dashboard. The application combines public safety records, spatial context, dashboard analytics, AWS deployment, monitoring, and artifact storage.

The broader portfolio goal is to demonstrate three cloud engineering phases:

1. Build a production style AWS architecture
2. Convert the infrastructure to Terraform
3. Add CI/CD deployment automation

This repository currently represents the application workload and early AWS Phase 1 deployment foundation.

## Portfolio Purpose

This project is designed to show the ability to:

- Build a real data driven web application
- Deploy a FastAPI app to AWS EC2
- Configure a persistent Linux service with `systemd`
- Use AWS CloudWatch and SNS for basic monitoring
- Use S3 for private project artifact storage
- Structure a project for future Terraform automation
- Structure a project for future CI/CD deployment
- Connect cloud infrastructure to a meaningful geospatial analytics use case

## Current Project Status

Current status:

```text
Local dashboard: working
Public EC2 dashboard: working
Persistent EC2 service: working
CloudWatch monitoring: configured
SNS alerting: configured
Private S3 artifact bucket: created
Runtime dependencies: cleaned
Architecture notes: documented
Process log: documented

```

## Current AWS Architecture

The current deployment uses an early Phase 1 AWS architecture.

```text
User
  ↓
Public EC2 IP on port 8000
  ↓
FastAPI dashboard application
  ↓
Local CSV based sample data
```

Current public dashboard endpoint:

```text
http://35.172.140.39:8000/dashboard
```

Current health endpoint:

```text
http://35.172.140.39:8000/health
```

Note: The current dashboard is exposed through direct EC2 access on port 8000 for development purposes. A future production architecture should place the application behind an Application Load Balancer.

## Current AWS Services Used

| AWS Service | Purpose |
|---|---|
| EC2 | Hosts the FastAPI dashboard application |
| Security Group | Controls SSH and dashboard access |
| CloudWatch | Provides basic monitoring through a CPU alarm |
| SNS | Sends alert notifications from CloudWatch |
| S3 | Stores private project artifacts such as screenshots, reports, and diagrams |
| IAM | Supports AWS account and service access configuration |

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
| / | Homepage |
| /health | Service health check |
| /dashboard | HTML dashboard |
| /api/summary | Summary metrics as JSON |
| /api/records | Sample records as JSON |
| /api/map-points | Converted arrest coordinates for map display |
| /api/by-district | Arrest counts by district |
| /api/by-severity | Felony versus misdemeanor counts |
| /api/top-offenses | Top offense descriptions |
| /api/by-hour | Arrest counts by hour of day |

## Geospatial Processing

The dashboard uses sample arrest data with projected X and Y coordinate fields.

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
      s3_test_artifact.txt
  data/
    sample_arrests.csv
    raw_geo/
  docs/
    aws_architecture_notes.md
    cloudwatch_monitoring_notes.md
    dashboard_enhancement_plan.md
    ec2_deployment_notes.md
    process_log.md
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

Local geospatial processing tools such as geopandas, pyogrio, and shapely may be used for preparing GeoJSON layers, but they are not required for the current EC2 runtime app.

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

## Current Security Group Access

| Port | Purpose | Source |
|---|---|---|
| 22 | SSH access | Current user IP |
| 8000 | FastAPI dashboard access | Current user IP |

This is a development configuration. The target production configuration should route public traffic through an Application Load Balancer instead of direct EC2 port access.

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
Application Load Balancer in public subnets
  ↓
EC2 FastAPI instances in private subnets
  ↓
Private data layer or local application data
  ↓
S3 artifact and export storage
```

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
- Load balancer
- Target group
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

1. Finalize README and documentation
2. Capture dashboard screenshots
3. Upload screenshots to S3 artifacts bucket
4. Create architecture diagram
5. Add Application Load Balancer
6. Add target group and health checks
7. Move toward Auto Scaling Group

Future:

1. Convert infrastructure to Terraform
2. Add CI/CD deployment pipeline
3. Add structured data storage option
4. Add additional dashboard filters
5. Add ML readiness endpoints or baseline modeling workflow

## Portfolio Narrative

This project demonstrates the ability to take a meaningful data application from local development to cloud deployment.

The project story:

```text
I built a geospatial risk intelligence dashboard using FastAPI and Durham public safety data, deployed it to AWS EC2, added persistent service management, configured CloudWatch and SNS monitoring, created private S3 artifact storage, and structured the project for future Terraform and CI/CD automation.
```

The application workload gives the AWS architecture practical meaning by connecting cloud infrastructure to public sector analytics, geospatial intelligence, and future applied ML readiness.
