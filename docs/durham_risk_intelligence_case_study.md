# Durham Risk Intelligence Dashboard — Portfolio Case Study

## Overview

The Durham Risk Intelligence Dashboard is an interactive tool built to make Durham city and county arrest data easier to explore. I chose this dataset because it is publicly available, but it comes as a large CSV file that is not easy to search, map, or understand on its own.

The dashboard brings the data together through maps, census tracts, summary measures, and charts. It also combines arrest data with U.S. Census and ACS information, such as income, poverty, age, education, household size, and vacancy. This gives users a better view of the places where activity is being recorded instead of looking at arrest records by themselves.

I also included exploratory analysis methods, including machine learning techniques and spatial analysis, to add more depth to the dashboard. The tool is meant to help people explore and better understand the data. It is not meant to predict behavior or direct enforcement activity.

## Problem and Approach

The issue was not that the data was unavailable. The issue was that it was difficult to use in its original form. Rows in a spreadsheet do not make it easy to see whether arrest activity is increasing, decreasing, or staying about the same over time. They also make it difficult to compare districts, see where activity is being recorded, or understand how patterns vary across the city.

I started by cleaning and organizing the arrest data so it could be viewed by time, district, offense type, and location. I then connected the records to census tracts, neighborhoods, district boundaries, and city geography. Adding Census and ACS information gave users more context when comparing areas.

The result is an interactive dashboard where users can work through maps, charts, filters, and tract level measures instead of relying only on static tables or maps.

## Data and Analytics

The dashboard focuses on Durham arrest data. Its main measures include total arrests, arrests per 1,000 residents, felony share, common offense types, and district activity. It also includes selected Census and ACS information to help users compare places in a more complete way.

A Local Moran’s I, or LISA, layer gives users another way to explore the map. It highlights hot spots, cold spots, and areas that look different from nearby tracts. In simple terms, it helps show where nearby areas have similar or different patterns of recorded arrest activity.

This is an exploratory tool. It does not predict future behavior, assign risk scores, or identify dangerous places. The Census and ACS measures are included to provide context. They should not be treated as simple explanations for arrest activity or as proof that a community characteristic causes it.

## Technical Architecture and Outcome

The application uses FastAPI for the backend and Leaflet for the map interface. It serves processed geographic data through API endpoints and displays it through map layers, charts, popups, and legends.

The dashboard runs on AWS through a single EC2 instance. Nginx handles public web traffic and sends it to the FastAPI application, which runs under systemd. Terraform manages the infrastructure, while GitHub Actions, AWS Systems Manager, CloudWatch, SNS, and Route 53 health checks support deployment, monitoring, and application health checks.

Recent updates improved the experience by adding clearer LISA tooltips, showing the selected map metric in popups, making map controls smoother, and compressing large data responses so the dashboard loads faster.

This project turned raw public data into a working, cloud deployed application that combines geospatial analysis, interactive visualization, public sector data, and AWS infrastructure.
