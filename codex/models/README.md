# Models

This folder contains fitted models, validation outputs, and model diagnostics.

## Main Files

- `metrics.json`: leave-one-draft-class-out regression metrics and tier-classifier confusion matrix.
- `iterations.md`: modeling iteration narrative.
- `feature_importance.csv`: permutation importance from the final gradient boosting model.
- `logo_regression_predictions.csv`: leave-one-draft-class-out predictions.
- `ridge_regressor.joblib`: final ridge regression model.
- `gbm_regressor.joblib`: final gradient boosting regression model.
- `rf_regressor.joblib`: final random forest regression model.
- `tier_classifier.joblib`: final gradient boosting classifier.

## Modeling Summary

The project trained a market-rank baseline, ridge regression, gradient boosting regression, random forest regression, bootstrapped prediction bands, and a tier classifier. The public market baseline remained very strong, so the final board uses model output as a disciplined modifier rather than a pure ranking engine.
