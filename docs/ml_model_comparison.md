# ML Model Comparison: Logistic Regression vs Random Forest

## Purpose

This document compares two baseline tract-level models for classifying elevated arrest activity:

- Logistic Regression
- Random Forest Classifier

Both models are exploratory and are part of an offline ML extension to the Durham Risk Intelligence Dashboard. They are intended for model comparison, interpretation, and responsible decision-support exploration before any dashboard integration.

## Modeling Objective

The modeling target is `elevated_arrest_activity_flag`.

- `1` = tract is in the top 25 percent by arrests per 1,000 residents
- `0` = all other tracts
- Unit of analysis: census tract
- Dataset size: 68 tracts
- Class counts: 51 non-elevated, 17 elevated

## Feature and Leakage Controls

Both models used the same 58-feature set and the same exclusions. Direct target/leakage variables and raw arrest-volume variables were excluded, including:

- `arrests_per_1000_population`
- `total_arrests`
- `arrests_density_per_sq_mi`
- `arrest_activity_share`
- `arrest_weekend_events`
- `arrest_evening_night_events`
- `arrest_night_events`
- `felony_arrests`
- `misdemeanor_arrests`

The remaining features include ACS/context indicators, housing, education, density, neighborhood overlap count, and arrest-pattern share variables.

## Model Results

| Metric | Logistic Regression | Random Forest |
|---|---:|---:|
| Accuracy | 0.7619 | 0.8571 |
| Precision | 0.5000 | 0.6250 |
| Recall | 1.0000 | 1.0000 |
| F1 | 0.6667 | 0.7692 |
| ROC AUC | 0.9875 | 0.9125 |
| Train Rows | 47 | 47 |
| Test Rows | 21 | 21 |
| Number of Features | 58 | 58 |

## Confusion Matrix Comparison

Logistic Regression:

```text
[[11, 5],
 [ 0, 5]]
```

Random Forest:

```text
[[13, 3],
 [ 0, 5]]
```

Both models correctly identified all elevated tracts in the test split. Random forest produced fewer false positives. Logistic regression had stronger ROC AUC on this specific split.

The test set is small, so these results should not be overclaimed.

## Interpretation

Logistic regression is more directly explainable because coefficients show feature direction and magnitude after scaling. Random forest can capture nonlinear relationships and interactions, but feature importance is less directly interpretable than coefficients.

Random forest performed better on accuracy, precision, and F1 for this split. Logistic regression remains a useful baseline because it is simpler and more transparent.

## Preferred Baseline

For responsible interpretation and portfolio explanation, logistic regression should remain the primary explainable baseline. Random forest should be presented as a comparison model that tests whether a nonlinear method improves classification performance.

Random forest should not be described as definitively better because the sample size is small.

## Limitations

- Only 68 census tracts.
- Only one held-out train/test split so far.
- No repeated cross-validation yet.
- No external validation.
- Arrest data reflects enforcement and administrative activity, not direct harm.
- Demographic features require careful interpretation.
- Model outputs should not be used for enforcement targeting or operational directives.

## Recommended Next Steps

1. Add repeated stratified cross-validation for both models.
2. Add a reduced feature set for interpretability.
3. Update the model card with random forest comparison results.
4. Create a notebook section or second notebook comparing both models.
5. Only consider API/dashboard integration after validation is stronger.

## Portfolio Talking Point

I compared an explainable logistic regression baseline with a nonlinear random forest classifier using the same leakage-controlled tract-level feature set. The random forest improved accuracy, precision, and F1 on the held-out split, while logistic regression remained the more transparent model for interpretation. I treated both models as exploratory because the dataset contains only 68 census tracts and requires additional validation before dashboard integration.
