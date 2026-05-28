# Dashboard MVP Summary

## Overview

The Durham Risk Intelligence Dashboard is a FastAPI based geospatial analytics application designed to support public-facing risk and resilience interpretation. It combines event data, municipal geography, census tract analytics, ACS demographic context, and neighborhood reference geography.

The dashboard should be understood as a preparedness and decision intelligence prototype. It is not an enforcement prediction tool.

## Major Capabilities

- Interactive analytical dashboard served through FastAPI.
- Leaflet map with point, cluster, density, and choropleth visualization modes.
- Chart.js summaries for district, severity, top offenses, and temporal activity.
- KPI cards for total arrests, hotspot areas, felony share, and recent activity trend.
- Unified Temporal Activity Explorer replacing separate month, weekday, and hour charts.
- Start date and end date filtering intended to update the full dashboard.
- Selected records table for reviewing filtered event records.
- Refined tract interaction behavior, including popup close clearing tract selection.

## Data Layers

- Arrest event records.
- Shooting event records.
- Durham municipal boundary.
- Durham County and administrative reference boundaries.
- Census tracts intersecting the Durham municipal boundary.
- ACS 5-year demographic indicators.
- Durham neighborhood context geography.

## Analytical Layers

Census tracts are the primary statistical geography. Full tract geometries are preserved rather than clipped to city limits so ACS joins and tract-level indicators remain consistent.

Tract-level enrichment outputs combine:

- ACS demographic indicators
- Aggregated arrest statistics
- Aggregated shooting statistics
- Normalized event rates
- Percentage-based contextual indicators
- Neighborhood overlap context

Population-normalized rates and percentage-based indicators are prioritized for tract comparison because they support clearer public-facing interpretation than raw counts alone.

## User Interaction Features

- Map mode switching between event points, clusters, density, and choropleth views.
- Choropleth metric dropdown for tract-level demographic, event, and contextual indicators.
- Dynamic choropleth legends with natural breaks and a sequential color scheme.
- Tract popups with neighborhood context and selected demographic/context metric values.
- Popup close behavior that clears tract selection.
- Spatial selection tools for exploratory filtering.
- Active query chips and selected records feedback.

## Outputs Generated

Key processed outputs include:

- `data/processed/arrests_with_tract_join.csv`
- `data/processed/durham_arrests_tract_enriched.csv`
- `data/processed/durham_arrests_tract_enriched.geojson`
- `data/processed/durham_shootings_tract_enriched.csv`
- `data/processed/durham_shootings_tract_enriched.geojson`
- `data/processed/durham_choropleth_metric_catalog.json`
- `data/processed/durham_neighborhoods_projected.geojson`
- `data/processed/durham_neighborhoods_web.geojson`
- `data/processed/durham_neighborhoods_inspection_summary.txt`

## Feature Freeze Status

The dashboard MVP is feature frozen and tagged in GitHub as:

```text
dashboard-mvp-v1
```

This tag is the stable checkpoint before beginning the next infrastructure phase. Future work should avoid adding new dashboard features unless there is a specific reason to reopen MVP scope.

## Next Phase

Phase 6: Infrastructure as Code with Terraform

The next phase will focus on repeatable AWS infrastructure for hosting the dashboard. Planned Terraform work includes:

- Create a `terraform/` directory.
- Add Terraform provider configuration.
- Provision EC2 infrastructure.
- Configure security groups.
- Reference or configure SSH/key access.
- Add project tagging.
- Add outputs for public IP and app URL.
- Later extend to monitoring resources such as CloudWatch alarms and SNS notifications.

The first Terraform version should remain simple, readable, and reproducible.

## Phase 6 Operations Update

The Terraform managed AWS deployment now includes EC2 infrastructure, security group hardening, Nginx public access on port `80`, internal FastAPI runtime on port `8000`, SNS alerting, CloudWatch infrastructure alarms, Route 53 application health monitoring, SSM deployment command support, and GitHub Actions deployment automation.

Current monitoring distinguishes between:

- EC2-level health: CPU utilization and EC2 status checks.
- Application-level health: Route 53 HTTP health check against `/health` on port `80`, with CloudWatch alarm evaluation on `HealthCheckStatus`.

Alert notifications reuse the existing SNS topic. Terraform also includes an EC2 `ami` lifecycle ignore rule to avoid unintended instance replacement when the latest Amazon Linux 2023 AMI changes.

Deployment automation now uses GitHub Actions with AWS OIDC and SSM. The workflow does not SSH into EC2 and does not require long-lived AWS access keys in GitHub. On push to `main`, the workflow assumes the Terraform managed deploy role, sends an SSM command to EC2, pulls the latest code, restarts the FastAPI `systemd` service, and validates the local `/health` endpoint.
