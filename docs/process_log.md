
# Durham AWS Risk Dashboard Process Log

## Completed Steps

1. Created project folder: `durham-aws-risk-dashboard`
2. Created project folders:
   - `app/`
   - `data/`
   - `scripts/`
   - `docs/`
3. Created project specific Python virtual environment:
   - `durham-risk-aws-env`
4. Installed starter FastAPI dependencies:
   - FastAPI
   - Uvicorn
   - Pandas
   - Python Multipart
   - Jinja2
5. Created starter FastAPI app:
   - `app/main.py`
6. Added homepage endpoint:
   - `/`
7. Added service health endpoint:
   - `/health`
8. Created 500 record random sample from Durham arrests data
9. Saved cleaned sample file:
   - `data/sample_arrests.csv`
10. Connected FastAPI app to sample arrest dataset
11. Added dashboard endpoint:
   - `/dashboard`
12. Removed temporary `random_sort` column from sample dataset
13. Added dashboard indicators:
   - total sample records
   - felony records
   - misdemeanor records
   - top district
   - top arrest type
   - most common offense description
14. Added JSON summary endpoint:
   - `/api/summary`
15. Added JSON records preview endpoint:
   - `/api/records`
16. Created dependency file:
   - `requirements.txt`
17. Created project README:
   - `README.md`
18. Created `.gitignore`
19. Created local startup script:
   - `scripts/run_local.sh`
20. Created production startup script:
   - `scripts/run_production.sh`
21. Tested production startup script locally:
   - `uvicorn app.main:app --host 0.0.0.0 --port 8000`
22. Created EC2 deployment notes:
   - `docs/ec2_deployment_notes.md`
23. Created CloudWatch monitoring notes:
   - `docs/cloudwatch_monitoring_notes.md`
## Current Local Endpoints

| Endpoint | Purpose |
|---|---|
| `/` | Homepage |
| `/health` | Health check |
| `/dashboard` | HTML dashboard |
| `/api/summary` | JSON dashboard metrics |
| `/api/records` | JSON record preview |

## Current Project Purpose

This project is being built as a cloud engineering portfolio project that will eventually demonstrate:

- AWS application deployment
- production style architecture
- public and private subnet design
- load balancing
- auto scaling
- monitoring
- Terraform automation
- CI/CD workflow
- future ML engineering expansion

## Phase 1 Checkpoint: Local Application Foundation Complete

At this stage, the local FastAPI foundation is complete. The project includes a working Durham Risk Intelligence Dashboard using a real 499 record sample of Durham arrest data.

Completed local components:

- FastAPI application created
- Project specific virtual environment configured
- Real sample arrest dataset added
- Homepage endpoint created
- Health check endpoint created
- HTML dashboard endpoint created
- JSON summary API endpoint created
- JSON records preview endpoint created
- README created
- `.gitignore` created
- Local startup script created
- AWS architecture notes started

The next phase is preparing the application for AWS EC2 deployment before expanding into load balancing, auto scaling, monitoring, Terraform, and CI/CD.

S3 artifacts bucket created:

- Created a private S3 bucket for project artifacts:
  - `durham-risk-dashboard-artifacts-byron-333973504198-us-east-1-an`

- Bucket purpose:
  - Store dashboard screenshots
  - Store architecture diagrams
  - Store exported reports or sample outputs
  - Store project documentation artifacts
  - Support future Terraform and CI/CD phases

- Bucket configuration:
  - Region: `us-east-1`
  - Block all public access: enabled
  - Object ownership: ACLs disabled
  - Default encryption: SSE-S3
  - Bucket Key: disabled

This adds S3 to the AWS Phase 1 architecture as a private artifact storage layer while keeping the dashboard itself hosted on EC2.

S3 artifact upload test completed:

- Created local artifacts folder structure:
  - `artifacts/screenshots/`
  - `artifacts/diagrams/`
  - `artifacts/reports/`

- Created a test artifact:
  - `artifacts/reports/s3_test_artifact.txt`

- Uploaded the test artifact to the private S3 bucket:
  - `durham-risk-dashboard-artifacts-byron-333973504198-us-east-1-an`

This confirms that the project now has both local and AWS based artifact storage for screenshots, architecture diagrams, reports, and future project documentation outputs.

Dashboard screenshots captured and uploaded to S3:

- Captured three dashboard screenshots from the public EC2 dashboard:
  - `dashboard_top_summary.png`
  - `dashboard_map_layers.png`
  - `dashboard_analytics_charts.png`

- Stored the screenshots locally in:
  - `artifacts/screenshots/`

- Uploaded the screenshots to the private S3 artifacts bucket:
  - `durham-risk-dashboard-artifacts-byron-333973504198-us-east-1-an`

- S3 folder path used:
  - `screenshots/`

This creates portfolio ready visual artifacts that can be used later in the README, architecture documentation, GitHub repository, and LinkedIn project summary.

## Phase 2 Checkpoint: Initial EC2 Deployment Complete

At this stage, the Durham Risk Intelligence Dashboard has been deployed to an AWS EC2 instance in the `us-east-1` region.

