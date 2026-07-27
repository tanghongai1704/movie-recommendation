# ML module

This folder contains the machine learning scaffolding for the recommendation system.

## Current status

The ML layer is not yet connected to a trained production model. The current backend uses a lightweight mock recommendation path for local development and UI validation.

## Intended structure

- `data/` — datasets and sample inputs
- `notebooks/` — experiment notebooks
- `training/` — training scripts and pipelines
- `models/` — trained artifacts and model metadata
- `services/` — recommendation service interfaces
- `mock/` — local mock provider for development
- `sagemaker/` — SageMaker deployment scaffolding
- `utils/` — preprocessing and helper modules

## Future flow

1. Dataset preparation
2. Preprocessing
3. Training
4. Model artifact export
5. SageMaker deployment
6. Backend integration via the service interface
