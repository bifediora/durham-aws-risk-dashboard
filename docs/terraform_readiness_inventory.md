# Terraform Readiness Inventory

## Durham Risk Intelligence Dashboard

## Purpose

This document inventories the manually created AWS resources for the Durham Risk Intelligence Dashboard so the project can prepare for a future Terraform phase.

This is a readiness document only.

No Terraform code is being written yet.

The purpose is to clearly document what currently exists in AWS, what Terraform may eventually manage, and what decisions need to be made before converting the infrastructure to Infrastructure as Code.

## Current Phase

The project is still in Phase 1:

```text
Phase 1: Build a production style AWS architecture
```

The next major phase will be:

```text
Phase 2: Convert infrastructure to Terraform
```

This document prepares for Phase 2 by identifying the current manually created AWS resources.

## Current Architecture Summary

Current working architecture:

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

The ASG path is also working:

```text
Custom AMI
  ↓
Launch Template
  ↓
Auto Scaling Group
  ↓
ASG-created EC2 instance
  ↓
Target Group
  ↓
Healthy target
```

Current transition strategy:

```text
Option A: Keep both healthy targets temporarily.
```

## Current Confirmed Status

```text
Application Load Balancer: working
Target Group: healthy
Healthy targets: 2
Original EC2 target: healthy
ASG-created EC2 target: healthy
Auto Scaling Group: created
ASG instance: InService and Healthy
ALB /health: working
ALB /dashboard: working
Direct EC2 public access on port 8000: blocked
GitHub documentation: current
```

## AWS Region

Current AWS region:

```text
us-east-1
```

Region name:

```text
N. Virginia
```

## Networking Inventory

### Current VPC

Current VPC:

```text
vpc-0c7c5a59a1b899fea
```

Current state:

```text
Default VPC
```

Terraform readiness note:

The current architecture uses the default VPC. A future Terraform version should likely define a custom VPC with public and private subnets.

Terraform decision needed:

```text
Recreate architecture in a custom Terraform-managed VPC rather than importing the default VPC.
```

### Subnets and Availability Zones

Current known working Availability Zone:

```text
us-east-1d
```

Current use:

```text
The ALB, Target Group, original EC2 target, and ASG-created target are operating in the current default VPC/subnet setup.
```

Terraform readiness note:

Subnets should be explicitly inventoried before Terraform conversion.

Future target design should include:

```text
Public subnets for ALB
Private subnets for EC2 application instances
Optional private subnets for future RDS
```

## Compute Inventory

### Original EC2 Instance

Instance name:

```text
durham-risk-dashboard-ec2
```

Known instance ID:

```text
i-07895b87a7d7eb25b
```

Purpose:

```text
Original manually created EC2 instance hosting the FastAPI dashboard application.
```

Current status:

```text
Running
Healthy in Target Group
Retained as part of Option A transition strategy
```

Application port:

```text
8000
```

Application service:

```text
durham-risk-dashboard
```

EC2 project path:

```text
/home/ubuntu/durham-aws-risk-dashboard
```

Terraform readiness note:

This original instance may not need to be imported into Terraform long term if the application layer is moved fully to Auto Scaling Group management.

Terraform decision needed:

```text
Decide whether the original manually created EC2 instance remains temporary and is eventually removed from the target group.
```

### ASG-created EC2 Instance

Purpose:

```text
EC2 instance created by the Auto Scaling Group using the Launch Template.
```

Current status:

```text
Running
InService
Healthy
Registered with Target Group
```

Terraform readiness note:

Future Terraform should manage the Auto Scaling Group and Launch Template rather than individual ASG-created instances.

Terraform decision needed:

```text
Do not manage ASG-created instances directly. Manage the Auto Scaling Group that creates them.
```

## Custom AMI Inventory

AMI name:

```text
durham-risk-dashboard-ami-v1
```

Purpose:

```text
Reusable image created from the working EC2 dashboard instance.
```

Current status:

```text
Available
Used by Launch Template
```

Captures:

- FastAPI application
- Python virtual environment
- Runtime dependencies
- systemd service
- Static assets
- Templates
- GeoJSON files
- Sample arrests CSV
- Working `/health` endpoint

Terraform readiness note:

Terraform can reference an existing AMI ID, but the AMI creation process itself may remain manual at first.

Future improvement:

```text
Move from custom AMI based deployment to clean AMI plus user data bootstrap or CI/CD deployment automation.
```

