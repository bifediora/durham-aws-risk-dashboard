# Durham Risk Intelligence Dashboard Interview Study Guide

## Purpose of This Guide

This guide helps prepare for interviews by translating the Durham Risk Intelligence Dashboard into clear, scenario based explanations.

It uses the SOART framework:

- Scenario: What was the situation or goal?
- Obstacle: What challenge or constraint had to be solved?
- Action: What did I do and why?
- Result: What changed or improved?
- Troubleshooting: What went wrong, what did I check, and how did I resolve it?

The goal is to explain the thought process behind the project, not just list the tools that were used.

## Project Summary

- The Durham Risk Intelligence Dashboard is a cloud deployed geospatial analytics application.
- It explores Durham public safety event data through maps, KPI summaries, charts, census tract context, ACS enrichment, and dashboard interactions.
- It evolved from a local FastAPI prototype into a Terraform managed AWS deployment.
- The final architecture uses EC2, Nginx, FastAPI/Uvicorn, systemd, Terraform, GitHub Actions, OIDC, AWS Systems Manager, CloudWatch, SNS, and Route 53 health checks.
- The dashboard is framed as a public-facing decision intelligence and preparedness prototype, not an enforcement prediction tool.

## SOART Framework

- Scenario: What was the situation or goal?
- Obstacle: What challenge or constraint had to be solved?
- Action: What did I do and why?
- Result: What changed or improved?
- Troubleshooting: What went wrong, what did I check, and how did I resolve it?

Each major project milestone below is organized with this structure so the project can be explained clearly in interviews.

## 1. Local FastAPI Dashboard Foundation

### Scenario

- I needed to build a local analytical dashboard foundation using real Durham public safety data.
- The goal was to start with a working application before moving into AWS deployment.

### Obstacle

- I needed a simple but expandable project structure.
- The app needed real data, dashboard routes, a health check, and local API endpoints.
- I wanted the foundation to be small enough to debug, but structured enough to grow.

### Action

- Created the project structure.
- Built the FastAPI app.
- Added homepage, dashboard, health, summary, and records endpoints.
- Connected the app to a cleaned sample arrests dataset.
- Added requirements, scripts, README notes, and process documentation.

### Result

- The local FastAPI foundation was complete.
- The app could serve HTML pages and JSON API endpoints.
- The project had a stable base for later AWS deployment.

### Troubleshooting

- Validated endpoints locally before moving to AWS.
- Checked `/health` early because it became the simplest way to confirm the app was alive.
- Started small and tested each piece before adding geospatial and cloud complexity.

### Interview Talking Points

- I started local first because cloud deployment is easier when the application is already proven.
- `/health` mattered early because it later supported EC2 testing, Nginx testing, Route 53 health checks, and deployment validation.
- I designed the project so a local analytics app could grow into a cloud engineering portfolio project.

## 2. Geospatial Dashboard Expansion

### Scenario

- I wanted the dashboard to move beyond static metrics into an interactive geospatial dashboard.
- The goal was to combine event data, map layers, charts, and neighborhood context in one analytical interface.

### Obstacle

- Source coordinates needed conversion.
- Outliers could distort the map.
- The dashboard needed to balance map interaction, charts, and visual clarity.
- Census tract and neighborhood layers had different roles and should not be confused.

### Action

- Added a Leaflet map.
- Converted coordinates from EPSG:2264 to EPSG:4326 for web mapping.
- Added bounding box filtering to reduce map distortion from outliers.
- Added Durham boundary, police beats, census tracts, neighborhood context, point, cluster, density, and choropleth modes.
- Added KPI cards, charts, temporal explorer, selected records, and tract popups.
- Preserved full census tract geometries for ACS consistency.
- Used neighborhoods as context and labels, not as the primary statistical geography.

### Result

- The dashboard became a stronger analytical prototype.
- It combined spatial, temporal, categorical, severity, and demographic context.
- The dashboard MVP was feature frozen and tagged as `dashboard-mvp-v1`.

### Troubleshooting

- Checked coordinate conversion when points did not line up with Durham geography.
- Used filtering to prevent bad coordinates from distorting the map.
- Reduced map clutter by refining legends, labels, layers, and popups.
- Kept census tracts as the analytical layer because ACS data and normalized rates depend on tract-level consistency.

### Interview Talking Points

- Census tracts were used because they support ACS joins, demographic context, and normalized rates.
- Full tract geometries were preserved so demographic joins stayed consistent with official tract boundaries.
- The dashboard is not predictive policing. It is framed around public-facing spatial analysis, preparedness, and decision intelligence.

