# Application Load Balancer and Target Group Notes

## Durham Risk Intelligence Dashboard

## Purpose

This document records the Application Load Balancer and Target Group setup for the Durham Risk Intelligence Dashboard.

This step moves the project from direct EC2 public IP access toward a more production style AWS architecture.

The previous access pattern was:

```text
User
  ↓
EC2 public IP on port 8000
  ↓
FastAPI dashboard application
```

The new access pattern is:

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

## Architecture Milestone

This is a major Phase 1 AWS architecture milestone.

The project now has:

- A working Application Load Balancer
- A working Target Group
- A registered EC2 target
- A working `/health` health check
- A healthy target status
- Dashboard access through the ALB DNS name

This improves the architecture by adding:

- A stable HTTP entry point
- Health check based routing
- Separation between public entry and application port
- A foundation for future Auto Scaling
- A foundation for future HTTPS
- A foundation for future Terraform and CI/CD automation

## AWS Resources Created

### Application Load Balancer

Load balancer name:

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

### Target Group

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

Target port:

```text
8000
```

Target health status after troubleshooting:

```text
Healthy
```

## Health Check Endpoint

The FastAPI application health check endpoint is:

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

The target group uses this endpoint to determine whether the EC2 instance is healthy.

## Confirmed ALB Request Flow

The working request flow is:

```text
Browser
  ↓
ALB DNS name on HTTP port 80
  ↓
ALB listener
  ↓
Target group
  ↓
EC2 instance on port 8000
  ↓
FastAPI application
  ↓
Dashboard or API response
```

Confirmed working ALB routes:

```text
/health
/dashboard
```

## Security Group Configuration

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

Inbound rule:

| Type | Protocol | Port | Source | Purpose |
|---|---|---|---|---|
| HTTP | TCP | 80 | Current user IP | Allows browser access to the ALB during development |

Outbound rule:

| Type | Protocol | Port | Destination | Purpose |
|---|---|---|---|---|
| Custom TCP | TCP | 8000 | 0.0.0.0/0 | Allows ALB outbound traffic to the FastAPI target on port 8000 |

Note:

The outbound rule is broad for the current development stage. The EC2 instance remains protected because its inbound rule only allows port `8000` traffic from the ALB security group.

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

This rule is the critical connection between the ALB and the EC2 application instance.

## Troubleshooting Notes

### Initial Target Status: Unused

The target group initially showed:

```text
Unused
```

Reason:

```text
Target is in an Availability Zone that is not enabled for the load balancer
```

Cause:

The EC2 instance was located in:

```text
us-east-1d
```

but the load balancer did not initially have that Availability Zone enabled.

Fix:

The ALB subnet mapping was updated to include the Availability Zone where the EC2 target was running.

### Target Status Changed to Unhealthy

After the Availability Zone was corrected, the target changed from `Unused` to:

```text
Unhealthy
```

Health status reason:

```text
Request timed out
```

This showed that the target group could now attempt to check the EC2 instance, but the connection to port `8000` was timing out.

### Verified FastAPI Was Running Correctly

On the EC2 instance, FastAPI was confirmed to be listening on all interfaces:

```bash
sudo ss -tulpn | grep 8000
```

Confirmed output showed:

```text
0.0.0.0:8000
```

The health check also worked locally on EC2:

```bash
curl http://127.0.0.1:8000/health
```

The health check also worked using the EC2 private IP:

```bash
curl http://172.31.40.20:8000/health
```

This confirmed the app itself was working and reachable on the EC2 network interface.

### Security Group Issue Found

The EC2 security group was correctly configured to allow port `8000` traffic from:

```text
sg-0039dbb4fe5326472
```

However, the ALB was initially attached to the wrong security group:

```text
sg-0f149ba485cdd5aae
default
```

This caused the EC2 security group rule to allow traffic from the intended ALB security group, while the actual ALB was using the default security group.

Fix:

The ALB security group attachment was changed from:

```text
sg-0f149ba485cdd5aae
```

to:

```text
sg-0039dbb4fe5326472
```

After this fix, the target group became healthy.

## Final Confirmed State

The final confirmed state is:

```text
Application Load Balancer: active
Target Group: attached to ALB listener
Target EC2 instance: registered
Target health status: Healthy
Health check path: /health
Dashboard through ALB: working
Health endpoint through ALB: working
```

The working architecture is now:

```text
User
  ↓
Application Load Balancer
  ↓
Target Group
  ↓
EC2 FastAPI instance
  ↓
Durham Risk Intelligence Dashboard
```

## Current Development Notes

Direct EC2 access on port `8000` may still be available temporarily.

Current development state may include:

```text
EC2 public IP on port 8000
ALB DNS name on port 80
```

The future preferred access path should be:

```text
User
  ↓
ALB DNS name
  ↓
EC2 target on port 8000
```

Later, direct public access to EC2 port `8000` should be removed or restricted so that user traffic goes through the ALB.

## Next Recommended Steps

Recommended next steps:

1. Document this ALB milestone in the process log
2. Update `docs/aws_architecture_notes.md`
3. Update `docs/project_checkpoint.md`
4. Update `README.md`
5. Test the dashboard through the ALB DNS name again
6. Consider removing direct browser access to EC2 port `8000` after ALB access is stable
7. Plan Auto Scaling Group setup
8. Prepare Terraform readiness notes

## Portfolio Significance

This milestone strengthens the cloud architecture story.

The project no longer only demonstrates a single EC2 hosted application. It now demonstrates the beginning of a production style AWS web architecture using a load balancer, target group, health checks, security group routing, and a working FastAPI application target.

The portfolio story now includes:

```text
I deployed a FastAPI geospatial dashboard to AWS EC2, added persistent service management, configured CloudWatch and SNS monitoring, created S3 artifact storage, pushed the project to GitHub, documented current and target architectures, and added an Application Load Balancer with target group health checks to move the project toward a production style AWS architecture.
```
