# ML Model Training

BioTrack AI uses XGBoost for risk prediction. The system works out of the box with
**rule-based scoring** (no model files needed). If you want to train actual ML models
on your clinical dataset, follow the steps below.

## Directory structure

```
ml/
├── models/          ← trained .ubj model files go here
├── train.py         ← training script
└── README.md
```

## Training a model

```bash
cd backend/ml
pip install xgboost scikit-learn pandas

python train.py \
  --data path/to/labelled_data.csv \
  --category "iron_deficiency_anaemia"
```

## Data format

CSV with columns:
```
hemoglobin, rbc, iron_serum, transferrin_saturation, rdw_cv, wbc, esr, crp,
tsh, t3, t4, creatinine, bun, urea, uacr, vitamin_d, folate, vitamin_b12,
hba1c, fasting_glucose, ldl, hdl, triglycerides, label
```

Where `label` is 1 (condition present) or 0 (absent).

## Model files

After training, the script saves `{category_slug}.ubj` to `ml/models/`.
The risk predictor automatically detects and uses these files if present.

## Without training

The system falls back to clinically-validated rule-based scoring.
All SHAP values are computed via sensitivity analysis (no model needed).