Completed EC2 deployment components:

- Created AWS account and selected Free plan
- Selected AWS region:
  - `us-east-1` / US East (N. Virginia)
- Created monthly AWS budget:
  - `$5`
  - 80% alert threshold
- Created EC2 key pair:
  - `durham-risk-dashboard-key`
- Stored private key securely:
  - `~/.ssh/durham-risk-dashboard-key.pem`
- Created EC2 instance:
  - `durham-risk-dashboard-ec2`
- Configured inbound security group rules:
  - SSH on port `22` from My IP
  - Custom TCP on port `8000` from My IP
- Connected to EC2 using SSH
- Updated Ubuntu server packages
- Installed Python, pip, venv, and Git
- Created project folder on EC2
- Created project specific Python virtual environment on EC2
- Installed FastAPI project dependencies on EC2
- Copied `sample_arrests.csv` from local machine to EC2
- Created production startup script on EC2
- Ran FastAPI app on EC2 using:
  - `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Successfully tested all application endpoints through the EC2 public IP

Working EC2 endpoints:

- `/`
- `/health`
- `/dashboard`
- `/api/summary`
- `/api/records?limit=5`

This deployment validates that the application can run on AWS infrastructure. The next phase will improve the deployment by adding process management, then later load balancing, auto scaling, monitoring, Terraform, and CI/CD.

## Phase 3 Checkpoint: Persistent EC2 Service Complete

At this stage, the Durham Risk Intelligence Dashboard is running persistently on EC2 using a `systemd` service.

Completed service management components:

- Created a `systemd` service file:
  - `/etc/systemd/system/durham-risk-dashboard.service`
- Configured the service to run the FastAPI app from the project virtual environment
- Set the working directory to:
  - `/home/ubuntu/durham-aws-risk-dashboard`
- Configured the app to run with:
  - `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Reloaded `systemd`
- Started the service with:
  - `sudo systemctl start durham-risk-dashboard`
- Enabled the service to start after reboot with:
  - `sudo systemctl enable durham-risk-dashboard`
- Confirmed service status:
  - `Active: active (running)`
- Successfully tested the app in the browser after service startup

Useful service commands:

```bash
sudo systemctl status durham-risk-dashboard
sudo systemctl restart durham-risk-dashboard
sudo systemctl stop durham-risk-dashboard
sudo journalctl -u durham-risk-dashboard -f

## Phase 4 Checkpoint: Basic CloudWatch Monitoring Started

At this stage, basic AWS monitoring has been started for the EC2 deployment.

Completed monitoring components:

- Created SNS topic:
  - `durham-risk-dashboard-alerts`
- Created email subscription for alert notifications
- Confirmed SNS email subscription
- Created CloudWatch CPU alarm:
  - `durham-risk-dashboard-high-cpu`
- Alarm metric:
  - EC2 `CPUUtilization`
- Alarm threshold:
  - Greater than 70%
- Evaluation period:
  - 5 minutes
- Notification destination:
  - SNS topic `durham-risk-dashboard-alerts`

This milestone adds operational awareness to the project and supports the cloud engineering goal of monitoring deployed infrastructure.

## Phase 5 Checkpoint: Geospatial Dashboard Functionality Started

At this stage, the dashboard has been upgraded from a basic metrics page into a styled geospatial dashboard prototype.

Completed geospatial dashboard components:

- Created template folder:
  - `app/templates/`
- Created static folders:
  - `app/static/css/`
  - `app/static/js/`
- Created styled homepage template:
  - `app/templates/index.html`
- Created styled dashboard template:
  - `app/templates/dashboard.html`
- Created custom stylesheet:
  - `app/static/css/styles.css`
- Created dashboard JavaScript file:
  - `app/static/js/dashboard.js`
- Refactored FastAPI to use Jinja2 templates
- Added static file serving through FastAPI
- Added map data API endpoint:
  - `/api/map-points`
- Installed `pyproj` for coordinate conversion
- Converted source coordinates from:
  - `EPSG:2264`
  - to `EPSG:4326`
- Added Leaflet.js interactive map
- Added OpenStreetMap basemap
- Added arrest location circle markers
- Added popup details for mapped arrest points
- Added Durham area bounding box filter to remove coordinate outliers
- Confirmed the map now focuses on Durham instead of zooming out to an incorrect outlier location

This milestone adds real geospatial functionality and improves the portfolio value of the dashboard.

Additional dashboard analytics completed:

- Added Chart.js to the dashboard template
- Added chart containers to:
  - `app/templates/dashboard.html`
- Added backend API endpoint:
  - `/api/by-district`
- Added backend API endpoint:
  - `/api/by-severity`
- Updated dashboard JavaScript:
  - `app/static/js/dashboard.js`
- Rendered arrests by district chart
- Rendered felony vs misdemeanor chart

This expands the dashboard from geospatial display into combined spatial and analytical public safety intelligence.

Additional map layer improvements completed:

- Added Durham County boundary GeoJSON layer:
  - `app/static/geojson/durham_county_boundary.geojson`
- Added police beats GeoJSON layer:
  - `app/static/geojson/police_beats.geojson`
- Added layer control to toggle map overlays:
  - Durham County Boundary
  - Police Beats
  - Arrest Points
- Added basemap toggle options:
  - Gray Map
  - Dark Map
  - OpenStreetMap
- Set Gray Map as the default basemap
- Updated police beat polygon outline color to muted blue:
  - `#60a5fa`
