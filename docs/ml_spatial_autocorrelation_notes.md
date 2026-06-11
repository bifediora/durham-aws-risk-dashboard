# Spatial Autocorrelation Notes: Moran's I and Local Moran's I

## Purpose

This analysis evaluates whether tract-level arrest activity is spatially clustered across Durham census tracts.

This is different from the ML classification models. ML classification evaluates whether contextual indicators classify elevated arrest activity. Moran's I evaluates whether observed arrest rates are spatially autocorrelated across neighboring tracts.

## Input Data

- Input file: `data/processed/durham_arrests_tract_enriched.geojson`
- Analysis variable: `arrests_per_1000_population`
- Number of tracts: 68
- Spatial weights: Queen contiguity
- Weights transform: row-standardized
- Islands: none
- Permutations: 999

This analysis uses all Durham census tracts in the input GeoJSON, not only tracts flagged as elevated.

## Global Moran's I

- Moran's I: 0.2443
- Expected I: -0.0149
- z_sim: 6.2846
- p_sim: 0.001

Global Moran's I indicates statistically significant positive spatial autocorrelation in tract-level arrest rates.

The positive Moran's I indicates positive spatial autocorrelation. Nearby tracts tend to have more similar arrest-rate values than expected under spatial randomness. The permutation p-value indicates that the global spatial pattern is statistically significant.

## Local Moran's I / LISA

Local Moran's I identifies specific local spatial association patterns.

Cluster meanings:

- High-High: high arrest-rate tract near other high arrest-rate tracts
- Low-Low: low arrest-rate tract near other low arrest-rate tracts
- High-Low: high arrest-rate tract near lower-rate neighboring tracts
- Low-High: low arrest-rate tract near higher-rate neighboring tracts
- Not significant: no statistically significant local spatial association at the selected threshold

At `p <= 0.05`:

- High-High: 6
- Low-Low: 4
- High-Low: 1
- Low-High: 0
- Not significant: 57

At `p <= 0.10`:

- High-High: 7
- Low-High: 1
- Low-Low: 10
- High-Low: 2
- Not significant: 48

## Interpretation

The global result suggests countywide spatial clustering in tract-level arrest rates. The local result identifies a small set of statistically significant high-rate and low-rate clusters.

High-High clusters indicate localized areas where high arrest-rate tracts are near other high arrest-rate tracts. Low-Low clusters indicate localized areas where low arrest-rate tracts are near other low arrest-rate tracts.

The High-Low tract is a spatial outlier, meaning a relatively high-rate tract near lower-rate neighboring tracts.

These findings are consistent with an exploratory spatial pattern. They do not imply causation.

## Relationship to ML Models

Logistic regression, random forest, and PCA logistic regression are classification models. Moran's I / LISA is a spatial statistical analysis.

The spatial autocorrelation analysis complements the ML models by evaluating whether observed arrest rates are geographically clustered. This strengthens the project's geospatial analytics narrative.

## Limitations

- Moran's I depends on the chosen spatial weights definition.
- Queen contiguity captures shared borders/vertices but not travel time, patrol areas, road networks, or social boundaries.
- Results are sensitive to tract boundaries and the modifiable areal unit problem.
- Arrest data reflects enforcement and administrative activity, not direct harm.
- Local cluster results should be interpreted as exploratory.
- Statistical significance does not explain why clustering occurs.
- This analysis should not be used for individual-level inference or enforcement targeting.

## Responsible Use

This spatial autocorrelation analysis evaluates whether tract-level arrest activity is spatially clustered across census tracts. It is an exploratory spatial analysis, not an individual-level risk model, and should not be interpreted as predicting criminal behavior.

## Portfolio Talking Point

I extended the dashboard's offline analytics layer with Global Moran's I and Local Moran's I to evaluate whether tract-level arrest rates were spatially autocorrelated. The analysis found statistically significant positive global spatial autocorrelation and identified localized High-High, Low-Low, and High-Low spatial association patterns. I treated the results as exploratory spatial evidence rather than operational predictions.
