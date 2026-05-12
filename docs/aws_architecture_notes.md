# AWS Architecture Notes

## Project Name

Durham Risk Intelligence Dashboard

## Project Purpose

The Durham Risk Intelligence Dashboard is a cloud hosted FastAPI application designed to demonstrate AWS cloud engineering fundamentals using a meaningful geospatial analytics workload.

The application uses sample Durham public safety data to support dashboard based analysis of arrest records, spatial patterns, offense categories, severity levels, and temporal trends.

This project is part of a broader cloud portfolio path with three major phases:

1. Build a production style AWS architecture
2. Convert the infrastructure to Terraform
3. Add CI/CD deployment automation

## Current Architecture Status

The current implementation is an early Phase 1 AWS architecture.

The dashboard is deployed on a single EC2 instance and served through a persistent `systemd` service. Monitoring has been added through CloudWatch and SNS. A private S3 bucket has also been created for project artifacts.

## Current AWS Services Implemented

| Service | Current Purpose |
|---|---|
| EC2 | Hosts the FastAPI dashboard application |
| Security Group | Controls inbound SSH and dashboard access |
| CloudWatch | Provides basic monitoring through a CPU alarm |
| SNS | Sends alert notifications from CloudWatch |
| S3 | Stores private project artifacts such as screenshots, reports, and diagrams |
| IAM | Supports AWS service access and account level security configuration |

## Current Application Runtime

The application runs on an Ubuntu EC2 instance.

Current runtime structure:

```text
User
  ↓
Public EC2 IP on port 8000
  ↓
FastAPI application
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

## EC2 Configuration

Current EC2 role in the architecture:

- Hosts the FastAPI application
- Serves the dashboard on port `8000`
- Runs the application through a persistent `systemd` service
- Uses a Python virtual environment for dependency isolation
- Reads sample data from the local EC2 project directory
- Serves templates, static files, JavaScript, CSS, and GeoJSON assets

Current EC2 project directory:

```text
/home/ubuntu/durham-aws-risk-dashboard
```

Current service name:

```text
durham-risk-dashboard
```

Service management commands:

```bash
sudo systemctl status durham-risk-dashboard --no-pager
sudo systemctl restart durham-risk-dashboard
```

## Security Group Configuration

Current security group access:

| Port | Purpose | Source |
|---|---|---|
| 22 | SSH access | Current user IP |
| 8000 | FastAPI dashboard access | Current user IP |

The current dashboard is intentionally restricted by source IP during development.

Future production architecture should move public access from direct EC2 port access to an Application Load Balancer.

## S3 Artifact Storage

A private S3 bucket has been created for project artifacts.

Bucket name:

```text
durham-risk-dashboard-artifacts-byron-333973504198-us-east-1-an
```

Bucket purpose:

- Store dashboard screenshots
- Store architecture diagrams
- Store exported reports
- Store project documentation artifacts
- Support future Terraform and CI/CD phases

Bucket configuration:

- Region: `us-east-1`
- Block all public access: enabled
- Object ownership: ACLs disabled
- Default encryption: SSE-S3
- Bucket Key: disabled

The bucket is not being used for public website hosting. It is currently a private artifact storage layer.

## Monitoring and Alerts

Basic monitoring has been configured through CloudWatch and SNS.

Current monitoring components:

- CloudWatch CPU alarm
- SNS topic for dashboard alerts
- Email notification subscription

Current alarm:

```text
durham-risk-dashboard-high-cpu
```

Current SNS topic:

```text
durham-risk-dashboard-alerts
```

This provides an early operational monitoring layer for the EC2 hosted dashboard.

## Current Application Features

The deployed dashboard currently includes:

- Styled FastAPI homepage
- Dashboard route
- Health check route
- Summary API route
- Records API route
- Map points API route
- Arrests by district API route
- Felony versus misdemeanor API route
- Top offenses API route
- Arrests by hour API route

Current dashboard visuals include:

- KPI cards
- Top district
- Top arrest type
- Most common offense description
- Interactive Leaflet map
- Durham County boundary layer
- Police beats overlay
- Arrest point overlay
- Gray, dark, and OpenStreetMap basemap toggles
- Layer toggles
- Arrests by district chart
- Felony versus misdemeanor chart
- Top 10 offense descriptions chart
- Arrests by hour chart

## Current Runtime Dependencies

The EC2 runtime app currently uses a cleaned `requirements.txt` focused on production runtime dependencies:

```text
fastapi==0.136.1
uvicorn==0.46.0
pandas==3.0.2
Jinja2==3.1.6
python-multipart==0.0.27
pyproj==3.7.2
```

Local geospatial processing dependencies such as `geopandas`, `pyogrio`, and `shapely` are not required for the deployed dashboard runtime unless GeoPackage conversion is performed directly on EC2.

## Target Production Architecture

The long term Phase 1 target is a more production style AWS architecture.

Target services include:

| Service | Target Purpose |
|---|---|
| VPC | Isolated cloud network for the application |
| Public Subnets | Host internet facing resources such as the Application Load Balancer |
| Private Subnets | Host EC2 application instances and future database resources |
| Internet Gateway | Allows public internet access to the load balancer |
| NAT Gateway | Allows private instances to access the internet for updates and dependencies |
| EC2 | Runs the FastAPI application |
| Application Load Balancer | Routes public traffic to healthy EC2 instances |
| Auto Scaling Group | Maintains and scales EC2 application instances |
| RDS | Future private database layer |
| S3 | Stores project artifacts, exports, and future data assets |
| CloudWatch | Logs, metrics, alarms, and operational monitoring |
| IAM | Secure permissions for AWS services and EC2 instances |

## Target Request Flow

The target production request flow is:

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

## Current Versus Target Architecture

| Component | Current State | Target State |
|---|---|---|
| Compute | Single EC2 instance | EC2 instances behind ALB |
| Public Access | Direct EC2 public IP on port 8000 | Application Load Balancer |
| Network | Default VPC | Custom VPC with public and private subnets |
| Scaling | Manual single instance | Auto Scaling Group |
| Data Layer | Local CSV file | Future RDS or structured storage |
| Artifacts | Private S3 bucket | Private S3 bucket managed by Terraform |
| Monitoring | CloudWatch CPU alarm and SNS | Expanded metrics, logs, health checks, and alarms |
| Deployment | Manual file copy and service restart | CI/CD pipeline |
| Infrastructure | Manually created AWS resources | Terraform managed infrastructure |

## Future Phase 1 Improvements

Recommended next AWS architecture improvements:

1. Create a custom VPC
2. Add public and private subnets
3. Add an Internet Gateway
4. Add route tables
5. Move toward an Application Load Balancer
6. Place the application behind the load balancer
7. Add a target group and health checks
8. Add a launch template
9. Add an Auto Scaling Group
10. Consider moving data storage to RDS or S3 based structured input

## Phase 2 Terraform Goal

After the Phase 1 architecture is stable, the infrastructure should be recreated using Terraform.

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

After Terraform is introduced, the project should add CI/CD deployment automation.

Target CI/CD components:

- GitHub repository
- CodePipeline
- CodeBuild
- CodeDeploy or deployment automation script
- Health check validation
- Deployment rollback strategy
- Documentation for deployment flow

## Portfolio Narrative

This project demonstrates the ability to take a data driven application from local development to cloud deployment.

The portfolio story is:

```text
I built a geospatial risk intelligence dashboard using FastAPI and Durham public safety data, deployed it to AWS EC2, added persistent service management, configured CloudWatch and SNS monitoring, created private S3 artifact storage, and structured the project for future Terraform and CI/CD automation.
```

The application workload gives the AWS architecture practical meaning by connecting cloud infrastructure to public sector analytics, geospatial intelligence, and future applied ML readiness.