Terraform decision needed:

```text
Decide whether Terraform should reference this AMI or whether a future automated build process should create AMIs separately.
```

## Launch Template Inventory

Launch Template name:

```text
durham-risk-dashboard-lt
```

Purpose:

```text
Defines how EC2 dashboard application instances are created.
```

Current configuration:

```text
AMI: durham-risk-dashboard-ami-v1
Key pair: durham-risk-dashboard-key
Security group: sg-08614f1873385ef42
User data: blank
Storage: default from AMI
```

Terraform readiness note:

The Launch Template is a strong candidate for Terraform management.

Terraform should eventually define:

- Launch Template name
- AMI ID
- Instance type
- Key pair
- Security group IDs
- Block device mappings
- Optional IAM instance profile
- Optional user data

Terraform decision needed:

```text
Decide whether to keep using custom AMI v1 or move to a user data bootstrap approach.
```

## Auto Scaling Group Inventory

Auto Scaling Group name:

```text
durham-risk-dashboard-asg
```

Purpose:

```text
Creates and manages EC2 application instances behind the Target Group.
```

Launch Template:

```text
durham-risk-dashboard-lt
```

Target Group:

```text
durham-risk-dashboard-tg
```

Capacity:

```text
Desired capacity: 1
Minimum capacity: 1
Maximum capacity: 2
```

Health check type:

```text
ELB
```

Health check grace period:

```text
300 seconds
```

Current status:

```text
ASG-created instance: InService
ASG-created instance health: Healthy
```

Terraform readiness note:

The Auto Scaling Group is a strong candidate for Terraform management.

Terraform should eventually define:

- ASG name
- VPC zone identifiers
- Launch Template reference
- Desired capacity
- Minimum capacity
- Maximum capacity
- Target Group attachment
- Health check type
- Health check grace period
- Tags
- Optional scaling policies

Terraform decision needed:

```text
Decide whether to keep desired capacity at 1 for cost control or later test desired capacity 2.
```

## Load Balancing Inventory

### Application Load Balancer

Load Balancer name:

```text
durham-risk-dashboard-alb
```

Type:

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

Purpose:

```text
Public HTTP entry point for the dashboard.
```

Current status:

```text
Working
/dashboard route working
/health route working
```

Terraform readiness note:

The ALB is a strong candidate for Terraform management.

Terraform should eventually define:

- Load Balancer name
- Internal or internet-facing setting
- Load Balancer type
- Security group
- Subnets
- Listener on port 80
- Listener rules
- Target Group forwarding

Future improvement:

```text
Add HTTPS using ACM and Route 53 if using a domain.
```

Terraform decision needed:

```text
Decide whether to keep HTTP only for portfolio demo or add HTTPS later.
```

### Target Group

Target Group name:

```text
durham-risk-dashboard-tg
```

Protocol and port:

```text
HTTP : 8000
```

Target type:

```text
Instance
```

Health check path:

```text
/health
```

Health check success code:

```text
200
```

Current status:

```text
Two healthy targets
Unhealthy targets: 0
```

Current targets:

```text
1. Original manually created EC2 instance
2. ASG-created EC2 instance
```

Terraform readiness note:

The Target Group is a strong candidate for Terraform management.

Terraform should eventually define:

- Target Group name
- Protocol
- Port
- VPC ID
- Health check path
- Health check interval
- Healthy threshold
- Unhealthy threshold
- Matcher code
- Target type

Terraform decision needed:

```text
Decide whether original manually created EC2 target remains temporary before Terraform conversion.
```

## Security Group Inventory

### ALB Security Group

Security group name:

```text
durham-risk-dashboard-alb-sg
```

Security group ID:

```text
sg-0039dbb4fe5326472
```

Purpose:

```text
Controls public browser access to the Application Load Balancer.
```

Current inbound behavior:

```text
HTTP 80 from current user IP during development
```

Current outbound behavior:

```text
TCP 8000 to EC2 application targets
```

Terraform readiness note:

The ALB security group is a strong candidate for Terraform management.

Terraform should eventually define:

- Inbound HTTP rule
- Optional inbound HTTPS rule
- Outbound traffic to EC2 application security group or application port
- Descriptions for each rule

Future improvement:

```text
Use HTTPS and restrict HTTP if a domain and certificate are added.
```

### EC2 Application Security Group

Security group name:

```text
launch-wizard-1
```

