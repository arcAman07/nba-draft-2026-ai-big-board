# Modeling Iteration Log

Run date: 2026-06-10.

## Iteration 0: Market-Rank Baseline

A ridge model using only historical draft slot as the public-market proxy. This is the hurdle model.

Metrics: `{'mae': 6.059093096158589, 'rmse': 7.2881687548710525, 'spearman': 0.6343938981690741}`

## Iteration 1: Ridge With Market + Trait Features

Added age, anthropometrics, per-40 production, efficiency, usage and BPM features. Ridge retained interpretability but did not capture non-linear age/size/stat interactions as well as boosting.

Metrics: `{'mae': 5.966282697298442, 'rmse': 7.2197225929816184, 'spearman': 0.6435149030163432}`

## Iteration 2: Gradient Boosting

Used shallow gradient boosting with leave-one-draft-class-out validation. This was selected as the primary value model because it improved MAE/Spearman versus the market baseline while remaining reasonably stable.

Metrics: `{'mae': 5.962567221738261, 'rmse': 7.329019270433344, 'spearman': 0.6205570483513188}`

## Iteration 3: Random Forest Check

Random forest was retained as an ensemble sanity check but not as the lead model when it lagged GBM or produced flatter top-end predictions.

Metrics: `{'mae': 5.894779256516746, 'rmse': 7.265760513490006, 'spearman': 0.6298908665668441}`

## Classifier

Tier classifier predicts bust/bench/rotation/starter/star classes from the same feature set. It is used as probability-flavored context, not as the ranking engine.

Metrics: `{'accuracy': 0.3943089430894309, 'labels': ['bust', 'bench', 'rotation', 'starter', 'star'], 'confusion_matrix': [[92, 41, 43, 1, 3], [57, 61, 107, 13, 0], [24, 62, 190, 34, 5], [4, 24, 101, 36, 19], [2, 2, 23, 31, 9]]}`