- Reduced arrest point marker size for cleaner map display
- Preserved overlay order:
  - Basemap
  - County boundary
  - Police beats
  - Arrest points

This improves the map from a simple point display into a more complete geospatial dashboard with operational geography, contextual boundaries, and user controlled map layers.

Additional dashboard analytics completed:

- Added `/api/top-offenses` endpoint in `app/main.py`
  - Returns the top offense descriptions by record count
  - Supports a configurable `limit` parameter
  - Default dashboard usage: `/api/top-offenses?limit=10`

- Added Top 10 Offense Descriptions chart to the dashboard
  - Added chart container in `app/templates/dashboard.html`
  - Added `renderTopOffensesChart()` in `app/static/js/dashboard.js`
  - Rendered as a horizontal bar chart for easier reading of long offense labels

- Added `/api/by-hour` endpoint in `app/main.py`
  - Parses `Arrest Time`
  - Extracts the hour of day
  - Returns all 24 hours with zero filled values where no records exist
  - Adds readable hour labels such as `12 AM`, `1 AM`, and `5 PM`

- Added Arrests by Hour chart to the dashboard
  - Added chart container in `app/templates/dashboard.html`
  - Added `renderHourChart()` in `app/static/js/dashboard.js`
  - Rendered as a line chart to show temporal patterning across the day

Current dashboard analytics now include:

- KPI cards
- Top district
- Top arrest type
- Most common offense description
- Arrests by district chart
- Felony vs misdemeanor chart
- Top 10 offense descriptions chart
- Arrests by hour chart

This improves the dashboard from a basic map and summary view into a stronger analytical prototype that combines spatial, categorical, severity, and temporal views of the sample Durham arrest data.

Updated EC2 redeployment completed:

- Copied updated local dashboard files to the EC2 instance:
  - `app/main.py`
  - `app/templates/`
  - `app/static/`
  - `data/sample_arrests.csv`
  - `requirements.txt`

- Reconnected to the EC2 instance using SSH:
  - `ssh -i ~/.ssh/durham-risk-dashboard-key.pem ubuntu@35.172.140.39`

- Updated Python dependencies on EC2 using:
  - `pip install -r requirements.txt`

- Restarted the persistent systemd service:
  - `sudo systemctl restart durham-risk-dashboard`

- Confirmed the FastAPI app was healthy locally on EC2:
  - `curl http://127.0.0.1:8000/health`

- Confirmed the new hourly analytics endpoint worked on EC2:
  - `curl http://127.0.0.1:8000/api/by-hour`

- Restored public browser access to the dashboard by updating the EC2 security group inbound rule for port `8000` to the current IP address.

- Confirmed the public dashboard is reachable at:
  - `http://35.172.140.39:8000/dashboard`

This redeployment confirms that the updated geospatial dashboard, analytics endpoints, static assets, templates, and dependency changes are now running on the AWS EC2 instance through the persistent systemd service.

README documentation updated:

- Rewrote `README.md` to reflect the current project status.
- Added project overview and portfolio purpose.
- Documented the three phase cloud engineering path:
  - Phase 1: Production style AWS architecture
  - Phase 2: Terraform Infrastructure as Code
  - Phase 3: CI/CD deployment automation
- Documented current AWS services:
  - EC2
  - Security Group
  - CloudWatch
  - SNS
  - S3
  - IAM
- Documented current dashboard features and API endpoints.
- Added local run instructions.
- Added EC2 deployment notes.
- Added current security group configuration.
- Added target Phase 1 architecture roadmap.
- Added future Terraform and CI/CD goals.
- Added a portfolio narrative connecting the FastAPI dashboard, AWS deployment, geospatial intelligence, and future automation work.

This README update makes the repository more suitable for GitHub portfolio review and clearly separates current implementation from future architecture goals.

## ALB and Target Group Milestone Completed

Created and configured the Application Load Balancer and Target Group for the Durham Risk Intelligence Dashboard.

This step moves the project from direct EC2 public IP access toward a more production style AWS architecture.

Previous access pattern:

```text
User
  ↓
EC2 public IP on port 8000
  ↓
FastAPI dashboard application
```

New access pattern:

```text
User
  ↓
Application Load Balancer on port 80
  ↓
Target Group
  ↓
EC2 FastAPI instance on port 8000
  ↓
FastAPI dashboard application
```

AWS resources configured:

- Application Load Balancer:
  - `durham-risk-dashboard-alb`

- Target Group:
  - `durham-risk-dashboard-tg`

- Target EC2 instance:
  - `durham-risk-dashboard-ec2`
  - Instance ID: `i-07895b87a7d7eb25b`

- Target group protocol and port:
  - `HTTP:8000`