Security group ID:

```text
sg-08614f1873385ef42
```

Purpose:

```text
Controls administrative and application access to EC2 dashboard instances.
```

Current inbound behavior:

```text
SSH 22 from current user IP
FastAPI 8000 from ALB security group only
```

Current desired security posture:

```text
Direct browser access to EC2 port 8000 remains blocked.
Application traffic reaches EC2 only through the ALB.
```

Terraform readiness note:

The current security group name came from the original EC2 launch wizard. A future Terraform version should create a cleaner named security group.

Future recommended name:

```text
durham-risk-dashboard-app-sg
```

Terraform decision needed:

```text
Create a new Terraform-managed EC2 application security group instead of preserving the launch-wizard name.
```

## Monitoring Inventory

### CloudWatch Alarm

Alarm name:

```text
durham-risk-dashboard-high-cpu
```

Purpose:

```text
Basic CPU monitoring for the dashboard infrastructure.
```

Current status:

```text
Configured
```

Terraform readiness note:

CloudWatch alarms are good Terraform candidates.

Terraform should eventually define:

- CPU alarm
- Target Group unhealthy host alarm
- ALB 5XX alarm
- ASG InService capacity alarm
- Notification actions through SNS

### Target Group and ALB Metrics Reviewed

Reviewed metrics:

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

Terraform readiness note:

Future Terraform should add alarms for the most important operational signals.

Recommended first future alarm:

```text
Target Group UnHealthyHostCount > 0
```

### Auto Scaling Group Metrics

Current state:

```text
ASG metrics collection was not enabled during initial ASG setup.
```

ASG health was validated through:

```text
EC2 → Auto Scaling Groups → durham-risk-dashboard-asg → Instance management
```

Confirmed:

```text
ASG-created instance: InService
ASG-created instance health: Healthy
```

Terraform readiness note:

Terraform can later enable ASG metrics collection.

Future metrics to monitor:

```text
GroupDesiredCapacity
GroupInServiceInstances
GroupTotalInstances
GroupPendingInstances
GroupTerminatingInstances
```

## SNS Inventory

SNS topic:

```text
durham-risk-dashboard-alerts
```

Purpose:

```text
Receives alert notifications from CloudWatch.
```

Current status:

```text
Configured
```

Terraform readiness note:

SNS topic and subscriptions can be managed by Terraform.

Terraform decision needed:

```text
Decide whether to manage email subscriptions manually or with Terraform.
```

Note:

Email subscriptions often require manual confirmation even when created through Terraform.

## S3 Inventory

S3 artifact bucket:

```text
durham-risk-dashboard-artifacts-byron-333973504198-us-east-1-an
```

Purpose:

```text
Private artifact storage for screenshots, reports, diagrams, and project documentation artifacts.
```

Current configuration:

```text
Region: us-east-1
Block all public access: enabled
Object ownership: ACLs disabled
Default encryption: SSE-S3
Bucket Key: disabled
```

Current screenshot artifacts:

```text
dashboard_top_summary.png
artifacts/screenshots/choropleth_analysis_view_2.png
dashboard_analytics_charts.png
```

Terraform readiness note:

The S3 artifact bucket is a strong candidate for Terraform management.

Terraform should eventually define:

- Bucket
- Block public access
- Server side encryption
- Versioning decision
- Lifecycle rules decision
- Tags

Terraform decision needed:

```text
Decide whether to import the existing bucket or create a new Terraform-managed bucket.
```

## IAM Inventory

Current IAM use:

```text
Basic account and AWS service access
No dedicated app instance role documented yet
```

Potential future IAM role:

```text
durham-risk-dashboard-ec2-role
```

Potential future permissions:

- Read specific S3 artifacts or data inputs
- Write logs to CloudWatch
- Use Systems Manager Session Manager
- Support CodeDeploy or deployment automation

Terraform readiness note:

IAM should be designed carefully before Terraform implementation.

Terraform decision needed:

```text
Create a least privilege EC2 instance role when moving toward production style Terraform.
```

## GitHub Inventory

GitHub repository:

```text
https://github.com/bifediora/durham-aws-risk-dashboard
```

Current branch:

```text
main
```

Purpose:

```text
Stores application source code, documentation, scripts, and project structure.
```

Terraform readiness note:

GitHub will be important for CI/CD in Phase 3.

Future CI/CD may connect GitHub to:

