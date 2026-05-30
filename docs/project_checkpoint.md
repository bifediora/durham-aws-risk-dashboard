# Project Checkpoint

## Durham Risk Intelligence Dashboard

## Checkpoint Purpose

This checkpoint captures the current state of the Durham Risk Intelligence Dashboard project before moving into the next major AWS architecture phase.

This file is intended to serve as a project memory and handoff document. It summarizes what has been built, what is currently working, what decisions have been made, and what should happen next.

The project began as a cloud engineering portfolio build focused on three major phases:

1. Build a production style AWS architecture
2. Convert the infrastructure to Terraform
3. Add CI/CD deployment automation

The dashboard application now serves as the project workload that gives the AWS architecture practical meaning.

## Current Project Direction

The dashboard functionality is considered strong enough for the current stage.

The project should avoid adding major dashboard features right now so the focus can remain on the original AWS cloud engineering path.

Current direction:

1. Freeze major dashboard functionality
2. Maintain documentation and GitHub quality
3. Use screenshots and architecture diagrams as portfolio artifacts
4. Continue AWS Phase 1 toward a production style architecture
5. Keep the Application Load Balancer as the preferred access path
6. Maintain EC2 port `8000` access as restricted to the ALB security group
7. Validate the Auto Scaling Group transition
8. Decide whether to keep or deregister the original manually created EC2 target
9. Prepare for Terraform
10. Prepare for CI/CD

## Current Application Workload

The FastAPI dashboard is working locally and on AWS EC2.

The dashboard is now also working through the Application Load Balancer.

Current dashboard features include:

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
- Gray, dark, and OpenStreetMap basemap toggles
- Layer controls
- Arrests by district chart
- Felony versus misdemeanor chart
- Top 10 offense descriptions chart
- Arrests by hour chart

Current backend API endpoints include:

- `/`
- `/health`
- `/dashboard`
- `/api/summary`
- `/api/records`
- `/api/map-points`
- `/api/by-district`
- `/api/by-severity`
- `/api/top-offenses`
- `/api/by-hour`

## Current Local Project State

Local project path:

```text
/Users/byron/Documents/Projects/durham-aws-risk-dashboard
```

Current local project structure:

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
  .gitignore
```

The dashboard uses a processed sample arrests CSV:

```text
data/sample_arrests.csv
```

Raw geospatial files and large data files are intentionally excluded from Git.

## Current AWS State

The project currently has a Phase 1 AWS deployment in progress.

AWS resources currently used:

- EC2
- Application Load Balancer
- Target Group
- Custom AMI
- Launch Template
- Auto Scaling Group
- Security Groups
- CloudWatch
- SNS
- S3
- IAM

Current EC2 public IP:

```text
35.172.140.39
```

Current preferred dashboard access pattern:

```text
http://<ALB-DNS-NAME>/dashboard
```

Current preferred health endpoint access pattern:

```text
http://<ALB-DNS-NAME>/health
```

Direct EC2 access on port `8000` may still be available temporarily for development and troubleshooting.

Current direct EC2 dashboard endpoint:

```text
http://35.172.140.39:8000/dashboard
```

Current direct EC2 health endpoint:

```text
http://35.172.140.39:8000/health
```

Current EC2 project path:

```text
/home/ubuntu/durham-aws-risk-dashboard
```

Current EC2 systemd service:

```text
durham-risk-dashboard
```

Useful EC2 service commands:

```bash
sudo systemctl status durham-risk-dashboard --no-pager
sudo systemctl restart durham-risk-dashboard
```

Current preferred development access pattern:

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

## Application Load Balancer State

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

Confirmed working ALB routes:

```text
/health
/dashboard
```

The dashboard and health endpoint have both been confirmed working through the ALB DNS name.

## Target Group State

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
## Auto Scaling Group State

Auto Scaling Group name:

```text
durham-risk-dashboard-asg

## Target Transition Strategy

The current transition strategy is Option A:

```text
Keep both healthy targets temporarily.

## Health Check State

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

This endpoint is used by the Target Group to determine whether the EC2 instance is healthy and available to receive traffic.

The health endpoint has been confirmed through:

- EC2 local curl
- EC2 private IP curl
- ALB DNS name in browser

## Current Security Group State

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

This means user traffic reaches the dashboard through the ALB on port `80`, while the EC2 application accepts application traffic on port `8000` from the ALB security group.

## ALB Troubleshooting Completed

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

FastAPI was then validated on EC2 using:

```bash
sudo ss -tulpn | grep 8000
curl http://127.0.0.1:8000/health
curl http://172.31.40.20:8000/health
```

FastAPI was confirmed to be listening on:

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

After this correction:

```text
Target Group status: Healthy
Health endpoint through ALB: Working
Dashboard through ALB: Working
```

Detailed ALB notes are stored in:

```text
docs/alb_target_group_notes.md
```

## Current S3 State

A private S3 artifacts bucket has been created.

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

Dashboard screenshots have been captured and uploaded to S3.

Current screenshot artifacts:

```text
dashboard_top_summary.png
artifacts/screenshots/choropleth_analysis_view_2.png
dashboard_analytics_charts.png
```

S3 screenshot folder:

```text
screenshots/
```

Local screenshot folder:

```text
artifacts/screenshots/
```

The screenshot files are ignored by Git and stored as private project artifacts in S3.

## Current Git and GitHub State

The project has been initialized as a Git repository.

Current branch:

```text
main
```

GitHub repository:

```text
https://github.com/bifediora/durham-aws-risk-dashboard
```

GitHub remote:

```text
https://github.com/bifediora/durham-aws-risk-dashboard.git
```

The repository has been pushed successfully to GitHub.

The local Git identity for this project is set to:

```text
Byron Ifediora
bifediora2@gmail.com
```

For future HTTPS GitHub pushes, the accepted authentication pattern was:

```text
Username: bifediora2@gmail.com
Password: GitHub personal access token
```

The GitHub remote points to:

```text
https://github.com/bifediora/durham-aws-risk-dashboard.git
```

Recent GitHub documentation updates include:

- ALB target group notes created and pushed
- Process log updated and pushed
- AWS architecture notes updated and pushed

## Current Git Safety State

The `.gitignore` has been strengthened to avoid committing sensitive or unnecessary files.

Ignored items include:

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

Important files intentionally tracked include:

- `README.md`
- `.gitignore`
- `app/main.py`
- `app/templates/`
- `app/static/css/`
- `app/static/js/`
- `app/static/geojson/`
- `data/sample_arrests.csv`
- `docs/`
- `scripts/`
- `requirements.txt`

Raw GeoPackage files are intentionally excluded from Git.

## Current Documentation State

Current documentation files include:

- `README.md`
- `docs/process_log.md`
- `docs/aws_architecture_notes.md`
- `docs/alb_target_group_notes.md`
- `docs/current_architecture_diagram.md`
- `docs/target_architecture_diagram.md`
- `docs/project_checkpoint.md`
- `docs/ec2_deployment_notes.md`
- `docs/cloudwatch_monitoring_notes.md`
- `docs/dashboard_enhancement_plan.md`

The README currently documents:

- Project overview
- Portfolio purpose
- Current AWS architecture
- Architecture documentation links
- Current AWS services
- S3 artifact bucket
- Screenshot artifacts
- Dashboard features
- API endpoints
- Geospatial processing
- Project structure
- Runtime dependencies
- Local run instructions
- EC2 deployment notes
- GitHub repository status
- Target Phase 1 architecture
- Phase 2 Terraform goal
- Phase 3 CI/CD goal
- Current roadmap
- Portfolio narrative

The current architecture diagram has been created in:

```text
docs/current_architecture_diagram.md
```

The target architecture diagram has been created in:

```text
docs/target_architecture_diagram.md
```

Detailed ALB setup notes have been created in:

```text
docs/alb_target_group_notes.md
```

The current architecture now follows this pattern:

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
- Target group health checks

## Current Runtime Dependencies

The current runtime `requirements.txt` is intentionally focused on the deployed application.

Current runtime dependencies:

```text
fastapi==0.136.1
uvicorn==0.46.0
pandas==3.0.2
Jinja2==3.1.6
python-multipart==0.0.27
pyproj==3.7.2
```

Local geospatial processing dependencies such as `geopandas`, `pyogrio`, and `shapely` are not required for the current EC2 runtime app unless GeoPackage conversion is performed directly on EC2.

## Current Project Assessment

The dashboard is strong enough for the current stage.

The project is not yet complete as a production style AWS architecture, but it has moved beyond a basic single EC2 public IP deployment and now includes a working ALB, Target Group, custom AMI, Launch Template, and Auto Scaling Group.

The current dashboard is useful as a portfolio workload because it demonstrates:

- A real FastAPI application
- A geospatial data use case
- API driven analytics
- Interactive mapping
- Static asset handling
- Public cloud deployment
- Persistent Linux service management
- Monitoring
- Artifact storage
- GitHub documentation
- Load balanced application access
- Target group health checks
- Security group based routing between ALB and EC2

The project is not yet complete as a production style AWS architecture, but it has moved beyond a basic single EC2 public IP deployment.

The current architecture is best described as:

```text
Phase 1 AWS deployment in progress with a working FastAPI dashboard on EC2, persistent service management, CloudWatch and SNS monitoring, private S3 artifact storage, GitHub documentation, a working Application Load Balancer with Target Group health checks, a custom AMI, a Launch Template, and an Auto Scaling Group that launched a healthy EC2 application target.
```

## Current Versus Target Architecture

| Component | Current State | Target State |
|---|---|---|
| Compute | Original EC2 instance plus ASG-created EC2 instance | EC2 instances fully managed by Auto Scaling Group |
| Public Access | Application Load Balancer on port `80` | Application Load Balancer with HTTPS and production DNS |
| Application Port | EC2 receives app traffic on port `8000` from ALB | Private EC2 app traffic from ALB only |
| Network | Default VPC | Custom VPC with public and private subnets |
| Scaling | Auto Scaling Group created with desired 1, min 1, max 2 | Auto Scaling policies and replacement testing |
| Data Layer | Local CSV file | Future RDS or structured storage |
| Artifacts | Private S3 bucket | Private S3 bucket managed by Terraform |
| Monitoring | CloudWatch CPU alarm, SNS, Target Group health check, and ASG health status | Expanded metrics, logs, health checks, alarms, and scaling policies |
| Deployment | Manual file copy, Git updates, and service restart | CI/CD pipeline |
| Infrastructure | Manually created AWS resources | Terraform managed infrastructure |

## Next Recommended Step

The next recommended AWS step is to decide how to transition from the original manually created EC2 instance to the Auto Scaling Group managed application layer.

Current Target Group state:

```text
Two healthy targets:
1. Original manually created EC2 instance
2. ASG-created EC2 instance