- Health check path:
  - `/health`

- Health check success code:
  - `200`

- Final target status:
  - `Healthy`

Confirmed working ALB routes:

```text
/health
/dashboard
```

Troubleshooting completed:

- Target group initially showed `Unused`.
- The reason was that the EC2 instance was in an Availability Zone not enabled for the load balancer.
- The ALB subnet mapping was updated to include the EC2 instance Availability Zone.
- Target status then changed to `Unhealthy`.
- Health status reason was `Request timed out`.
- Verified FastAPI was running correctly on EC2 using:

```bash
sudo ss -tulpn | grep 8000
curl http://127.0.0.1:8000/health
curl http://172.31.40.20:8000/health
```

- Confirmed FastAPI was listening on:

```text
0.0.0.0:8000
```

- Confirmed the health endpoint worked locally and through the EC2 private IP.
- Found that the ALB was attached to the wrong security group:
  - `sg-0f149ba485cdd5aae`
- Corrected the ALB security group attachment to:
  - `sg-0039dbb4fe5326472`
  - `durham-risk-dashboard-alb-sg`
- Confirmed the EC2 security group allowed port `8000` traffic from the ALB security group.
- After correcting the ALB security group attachment, the target group became healthy.
- Confirmed the dashboard and health endpoint opened successfully through the ALB DNS name.

Security group configuration confirmed:

- ALB security group:
  - `sg-0039dbb4fe5326472`
  - `durham-risk-dashboard-alb-sg`

- EC2 security group:
  - `sg-08614f1873385ef42`
  - `launch-wizard-1`

- EC2 inbound rule:
  - Port: `8000`
  - Source: `sg-0039dbb4fe5326472`
  - Purpose: allow FastAPI traffic from the ALB

A detailed ALB setup and troubleshooting note was also created:

```text
docs/alb_target_group_notes.md
```

This milestone confirms that the project now has a working load balanced access path and has moved closer to the original Phase 1 production style AWS architecture goal.


## Security Group Tightening Confirmed

Confirmed that direct public browser access to the EC2 FastAPI application on port `8000` is no longer available.

The dashboard should now be accessed through the Application Load Balancer rather than through the EC2 public IP and port `8000`.

Expected access pattern:

```text
User
  ↓
Application Load Balancer on port 80
  ↓
Target Group
  ↓
EC2 FastAPI application on port 8000
```

Confirmed result:

```text
Direct EC2 dashboard URL:
http://35.172.140.39:8000/dashboard

Result:
Site could not be reached
```

This is the desired result because the EC2 application port should not be directly exposed to the browser.

The working dashboard access path remains:

```text
http://\<ALB-DNS-NAME\>/dashboard
```

Current security group posture:

```text
ALB security group:
- Allows HTTP traffic on port 80 from the current user IP

EC2 security group:
- Allows SSH on port 22 from the current user IP
- Allows FastAPI traffic on port 8000 from the ALB security group only
```

This confirms that public user traffic now flows through the Application Load Balancer, while the EC2 application instance only accepts application traffic from the ALB security group.

## Auto Scaling Group Milestone Completed

Created and validated the Auto Scaling Group for the Durham Risk Intelligence Dashboard.

This step moves the project further into the Phase 1 production style AWS architecture path by shifting from a single manually managed EC2 application instance toward an Auto Scaling based application layer.

Previous architecture pattern:

```text
User
  ↓
Application Load Balancer on port 80
  ↓
Target Group
  ↓
Single manually created EC2 FastAPI application instance on port 8000
```

New architecture pattern:

```text
User
  ↓
Application Load Balancer on port 80
  ↓
Target Group
  ↓
Auto Scaling Group
  ↓
EC2 FastAPI application instance created from Launch Template
```

AWS resources completed:

- Custom AMI:
  - `durham-risk-dashboard-ami-v1`

- Launch Template:
  - `durham-risk-dashboard-lt`

- Auto Scaling Group:
  - `durham-risk-dashboard-asg`

- Target Group:
  - `durham-risk-dashboard-tg`

- Application Load Balancer:
  - `durham-risk-dashboard-alb`

Auto Scaling Group capacity settings:

```text
Desired capacity: 1
Minimum capacity: 1
Maximum capacity: 2
```

Health check configuration:

```text
Health check type: ELB
Health check grace period: 300 seconds
Target Group health check path: /health
Target Group health check success code: 200
Application port: 8000
```

Validation completed:

- Auto Scaling Group was created successfully.
- Auto Scaling Group used the Launch Template.
- Auto Scaling Group launched a new EC2 instance.
- ASG created EC2 instance reached `Running` state.
- ASG created EC2 instance reached `InService` lifecycle state.
- ASG created EC2 instance showed `Healthy` status.
- ASG created EC2 instance registered with the existing Target Group.
- Target Group showed two healthy targets:
  - Original manually created EC2 instance
  - ASG created EC2 instance
- ALB `/health` route was tested successfully.
- ALB `/dashboard` route was tested successfully.

Current confirmed request flow:

