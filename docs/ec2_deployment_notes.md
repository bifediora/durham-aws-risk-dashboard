# EC2 Deployment Notes

## Deployment Goal

Deploy the Durham Risk Intelligence Dashboard to a single AWS EC2 instance as the first cloud deployment milestone.

This single instance deployment is not the final architecture. It is the first AWS validation step before adding:

- Application Load Balancer
- private subnets
- Auto Scaling Group
- RDS
- CloudWatch alarms
- Terraform
- CI/CD

## Current Application

The application is a FastAPI dashboard that serves:

| Endpoint | Purpose |
|---|---|
| `/` | Homepage |
| `/health` | Health check |
| `/dashboard` | HTML dashboard |
| `/api/summary` | JSON summary metrics |
| `/api/records` | JSON sample records |

## Production Startup Command

The application can be started with:

```bash
./scripts/run_production.sh

uvicorn app.main:app --host 0.0.0.0 --port 8000

Developer machine
  ↓
GitHub repository or copied project files
  ↓
EC2 instance
  ↓
Python virtual environment
  ↓
Install requirements.txt
  ↓
Run FastAPI app with production startup script
  ↓
Access app through EC2 public IP on port 8000

