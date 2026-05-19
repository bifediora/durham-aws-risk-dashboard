# Auto Scaling Group Notes

## Durham Risk Intelligence Dashboard

## Purpose

This document records the Auto Scaling Group milestone for the Durham Risk Intelligence Dashboard.

This step moves the project from a single manually managed EC2 application instance toward an Auto Scaling based architecture where EC2 application instances can be created and managed from a Launch Template.

## Architecture Context

Before this milestone, the working architecture was:

```text
User
  ↓
Application Load Balancer on port 80
  ↓
Target Group
  ↓
Single manually created EC2 FastAPI application instance on port 8000
  ↓
Local CSV based sample data
```

After this milestone, the architecture includes an Auto Scaling Group:

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

During validation, the Target Group contained two healthy targets:

```text
Original manually created EC2 instance
ASG-created EC2 instance
```

This is acceptable during the transition and testing stage.

## Completed Milestone

Completed:

```text
Auto Scaling Group created
Auto Scaling Group attached to existing Target Group
Auto Scaling Group used the Launch Template
ASG-created EC2 instance launched successfully
ASG-created EC2 instance reached InService status
ASG-created EC2 instance became healthy
Target Group showed two healthy targets
ALB /health route worked
ALB /dashboard route worked
```

## Auto Scaling Group

Auto Scaling Group name:

```text
durham-risk-dashboard-asg
```

Launch Template used:

```text
durham-risk-dashboard-lt
```

Target Group attached:

```text
durham-risk-dashboard-tg
```

Application Load Balancer:

```text
durham-risk-dashboard-alb
```

## Capacity Settings

The Auto Scaling Group was created with conservative capacity settings:

```text
Desired capacity: 1
Minimum capacity: 1
Maximum capacity: 2
```

Reason:

The purpose of this stage is not heavy traffic scaling.

The purpose is to demonstrate:

- Launch Template integration
- Auto Scaling Group creation
- Target Group registration
- Health check based application validation
- Load balanced access to healthy EC2 targets
- A foundation for future resilience and scaling

A maximum of `2` keeps costs controlled while still demonstrating scaling readiness.

## Health Check Configuration

Health check type:

```text
ELB
```

Health check grace period:

```text
300 seconds
```

Target Group health check:

```text
Protocol: HTTP
Path: /health
Success code: 200
Port: traffic port / 8000
```

FastAPI health endpoint:

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

## Why ELB Health Checks Were Used

ELB health checks were used because this project needs to verify that the application is healthy from the Load Balancer perspective.

EC2 health checks only confirm that the instance itself is running.

ELB health checks confirm that the FastAPI dashboard application is responding correctly through the target group health check path.

This is better aligned with the production style goal of routing user traffic only to healthy application targets.

## Launch Template Relationship

The Auto Scaling Group uses the existing Launch Template:

```text
durham-risk-dashboard-lt
```

The Launch Template was created from the custom AMI:

```text
durham-risk-dashboard-ami-v1
```

Relationship:

```text
Custom AMI
  ↓
Captured the working EC2 dashboard server

Launch Template
  ↓
Defines how future EC2 instances should be created

Auto Scaling Group
  ↓
Uses the Launch Template to create and maintain EC2 instances

Target Group
  ↓
Checks whether those instances are healthy

Application Load Balancer
  ↓
Routes user traffic to healthy targets
```

## Security Group Configuration

The Auto Scaling Group created instances from the Launch Template.

The Launch Template uses the EC2 application security group:

```text
launch-wizard-1
sg-08614f1873385ef42
```

This is the correct security group for EC2 application instances.

The EC2 application security group allows:

```text
SSH 22:
Source = current user IP

FastAPI 8000:
Source = ALB security group only
```

The ALB security group is:

```text
durham-risk-dashboard-alb-sg
sg-0039dbb4fe5326472
```

The ALB security group controls public browser access to the Load Balancer.

Current desired traffic pattern:

```text
User browser
  ↓
ALB on port 80
  ↓
EC2 app target on port 8000 from ALB security group only
```

Direct browser access to EC2 port `8000` should remain blocked.

## Validation Results

The Auto Scaling Group created a new EC2 instance.

The new instance reached:

```text
Lifecycle state: InService
Health status: Healthy
```