## 3. Initial EC2 Deployment

### Scenario

- I needed to prove the local FastAPI dashboard could run on AWS infrastructure.
- This was the first step from local prototype to cloud hosted application.

### Obstacle

- Moving from local development to cloud hosting required EC2 setup, SSH access, dependencies, security group rules, and public testing.
- Local success did not guarantee the app would be reachable over the internet.

### Action

- Created an EC2 instance in `us-east-1`.
- Configured SSH access.
- Installed Python, pip, venv, Git, and dependencies.
- Copied project data and app files.
- Ran Uvicorn on port `8000`.
- Tested `/`, `/health`, `/dashboard`, `/api/summary`, and `/api/records`.

### Result

- The dashboard successfully ran on AWS EC2.
- The project moved from a local prototype to a deployed cloud application.

### Troubleshooting

- Validated the app locally on EC2 with `curl`.
- Confirmed security group rules allowed the required access.
- Confirmed Uvicorn was bound to `0.0.0.0`.
- Confirmed browser access through the public IP and port.

### Interview Talking Points

- Local success means the app works. Cloud success means the app, network, host, and security rules all work together.
- Security groups and health checks mattered because they helped separate application issues from network access issues.

## 4. Persistent systemd Service

### Scenario

- The app needed to keep running after the SSH session ended or the instance restarted.

### Obstacle

- Running Uvicorn manually in a terminal was not reliable enough for a deployed app.
- The app needed a process manager and logs.

### Action

- Created a `systemd` service.
- Set the working directory.
- Configured the service to run Uvicorn from the project virtual environment.
- Started and enabled the service.
- Verified the service was active.

### Result

- The FastAPI app became a persistent Linux service.
- The dashboard could survive terminal disconnects and instance restarts.

### Troubleshooting

- Used `systemctl status` to check service state.
- Used `journalctl -u durham-risk-dashboard -f` to inspect logs.
- Restarted the service after updates.
- Confirmed `/health` after restarting.

### Interview Talking Points

- `systemd` is more production like than a manual terminal command because it manages lifecycle, restarts, and logs.
- Service logs are usually the fastest place to debug deployment problems.

## 5. Nginx Reverse Proxy and Port Hardening

### Scenario

- I wanted public traffic to use standard HTTP port `80` instead of direct access to FastAPI on port `8000`.

### Obstacle

- FastAPI was originally exposed directly.
- Port `8000` should be treated as an internal application runtime port.
- The public entry point needed to be cleaner and easier for users.

### Action

- Installed and configured Nginx.
- Forwarded public port `80` traffic to FastAPI on `127.0.0.1:8000`.
- Updated Terraform security group rules.
- Removed public inbound access to port `8000`.
- Kept FastAPI internal behind Nginx.

### Result

- Public users access the dashboard through Nginx on port `80`.
- FastAPI remains internal on port `8000`.
- The deployment has cleaner public and internal runtime separation.

### Troubleshooting

- Tested Nginx syntax with `sudo nginx -t`.
- Confirmed Nginx was running.
- Curled `/health` locally and publicly.
- Verified the security group allowed port `80` and removed public access to port `8000`.

### Interview Talking Points

- Nginx was added to act as the public web entry point.
- Port `8000` was removed from public access because FastAPI should run as an internal app service.
- This improved the security posture by separating public web traffic from the internal application runtime.

## 6. Terraform Infrastructure Foundation

### Scenario

- I needed the infrastructure to become reproducible instead of manually created.

### Obstacle

- Manually created cloud resources are difficult to recreate, review, and extend.
- Terraform state, variables, SSH rules, and sensitive values needed careful handling.

### Action

- Created a Terraform workspace.
- Added AWS provider configuration.
- Added variables and outputs.
- Provisioned EC2 and a security group.
- Used Amazon Linux 2023 AMI lookup.
- Referenced an existing EC2 key pair.
- Restricted SSH access to an approved CIDR.
- Added Terraform state and tfvars files to `.gitignore`.

### Result

- Terraform could provision the EC2 infrastructure foundation.
- Outputs documented instance details, public IP, DNS, app URL, and SSH command.
- Infrastructure became more reproducible and reviewable.

### Troubleshooting

- Used `terraform fmt` to keep files consistent.
- Used `terraform init` to initialize the workspace.
- Used `terraform validate` to catch configuration issues.
- Reviewed `terraform plan` before applying changes.
- Protected state and local secrets from Git.

