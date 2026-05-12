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

The project should avoid adding major dashboard features right now so the focus can return to the original AWS cloud engineering path.

Current direction:

1. Freeze major dashboard functionality
2. Maintain documentation and GitHub quality
3. Use screenshots and architecture diagrams as portfolio artifacts
4. Continue AWS Phase 1 toward a production style architecture
5. Create target architecture documentation
6. Add an Application Load Balancer
7. Add a target group and health checks
8. Move toward an Auto Scaling Group
9. Prepare for Terraform
10. Prepare for CI/CD

## Current Application Workload

The FastAPI dashboard is working locally and on AWS EC2.

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
    aws_architecture_notes.md
    cloudwatch_monitoring_notes.md
    current_architecture_diagram.md
    dashboard_enhancement_plan.md
    ec2_deployment_notes.md
    process_log.md
    project_checkpoint.md
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

The project currently has an early Phase 1 AWS deployment.

AWS resources currently used:

- EC2
- Security Group
- CloudWatch
- SNS
- S3
- IAM

Current EC2 public IP:

```text
35.172.140.39
```

Current public dashboard endpoint:

```text
http://35.172.140.39:8000/dashboard
```

Current health endpoint:

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

Current development access pattern:

```text
User
  ↓
EC2 Public IP on port 8000
  ↓
FastAPI dashboard application
  ↓
Local CSV based sample data
```

This is functional but not yet the target production style architecture.

## Current Security Group State

Current security group access:

| Port | Purpose | Source |
|---|---|---|
| 22 | SSH access | Current user IP |
| 8000 | FastAPI dashboard access | Current user IP |

The current dashboard is intentionally restricted by source IP during development.

Future production architecture should move public access from direct EC2 port access to an Application Load Balancer.

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
dashboard_map_layers.png
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
- `docs/current_architecture_diagram.md`
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

This diagram documents the current deployment pattern:

```text
User
  ↓
EC2 public IP on port 8000
  ↓
FastAPI dashboard
  ↓
Local sample data, templates, static assets, GeoJSON layers, and charts
```

Supporting AWS services include:

- CloudWatch
- SNS
- S3
- GitHub
- EC2 security group controls

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

The project should now prioritize AWS architecture maturity over additional dashboard functionality.

The current dashboard is useful as a portfolio workload because it demonstrates:

- A real FastAPI application
- A geospatial data use case
- API driven analytics
- Interactive mapping
- Static asset handling
- Public EC2 deployment
- Persistent Linux service management
- Monitoring
- Artifact storage
- GitHub documentation

The project is not yet complete as a production style AWS architecture.

The current architecture is best described as:

```text
Early Phase 1 AWS deployment with a working EC2 hosted FastAPI application, monitoring, S3 artifact storage, GitHub documentation, and a clear path toward load balancing, Auto Scaling, Terraform, and CI/CD.
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

## Next Recommended Step

The next recommended step is to create a target architecture diagram before building the next AWS component.

Recommended next file:

```text
docs/target_architecture_diagram.md
```

The target architecture diagram should show:

```text
User
  ↓
Application Load Balancer
  ↓
EC2 application instances
  ↓
Private data layer or structured storage
  ↓
S3 artifacts
  ↓
CloudWatch and SNS monitoring
```

After the target architecture diagram is created, the next real AWS build step should be:

```text
Application Load Balancer + Target Group + Health Check
```

This will begin moving the project away from direct EC2 public IP access and toward the original Phase 1 production style architecture.

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

- Target architecture documentation
- Application Load Balancer
- Target group
- Health checks
- Security group adjustments
- Auto Scaling planning
- Terraform readiness
- CI/CD readiness

## Portfolio Narrative at This Checkpoint

The current portfolio story is:

```text
I built a geospatial risk intelligence dashboard using FastAPI and Durham public safety data, deployed it to AWS EC2, added persistent service management, configured CloudWatch and SNS monitoring, created private S3 artifact storage, captured dashboard screenshots as S3 artifacts, pushed the project to GitHub, documented the current AWS architecture, and structured the project for future Terraform and CI/CD automation.
```

The next phase will strengthen the AWS architecture by moving toward load balancing, health checks, scaling, and eventually infrastructure as code.