```text
User
  ↓
Application Load Balancer
  ↓
Target Group
  ↓
Healthy EC2 targets
      ├── Original manually created EC2 instance
      └── ASG created EC2 instance
```

Current confirmed ASG path:

```text
Custom AMI
  ↓
Launch Template
  ↓
Auto Scaling Group
  ↓
ASG created EC2 instance
  ↓
Target Group
  ↓
Healthy target
```

Security posture remains:

```text
Browser access:
Application Load Balancer on port 80

Application access:
EC2 port 8000 from ALB security group only

Administrative access:
SSH port 22 from current user IP
```

Direct public browser access to EC2 port `8000` remains blocked.

Important transition note:

The original manually created EC2 instance has not been removed yet. This is intentional. Both the original EC2 target and the ASG created EC2 target are currently healthy in the Target Group.

The original manually created EC2 instance should not be terminated or deregistered until the ASG created instance has been fully validated and the transition strategy is documented.

A detailed Auto Scaling Group milestone note was also created:

```text
docs/auto_scaling_group_notes.md
```

This milestone confirms that the project now demonstrates:

- Load balanced access
- Target Group health checks
- Custom AMI creation
- Launch Template creation
- Auto Scaling Group creation
- ASG managed EC2 instance launch
- Healthy ASG target registration
- ALB routing to healthy backend targets

Portfolio significance:

```text
The project now demonstrates a progression from a manually deployed EC2 FastAPI dashboard to a load balanced architecture with a reusable AMI, Launch Template, and Auto Scaling Group capable of creating healthy application instances behind an Application Load Balancer.
```
## Option A Selected: Keep Both Healthy Targets Temporarily

After validating the Auto Scaling Group milestone, the project selected Option A for the immediate transition strategy.

Option A means keeping both healthy targets temporarily in the Target Group:

```text
Target Group:
durham-risk-dashboard-tg

Healthy targets:
1. Original manually created EC2 instance
2. ASG-created EC2 instance
```

This approach is intentionally cautious.

The original manually created EC2 instance remains available as a known working fallback while the ASG-created instance continues to prove it can reliably serve the Durham Risk Intelligence Dashboard.

Current confirmed architecture:

```text
User
  ↓
Application Load Balancer on port 80
  ↓
Target Group
  ↓
Two healthy EC2 targets
      ├── Original manually created EC2 instance
      └── ASG-created EC2 instance
```

Reason for keeping both targets temporarily:

- The ASG-created instance is healthy and working
- The original EC2 instance is also healthy and working
- Keeping both targets reduces transition risk
- The dashboard remains available through the ALB
- The project can observe stability before moving to an ASG-managed-only application layer

Current confirmed status:

```text
Application Load Balancer: working
Target Group: working
Original EC2 target: healthy
ASG-created EC2 target: healthy
Auto Scaling Group: created
ASG instance: InService and Healthy
ALB /health: working
ALB /dashboard: working
Direct EC2 public access on port 8000: blocked
```

Transition decision:

```text
Do not deregister or terminate the original manually created EC2 instance yet.
```

Next decision point:

```text
After additional validation, decide whether to deregister the original manually created EC2 target and allow the Auto Scaling Group to manage the application layer.
```

This keeps the project stable while preserving a clear path toward an ASG-managed architecture.

## Option A Validation Confirmed

Validated the Option A transition strategy for the Durham Risk Intelligence Dashboard.

Option A means keeping both healthy targets temporarily in the Target Group:

```text
Target Group:
durham-risk-dashboard-tg

Healthy targets:
1. Original manually created EC2 instance
2. ASG-created EC2 instance
```

Validation completed:

```text
Target Group healthy targets: 2
Original manually created EC2 target: Healthy
ASG-created EC2 target: Healthy
ALB /health route: Working
ALB /dashboard route: Working
```

Current confirmed architecture:

```text
User
  ↓
Application Load Balancer on port 80
  ↓
Target Group
  ↓
Two healthy EC2 targets
      ├── Original manually created EC2 instance
      └── ASG-created EC2 instance
```

Decision:

```text
Keep both healthy targets temporarily.
```

Reason:

This maintains a cautious and stable transition path. The original manually created EC2 instance remains available as a fallback while the ASG-created instance continues to prove it can reliably serve the dashboard.

Next future transition:

```text
Plan an ASG-only transition by deregistering the original manually created EC2 target after additional validation.
```

Do not terminate the original EC2 instance yet.

## Dual Target CloudWatch Monitoring Review Completed

Reviewed CloudWatch and AWS console monitoring for the current dual target validation period.

Current transition strategy remains Option A:

```text
Keep both healthy targets temporarily.
```

Current Target Group:

```text
durham-risk-dashboard-tg
```

Current healthy targets:

```text
1. Original manually created EC2 instance
2. ASG-created EC2 instance
```

CloudWatch Application Load Balancer and Target Group metrics reviewed:

```text
HealthyHostCount
UnHealthyHostCount
HTTP response code metrics
```

Confirmed result:

```text
HealthyHostCount: 2
UnHealthyHostCount: 0
ALB 5XX errors: none
Target 5XX errors: none
```

The live Target Group console also confirmed:

