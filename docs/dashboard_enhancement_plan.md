# Dashboard Enhancement Plan

## Pivot Reason

The current Durham Risk Intelligence Dashboard successfully demonstrates AWS deployment readiness, but the dashboard itself has limited analytical and geospatial functionality.

Before continuing to Application Load Balancer, Auto Scaling, Terraform, and CI/CD work, the dashboard should be improved so it demonstrates real portfolio value.

## Enhancement Goal

Build a stylish, functional geospatial dashboard that analyzes Durham arrest activity by:

- place
- time
- offense type
- operational geography
- severity
- demographic attributes

## Current Dashboard Limitations

The current dashboard only provides:

- total sample records
- felony record count
- misdemeanor record count
- top district
- top arrest type
- most common offense description
- basic JSON record preview

This is useful for AWS deployment testing, but not enough for a polished portfolio project.

## Planned Dashboard Improvements

### 1. Stylish User Interface

Improve the dashboard layout with:

- modern page header
- summary metric cards
- clear section spacing
- styled tables
- readable typography
- dashboard grid layout
- responsive design
- professional color palette

### 2. Geospatial Functionality

Add real geospatial functionality using arrest coordinates.

Planned features:

- interactive map using `X` and `Y`
- arrest points displayed on the map
- popup details for each arrest point
- district or beat based summaries
- tract based summaries
- future hotspot or clustering layer

### 3. Time Based Analytics

Add charts and summaries for:

- arrests by hour
- arrests by day of week
- arrests by month
- peak activity windows

### 4. Offense and Severity Analytics

Add breakdowns for:

- top offense descriptions
- felony vs misdemeanor records
- arrest type distribution
- UCR code distribution

### 5. Operational Geography Analytics

Add summaries for:

- district
- beat
- tract
- top arrest locations

### 6. API Expansion

Add additional JSON endpoints to support the dashboard:

| Endpoint | Purpose |
|---|---|
| `/api/summary` | Current summary metrics |
| `/api/records` | Record preview |
| `/api/map-points` | Coordinates and popup data for map |
| `/api/by-district` | Arrest counts by district |
| `/api/by-beat` | Arrest counts by beat |
| `/api/by-hour` | Arrest counts by hour |
| `/api/by-day` | Arrest counts by day of week |
| `/api/top-offenses` | Most common offense descriptions |

### 7. Frontend Libraries

Use lightweight frontend libraries:

| Library | Purpose |
|---|---|
| Leaflet.js | Interactive map |
| Chart.js | Dashboard charts |
| Custom CSS | Styling and layout |
| Jinja2 | HTML templates rendered by FastAPI |

## Recommended Next Technical Direction

Refactor the app from inline HTML responses to template based rendering.

New structure:

```text
durham-aws-risk-dashboard/
  app/
    main.py
    templates/
      dashboard.html
      index.html
    static/
      css/
        styles.css
      js/
        dashboard.js
  data/
    sample_arrests.csv
  docs/
  scripts/
