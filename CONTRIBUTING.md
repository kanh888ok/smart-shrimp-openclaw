# Contributing

Use small, reviewable changes.

## Local check

```bash
python -m compileall .
```

## Data policy

Do not commit private pond logs, API keys, cloud-resource identifiers, trained model binaries, or generated reports. Keep new public datasets documented in `data/README.md` with source and license notes.

## Metric policy

When adding model results, state the dataset, split/validation method, target variable, and whether the data are real, simulated, or augmented.
