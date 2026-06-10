# Model Card: Logistic Regression Baseline for Tract-Level Arrest Activity

## Model Overview

This is a baseline logistic regression model for the Durham Risk Intelligence Dashboard ML Phase 1 work. It classifies census tracts into elevated and non-elevated arrest activity groups.

The unit of analysis is the census tract. The model is part of an exploratory machine learning extension to the dashboard and is intended to support explainable tract-level analysis before any dashboard integration.

## Intended Use

This model is intended for analytical review, portfolio demonstration, and decision-support exploration. It shows how tract-level contextual features can be used in an explainable ML workflow.

The model is intended to support interpretation of tract-level arrest activity patterns, not operational enforcement decisions.

## Not Intended For

- Not crime prediction.
- Not individual-level risk scoring.
- Not a prediction of future criminal behavior.
- Not a tool for enforcement targeting.
- Not causal evidence about demographic groups or neighborhoods.

## Target Definition

Target column:

```text
elevated_arrest_activity_flag
```

Target definition:

- `1` = census tract is in the top 25 percent of tracts by arrests per 1,000 residents.
- `0` = all other census tracts.

The threshold is derived from `arrests_per_1000_population`. The `arrests_per_1000_population` column is excluded from model features to avoid direct leakage from the target definition.

## Input Data

Input dataset:

```text
ml/outputs/ml_tract_dataset.csv
```

Source dataset used to build the ML dataset:

```text
data/processed/durham_arrests_tract_enriched.csv
```

The dataset contains 68 census tracts. The dashboard and ML layer should be treated as arrest-focused.

## Feature Design

The model uses numeric tract-level features after excluding direct leakage, identifier, geometry/name, and text/categorical label fields.

Feature groups include:

- ACS demographic and socioeconomic context.
- Housing and vacancy indicators.
- Education indicators.
- Population density.
- Neighborhood overlap count.
- Arrest-pattern share/context features such as weekend share, evening/night share, night share, felony share, and misdemeanor share.

Raw arrest count and direct rate variables were excluded to reduce leakage and avoid allowing the model to learn direct proxies for the target.

## Excluded Leakage / Identifier Columns

Excluded columns from the current training run include:

- `GEOID`
- `NAME`
- `arrest_activity_share`
- `arrest_evening_night_events`
- `arrest_night_events`
- `arrest_weekend_events`
- `arrests_density_per_sq_mi`
- `arrests_per_1000_population`
- `county`
- `elevated_arrest_activity_flag`
- `felony_arrests`
- `misdemeanor_arrests`
- `most_common_arrest_type`
- `most_common_offense`
- `primary_neighborhood`
- `secondary_neighborhoods`
- `state`
- `total_arrests`
- `tract`
- `tract_geoid`
- `tract_name`

These exclusions cover direct target/leakage variables, raw arrest-volume fields, tract identifiers, and text/categorical labels.

## Model Details

- Algorithm: Logistic Regression.
- Preprocessing: median imputation and standard scaling.
- Train/test split: stratified 70/30 split.
- Random state: `42`.
- Class weighting: `balanced`.

Output artifacts:

- `ml/outputs/logistic_regression_metrics.json`
- `ml/outputs/logistic_regression_coefficients.csv`
- `ml/outputs/logistic_regression_predictions.csv`
- `ml/models/logistic_regression_model.joblib`

## Evaluation Summary

Current evaluation values from `ml/outputs/logistic_regression_metrics.json`:

| Metric | Value |
|---|---:|
| Accuracy | 0.7619 |
| Precision | 0.5000 |
| Recall | 1.0000 |
| F1 | 0.6667 |
| ROC AUC | 0.9875 |

Confusion matrix:

```text
[[11, 5],
 [ 0, 5]]
```

Training and test split:

- Train rows: 47
- Test rows: 21

Class counts:

- Non-elevated tracts (`0`): 51
- Elevated tracts (`1`): 17

Recall is high, meaning the model identified all elevated tracts in the held-out test split. Precision is lower, meaning some non-elevated tracts were classified as elevated.

Because the dataset is small, metrics should be interpreted cautiously. The high ROC AUC should not be overclaimed.

## Interpretation

Logistic regression coefficients show associations after preprocessing and standard scaling. They do not imply causation.

Demographic variables require careful interpretation and should not be used to stigmatize communities or imply individual-level risk. Arrest data reflects enforcement and administrative activity, not direct harm.

## Limitations

- Small sample size: 68 census tracts.
- Single geography: Durham County / Durham-area tract context.
- Arrest data is not equivalent to crime harm.
- Arrest data may reflect enforcement patterns, reporting practices, administrative processes, and spatial policing activity.
- Model results may not generalize to other cities or time periods.
- The model should not be used as an operational directive.
- The model has not yet been validated using repeated cross-validation or external validation.

## Responsible Use

Results should support transparent analytical review. Outputs should be interpreted as contextual indicators.

The model should not stigmatize neighborhoods or demographic groups. Any public-facing use should include plain-language caveats. Further validation is required before dashboard integration.

## Future Improvements

- Add cross-validation.
- Compare with random forest classifier.
- Add a reduced feature set to improve interpretability.
- Add temporal validation if future time-sliced data is created.
- Add tract-month count modeling with Poisson or negative binomial regression if appropriate.
- Add model monitoring / periodic refresh only after the data refresh process is formalized.

## Portfolio Talking Point

I built a reproducible baseline ML workflow that creates a tract-level dataset, defines an elevated arrest activity target, excludes direct leakage variables, trains an explainable logistic regression model, exports metrics and coefficients, and documents limitations through a model card and exploration notebook.