The Target Group showed:

```text
Two healthy targets
```

The two targets were:

```text
Original manually created EC2 instance
ASG-created EC2 instance
```

The ALB routes were tested successfully:

```text
/health
/dashboard
```

Confirmed result:

```text
ALB /health: working
ALB /dashboard: working
```

## Current Architecture After ASG Creation

The current confirmed architecture is:

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

The Auto Scaling Group path is confirmed:

```text
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

## Important Transition Note

The original manually created EC2 instance was not removed during this milestone.

This was intentional.

The original instance should remain in place until the ASG-created instance is fully validated and the transition strategy is documented.

For now, both targets being healthy is acceptable.

Later, the project can decide whether to:

1. Keep both targets temporarily
2. Deregister the original manually created EC2 instance from the Target Group
3. Allow the Auto Scaling Group to manage the application layer
4. Eventually terminate the original manually created instance if it is no longer needed

Do not terminate the original EC2 instance without first confirming the ASG-created instance can fully carry the dashboard workload.

## Cost Control Note

The Auto Scaling Group currently has:

```text
Desired capacity: 1
Minimum capacity: 1
Maximum capacity: 2
```

Because the original manually created EC2 instance is still running, there may currently be two EC2 instances running.

This is acceptable for validation, but the project should review cost impact before leaving both instances active long term.

## What This Milestone Demonstrates

This milestone demonstrates:

- EC2 application deployment
- Persistent systemd based application service
- Custom AMI creation
- Launch Template creation
- Auto Scaling Group creation
- Target Group integration
- ELB health checks
- ALB routing to healthy targets
- Security group controlled application traffic
- Movement toward repeatable and resilient AWS infrastructure

## Portfolio Significance

This milestone strengthens the cloud engineering portfolio story.

The project no longer only shows a single EC2 hosted dashboard.

It now shows a progression toward production style infrastructure:

```text
Single EC2 instance
  ↓
Application Load Balancer
  ↓
Target Group health checks
  ↓
Custom AMI
  ↓
Launch Template
  ↓
Auto Scaling Group
  ↓
Healthy ASG-created application target
```

Portfolio explanation:

```text
I moved a FastAPI geospatial dashboard from a single manually managed EC2 instance toward a more resilient AWS architecture by creating a custom AMI, building a Launch Template, and configuring an Auto Scaling Group that launched a healthy application instance behind an Application Load Balancer.
```

## Interview Explanation

A simple way to explain this:

```text
The AMI is the saved image of the working server.
The Launch Template is the recipe for creating new servers from that image.
The Auto Scaling Group is the manager that keeps the right number of servers running.
The Target Group checks whether those servers are healthy.
The Load Balancer sends users only to healthy servers.
```

In this project, the Auto Scaling Group successfully created a new EC2 instance from the Launch Template. That instance registered with the Target Group, passed the `/health` check, and became available through the Application Load Balancer.

## Current Confirmed Status

```text
Application Load Balancer: working
Target Group: working
Original EC2 target: healthy
ASG-created EC2 target: healthy
Auto Scaling Group: created
ASG instance lifecycle state: InService
ASG instance health status: Healthy
ALB /health: working
ALB /dashboard: working
Direct EC2 public access on port 8000: blocked
GitHub documentation: in progress
```

## Next Recommended Steps

Recommended next steps:

1. Document this Auto Scaling Group milestone in the process log
2. Update `docs/aws_architecture_notes.md`
3. Update `docs/project_checkpoint.md`
4. Update `README.md`
5. Decide whether to keep or deregister the original manually created EC2 target
6. Confirm cost impact of running both the original EC2 instance and the ASG-created instance
7. Consider testing ASG replacement behavior later
8. Prepare for Terraform readiness documentation

## Future Improvement

A future improvement is to move from a custom AMI based Launch Template to a clean Ubuntu AMI with user data bootstrap.

That future approach would use startup automation to:

- Install dependencies
- Clone the GitHub repository
- Create the Python virtual environment
- Install `requirements.txt`
- Configure the systemd service
- Start the FastAPI application
- Validate the `/health` endpoint

That would be more production aligned and better suited for Terraform and CI/CD.

For this stage, the custom AMI approach is acceptable because it clearly demonstrates the core AWS architecture concepts.