### Interview Talking Points

- Terraform was introduced after a working deployment so the infrastructure could be codified from a known reference.
- The hybrid learning approach let me preserve a stable dashboard while building Terraform incrementally.
- State files and local variable files should not be committed because they can contain sensitive or environment specific information.

## 7. EC2 Bootstrap Automation with Terraform user_data

### Scenario

- Terraform could create the EC2 instance, but the application setup was still manual.

### Obstacle

- When Terraform replaced the instance, manual packages, repo clone, service files, and Nginx configuration were lost.
- Infrastructure provisioning alone did not guarantee a recoverable app runtime.

### Action

- Created `infra/scripts/ec2_bootstrap.sh`.
- Connected it to Terraform `user_data`.
- Enabled `user_data_replace_on_change`.
- Automated package installation, repo clone, virtual environment creation, dependency install, systemd service creation, Nginx config, and service startup.

### Result

- New EC2 instances could recreate the dashboard runtime automatically.
- The deployment became more reproducible and resilient.

### Troubleshooting

- Validated bootstrap success through `/health`.
- Confirmed Nginx served the app on port `80`.
- Checked service status and logs.
- Documented that changing `user_data` may intentionally replace the instance.

### Interview Talking Points

- Provisioning creates the server. Bootstrapping configures the server to run the application.
- This mattered because instance replacement exposed the risk of manual setup.
- `user_data` improved recoverability because a new EC2 instance could rebuild the runtime on launch.

## 8. CloudWatch, SNS, and Route 53 Health Monitoring

### Scenario

- The deployed dashboard needed operational visibility.

### Obstacle

- EC2 might be running while the application is unhealthy.
- Infrastructure monitoring alone is not the same as application health monitoring.
- Alerts needed a clear notification path.

### Action

- Added CloudWatch alarms for EC2 CPU utilization and status check failure.
- Added SNS email alerting.
- Added a Route 53 HTTP health check for the public `/health` endpoint.
- Added a CloudWatch alarm on Route 53 `HealthCheckStatus`.

### Result

- Monitoring now covers both EC2 infrastructure health and application endpoint health.
- Alerts can be routed through SNS.
- `/health` is checked through the public Nginx endpoint on port `80`.

### Troubleshooting

- Confirmed CloudWatch metrics existed.
- Confirmed the SNS email subscription.
- Checked spam when the SNS confirmation email was not obvious.
- Confirmed the Route 53 health check was `OK`.
- Confirmed `/health` returned healthy JSON.

### Interview Talking Points

- `/health` monitoring matters because it tests whether the public application endpoint responds, not just whether EC2 is alive.
- EC2 status checks monitor infrastructure health. Route 53 health checks monitor application availability through the public path.
- SNS completes the alerting path by turning alarm state changes into notifications.

## 9. GitHub Actions Deployment Automation with OIDC and SSM

### Scenario

- I wanted automated deployments from GitHub to EC2 without manually SSHing into the server.

### Obstacle

- GitHub hosted runners should not need SSH access to EC2.
- I wanted to avoid long lived AWS access keys in GitHub.
- EC2 needed to receive deployment commands securely.

### Action

- Added SSM support to the Terraform managed EC2 instance.
- Added GitHub Actions OIDC provider and deploy role through Terraform.
- Created `.github/workflows/deploy.yml`.
- Used GitHub Actions to assume the AWS IAM role through OIDC.
- Used AWS Systems Manager to run deployment commands on EC2.
- The deployment pulls latest code, checks requirements, restarts the systemd service, and validates local `/health`.

### Result

- Pushes to `main` can trigger deployment automation.
- GitHub Actions does not SSH into EC2.
- No long lived AWS keys are stored in GitHub.
- The deployment workflow validates service health after restart.

### Troubleshooting

- Confirmed the SSM managed instance was online.
- Confirmed the IAM role trust policy allowed GitHub OIDC.
- Confirmed workflow permissions.
- Confirmed the SSM command succeeded.
- Confirmed local `/health` passed after restart.

### Interview Talking Points

- OIDC is safer than long lived keys because credentials are short lived and tied to the workflow identity.
- SSM avoids opening SSH access to GitHub runners.
- Health validation makes deployment safer because the workflow checks the service after restart.

## 10. ALB and Auto Scaling Exploration

### Scenario

