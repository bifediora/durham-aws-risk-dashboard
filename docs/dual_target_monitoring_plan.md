# Dual Target Monitoring Plan

## Durham Risk Intelligence Dashboard

## Purpose

This document defines the monitoring plan for the current dual target validation period.

The project is currently using Option A:

```text
Keep both healthy targets temporarily.
```

This means the Target Group currently includes:

```text
1. Original manually created EC2 instance
2. ASG-created EC2 instance
```

Both targets are healthy and the dashboard is working through the Application Load Balancer.

## Current Architecture

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

## Current Confirmed Status

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

## Why Monitoring Matters Now

The Auto Scaling Group milestone is working, but the project is intentionally not cutting over to ASG-only yet.

The current goal is to observe stability before making a final transition decision.

Monitoring helps confirm:

- Both targets remain healthy
- The ALB continues routing successfully
- The ASG-created instance remains stable
- The Target Group does not show unhealthy targets
- The dashboard remains available through the ALB
- There are no unexpected 5XX errors
- The ASG maintains the desired capacity

## Resources to Monitor

### Application Load Balancer

Resource:

```text
durham-risk-dashboard-alb
```

Monitor for:

- Request count
- HTTP 5XX errors
- Target response errors
- Load balancer availability
- Listener behavior on port `80`

Important question:

```text
Can users still reach /health and /dashboard through the ALB?
```

### Target Group

Resource:

```text
durham-risk-dashboard-tg
```

Monitor for:

- Healthy host count
- Unhealthy host count
- Target health status
- Health check failures
- Target response behavior

Expected state during Option A:

```text
Healthy targets: 2
Unhealthy targets: 0
```

### Auto Scaling Group

Resource:

```text
durham-risk-dashboard-asg
```

Monitor for:

- Desired capacity
- Minimum capacity
- Maximum capacity
- InService instances
- Pending instances
- Terminating instances
- Health status
- Activity history

Expected current ASG state:

```text
Desired capacity: 1
Minimum capacity: 1
Maximum capacity: 2
ASG-created instance: InService
ASG-created instance health: Healthy
```

### EC2 Instances

Resources:

```text
Original manually created EC2 instance
ASG-created EC2 instance
```

Monitor for:

- Instance state
- EC2 status checks
- CPU utilization
- Network in and out
- System reachability
- Instance reachability

Expected current state:

```text
Original EC2 instance: running
ASG-created EC2 instance: running
Both status checks: passing
```

### FastAPI Application

Application endpoint:

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

Monitor manually through the ALB:

```text
http://durham-risk-dashboard-alb-1259826957.us-east-1.elb.amazonaws.com/health
```

Dashboard route:

```text
http://durham-risk-dashboard-alb-1259826957.us-east-1.elb.amazonaws.com/dashboard
```

Expected result:

```text
/health returns healthy JSON
/dashboard opens successfully
```

## Manual Validation Checklist

During the validation period, periodically confirm:

```text
Target Group healthy targets: 2
Target Group unhealthy targets: 0
Original EC2 target: Healthy
ASG-created EC2 target: Healthy
ASG instance lifecycle state: InService
ASG health status: Healthy
ALB /health route: Working
ALB /dashboard route: Working
Direct EC2 public access on port 8000: Blocked
```

## Recommended CloudWatch Metrics to Review

### Target Group Metrics

Recommended metrics:

```text
HealthyHostCount
UnHealthyHostCount
TargetResponseTime
HTTPCode_Target_5XX_Count
HTTPCode_Target_4XX_Count
```

Most important for this stage:

```text
HealthyHostCount
UnHealthyHostCount
HTTPCode_Target_5XX_Count
```

### Application Load Balancer Metrics

Recommended metrics:

```text
RequestCount
HTTPCode_ELB_5XX_Count
HTTPCode_ELB_4XX_Count
TargetResponseTime
```

Most important for this stage:

```text
RequestCount
HTTPCode_ELB_5XX_Count
TargetResponseTime
```

### Auto Scaling Group Metrics

Recommended metrics:

```text
GroupDesiredCapacity
GroupInServiceInstances
GroupPendingInstances
GroupTerminatingInstances
GroupTotalInstances
```

Most important for this stage:

```text
GroupDesiredCapacity
GroupInServiceInstances
GroupTotalInstances
```

### EC2 Metrics

Recommended metrics:

```text
CPUUtilization
NetworkIn
NetworkOut
StatusCheckFailed
StatusCheckFailed_Instance
StatusCheckFailed_System
```

Most important for this stage:

```text
CPUUtilization
StatusCheckFailed
```

## Potential Future Alarms

Potential CloudWatch alarms to add later:

```text
Target Group unhealthy host count greater than 0
ALB 5XX errors greater than 0
Target 5XX errors greater than 0
ASG InService instances less than desired capacity
EC2 status check failed
High CPU utilization
```

Recommended first alarm to add later:

```text
Target Group UnHealthyHostCount > 0
```

Reason:

This directly monitors whether any target behind the ALB is failing health checks.

## Option A Stability Criteria

Option A is considered stable if:

```text
Both targets remain healthy
ALB /health continues working
ALB /dashboard continues working
ASG-created instance remains InService and Healthy
No unexpected unhealthy targets appear
No persistent 5XX errors appear
Direct EC2 port 8000 remains blocked from public browser access
```

## When to Consider ASG-Only Transition

The project can consider moving from Option A to ASG-only after:

```text
The ASG-created instance remains healthy over a validation period
The dashboard works reliably through the ALB
The Target Group remains stable
No major errors appear in ALB or Target Group monitoring
The original EC2 instance is no longer needed as a fallback
```

The ASG-only transition would involve:

```text
Deregister original manually created EC2 target
Keep ASG-created EC2 target in the Target Group
Confirm ALB /health works
Confirm ALB /dashboard works
Confirm Target Group remains healthy
```

## Current Decision

Current decision:

```text
Do not deregister or terminate the original manually created EC2 instance yet.
```

Reason:

The project is in a stable dual target validation period.

The original manually created EC2 instance remains available as a fallback while the ASG-created instance continues to prove stability.

## Portfolio Significance

This monitoring step strengthens the operational maturity of the project.

The project now demonstrates not only that AWS infrastructure can be created, but also that the architecture can be validated and observed before making transition decisions.

Portfolio explanation:

```text
After creating a custom AMI, Launch Template, and Auto Scaling Group, I kept the original EC2 instance and ASG-created instance healthy behind the same Target Group during a validation period. I then defined a monitoring plan to observe target health, ALB availability, ASG instance status, and application health before moving to an ASG-managed-only architecture.
```

## Next Recommended Step

After this monitoring plan is committed, the next practical step is:

```text
Review CloudWatch metrics for the Target Group, ALB, and Auto Scaling Group.
```

The next documentation step is:

```text
Update the process log and checkpoint to reference the dual target monitoring plan.
```