- CodePipeline
- CodeBuild
- CodeDeploy
- Deployment scripts
- Health check validation

## Resource Tagging Readiness

Future Terraform-managed resources should use consistent tags.

Recommended tags:

```text
Project = Durham Risk Intelligence Dashboard
Environment = dev
Owner = Byron Ifediora
ManagedBy = Terraform
Purpose = Cloud portfolio project
```

For resources still created manually, use:

```text
ManagedBy = Manual
```

Terraform readiness note:

Tagging should be standardized before Phase 2.

## Terraform Management Strategy Options

There are three possible Terraform approaches.

### Option 1: Recreate Infrastructure With Terraform

This means creating new Terraform-managed resources and eventually replacing the manually created resources.

Pros:

- Cleaner Terraform state
- Avoids complex imports
- Good for learning
- Easier to structure properly

Cons:

- Requires careful migration
- May temporarily duplicate resources
- Requires cost awareness

### Option 2: Import Existing Resources Into Terraform

This means importing manually created AWS resources into Terraform state.

Pros:

- Preserves existing resources
- Avoids rebuilding everything

Cons:

- More complex
- Terraform code must match existing resources exactly
- Higher risk of drift or state confusion for a learning project

### Option 3: Hybrid Learning Approach

This means documenting existing resources, then recreating a cleaner version in Terraform later.

Pros:

- Best learning path
- Reduces risk to working infrastructure
- Allows cleaner design
- Good portfolio explanation

Cons:

- Manual and Terraform resources may overlap temporarily

## Recommended Terraform Strategy

Recommended approach:

```text
Option 3: Hybrid Learning Approach
```

Reason:

The current AWS architecture is working and should not be disrupted immediately.

A future Terraform version can recreate the architecture cleanly, likely with:

- Custom VPC
- Public subnets
- Private subnets
- ALB
- Target Group
- Launch Template
- Auto Scaling Group
- Security groups
- S3
- CloudWatch
- SNS

This approach preserves the working manual architecture while allowing a cleaner Terraform design.

## Terraform Readiness Checklist

Before writing Terraform code, confirm:

```text
All major AWS resources are inventoried
Current VPC and subnet choices are understood
Security group rules are documented
ALB and Target Group settings are documented
ASG capacity and health check settings are documented
S3 configuration is documented
CloudWatch and SNS setup is documented
Tagging strategy is defined
Decision made on import versus recreate
Decision made on custom VPC design
Decision made on AMI versus user data bootstrap
```

## Immediate Next Terraform Readiness Actions

Recommended next actions:

1. Keep the current working AWS architecture stable
2. Continue Option A dual target validation
3. Do not deregister or terminate original EC2 yet
4. Standardize Terraform resource naming conventions
5. Decide whether Phase 2 will recreate resources or import existing resources
6. Plan Terraform folder structure
7. Create Terraform backend strategy later
8. Create Terraform variables strategy later
9. Create Terraform outputs strategy later

## Suggested Future Terraform Folder Structure

Possible Terraform structure:

```text
infra/
  terraform/
    environments/
      dev/
        main.tf
        variables.tf
        outputs.tf
        terraform.tfvars
    modules/
      network/
      security/
      alb/
      compute/
      monitoring/
      storage/
```

Simpler first version:

```text
infra/
  terraform/
    main.tf
    variables.tf
    outputs.tf
    terraform.tfvars.example
```

Recommended first Terraform version:

```text
Start simple with a single environment and avoid over modularizing too early.
```

## Portfolio Significance

This inventory strengthens the project by showing disciplined cloud engineering practice.

The project now has:

- Working AWS infrastructure
- Documented architecture
- Load balanced application access
- Target Group health checks
- Custom AMI
- Launch Template
- Auto Scaling Group
- Monitoring review
- Terraform readiness inventory

Portfolio explanation:

```text
After manually building and validating the AWS architecture, I created a Terraform readiness inventory that identifies the EC2, ALB, Target Group, Auto Scaling, S3, CloudWatch, SNS, IAM, security group, and networking resources that would need to be managed or recreated in Infrastructure as Code.
```

## Current Recommendation

Do not start Terraform coding yet.

First, review this inventory and decide:

```text
Will Phase 2 recreate the infrastructure cleanly with Terraform,
or will it attempt to import the existing manually created resources?
```

Recommended answer:

```text
Recreate a clean Terraform-managed version later while preserving the current working manual architecture as a reference.
```
