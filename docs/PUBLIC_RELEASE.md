# GitHub public release notes

This repository was prepared from the original OpenClaw shrimp-farming competition package so that it can be uploaded to GitHub as a reproducible demo project.

## Changes made

- Flattened the original nested package into a single repository root.
- Rewrote `README.md` for GitHub usage: quick start, Docker, structure, data, and metric interpretation.
- Added `.env.example`, `.gitattributes`, `.gitignore`, `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, and GitHub Actions compile check.
- Split dependencies into `requirements.txt` and `requirements-advanced.txt`.
- Replaced OpenClaw/cloud/API credentials with placeholders in `config/openclaw.example.json`.
- Removed private cloud/server screenshots, archived draft materials, generated DOCX reports, caches, and runtime outputs.
- Generalized personal/team identifiers in public text files.
- Added `data/README.md`, `reports/README.md`, and `docs/DATA_AND_METRICS.md` to separate real measurements, simulation data, and experiment metrics.

## Interpretation boundary

This is a research/competition prototype. The water-quality, feeding, ROI, and model-performance outputs are demo or experiment results unless a future deployment supplies calibrated sensors and complete production-cycle validation.

## License

The included `LICENSE` keeps all rights reserved. Replace it with an OSI-approved license only if you intend to release the project as open source.