Review whether to keep both targets temporarily or deregister the original manually created EC2 target after confirming the ASG-created instance can carry the dashboard workload.

Next Architecture Steps
Test ASG replacement behavior
Add basic scaling policies later
Prepare Terraform readiness documentation
Prepare CI/CD readiness documentation

## Guidance for Future Work

Do not add major dashboard functionality for now.

Avoid adding:

- Advanced filters
- Machine learning features
- User authentication
- RDS integration
- Complex spatial modeling
- Large new frontend features

Focus next on:

- ALB first access pattern
- Security group tightening
- Launch template
- Auto Scaling Group
- Target group integration
- Terraform readiness
- CI/CD readiness

## Portfolio Narrative at This Checkpoint

The current portfolio story is:

```text
I built a geospatial risk intelligence dashboard using FastAPI and Durham public safety data, deployed it to AWS EC2, added persistent service management, configured CloudWatch and SNS monitoring, created private S3 artifact storage, captured dashboard screenshots as S3 artifacts, pushed the project to GitHub, documented the current and target AWS architecture, placed the application behind an Application Load Balancer with Target Group health checks, tightened the security group path so public dashboard access flows through the ALB while the EC2 application port only accepts traffic from the ALB security group, created a custom AMI, built a Launch Template, and configured an Auto Scaling Group that launched a healthy EC2 application instance behind the Load Balancer.
```

The next phase will strengthen the AWS architecture by validating the Auto Scaling Group transition, deciding whether to deregister the original manually created EC2 target, testing replacement behavior later, and eventually converting the infrastructure to Terraform with CI/CD deployment automation.

## Phase 2 Readiness Checkpoint - Terraform Starter Workspace Complete

The Terraform readiness milestone is complete.

The project now has a clean Terraform starter workspace in:

`infra/terraform/`

Completed Terraform readiness work:

- Created Terraform workspace folder structure.
- Added Terraform README.
- Added starter Terraform files:
  - `main.tf`
  - `variables.tf`
  - `outputs.tf`
  - `terraform.tfvars.example`
- Installed Terraform locally on macOS.
- Ran `terraform fmt -check`.
- Ran `terraform init`.
- Downloaded the AWS provider.
- Committed `.terraform.lock.hcl`.
- Ignored the local `.terraform/` working directory.
- Ran `terraform validate`.

Result:

- Terraform is ready for future infrastructure as code development.
- No AWS resources were created, changed, or destroyed.
- The current manually created AWS architecture remains stable.
- The project will continue using the hybrid learning approach.

Current pause point:

The project is ready to discuss the next major direction.

Remaining options:

- Option B: Begin designing the future Terraform architecture.
- Option C: Return to dashboard application improvements.
- Option D: Prepare the current AWS architecture for a portfolio write up.

Recommended next discussion:

Decide whether the next phase should focus on infrastructure as code, dashboard feature improvement, or professional portfolio presentation.
