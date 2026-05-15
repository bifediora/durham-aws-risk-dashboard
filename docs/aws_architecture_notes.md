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

The current implementation is a Phase 1 AWS architecture in progress.

The dashboard is deployed on a single EC2 instance and served through a persistent `systemd` service. The application is now placed behind an Application Load Balancer and Target Group. The target group health check is working, the EC2 target is healthy, and the dashboard is reachable through the ALB DNS name.

Monitoring has been added through CloudWatch and SNS. A private S3 bucket has also been created for project artifacts.

## Current AWS Services Implemented

| Service | Current Purpose |
|---|---|
| EC2 | Hosts the FastAPI dashboard application |
| Application Load Balancer | Provides the public HTTP entry point for the dashboard |
| Target Group | Routes ALB traffic to the EC2 FastAPI application on port `8000` |
| Security Groups | Control inbound SSH, ALB access, and ALB to EC2 application traffic |
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

## Application Load Balancer Configuration

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

IP address type:

```text
IPv4
```

Listener:

```text
HTTP : 80
```

Default action:

```text
Forward to durham-risk-dashboard-tg
```

Confirmed working routes through the ALB:

```text
/health
/dashboard
```

## Target Group Configuration

Target group name:

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

Protocol version:

```text
HTTP1
```

Health check protocol:

```text
HTTP
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

## Health Check Endpoint

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

## EC2 Configuration

Current EC2 role in the architecture:

- Hosts the FastAPI application
- Serves the dashboard on port `8000`
- Runs the application through a persistent `systemd` service
- Uses a Python virtual environment for dependency isolation
- Reads sample data from the local EC2 project directory
- Serves templates, static files, JavaScript, CSS, and GeoJSON assets
- Receives dashboard traffic from the Application Load Balancer

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

Runtime validation commands:

```bash
sudo ss -tulpn | grep 8000
curl http://127.0.0.1:8000/health
```

Confirmed FastAPI listener:

```text
0.0.0.0:8000
```

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

Purpose:

```text
Allows HTTP access to the Durham Risk Intelligence Dashboard Application Load Balancer.
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

This configuration means user traffic reaches the dashboard through the ALB on port `80`, while the EC2 application only accepts application traffic on port `8000` from the ALB security group.

## ALB Troubleshooting Summary

During setup, the target group initially showed:

```text
Unused
```

Reason:

```text
Target is in an Availability Zone that is not enabled for the load balancer
```

Fix:

The ALB subnet mapping was updated to include the Availability Zone where the EC2 target was running.

After that fix, the target status changed to:

```text
Unhealthy
```

Health status reason:

```text
Request timed out
```

The FastAPI application was then validated directly on EC2 using:

```bash
sudo ss -tulpn | grep 8000
curl http://127.0.0.1:8000/health
curl http://172.31.40.20:8000/health
```

The application was confirmed to be listening on:

```text
0.0.0.0:8000
```

The main issue was that the ALB was initially attached to the wrong security group:

```text
sg-0f149ba485cdd5aae
default
```

The EC2 security group was allowing port `8000` traffic from the intended ALB security group:

```text
sg-0039dbb4fe5326472
```

but the ALB itself was not using that security group.

Fix:

The ALB security group attachment was changed to:

```text
sg-0039dbb4fe5326472
durham-risk-dashboard-alb-sg
```

After this correction, the target group became healthy and the dashboard opened successfully through the ALB DNS name.

Detailed notes are stored in:

```text
docs/alb_target_group_notes.md
```

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
- Target group health check through the ALB

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

The long term Phase 1 target is a more complete production style AWS architecture.

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
| Compute | Single EC2 instance | EC2 instances managed by launch template and Auto Scaling Group |
| Public Access | Application Load Balancer on port `80` | Application Load Balancer with HTTPS and production DNS |
| Application Port | EC2 receives app traffic on port `8000` from ALB | Private EC2 app traffic from ALB only |
| Network | Default VPC | Custom VPC with public and private subnets |
| Scaling | Manual single instance | Auto Scaling Group |
| Data Layer | Local CSV file | Future RDS or structured storage |
| Artifacts | Private S3 bucket | Private S3 bucket managed by Terraform |
| Monitoring | CloudWatch CPU alarm, SNS, and target group health check | Expanded metrics, logs, health checks, and alarms |
| Deployment | Manual file copy, Git updates, and service restart | CI/CD pipeline |
| Infrastructure | Manually created AWS resources | Terraform managed infrastructure |

## Future Phase 1 Improvements

Recommended next AWS architecture improvements:

1. Review and tighten direct EC2 public access
2. Keep user traffic flowing through the ALB
3. Create a launch template
4. Add an Auto Scaling Group
5. Attach the Auto Scaling Group to the existing Target Group
6. Consider HTTPS with ACM certificate and Route 53 if using a domain
7. Create a custom VPC
8. Add public and private subnets
9. Move application instances into private subnets
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
- Application Load Balancer
- Target Group
- Launch Template
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

This project demonstrates the ability to take a data driven application from local development to cloud deployment and then progressively mature the cloud architecture.

The portfolio story is:

```text
I built a geospatial risk intelligence dashboard using FastAPI and Durham public safety data, deployed it to AWS EC2, added persistent service management, configured CloudWatch and SNS monitoring, created private S3 artifact storage, documented the current and target AWS architectures, and placed the application behind an Application Load Balancer with Target Group health checks to move the project toward a production style AWS architecture.
```

The application workload gives the AWS architecture practical meaning by connecting cloud infrastructure to public sector analytics, geospatial intelligence, and future applied ML readiness.
