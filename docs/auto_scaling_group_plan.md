# Auto Scaling Group Plan

## Durham Risk Intelligence Dashboard

## Purpose

This document plans the Auto Scaling Group for the Durham Risk Intelligence Dashboard.

The Auto Scaling Group will use the existing Launch Template to create and manage EC2 application instances behind the Application Load Balancer.

This is the next step in moving the project from a single EC2 instance toward a more resilient Phase 1 AWS architecture.

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
Custom AMI: available
Launch Template: created
```

## Target Architecture After Auto Scaling Group

The target architecture after this step is:

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
  ↓
Local CSV based sample data
```

## What the Auto Scaling Group Does

The Auto Scaling Group manages EC2 application instances.

It can:

- Create EC2 instances from a Launch Template
- Keep a desired number of instances running
- Replace unhealthy instances
- Register instances with a Target Group
- Support scaling policies later
- Improve resilience compared with a single manually managed instance

The Auto Scaling Group does not replace the Load Balancer.

The Load Balancer still handles public traffic.

The Auto Scaling Group manages the EC2 application layer behind the Load Balancer.

## Relationship Between Components

```text
Launch Template
  ↓
Defines how EC2 instances should be created

Auto Scaling Group
  ↓
Uses the Launch Template to create and maintain EC2 instances

Target Group
  ↓
Receives healthy EC2 instances from the Auto Scaling Group

Application Load Balancer
  ↓
Routes user traffic to healthy targets in the Target Group
```

## Planned Auto Scaling Group Configuration

| Setting | Planned Value |
|---|---|
| Auto Scaling Group name | `durham-risk-dashboard-asg` |
| Launch Template | `durham-risk-dashboard-lt` |
| Launch Template AMI | `durham-risk-dashboard-ami-v1` |
| Target Group | `durham-risk-dashboard-tg` |
| Load Balancer | `durham-risk-dashboard-alb` |
| Desired capacity | `1` |
| Minimum capacity | `1` |
| Maximum capacity | `2` |
| Health check type | ELB |
| Health check grace period | 300 seconds |
| VPC | Same VPC as the current EC2, ALB, and Target Group |
| Subnets | Use subnets enabled for the ALB and compatible with the current target group |
| Scaling policy | None for the first version |
| Instance maintenance policy | Default |

## Recommended Capacity Settings for This Stage

For this portfolio stage, use conservative capacity settings:

```text
Desired capacity: 1
Minimum capacity: 1
Maximum capacity: 2
```

Reason:

The goal is not heavy traffic scaling yet.

The goal is to demonstrate:

- Auto Scaling Group creation
- Launch Template integration
- Target Group registration
- Health check based instance management
- Basic resilience
- Future scaling readiness

A maximum of `2` keeps cost low while still showing that the architecture can scale.

## Health Check Design

Use ELB health checks.

The Target Group health check is already configured as:

```text
Protocol: HTTP
Path: /health
Success code: 200
Port: traffic port / 8000
```

The FastAPI application health endpoint is:

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

The Auto Scaling Group should rely on the Target Group health check so that instances are judged based on whether the application is actually reachable through the load balanced path.

## Why Use ELB Health Checks

EC2 health checks only verify whether the EC2 instance itself is running.

ELB health checks verify whether the application target is healthy from the Load Balancer perspective.

For this project, ELB health checks are better because the goal is to confirm that the FastAPI dashboard application is reachable and responding correctly.

## Network and Subnet Considerations

The current project is still using the default VPC.

The Auto Scaling Group should be created in the same VPC used by:

- Current EC2 instance
- Application Load Balancer
- Target Group

The selected subnets should be compatible with the ALB and Target Group.

For this stage, use the same Availability Zone/subnet pattern already proven to work with the current EC2 instance and ALB.

Later, when the project moves to a custom VPC, the Auto Scaling Group can be redesigned to use private subnets.

## Security Group Considerations

The Launch Template should use the EC2 application security group:

```text
launch-wizard-1
sg-08614f1873385ef42
```

This security group supports the desired access pattern:

```text
SSH 22:
Source = current user IP

FastAPI 8000:
Source = ALB security group only
```

The Auto Scaling Group should create instances that inherit this EC2 application security group through the Launch Template.

The ALB security group remains:

```text
durham-risk-dashboard-alb-sg
sg-0039dbb4fe5326472
```

The ALB security group controls public browser access to the Load Balancer.

## Desired Access Pattern

The desired user traffic path is:

```text
User
  ↓
Application Load Balancer on port 80
  ↓
Target Group
  ↓
EC2 instances on port 8000
```

The undesired direct access path is:

```text
User
  ↓
EC2 public IP on port 8000
```

That direct EC2 path should remain blocked.

## Important Design Decision

The first Auto Scaling Group should be simple.

Do not add advanced scaling policies yet.

The first version should focus on:

- Creating the Auto Scaling Group
- Using the Launch Template
- Connecting to the existing Target Group
- Confirming the ASG-created instance becomes healthy
- Confirming the dashboard still opens through the ALB
- Confirming the architecture remains secure

Scaling policies can be added later after the basic ASG is working.

## Potential Issue to Watch For

Because the current Launch Template uses a custom AMI from the existing EC2 instance, new instances should already contain the application.

However, after the ASG launches a new instance, verify that:

- The systemd service starts correctly
- FastAPI listens on `0.0.0.0:8000`
- The `/health` endpoint returns `200`
- The instance registers as healthy in the Target Group
- The dashboard opens through the ALB

Useful EC2 validation commands if SSH is needed:

```bash
sudo systemctl status durham-risk-dashboard --no-pager
sudo ss -tulpn | grep 8000
curl http://127.0.0.1:8000/health
```

## Cost Control

To limit cost during this stage:

```text
Desired capacity: 1
Minimum capacity: 1
Maximum capacity: 2
```

This prevents the Auto Scaling Group from launching many instances.

The current manually created EC2 instance may still exist during the transition.

Before keeping both the original EC2 instance and the ASG-created instance running long term, review cost impact.

## Transition Plan

The initial transition should be cautious.

Recommended transition sequence:

1. Create the Auto Scaling Group using the Launch Template
2. Attach it to the existing Target Group
3. Set desired capacity to `1`
4. Wait for the ASG-created instance to launch
5. Confirm the new instance registers with the Target Group
6. Confirm the new instance becomes healthy
7. Test the ALB `/health` endpoint
8. Test the ALB `/dashboard` endpoint
9. Confirm the original manually created EC2 instance is still healthy
10. Decide later whether to remove the original manually registered target

Do not immediately terminate the original EC2 instance until the ASG-created instance is verified.

## Target Group Consideration

The current Target Group already has the original EC2 instance registered.

When the Auto Scaling Group is attached to the Target Group, the ASG-created instance should also register with the same Target Group.

For a short period, the Target Group may have:

```text
Original manually created EC2 instance
ASG-created EC2 instance
```

This is acceptable during testing.

After the ASG-created instance is confirmed healthy, the original manually registered instance can be reviewed.

Later, the architecture should preferably allow the Auto Scaling Group to manage the application instances.

## Portfolio Significance

Adding an Auto Scaling Group strengthens the project by showing movement toward resilience and repeatable infrastructure.

The project will demonstrate:

- Load balanced access
- Health checked targets
- Repeatable EC2 instance creation
- Automatic instance management
- Foundation for scaling
- Foundation for Terraform
- Foundation for CI/CD

Portfolio explanation:

```text
I moved the dashboard from a single manually managed EC2 instance toward a more resilient AWS architecture by creating a custom AMI, building a Launch Template, and planning an Auto Scaling Group that can create and maintain healthy FastAPI application instances behind an Application Load Balancer.
```

## Interview Explanation

A simple way to explain the Auto Scaling Group:

```text
The Launch Template is the recipe for creating app servers.
The Auto Scaling Group is the manager that keeps the right number of app servers running.
The Target Group checks whether those servers are healthy.
The Load Balancer sends users only to healthy servers.
```

In this project, the Auto Scaling Group will use the dashboard Launch Template to create EC2 instances that run the FastAPI application. Those instances will be attached to the Target Group, checked through the `/health` endpoint, and served to users through the Application Load Balancer.

## Success Criteria

The Auto Scaling Group milestone is successful when:

```text
Auto Scaling Group: created
Launch Template: attached
Desired capacity: 1
Minimum capacity: 1
Maximum capacity: 2
ASG-created instance: running
ASG-created instance: registered with Target Group
Target Group health: healthy
ALB /health route: working
ALB /dashboard route: working
Direct EC2 port 8000 browser access: still blocked
```

## Next AWS Console Step

After this plan is committed, create the Auto Scaling Group in AWS Console.

AWS path:

```text
AWS Console
  → EC2
  → Auto Scaling Groups
  → Create Auto Scaling group
```

Use:

```text
Auto Scaling Group name:
durham-risk-dashboard-asg
```

Use Launch Template:

```text
durham-risk-dashboard-lt
```

Attach to Target Group:

```text
durham-risk-dashboard-tg
```

Use capacity:

```text
Desired: 1
Minimum: 1
Maximum: 2
```

Use health check type:

```text
ELB
```

## Immediate Next Actions

1. Save this document as `docs/auto_scaling_group_plan.md`
2. Confirm the file has the full content
3. Commit and push the planning document
4. Create the Auto Scaling Group in AWS Console
5. Confirm the ASG-created EC2 instance launches
6. Confirm the ASG-created instance becomes healthy in the Target Group
7. Test the dashboard through the ALB
8. Document the Auto Scaling Group milestone