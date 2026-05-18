# Launch Template Plan

## Durham Risk Intelligence Dashboard

## Purpose

This document plans the EC2 Launch Template for the Durham Risk Intelligence Dashboard.

The Launch Template will define how future EC2 application instances should be created for the dashboard application.

This is the next step toward adding an Auto Scaling Group.

## Current Architecture

The current working architecture is:

```text
User
  ↓
Application Load Balancer on port 80
  ↓
Target Group
  ↓
Single EC2 FastAPI application instance on port 8000
  ↓
Local CSV based sample data
```

Current confirmed status:

```text
Application Load Balancer: working
Target Group: healthy
Dashboard through ALB: working
Direct EC2 public access on port 8000: blocked
EC2 port 8000 access: allowed from ALB security group only
SSH access: allowed from current user IP
```

## Target Next Architecture

The next target architecture is:

```text
User
  ↓
Application Load Balancer on port 80
  ↓
Target Group
  ↓
Auto Scaling Group
  ↓
EC2 FastAPI application instances created from Launch Template
```

## What the Launch Template Should Define

The Launch Template should define the reusable EC2 configuration for dashboard application instances.

Planned settings:

| Setting | Planned Value |
|---|---|
| Launch template name | `durham-risk-dashboard-lt` |
| AMI | Custom AMI created from the current working EC2 instance |
| Instance type | Same as current EC2 instance for now |
| Key pair | `durham-risk-dashboard-key` |
| Security group | `launch-wizard-1` / `sg-08614f1873385ef42` |
| Application port | `8000` |
| ALB security group source | `sg-0039dbb4fe5326472` |
| Storage | Same or similar to current EC2 root volume |
| IAM role | Add later if needed for S3, CloudWatch logs, SSM, or deployment automation |
| User data | Leave blank for now if using a custom AMI |

## Important Design Decision

There are two possible approaches.

### Option 1: Create a Custom AMI From the Current Working EC2 Instance

This captures the current server state, including:

- Project files
- Python virtual environment
- systemd service
- Installed dependencies
- Dashboard application
- Static assets
- GeoJSON layers
- Local sample data
- Working `/health` endpoint

This is the simplest next step for learning Auto Scaling because the Launch Template can use the custom AMI to create similar working instances.

### Option 2: Use a Clean Ubuntu AMI With User Data Bootstrap

This uses a fresh Ubuntu image and a startup script to install and configure everything automatically.

The user data script would need to:

- Update packages
- Install Python and required system dependencies
- Clone the GitHub repository
- Create the Python virtual environment
- Install `requirements.txt`
- Configure the systemd service
- Start the FastAPI application
- Validate the `/health` endpoint

This approach is more production aligned, but it adds more moving parts.

## Recommended Approach for This Stage

Use Option 1 first:

```text
Create a custom AMI from the current working EC2 instance.
```

Reason:

The current priority is to understand and demonstrate:

- Launch Template creation
- Auto Scaling Group setup
- Target Group integration
- Instance health checks
- ALB routing to healthy instances

After that is working, the project can later evolve toward a cleaner user data bootstrap approach.

## Launch Template Relationship to Auto Scaling

The Launch Template does not scale the app by itself.

It only defines the EC2 instance recipe.

The Auto Scaling Group will use the Launch Template to create and manage EC2 instances.

Relationship:

```text
Launch Template
  ↓
Defines how instances are created

Auto Scaling Group
  ↓
Uses the Launch Template to create, replace, and maintain instances

Target Group
  ↓
Receives healthy instances from the Auto Scaling Group

Application Load Balancer
  ↓
Routes user traffic to healthy targets
```

## Planned Launch Template Configuration

### Launch Template Name

Use:

```text
durham-risk-dashboard-lt
```

### AMI

Use a custom AMI created from the current working EC2 instance.

Reason:

The current EC2 instance already has the FastAPI app, virtual environment, service configuration, and project files working correctly.

### Instance Type

Use the same instance type as the current EC2 instance for now.

This avoids introducing performance or compatibility changes during the Launch Template and Auto Scaling Group setup.

### Key Pair

Use:

```text
durham-risk-dashboard-key
```

This keeps SSH access available for troubleshooting future instances if needed.

### Security Group

Use the current EC2 application security group:

```text
launch-wizard-1
sg-08614f1873385ef42
```

This security group currently supports the desired architecture:

```text
SSH 22:
Source = current user IP

FastAPI 8000:
Source = ALB security group only
```

### Storage

Use the same or similar root volume configuration as the current EC2 instance.

Recommended current setting:

```text
Root volume: same size as current EC2
Volume type: gp3 or gp2
Delete on termination: enabled
```

Do not add extra storage complexity at this stage.

### IAM Role

Leave blank for now unless the current EC2 instance already has a role attached.

Potential future IAM role uses include:

- S3 artifact access
- CloudWatch logs
- AWS Systems Manager Session Manager
- CodeDeploy
- Deployment automation

### User Data

Leave user data blank for the first Launch Template if using a custom AMI.

Reason:

The custom AMI should already contain the working application configuration.

Later, the project can add user data to support automated bootstrapping from a clean Ubuntu AMI.

## Security Considerations

The Launch Template should preserve the current security posture.

Desired access pattern:

```text
User
  ↓
Application Load Balancer on port 80
  ↓
EC2 application port 8000 from ALB security group only
```

The EC2 instance should not expose port `8000` directly to the public browser.

The ALB should remain the public HTTP entry point.

The EC2 security group should keep:

```text
SSH 22:
Source = current user IP

FastAPI 8000:
Source = ALB security group only
```

The ALB security group should keep:

```text
HTTP 80:
Source = current user IP during development
```

Later, if this becomes a public demo, the ALB inbound rule can be changed to support broader HTTP or HTTPS access.

## Portfolio Significance

Adding a Launch Template shows movement from a manually configured EC2 server toward repeatable infrastructure.

This supports the portfolio story:

```text
I moved a manually deployed FastAPI dashboard toward a more resilient AWS architecture by placing it behind an Application Load Balancer, restricting direct EC2 application access, and preparing a Launch Template so future instances can be created consistently and managed by an Auto Scaling Group.
```

## Interview Explanation

A Launch Template is the reusable configuration that tells AWS how to create new EC2 instances.

In this project, the Launch Template will define the server image, instance type, key pair, storage, and security group settings needed to run the Durham Risk Intelligence Dashboard.

The Auto Scaling Group will later use this Launch Template to create and manage dashboard application instances behind the Application Load Balancer.

Simple analogy:

```text
The Launch Template is the recipe.
The Auto Scaling Group is the kitchen manager that uses the recipe to create more workers.
The Target Group checks which workers are healthy.
The Application Load Balancer sends users to healthy workers.
```

## Next Step After This Plan

The next AWS console step should be:

```text
Create a custom AMI from the current working EC2 instance.
```

After the AMI is available, create:

```text
Launch Template: durham-risk-dashboard-lt
```

Then use that Launch Template to create:

```text
Auto Scaling Group
```

## Immediate Next Actions

1. Save this document as `docs/launch_template_plan.md`
2. Confirm the file has the full content
3. Commit and push the planning document
4. Create a custom AMI from the current working EC2 instance
5. Create the Launch Template in AWS Console
6. Use the Launch Template to create the Auto Scaling Group