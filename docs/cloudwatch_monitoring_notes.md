# CloudWatch Monitoring Notes

## Monitoring Goal

Add basic operational visibility for the Durham Risk Intelligence Dashboard running on AWS EC2.

The goal is to show that the application is not just deployed, but can be monitored for health, performance, and reliability.

## Current Deployment

The FastAPI application is running on a single EC2 instance using a `systemd` service.

Current public endpoint pattern:

```text
http://EC2_PUBLIC_IP:8000