```text
Two healthy targets
Zero unhealthy targets
```

Auto Scaling Group status was reviewed through the Auto Scaling Group console because ASG group metrics collection was not enabled during the initial ASG setup.

Confirmed ASG result:

```text
Auto Scaling Group: durham-risk-dashboard-asg
ASG-created instance: InService
ASG-created instance health: Healthy
Desired capacity: 1
Minimum capacity: 1
Maximum capacity: 2
```

Current confirmed architecture remains:

```text
User
  ↓
Application Load Balancer on port 80
  ↓
Target Group
  ↓
Two healthy EC2 targets
      ├── Original manually created EC2 instance
      └── ASG-created EC2 instance
```

Monitoring conclusion:

```text
The dual target architecture is stable.
Both targets are healthy.
No server side 5XX errors were observed.
The Auto Scaling Group instance remains InService and Healthy.
```

Current decision:

```text
Do not deregister or terminate the original manually created EC2 instance yet.
```

Future monitoring improvement:

```text
Enable Auto Scaling Group metrics collection in CloudWatch if deeper ASG metric visibility is needed.
```

## Terraform Strategy Selected: Hybrid Learning Approach

Selected the Terraform strategy for the next phase of the Durham Risk Intelligence Dashboard project.

Chosen strategy:

```text
Option 3: Hybrid Learning Approach
```

## Step 199 - Terraform starter workspace initialized and validated

Initialized the Terraform starter workspace in `infra/terraform`.

Completed checks:

- Installed Terraform locally on macOS.
- Ran `terraform fmt -check`.
- Ran `terraform init`.
- Downloaded the AWS provider.
- Committed `.terraform.lock.hcl`.
- Added `infra/terraform/.terraform/` to `.gitignore`.
- Ran `terraform validate`.

Result:

- Terraform starter workspace is ready for future infrastructure as code development.
- No AWS resources were created, changed, or destroyed.
- Current manual AWS architecture remains stable.

## Phase 5 - Dashboard MVP Polish and Analytical Layer Expansion

Date: May 2026

Completed the dashboard MVP polish phase and prepared the project for the next infrastructure phase.

Work completed:

- Preserved the dashboard as a FastAPI based analytical web application.
- Refined the interactive Leaflet map interface.
- Supported point, cluster, density, and choropleth map visualization modes.
- Integrated Durham municipal boundary geography.
- Added census tracts intersecting the Durham municipal boundary as the primary analytical geography.
- Preserved full census tract geometries rather than clipping them to city limits.
- Built spatial join workflows connecting event records to census tracts.
- Built tract-level enrichment outputs combining ACS demographic indicators and event aggregates.
- Added enriched arrest and shooting event outputs.
- Added neighborhood context geography as an interpretive reference layer.
- Added KPI cards for total arrests, hotspot areas, felony share, and recent activity trend.
- Added chart summaries for district, severity, top offenses, and temporal patterns.
- Consolidated separate temporal charts into a single Temporal Activity Explorer.
- Added start date and end date filtering intended to update the full dashboard.
- Added selected records functionality for reviewing filtered event records.
- Refined tract popup behavior so closing a popup clears tract selection.
- Preserved the current dashboard layout and stopped further UI iteration.
- Committed the final dashboard MVP to GitHub.
- Created the Git tag `dashboard-mvp-v1` as a stable checkpoint before beginning Terraform work.

Key design decisions:

- Census tracts remain the primary analytical geography for ACS joins, normalized rates, choropleths, and demographic analytics.
- Neighborhoods are used as context geography for labels, public interpretation, and place-based orientation, not as the primary statistical engine.
- Full tract geometries are preserved to maintain consistency with Census and ACS data.
- The dashboard is framed as a preparedness and decision intelligence prototype, not as an enforcement prediction tool.
- Population-normalized rates and percentage-based contextual indicators are prioritized for public-facing tract comparison.
- The dashboard MVP is feature frozen so the next phase can focus on infrastructure and deployment maturity.

Files and outputs created or updated:

```text
app/main.py
app/templates/dashboard.html
app/static/js/dashboard.js
app/static/css/styles.css
data/processed/arrests_with_tract_join.csv
data/processed/durham_arrests_tract_enriched.csv
data/processed/durham_arrests_tract_enriched.geojson
data/processed/durham_shootings_tract_enriched.csv
data/processed/durham_shootings_tract_enriched.geojson
data/processed/durham_choropleth_metric_catalog.json
data/processed/durham_neighborhoods_projected.geojson
data/processed/durham_neighborhoods_web.geojson
data/processed/durham_neighborhoods_inspection_summary.txt
scripts/build_event_tract_enrichment.py
scripts/build_neighborhood_context.py
```

Final status:

```text
Dashboard MVP feature frozen.
Stable Git tag: dashboard-mvp-v1
```

Next phase:

```text
Phase 6: Infrastructure as Code with Terraform
```

Phase 6 objective:

Provision the AWS infrastructure needed to host the Durham Risk Intelligence Dashboard in a repeatable and documented way.

Planned Terraform focus:

- Create a `terraform/` directory.
- Add Terraform provider configuration.
- Provision EC2 infrastructure.
- Configure security groups.
- Reference or configure SSH/key access.
- Add project tagging.
- Add outputs for public IP and app URL.
- Later extend to monitoring resources such as CloudWatch alarms and SNS notifications.
- Keep the first Terraform version simple and reproducible.

## Phase 6: Terraform Infrastructure Foundation

Date: May 2026

### Purpose

Started the Infrastructure as Code phase by creating a Terraform managed AWS foundation for the Durham Risk Intelligence Dashboard. This phase is intended to make the dashboard infrastructure reproducible while keeping the Terraform managed environment separate from the original manually created AWS deployment.

### Work completed

- Confirmed AWS CLI authentication using IAM user `terraform-dev-user`.
- Confirmed Terraform workspace validation.
- Added Terraform variables for EC2 configuration.
- Added a Terraform managed EC2 instance.
- Added a Terraform managed security group.
- Used an Amazon Linux 2023 AMI lookup through Terraform.
- Referenced the existing EC2 key pair `durham-risk-dashboard-key`.
- Restricted SSH access to the approved CIDR `136.47.213.3/32`.
- Opened dashboard application port `8000`.
- Applied Terraform successfully.
- Added Terraform outputs for instance, network access, dashboard URL, and SSH command details.
- Confirmed SSH access to the Terraform managed EC2 instance.
- Confirmed the instance is running Amazon Linux 2023.
- Added Terraform state files and tfvars files to `.gitignore`.
- Committed the Terraform foundation with `Add Terraform EC2 infrastructure foundation`.

### Resources created

```text
EC2 instance: i-0b166d555696c2385
Security group: sg-0624970f231477fae
Public IP: 98.93.40.196
Public DNS: ec2-98-93-40-196.compute-1.amazonaws.com
```

Terraform outputs now include:

```text
dashboard_instance_id
dashboard_public_ip
dashboard_public_dns
dashboard_security_group_id
dashboard_app_url
dashboard_ssh_command
```

### Validation completed

- Terraform validation completed successfully.
- Terraform apply completed successfully.
- Terraform outputs returned the expected EC2 and security group values.
- SSH access to the Terraform managed instance was confirmed.
- The EC2 host was confirmed as Amazon Linux 2023.

### Security notes

- AWS access keys, secret keys, credential files, and local credential paths are not documented in the repository.
- SSH access is restricted to a single approved IP CIDR.
- Terraform state files and local variable files are ignored by Git.
- Terraform changes should remain separate from dashboard feature work.

### Current status

Terraform now provisions the initial AWS infrastructure foundation for the dashboard:

- EC2 instance
- Security group
- Application port access
- SSH access rule
- Useful operational outputs

The Terraform managed environment remains separate from the original manually created AWS deployment.

### Next step

Install and configure the dashboard application on the Terraform managed EC2 instance in a later phase. Do not proceed to application installation or `systemd` setup until the Terraform foundation documentation is reviewed.

### Terraform EC2 Application Deployment and systemd Service

#### Purpose

Documented the first successful application deployment onto the Terraform managed EC2 instance. This checkpoint confirms that the dashboard can run on the new Terraform provisioned server while preserving the hybrid learning approach: Terraform provisions the infrastructure foundation, and application setup is performed manually for inspection and documentation before later automation.

#### Work completed

- Confirmed SSH access to the Terraform managed EC2 instance.
- Confirmed the EC2 instance is running Amazon Linux 2023.
- Installed base system packages:
  - `git`
  - `python3`
  - `python3-pip`
  - `python3-devel`
  - `gcc`
  - `nginx`
- Cloned the GitHub repository onto the EC2 instance.
- Installed Python 3.11 and used it for the project virtual environment.
- Installed application dependencies in the project virtual environment.
- Identified missing runtime dependency `shapely`.
- Added `shapely` to `requirements.txt` and committed the dependency update.
- Started the FastAPI dashboard successfully with Uvicorn.
- Created a persistent `systemd` service for the dashboard.
- Enabled and started the `systemd` service.
- Confirmed the service is active and running.

#### Runtime environment

```text
Instance operating system: Amazon Linux 2023
Python runtime: Python 3.11
Application server: Uvicorn
Service manager: systemd
Public application port: 8000
```

#### Deployment path

```text
/home/ec2-user/durham-aws-risk-dashboard
/home/ec2-user/durham-aws-risk-dashboard/durham-risk-aws-env
```

#### Service management

```text
/etc/systemd/system/durham-risk-dashboard.service
```

The dashboard service is enabled and running through `systemd`.

#### Validation completed

- SSH access to the Terraform managed EC2 instance was confirmed.
- The dashboard application started successfully with Uvicorn.
- The `systemd` service was confirmed active and running.
- The health endpoint returned:

```json
{"status":"healthy","service":"Durham Risk Intelligence Dashboard","version":"0.3.6"}
```

- The dashboard is publicly accessible at:

```text
http://98.93.40.196:8000
```

#### Current status