- I explored more production style AWS patterns involving ALB, Target Group, Custom AMI, Launch Template, and Auto Scaling Group.

### Obstacle

- The ALB initially showed target group issues.
- Availability Zone mapping and security group attachment needed troubleshooting.
- The architecture became more complex than the final portfolio path required.

### Action

- Created ALB and Target Group.
- Configured health checks.
- Troubleshot target group `Unused` and `Unhealthy` states.
- Corrected Availability Zone and security group issues.
- Created AMI, Launch Template, and Auto Scaling Group.
- Validated healthy targets.

### Result

- I learned and documented load balancing and Auto Scaling patterns.
- These experiments were preserved in docs as learning notes.
- The final architecture intentionally returned to a simpler Terraform managed single instance deployment for clarity and portfolio focus.

### Troubleshooting

- Checked target group health status.
- Confirmed ALB subnet mappings included the EC2 Availability Zone.
- Confirmed FastAPI listened on `0.0.0.0:8000`.
- Confirmed the EC2 security group allowed traffic from the ALB security group.
- Confirmed `/health` returned 200.

### Interview Talking Points

- The ALB and ASG work was valuable because it showed how load balancing and scaling patterns work in AWS.
- I weighed complexity against project clarity and chose the simpler current architecture for the portfolio version.
- This shows learning without overengineering the final deliverable.

## 11. README and Architecture Diagram Polish

### Scenario

- The project needed to be understandable to recruiters and technical reviewers.

### Obstacle

- A technical project can be strong but hard to review if the README, diagrams, screenshots, and narrative are unclear.
- Older screenshot references and diagrams needed cleanup.

### Action

- Rewrote the README into a portfolio narrative.
- Added dashboard screenshots.
- Added a Data Sources section.
- Cited the neighborhood source.
- Added a cleaner AWS reference style architecture diagram.
- Fixed broken image paths.
- Added checkpoints to the process log.

### Result

- The GitHub repository became clearer and more portfolio ready.
- The README now explains the project, architecture, data sources, deployment, monitoring, limitations, and future improvements.
- The diagram visually communicates the current AWS flow.

### Troubleshooting

- Fixed broken screenshot paths.
- Removed outdated references.
- Resized diagrams for README rendering.
- Confirmed GitHub rendering and clean Git status.

### Interview Talking Points

- Communication and documentation are part of engineering because they make the system easier to review, maintain, and hand off.
- The README was designed for fast review by technical and nontechnical audiences.
- Diagrams help communicate system design faster than text alone.

## High Value Interview Questions and Answer Outlines

### 1. Walk me through this project.

- Main answer: It started as a local FastAPI dashboard for Durham public safety event data and evolved into a Terraform managed AWS deployment with Nginx, monitoring, and automated deployment.
- Key phrases to remember: geospatial analytics, public-facing decision intelligence, FastAPI to AWS, Terraform, Nginx, GitHub Actions, SSM.
- Technical details to mention if asked: Leaflet, Chart.js, census tracts, ACS enrichment, EC2, systemd, Route 53 health check.

### 2. Why did you build it?

- Main answer: I wanted a portfolio project that connected data analysis, geospatial thinking, cloud infrastructure, and deployment automation.
- Key phrases to remember: end to end project, practical cloud engineering, public safety interpretation.
- Technical details to mention if asked: local prototype, AWS deployment, monitoring, CI/CD.

### 3. Why did you use FastAPI?

- Main answer: FastAPI gave me a clean way to serve both dashboard pages and API endpoints from one Python application.
- Key phrases to remember: lightweight, Python friendly, API first, easy health endpoint.
- Technical details to mention if asked: Uvicorn, `/health`, JSON endpoints, templates and static assets.

### 4. Why did you use Nginx?

- Main answer: Nginx provides a standard public web entry point on port `80` while FastAPI runs internally.
- Key phrases to remember: reverse proxy, public entry point, internal app runtime.
- Technical details to mention if asked: `80 -> 127.0.0.1:8000`, Nginx syntax testing, systemd service remains separate.

### 5. Why did you remove public access to port 8000?

- Main answer: Once Nginx handled public traffic, direct public access to FastAPI was unnecessary and less clean.
- Key phrases to remember: reduce exposed surface, internal runtime port, public traffic through Nginx.
- Technical details to mention if asked: Terraform security group changed, `dashboard_internal_app_port = 8000`.

### 6. Why did you use Terraform?

