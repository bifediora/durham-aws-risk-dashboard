# AMI and Launch Template Notes

## Durham Risk Intelligence Dashboard

## Purpose

This document records the custom AMI and EC2 Launch Template milestone for the Durham Risk Intelligence Dashboard.

This step moves the project from a single manually configured EC2 instance toward repeatable EC2 instance creation and future Auto Scaling Group support.

## Architecture Context

The current working architecture is:

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

## Completed Milestone

Completed:

```text
Custom AMI created from working EC2 instance
Launch Template created using custom AMI
Launch Template configured with EC2 application security group
```

## Custom AMI

AMI name:

```text
durham-risk-dashboard-ami-v1
```

Purpose:

```text
Reusable server image for the Durham Risk Intelligence Dashboard FastAPI application.
```

The AMI was created from the current working EC2 instance:

```text
durham-risk-dashboard-ec2
```

The custom AMI captures the working server state, including:

- Ubuntu EC2 operating system state
- Durham Risk Intelligence Dashboard project files
- FastAPI application
- Python virtual environment
- Installed runtime dependencies
- Static assets
- Templates
- GeoJSON layers
- Local sample arrests CSV
- systemd service configuration
- Working `/health` endpoint
- Working dashboard route

## Why a Custom AMI Was Used

Two approaches were considered:

1. Create a custom AMI from the current working EC2 instance
2. Use a clean Ubuntu AMI with user data bootstrap

The project selected Option 1 for this stage:

```text
Create a custom AMI from the current working EC2 instance.
```

Reason:

This is the simplest and lowest friction path for learning and demonstrating:

- Launch Templates
- Auto Scaling Groups
- Target Group registration
- ALB health checks
- Instance replacement
- Repeatable EC2 application instance creation

A user data bootstrap approach can be added later as the architecture matures.

## Launch Template

Launch Template name:

```text
durham-risk-dashboard-lt
```

Template version description:

```text
Launch template for Durham Risk Intelligence Dashboard using custom AMI v1.
```

The Launch Template uses:

```text
AMI: durham-risk-dashboard-ami-v1
```

## Launch Template Configuration

The Launch Template was configured with the following values:

| Setting | Value |
|---|---|
| Launch Template name | `durham-risk-dashboard-lt` |
| AMI | `durham-risk-dashboard-ami-v1` |
| Instance type | Same as current working EC2 instance |
| Key pair | `durham-risk-dashboard-key` |
| Security group | `launch-wizard-1` / `sg-08614f1873385ef42` |
| Storage | Default from AMI |
| User data | Blank for now |

## Security Group Used

The Launch Template uses the EC2 application security group:

```text
launch-wizard-1
sg-08614f1873385ef42
```

This is the correct security group for EC2 application instances.

The Launch Template should not use the ALB security group.

## Current Security Group Design

The current desired security posture is:

```text
User traffic:
Browser → ALB on port 80

Application traffic:
ALB → EC2 FastAPI app on port 8000

Administrative traffic:
Current user IP → EC2 SSH on port 22
```

Current EC2 security group behavior:

```text
SSH 22:
Source = current user IP

FastAPI 8000:
Source = ALB security group only
```

Current ALB security group behavior:

```text
HTTP 80:
Source = current user IP during development
```

## Why the Launch Template Uses the EC2 Security Group

The Launch Template creates EC2 application instances.

Therefore, it should use the EC2 application security group:

```text
sg-08614f1873385ef42
```

This allows new EC2 instances created from the Launch Template to receive traffic from the ALB on port `8000`.

It also keeps direct public browser access to EC2 port `8000` blocked.

## What the Launch Template Does

The Launch Template does not create scaling by itself.

It defines the reusable EC2 instance recipe.

The Auto Scaling Group will later use the Launch Template to create and manage EC2 instances.

Relationship:

```text
Launch Template
  ↓
Defines how EC2 instances should be created

Auto Scaling Group
  ↓
Uses the Launch Template to create and maintain instances

Target Group
  ↓
Receives healthy EC2 instances

Application Load Balancer
  ↓
Routes user traffic to healthy targets
```

## Why This Matters

Before this milestone, the project relied on one manually configured EC2 instance.

After this milestone, the project has a reusable EC2 creation pattern.

This is important because future EC2 application instances can now be created with the same baseline configuration.

This supports:

- Repeatable infrastructure
- Instance replacement
- Auto Scaling Group setup
- Health check based routing
- Future Terraform conversion
- Future CI/CD deployment automation

## Current Confirmed State

Current confirmed project state:

```text
Application Load Balancer: working
Target Group: healthy
Dashboard through ALB: working
Direct EC2 public access on port 8000: blocked
EC2 port 8000 access: allowed from ALB security group only
Custom AMI: available
Launch Template: created
Launch Template security group: EC2 application security group
```

## Portfolio Significance

This milestone strengthens the AWS architecture story.

The project now demonstrates movement from a manually configured EC2 deployment toward repeatable cloud infrastructure.

Portfolio explanation:

```text
I created a custom AMI from the working EC2 dashboard instance and used it to build a Launch Template. This prepares the application for Auto Scaling because AWS now has a reusable recipe for creating new FastAPI application instances behind the Application Load Balancer.
```

## Interview Explanation

A simple way to explain this:

```text
The AMI is a snapshot of the working server.
The Launch Template is the recipe for creating future servers from that snapshot.
The Auto Scaling Group will use that recipe to create and maintain application servers.
The Target Group checks whether those servers are healthy.
The Load Balancer sends users only to healthy servers.
```

## Next Step

The next step is:

```text
Plan and create the Auto Scaling Group.
```

The Auto Scaling Group should use:

```text
Launch Template: durham-risk-dashboard-lt
Target Group: durham-risk-dashboard-tg
```

The Auto Scaling Group will help move the architecture toward:

```text
Application Load Balancer
  ↓
Target Group
  ↓
Auto Scaling Group
  ↓
EC2 instances created from Launch Template
```