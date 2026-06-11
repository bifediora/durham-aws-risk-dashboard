# PCA-Compressed Logistic Regression Notes

## Purpose

PCA was added to evaluate whether correlated tract-level contextual indicators could be compressed into lower-dimensional components while preserving useful classification signal for elevated tract-level arrest activity.

This is an exploratory analytical model for decision-support interpretation. It works at the census tract level and uses contextual components derived from tract-level contextual indicators.

## Why PCA Was Considered

The original ML dataset included 58 leakage-controlled features. Many of these features are correlated ACS, housing, demographic, education, labor force, and arrest-pattern indicators.

PCA reduces correlated variables into lower-dimensional components. This can help test whether a smaller set of contextual components can retain meaningful classification signal while reducing feature dimensionality.

## Model Design

- Input: `ml/outputs/ml_tract_dataset.csv`
- Target: `elevated_arrest_activity_flag`
- Original features before PCA: 58
- Rows: 68 census tracts
- Class counts: 51 non-elevated, 17 elevated
- Tested PCA components: 5, 6, 7, 8
- Pipeline: median imputation, standard scaling, PCA, logistic regression
- Cross-validation: RepeatedStratifiedKFold, 5 splits, 10 repeats
- Metrics: accuracy, precision, recall, F1, ROC AUC

## Results Summary

| PCA Components | Accuracy | Precision | Recall | F1 | ROC AUC |
|---:|---:|---:|---:|---:|---:|
| 5 | 0.6935 | 0.4567 | 0.6433 | 0.5083 | 0.7849 |
| 6 | 0.7755 | 0.5772 | 0.7483 | 0.6255 | 0.8493 |
| 7 | 0.7831 | 0.5898 | 0.7433 | 0.6305 | 0.8567 |
| 8 | 0.7927 | 0.6070 | 0.7583 | 0.6487 | 0.8638 |

Eight components produced the highest mean F1. Seven components was selected because it was within 0.02 F1 of the best result and was more parsimonious.

## Working Component Labels

These are working interpretive labels based on the highest absolute loadings. They are not definitive causal constructs.

### PC1: Population / Housing Scale Component

Strong loadings: education population count, owner-occupied units, total population, poverty-status population, male/female population, occupied housing units, civilian labor force.

### PC2: Socioeconomic / Education Context Component

Strong loadings: education rates, median household income, poverty count/rate, youth share, and race/ethnicity share variables.

### PC3: Housing Tenure / Household Structure Component

Strong loadings: renter-occupied units/share, owner-occupancy share, vacancy, average household size, median age, tract area.

### PC4: Spatial Size / Evening-Night Arrest Pattern Component

Strong loadings: tract area, evening/night arrest share, night arrest share, sex composition, vacancy, household size.

### PC5: Labor Force / Arrest Composition Component

Strong loadings: unemployment rate/count, felony share, misdemeanor share, youth share, weekend arrest share, household size.

### PC6: Demographic Composition / Household Age Structure Component

Strong loadings: demographic share variables, sex composition, senior share, median age, average household size, evening/night arrest share.

### PC7: Arrest Type Composition / Neighborhood Complexity Component

Strong loadings: misdemeanor share, felony share, neighborhood overlap count, sex composition, tract area, selected demographic share variables.

## Interpretation

PCA compressed 58 features into 7 contextual components. The selected model retained meaningful classification signal.

The result supports the idea that correlated tract-level indicators can be summarized into broader contextual dimensions. The PCA model should be interpreted as exploratory and analytical, not operational.

## Limitations

- Only 68 census tracts.
- PCA components are mathematical combinations, not natural constructs.
- Component labels are subjective and based on loadings.
- PCA is unsupervised and does not know the target.
- Results should not be used for individual-level inference.
- The model classifies elevated arrest activity based on historical arrest data and contextual indicators; it does not identify causes.

## Responsible Use

This PCA-compressed logistic regression model evaluates whether correlated tract-level contextual indicators can be represented as lower-dimensional components for elevated arrest activity classification. It is not an individual-level risk model and should not be interpreted as predicting criminal behavior.