- Main answer: Terraform made the infrastructure reproducible, reviewable, and easier to extend.
- Key phrases to remember: Infrastructure as Code, repeatability, plan before apply.
- Technical details to mention if asked: EC2, security group, IAM, SNS, CloudWatch, Route 53 health check.

### 7. What did Terraform manage?

- Main answer: Terraform manages the EC2 instance, security group, IAM roles, SSM support, GitHub OIDC role, SNS, CloudWatch alarms, and Route 53 health check.
- Key phrases to remember: infrastructure foundation, monitoring, identity, deployment support.
- Technical details to mention if asked: outputs, variables, `user_data`, AMI lifecycle handling.

### 8. What did user_data solve?

- Main answer: `user_data` solved the gap between creating a server and actually configuring it to run the app.
- Key phrases to remember: bootstrap automation, recoverable instance, reduced manual setup.
- Technical details to mention if asked: installs packages, clones repo, creates venv, installs requirements, creates systemd and Nginx config.

### 9. Why GitHub Actions, OIDC, and SSM?

- Main answer: This allowed deployment from GitHub without SSH and without storing long lived AWS keys.
- Key phrases to remember: identity federation, SSM command execution, safer deployment path.
- Technical details to mention if asked: workflow dispatch, push to main, AWS-RunShellScript, local health check.

### 10. Why not SSH from GitHub Actions?

- Main answer: SSH from hosted runners would require opening access and managing keys. SSM avoids that.
- Key phrases to remember: no runner SSH access, no private key in GitHub, AWS managed command channel.
- Technical details to mention if asked: SSM managed instance, IAM role permissions.

### 11. What does CloudWatch monitor?

- Main answer: CloudWatch monitors EC2 CPU, EC2 status checks, and the Route 53 health check metric.
- Key phrases to remember: infrastructure health and application health.
- Technical details to mention if asked: `CPUUtilization`, `StatusCheckFailed`, `HealthCheckStatus`.

### 12. Why Route 53 health checks?

- Main answer: Route 53 checks the public `/health` endpoint through Nginx, so it validates the user-facing application path.
- Key phrases to remember: public endpoint monitoring, application availability.
- Technical details to mention if asked: HTTP check, port `80`, `/health`, CloudWatch alarm.

### 13. What is the difference between EC2 health and application health?

- Main answer: EC2 health tells me whether the instance is healthy. Application health tells me whether the dashboard endpoint is responding.
- Key phrases to remember: server alive is not the same as app healthy.
- Technical details to mention if asked: status checks versus `/health` endpoint.

### 14. What was the hardest problem?

- Main answer: The biggest lesson was that Terraform provisioning alone did not preserve manual app setup after instance replacement.
- Key phrases to remember: instance replacement, lost manual configuration, bootstrap automation.
- Technical details to mention if asked: `user_data`, systemd, Nginx, dependency install.

### 15. What would you improve next?

- Main answer: I would add HTTPS and DNS, improve logging, and add stronger deployment test gates.
- Key phrases to remember: HTTPS, Route 53 DNS, CloudWatch logs, CI/CD validation.
- Technical details to mention if asked: ACM, domain, log forwarding, workflow status notifications.

### 16. Why is the final architecture single instance?

- Main answer: The final version is intentionally a clear portfolio deployment rather than a multi-AZ production system.
- Key phrases to remember: clarity, cost control, focused learning, portfolio ready.
- Technical details to mention if asked: earlier ALB/ASG work was exploratory and documented separately.

### 17. What did you learn from the ALB/ASG work?

- Main answer: I learned target groups, health checks, subnet mapping, launch templates, AMIs, and Auto Scaling basics.
- Key phrases to remember: valuable exploration, not final path.
- Technical details to mention if asked: target health, `Unused`, `Unhealthy`, security group source rules.

### 18. How did you avoid overengineering?

- Main answer: I kept the final architecture aligned with the project goal: a clear, working, monitored portfolio deployment.
- Key phrases to remember: right sized architecture, documented tradeoffs.
- Technical details to mention if asked: single EC2, Nginx, Terraform, SSM deployment, health monitoring.

### 19. How did you think about security?

- Main answer: I reduced public exposure, used IAM roles, avoided long lived GitHub keys, restricted SSH, and kept FastAPI internal.
- Key phrases to remember: least privilege, internal app port, OIDC, SSM, no public 8000.
- Technical details to mention if asked: security group rules, SNS no secrets, `.gitignore` for tfvars and state.

### 20. How would this scale in a more production ready version?