The dashboard now runs successfully on the Terraform managed EC2 instance. Terraform currently manages the EC2 instance and security group, while application installation and service configuration were performed manually after provisioning.

#### Next step

The next likely improvement is to add Nginx reverse proxy configuration or CloudWatch monitoring for the Terraform managed deployment. Do not proceed to Nginx, CloudWatch, or Terraform automation until this deployment checkpoint is reviewed.

### Nginx Reverse Proxy for Public Dashboard Access

#### Purpose

Documented the successful Nginx reverse proxy milestone for the Terraform managed EC2 deployment. This checkpoint moves public dashboard access from direct FastAPI port access to standard HTTP traffic on port `80`, while keeping the FastAPI application running internally through `systemd` on port `8000`.

#### Work completed

- Configured Nginx as a reverse proxy on the Terraform managed EC2 instance.
- Forwarded public HTTP traffic from port `80` to the FastAPI application on `127.0.0.1:8000`.
- Created the Nginx configuration manually on the EC2 instance:

```text
/etc/nginx/conf.d/durham-risk-dashboard.conf
```

- Tested the Nginx configuration syntax successfully with `sudo nginx -t`.
- Enabled and restarted the Nginx service.
- Confirmed Nginx is active and running.
- Confirmed the dashboard now loads publicly without requiring `:8000`.

#### Reverse proxy routing pattern

```text
Public user
  -> port 80
  -> Nginx
  -> 127.0.0.1:8000
  -> FastAPI app
```

#### Terraform security group update

- Updated the Terraform managed security group to allow inbound HTTP traffic on port `80`.
- Terraform plan showed:

```text
Plan: 0 to add, 1 to change, 0 to destroy.
```

- Terraform apply updated the security group in place.
- Terraform continues to manage the EC2 instance and security group, while Nginx configuration was performed manually as part of the hybrid learning workflow.

#### Validation completed

- Local reverse proxy health check succeeded on the EC2 instance:

```text
curl http://127.0.0.1/health
```

- Public reverse proxy health check succeeded from the local machine:

```text
curl http://98.93.40.196/health
```

- Current public dashboard URL:

```text
http://98.93.40.196
```

- Current health check URL:

```text
http://98.93.40.196/health
```

#### Current status

The Terraform managed EC2 deployment now serves the dashboard through Nginx on standard HTTP port `80`. FastAPI continues to run internally on port `8000` through the `systemd` service.

#### Next step

The next likely improvement is CloudWatch monitoring, deployment automation, HTTPS, or domain setup. Do not proceed to CloudWatch, HTTPS, Route 53, or CI/CD until this Nginx reverse proxy checkpoint is reviewed.

### CloudWatch and SNS Monitoring

#### Purpose

Documented the first Terraform managed monitoring milestone for the Durham Risk Intelligence Dashboard deployment. This checkpoint adds basic operational visibility and alerting for the Terraform managed EC2 instance while keeping the dashboard MVP application unchanged.

#### Work completed

- Confirmed the Terraform managed EC2 instance is running.
- Confirmed CloudWatch is receiving EC2 CPU metrics.
- Added Terraform monitoring variables:
  - `alert_email`
  - `cpu_alarm_threshold`
  - `cpu_alarm_period`
  - `cpu_alarm_evaluation_periods`
- Added a Terraform managed SNS topic.
- Added a Terraform managed CloudWatch alarm for EC2 high CPU.
- Added a Terraform managed CloudWatch alarm for EC2 status check failure.
- Applied Terraform successfully.
- Confirmed the CloudWatch alarms exist.
- Added an SNS email subscription.
- Confirmed the SNS email subscription after the AWS confirmation email was found in spam.
- Confirmed both alarm states are `OK`.
- Committed Terraform monitoring changes with `Add CloudWatch alarms and SNS alerting`.

#### Monitoring resources created

```text
SNS topic: durham-risk-dashboard-dev-alerts
CloudWatch alarm: durham-risk-dashboard-dev-ec2-high-cpu
CloudWatch alarm: durham-risk-dashboard-dev-ec2-status-check-failed
```

Monitored signals:

- EC2 CPU utilization
- EC2 status check failure

#### Alerting setup

- Alerts are routed through the Terraform managed SNS topic.
- The email subscription was confirmed through AWS SNS.
- The alert email value is provided locally through Terraform variables and should not be committed.

#### Validation completed

- Terraform apply completed successfully.
- CloudWatch alarms were visible in AWS.
- SNS email subscription was confirmed.
- Alarm states were confirmed:

```text
CPUUtilization: OK
StatusCheckFailed: OK
```

#### Current status

The Terraform managed deployment now includes basic CloudWatch monitoring and SNS email alerting for EC2 infrastructure health. The dashboard remains publicly available through Nginx on port `80`:

```text
http://98.93.40.196
```

Health check URL:

```text
http://98.93.40.196/health
```

#### Next step

The next likely monitoring improvement is application health check monitoring, log forwarding, a CloudWatch dashboard, or notification refinement. Do not proceed to application health monitoring, HTTPS, Route 53, or CI/CD until this monitoring checkpoint is reviewed.
