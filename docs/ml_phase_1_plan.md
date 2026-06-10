# ML Phase 1 Plan: Explainable Tract-Level Arrest Activity Modeling

## Purpose

ML Phase 1 adds a cautious, explainable machine learning layer to the Durham Risk Intelligence Dashboard before any model code is written. The goal is to support analytical interpretation of tract-level arrest activity while staying aligned with the dashboard's current risk intelligence, preparedness, and decision-support framing.

The initial purpose is to classify census tracts into elevated and non-elevated arrest activity groups based on arrests per 1,000 residents. Tract-level contextual indicators will be used to study associations and patterns, not to predict individual behavior or make enforcement decisions.

## Why This Fits the Current Dashboard

This extension fits the current dashboard because the application already uses census tracts as the primary analytical geography. It preserves full census tract geometries for analytical consistency and combines arrest activity with ACS-based tract context.

The dashboard already emphasizes normalized rates, public-facing spatial comparison, choropleth interpretation, and tract-level enrichment. A tract-level ML layer can build on those outputs without changing the project's analytical unit or public-facing purpose.

The dashboard is a decision intelligence and preparedness prototype, not an enforcement prediction tool. Arrest data should be understood as arrest and enforcement activity recorded through administrative processes. It is not a direct measure of crime harm, future crime, or individual risk.

## Modeling Objective

The initial modeling objective is to classify census tracts into elevated or non-elevated arrest activity groups.

Target variable:

```text
elevated_arrest_activity_flag
```

Target definition:

- `1` = census tract is in the top 25 percent of tracts by arrests per 1,000 residents
- `0` = all other census tracts

This is a first-pass binary classification design. It is intended to create an explainable baseline for tract-level arrest activity analysis, not a definitive risk score or operational directive.

## Why Logistic Regression First

Logistic regression is the appropriate starting model because the first target is binary. It is explainable, easier to interpret, and provides a useful baseline before considering more complex models.

Logistic regression also supports careful communication about association rather than prediction. Coefficients can be reviewed and documented, which helps avoid overclaiming and keeps the first ML phase aligned with the dashboard's public-facing analytical purpose.

## Why Random Forest Second

Random forest is a useful second model because it can capture nonlinear relationships that logistic regression may miss. It can also provide a performance comparison against the logistic regression baseline and produce feature importance outputs for review.

Random forest should come after the baseline model is working. Its outputs need to be explained clearly and used cautiously, especially because feature importance does not prove causation and can be sensitive to correlated features.

## Candidate Features

Candidate features should be built from existing processed tract-level arrest and ACS outputs where possible. Features should remain tract-level and should support contextual interpretation.

### Tract Context Features

Examples include:

- population
- poverty rate
- vacancy rate
- median household income
- average household size
- percent under 18
- percent bachelor's degree
- race and ethnicity percentage variables, interpreted responsibly as contextual indicators rather than causal explanations or community labels

Demographic variables require careful interpretation. They should be used to understand broader structural and contextual patterns, not to stigmatize communities or imply individual risk.

### Arrest Activity Features

Examples include:

- total arrests
- arrests per 1,000 residents
- felony share
- misdemeanor share
- top offense category indicators if available
- district or beat context if available

These features describe recorded arrest activity and related administrative patterns. They should not be described as direct measurements of crime harm.

### Temporal Features

Examples include:

- weekend arrest share
- nighttime arrest share
- peak hour arrest share
- monthly arrest count
- recent activity trend
- rolling 30 day arrest count if data supports it
- rolling 90 day arrest count if data supports it

Temporal features may be added after the baseline model is working. The first pass should prioritize a clear tract-level dataset and an explainable binary classification target.

## Models to Implement

1. Logistic Regression baseline
2. Random Forest classifier
3. Optional later extension: Poisson or negative binomial model for tract-month arrest counts

Poisson or negative binomial models are better suited if the project later models arrest counts over time. Those models would support count-based tract-month analysis rather than the first-pass elevated versus non-elevated classification target.

## Evaluation Plan

Evaluation should be scaled to the number of available census tracts. If the sample is small, cross validation may be more appropriate than a simple train/test split. If there are enough tract observations, a train/test split can be used for a straightforward first evaluation.

Initial evaluation outputs should include:

- accuracy
- precision
- recall
- F1 score
- ROC AUC if appropriate
- confusion matrix
- feature importance or coefficients

The evaluation should include caution around small sample size if there are limited census tracts. Model metrics should be interpreted as early evidence about tract-level pattern recognition, not as proof that the model generalizes to all settings or future periods.

## Outputs to Create Later

Future ML implementation should create a separate ML workspace without changing the live dashboard first:

```text
ml/
  scripts/
    build_ml_dataset.py
    train_logistic_regression.py
    train_random_forest.py
  notebooks/
    01_tract_level_ml_modeling.ipynb
  outputs/
    ml_tract_dataset.csv
    model_metrics.json
    logistic_coefficients.csv
    random_forest_feature_importance.csv
    tract_arrest_activity_scores.csv
  models/
    logistic_regression_model.joblib
    random_forest_model.joblib
docs/
  ml_model_card.md
```

## Dashboard Integration Later

ML outputs should not be added to the live dashboard immediately. The model should be built, evaluated, reviewed, and documented before any API or interface exposure.

Recommended sequence:

1. Build ML dataset.
2. Train and evaluate baseline model.
3. Review model outputs.
4. Document model assumptions and limitations.
5. Only then expose outputs through FastAPI or dashboard layers.

Potential later endpoints:

- `/api/ml/model-summary`
- `/api/ml/tract-scores`
- `/api/ml/feature-importance`

## Responsible Use and Limitations

This is not crime prediction. It is not individual-level risk scoring. It does not predict future criminal behavior.

Arrest data reflects enforcement activity and administrative processes, not only direct harm. Model outputs should be interpreted as contextual indicators, not operational directives.

Demographic variables require careful interpretation and should not be used to stigmatize communities. Results should support transparency, preparedness, and analytical review.

The model should remain aligned with the dashboard's decision intelligence framing. Its purpose is to help analysts understand tract-level arrest activity patterns in context, not to prescribe enforcement action.

## Interview Talking Points

- I started with logistic regression because the first target is binary and explainable.
- I planned random forest second to compare nonlinear performance and feature importance.
- I kept the unit of analysis at the census tract level to match the dashboard's analytical geography.
- I used arrests per 1,000 residents to avoid raw count bias.
- I separated model development from dashboard deployment so the model could be validated before being exposed.
- I avoided computer vision because it does not fit the current dashboard use case.
- I would treat model refresh as periodic, not continuous, because the source data updates periodically.

## Next Implementation Step

The next step after this planning document is:

Build the ML dataset from the existing processed tract-level arrest and ACS outputs.