- Main answer: I would add HTTPS, DNS, centralized logs, a load balancer, multiple instances or containers, managed data storage, and stronger CI/CD gates.
- Key phrases to remember: production path, high availability, observability.
- Technical details to mention if asked: ALB, ASG, ECS or App Runner, RDS or S3, CloudWatch dashboard.

## STAR/SOART Interview Stories

### 1. Moving from Local App to AWS Deployment

- Scenario: I had a local FastAPI dashboard and needed to prove it could run as a cloud application.
- Obstacle: Cloud deployment required host setup, dependencies, security groups, network access, and endpoint validation.
- Action: I launched EC2, installed dependencies, ran Uvicorn, opened the required access, and tested key routes.
- Result: The dashboard moved from local prototype to a working AWS hosted app.
- Troubleshooting: I used `curl`, checked binding to `0.0.0.0`, verified security groups, and tested the browser path.

### 2. Hardening the App Behind Nginx

- Scenario: The app was reachable directly on FastAPI port `8000`, but I wanted a cleaner public access pattern.
- Obstacle: Direct public app port exposure was not the right long term pattern.
- Action: I configured Nginx on port `80`, proxied to `127.0.0.1:8000`, and removed public inbound access to port `8000`.
- Result: Public users now reach Nginx, while FastAPI stays internal.
- Troubleshooting: I tested `sudo nginx -t`, checked Nginx service status, and validated public `/health`.

### 3. Automating Deployment with GitHub Actions, OIDC, and SSM

- Scenario: I wanted deployment from GitHub without manual SSH.
- Obstacle: GitHub runners should not need SSH access or long lived AWS keys.
- Action: I added SSM support, created a GitHub OIDC deploy role, and built a GitHub Actions workflow that sends SSM commands to EC2.
- Result: Pushes to `main` can deploy, restart the service, and validate local health.
- Troubleshooting: I checked SSM managed instance status, IAM trust policy, workflow permissions, command output, and `/health`.

### 4. Adding Monitoring and Alerting

- Scenario: The dashboard needed operational visibility after deployment.
- Obstacle: EC2 can be healthy while the application is down, so infrastructure monitoring was not enough.
- Action: I added EC2 CloudWatch alarms, SNS email alerts, a Route 53 health check for `/health`, and a CloudWatch alarm on `HealthCheckStatus`.
- Result: The project monitors both infrastructure health and application endpoint health.
- Troubleshooting: I confirmed metrics, alarm states, SNS subscription, Route 53 health check status, and the public health response.

### 5. Choosing a Simpler Final Architecture After ALB/ASG Exploration

- Scenario: I explored ALB, Target Group, AMI, Launch Template, and Auto Scaling patterns.
- Obstacle: That architecture added complexity beyond what the portfolio version needed.
- Action: I documented the learning, validated the concepts, and chose a simpler Terraform managed single instance design for the final path.
- Result: The final project stayed clear, explainable, and aligned with the portfolio goal.
- Troubleshooting: I worked through target health, subnet mapping, security group attachment, and health check behavior.

## Troubleshooting Study Sheet

### App not reachable in browser

- Symptom: Browser cannot load the dashboard.
- Likely cause: App not running, Nginx down, security group issue, or wrong URL.
- Checks: `systemctl status`, `curl /health`, Nginx status, security group inbound rules.
- Fix: Restart the service, restart Nginx, correct security group rules, or use the correct public URL.
- Interview takeaway: Browser failures can be app, host, proxy, or network problems.

### FastAPI running locally but not publicly reachable

- Symptom: `curl localhost:8000/health` works, but browser access fails.
- Likely cause: Uvicorn binding, Nginx config, security group, or public path issue.
- Checks: Confirm binding, test Nginx proxy, check port `80`, inspect security group.
- Fix: Bind internally behind Nginx and route public traffic through port `80`.
- Interview takeaway: Local service health and public reachability are different checks.

### Security group blocking access

- Symptom: App runs but external traffic times out.
- Likely cause: Missing inbound rule or wrong port.
- Checks: Review inbound rules for SSH, HTTP, and removed public `8000`.
- Fix: Allow public HTTP on `80`, restrict SSH, keep FastAPI port internal.
- Interview takeaway: Security groups are part of the application access path.

### Nginx misconfiguration

