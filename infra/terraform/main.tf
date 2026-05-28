# Durham Risk Intelligence Dashboard
# Terraform infrastructure configuration

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "Terraform"
  }

  name_prefix = "${var.project_name}-${var.environment}"

  github_repo_full_name = "${var.github_repo_owner}/${var.github_repo_name}"
  github_branch_subject = "repo:${local.github_repo_full_name}:ref:refs/heads/${var.github_deploy_branch}"
}

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_security_group" "dashboard_ec2" {
  name        = "${local.name_prefix}-ec2-sg"
  description = "Security group for the Durham Risk Intelligence Dashboard EC2 instance"

  ingress {
    description = "Allow SSH from approved IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  ingress {
    description = "Allow HTTP traffic to Nginx reverse proxy"
    from_port   = var.http_port
    to_port     = var.http_port
    protocol    = "tcp"
    cidr_blocks = [var.allowed_app_cidr]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ec2-sg"
  })
}

resource "aws_iam_role" "dashboard_ec2_ssm_role" {
  name = "${local.name_prefix}-ec2-ssm-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ec2-ssm-role"
  })
}

resource "aws_iam_role_policy_attachment" "dashboard_ec2_ssm_core" {
  role       = aws_iam_role.dashboard_ec2_ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "dashboard_ec2_ssm_profile" {
  name = "${local.name_prefix}-ec2-ssm-profile"
  role = aws_iam_role.dashboard_ec2_ssm_role.name

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ec2-ssm-profile"
  })
}

resource "aws_iam_openid_connect_provider" "github_actions" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com"
  ]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-github-actions-oidc"
  })
}

resource "aws_iam_role" "github_actions_deploy_role" {
  name = "${local.name_prefix}-github-actions-deploy-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github_actions.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
            "token.actions.githubusercontent.com:sub" = local.github_branch_subject
          }
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-github-actions-deploy-role"
  })
}

resource "aws_iam_role_policy" "github_actions_ssm_deploy_policy" {
  name = "${local.name_prefix}-github-actions-ssm-deploy-policy"
  role = aws_iam_role.github_actions_deploy_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowSendCommandToDashboardInstance"
        Effect = "Allow"
        Action = [
          "ssm:SendCommand"
        ]
        Resource = [
          aws_instance.dashboard.arn,
          "arn:aws:ssm:${var.aws_region}::document/AWS-RunShellScript"
        ]
      },
      {
        Sid    = "AllowReadCommandResults"
        Effect = "Allow"
        Action = [
          "ssm:GetCommandInvocation",
          "ssm:ListCommandInvocations",
          "ssm:ListCommands"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_instance" "dashboard" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.dashboard_ec2.id]
  iam_instance_profile   = aws_iam_instance_profile.dashboard_ec2_ssm_profile.name

  user_data                   = file("${path.module}/../scripts/ec2_bootstrap.sh")
  user_data_replace_on_change = true

  lifecycle {
    ignore_changes = [
      ami
    ]
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ec2"
  })
}

resource "aws_sns_topic" "dashboard_alerts" {
  name = "${local.name_prefix}-alerts"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-alerts"
  })
}

resource "aws_sns_topic_subscription" "dashboard_alert_email" {
  count     = var.alert_email == "" ? 0 : 1
  topic_arn = aws_sns_topic.dashboard_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_cloudwatch_metric_alarm" "dashboard_status_check_failed" {
  alarm_name          = "${local.name_prefix}-ec2-status-check-failed"
  alarm_description   = "Triggers when the Terraform managed dashboard EC2 instance fails a status check."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "StatusCheckFailed"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Maximum"
  threshold           = 1
  treat_missing_data  = "notBreaching"

  dimensions = {
    InstanceId = aws_instance.dashboard.id
  }

  alarm_actions = [aws_sns_topic.dashboard_alerts.arn]
  ok_actions    = [aws_sns_topic.dashboard_alerts.arn]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ec2-status-check-failed"
  })
}

resource "aws_cloudwatch_metric_alarm" "dashboard_high_cpu" {
  alarm_name          = "${local.name_prefix}-ec2-high-cpu"
  alarm_description   = "Triggers when the Terraform managed dashboard EC2 instance has sustained high CPU utilization."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = var.cpu_alarm_evaluation_periods
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = var.cpu_alarm_period
  statistic           = "Average"
  threshold           = var.cpu_alarm_threshold
  treat_missing_data  = "notBreaching"

  dimensions = {
    InstanceId = aws_instance.dashboard.id
  }

  alarm_actions = [aws_sns_topic.dashboard_alerts.arn]
  ok_actions    = [aws_sns_topic.dashboard_alerts.arn]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ec2-high-cpu"
  })
}

resource "aws_route53_health_check" "dashboard_app_health" {
  ip_address        = aws_instance.dashboard.public_ip
  port              = var.http_port
  type              = "HTTP"
  resource_path     = var.app_health_check_path
  failure_threshold = var.app_health_check_failure_threshold
  request_interval  = var.app_health_check_request_interval

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-app-health-check"
  })
}

resource "aws_cloudwatch_metric_alarm" "dashboard_app_health_failed" {
  alarm_name          = "${local.name_prefix}-app-health-check-failed"
  alarm_description   = "Triggers when the dashboard application health endpoint fails Route 53 health checks."
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  period              = 60
  statistic           = "Minimum"
  threshold           = 1
  treat_missing_data  = "breaching"

  dimensions = {
    HealthCheckId = aws_route53_health_check.dashboard_app_health.id
  }

  alarm_actions = [aws_sns_topic.dashboard_alerts.arn]
  ok_actions    = [aws_sns_topic.dashboard_alerts.arn]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-app-health-check-failed"
  })
}