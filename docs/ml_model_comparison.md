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

## Single Held-Out Split Results

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

## Repeated Cross-Validation Results

A repeated stratified cross-validation evaluation was added to avoid relying only on one 70/30 train/test split.

Evaluation setup:

- Method: RepeatedStratifiedKFold
- 5 splits
- 10 repeats
- 50 evaluations per model
- Same 58-feature leakage-controlled feature set
- Same 68 census tracts
- Same target: `elevated_arrest_activity_flag`

| Metric | Logistic Regression Mean | Logistic Regression Std | Random Forest Mean | Random Forest Std |
|---|---:|---:|---:|---:|
| Accuracy | 0.7997 | 0.0866 | 0.7430 | 0.1052 |
| Precision | 0.6166 | 0.1921 | 0.5269 | 0.2213 |
| Recall | 0.6950 | 0.2420 | 0.7033 | 0.2777 |
| F1 | 0.6236 | 0.1616 | 0.5689 | 0.1837 |
| ROC AUC | 0.8839 | 0.0840 | 0.8587 | 0.1012 |

On the single held-out split, random forest had stronger accuracy, precision, and F1. Across repeated cross-validation, logistic regression performed slightly better on accuracy, precision, F1, and ROC AUC. Random forest had slightly higher mean recall.

This reinforces logistic regression as the preferred explainable baseline. Random forest remains useful as a nonlinear comparison model. Because the dataset is small, neither model should be treated as production-ready.

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

Logistic regression remains the preferred baseline because it is explainable and performed slightly better overall in repeated cross-validation. Random forest should be presented as a comparison model that tests nonlinear performance.

Neither model should be described as definitively superior because the dataset is small and no external validation has been done.

## Limitations

- Only 68 census tracts.
- Repeated cross-validation has been added, but it still uses the same small dataset.
- No external validation.
- Arrest data reflects enforcement and administrative activity, not direct harm.
- Demographic features require careful interpretation.
- Model outputs should not be used for enforcement targeting or operational directives.

## Recommended Next Steps

1. Add a reduced feature set for interpretability.
2. Update or add a notebook section comparing single-split and cross-validation results.
3. Consider calibration analysis if probabilities are later exposed.
4. Consider API/dashboard integration only after deciding what output is appropriate to expose.
5. Preserve responsible-use caveats in any public-facing ML layer.

## Portfolio Talking Point

I compared an explainable logistic regression baseline with a nonlinear random forest classifier using the same leakage-controlled tract-level feature set. The random forest improved accuracy, precision, and F1 on the held-out split, while repeated cross-validation showed logistic regression performing slightly better overall and remaining the more transparent model for interpretation. I treated both models as exploratory because the dataset contains only 68 census tracts and requires additional validation before dashboard integration.