- Symptom: Public endpoint gives bad gateway or does not proxy correctly.
- Likely cause: Wrong proxy target, syntax issue, or Nginx not restarted.
- Checks: `sudo nginx -t`, Nginx logs, service status, local FastAPI health.
- Fix: Correct config, restart Nginx, confirm `127.0.0.1:8000`.
- Interview takeaway: Test the proxy separately from the app.

### systemd service not running

- Symptom: `/health` fails and Uvicorn is not active.
- Likely cause: Bad service file, missing dependency, wrong working directory, or failed restart.
- Checks: `systemctl status`, `journalctl`, virtual environment path.
- Fix: Correct service config, install missing dependencies, restart service.
- Interview takeaway: `systemd` logs are essential for deployment debugging.

### Missing Python dependency

- Symptom: Service fails after deploy with import error.
- Likely cause: `requirements.txt` missing a runtime package.
- Checks: `journalctl`, manual import test, requirements install output.
- Fix: Add dependency to `requirements.txt`, reinstall, restart service.
- Interview takeaway: Deployment reveals runtime dependency gaps that local environments can hide.

### Terraform instance replacement removed manual setup

- Symptom: New EC2 instance exists but app setup is gone.
- Likely cause: Manual configuration was not automated.
- Checks: Instance replacement plan, package state, repo path, service files.
- Fix: Add `user_data` bootstrap script to recreate runtime automatically.
- Interview takeaway: Infrastructure provisioning and application bootstrapping are different responsibilities.

### SNS email confirmation went to spam

- Symptom: SNS topic exists but alerts do not arrive.
- Likely cause: Email subscription not confirmed.
- Checks: SNS subscription status and spam folder.
- Fix: Confirm the AWS SNS email subscription.
- Interview takeaway: Alerting is not complete until the notification endpoint is confirmed.

### Route 53 health check issues

- Symptom: Health check not `OK`.
- Likely cause: Public `/health` not reachable, wrong path, wrong port, or app unhealthy.
- Checks: `curl http://public-ip/health`, Route 53 target, CloudWatch metric.
- Fix: Correct target path or port, fix Nginx or app health.
- Interview takeaway: Route 53 health checks validate the public application path.

### GitHub Actions deployment failure

- Symptom: Workflow fails before or during deployment.
- Likely cause: OIDC trust issue, permission issue, SSM command failure, or app restart failure.
- Checks: GitHub logs, AWS role trust, workflow permissions, SSM command output.
- Fix: Correct IAM permissions, workflow config, or EC2 deployment commands.
- Interview takeaway: CI/CD failures should be debugged step by step through identity, command execution, and app validation.

### SSM managed instance not online

- Symptom: GitHub Actions cannot send commands to EC2.
- Likely cause: Missing IAM instance profile, SSM agent issue, or instance not connected.
- Checks: SSM Fleet Manager, IAM role attachment, EC2 status.
- Fix: Attach SSM role, confirm agent and instance profile, recreate if needed.
- Interview takeaway: SSM deployment depends on EC2 identity and managed instance status.

### Broken README image paths

- Symptom: GitHub README does not render screenshots or diagrams.
- Likely cause: Wrong filename, missing file, or bad relative path.
- Checks: `ls`, GitHub file browser, Markdown image syntax.
- Fix: Update image paths to committed files.
- Interview takeaway: Documentation quality affects how quickly reviewers understand the project.

### Git ignored artifacts folder

- Symptom: Generated screenshots or diagrams do not appear in Git.
- Likely cause: Ignore pattern excludes artifacts.
- Checks: `git status`, `.gitignore`, `git check-ignore`.
- Fix: Adjust ignore rules or explicitly track intended portfolio artifacts.
- Interview takeaway: Portfolio assets need to be versioned if the README depends on them.

## Key Technical Concepts to Review

- FastAPI: Python web framework used to serve dashboard routes and API endpoints.
- Uvicorn: ASGI server that runs the FastAPI app.
- Nginx reverse proxy: Public web entry point that forwards traffic to the internal app.
- systemd: Linux service manager used to keep the app running.
- EC2: AWS virtual server hosting the dashboard.
- Security groups: AWS network firewall rules controlling inbound and outbound traffic.
- Terraform: Infrastructure as Code tool used to manage AWS resources.
- Terraform state: Tracks managed infrastructure and should be protected.
- user_data: EC2 bootstrap script mechanism used to configure the server on launch.
- IAM role: AWS identity used to grant permissions without hardcoded credentials.
- OIDC: Identity federation method used by GitHub Actions to assume an AWS role.
- AWS Systems Manager: AWS service used to send deployment commands to EC2 without SSH from GitHub.
- GitHub Actions: CI/CD automation platform used to deploy on push to `main`.
- CloudWatch alarms: AWS alarms used for EC2 and health check monitoring.
- SNS: Notification service used for email alerting.
- Route 53 health checks: Public HTTP checks against `/health` on port `80`.
- Leaflet: JavaScript mapping library used for the interactive dashboard map.
- Chart.js: JavaScript charting library used for dashboard visualizations.
- Census tracts: Primary statistical geography for ACS joins and normalized metrics.
- ACS enrichment: Demographic context added to tract-level analysis.
- Choropleth map: Thematic map showing rates, percentages, or contextual indicators by tract.
- EPSG coordinate conversion: Projection conversion needed to display local coordinates on a web map.
- Health endpoint: Simple endpoint that confirms the application is responding.

## One Minute Project Pitch

The Durham Risk Intelligence Dashboard is a cloud deployed geospatial analytics project that explores Durham public safety event data through an interactive FastAPI dashboard. It combines Leaflet maps, KPI summaries, charts, census tract analysis, ACS demographic enrichment, and neighborhood context. I started with a local dashboard, then deployed it to AWS on EC2 behind Nginx, with FastAPI running internally through systemd. I later added Terraform for infrastructure, CloudWatch and SNS for monitoring, Route 53 health checks for the public `/health` endpoint, and GitHub Actions deployment automation using OIDC and AWS Systems Manager. The project is designed as a public-facing preparedness and decision intelligence prototype, not an enforcement prediction tool.

## Two Minute Technical Walkthrough

- I started by building a local FastAPI dashboard with routes for the homepage, dashboard, health check, summary metrics, and records.
- I expanded it into a geospatial dashboard using Leaflet, Chart.js, Durham boundaries, census tracts, neighborhood context, and ACS enriched tract data.
- Census tracts became the main analytical geography because they support demographic joins and normalized rates.
- After the local dashboard worked, I deployed it to EC2 and used Uvicorn to run the FastAPI app.
- I added `systemd` so the app would keep running after SSH sessions ended or the instance restarted.
- I added Nginx as the public reverse proxy on port `80`, while FastAPI stayed internal on localhost port `8000`.
- I introduced Terraform to manage EC2, security groups, IAM roles, monitoring resources, SSM support, and outputs.
- I added a bootstrap script through Terraform `user_data` so a new EC2 instance could recreate the app runtime automatically.
- I added CloudWatch alarms for EC2 health and Route 53 health checks for the public `/health` endpoint.
- I added SNS so alarm notifications had an email alert path.
- I automated deployment with GitHub Actions, OIDC, and AWS Systems Manager so GitHub can deploy without SSH and without long lived AWS keys.
- The current limitation is that this is a portfolio ready single instance deployment, not a multi-AZ production system.
- Next improvements would be HTTPS, Route 53 DNS, stronger logging, and broader deployment test gates.

## Short Answers for Recruiters

### What did you build?

- A cloud deployed geospatial dashboard for exploring Durham public safety event data with maps, charts, KPIs, and demographic context.

### What cloud services did you use?

- EC2, IAM, Systems Manager, CloudWatch, SNS, Route 53 health checks, and Terraform managed AWS infrastructure.

### What was automated?

- EC2 bootstrap setup through `user_data` and application deployment through GitHub Actions, OIDC, and SSM.

### What was monitored?

- EC2 CPU, EC2 status checks, and the public `/health` endpoint through Route 53 and CloudWatch.

### What security improvements did you make?

- Removed public access to FastAPI port `8000`, routed public traffic through Nginx on port `80`, restricted SSH, used IAM roles, used OIDC instead of long lived GitHub keys, and deployed through SSM instead of SSH from GitHub runners.

### What would you do next?

- Add HTTPS and DNS, improve logs and dashboards, add stronger CI/CD checks, and consider a more available architecture if the project needed production scale.

## Final Review Checklist

- [ ] Can I explain the current architecture?
- [ ] Can I explain why Nginx is used?
- [ ] Can I explain why FastAPI is internal?
- [ ] Can I explain Terraform's role?
- [ ] Can I explain GitHub Actions, OIDC, and SSM?
- [ ] Can I explain monitoring and alerting?
- [ ] Can I explain why ALB/ASG are not the final path?
- [ ] Can I explain what I would improve next?
- [ ] Can I explain the project in one minute?
