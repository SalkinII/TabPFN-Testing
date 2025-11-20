# TabPFN Testing Project

This repository contains testing and demonstration code for TabPFN, a fast machine learning model for tabular data that requires no hyperparameter tuning.

## Contents

- **TabPFN_Demo_Local.ipynb**: Comprehensive Jupyter notebook demonstrating TabPFN capabilities including:
  - Classification and regression tasks
  - Text data handling
  - Unsupervised learning (anomaly detection, data imputation)
  - Model interpretability (SHAP values, embeddings)
  - Time series forecasting
  - Causal inference applications

- **csv1k/**: Dataset folder containing sample CSV files for testing
- **csvlate/**: Additional dataset folder with CSV files

## Getting Started

### Installation

Install the required dependencies:

```bash
pip install tabpfn tabpfn-client tabpfn-extensions[all]
```

For additional features:
```bash
pip install tabpfn-time-series  # For time series forecasting
pip install econml  # For causal inference
```

### Usage

Open `TabPFN_Demo_Local.ipynb` in Jupyter Notebook or JupyterLab to explore the examples.

## Features Demonstrated

- **Classification**: Parkinson's Disease prediction
- **Regression**: Boston Housing price prediction
- **Text Data**: Native text handling capabilities
- **Unsupervised Learning**: Data generation, outlier detection, missing value imputation
- **Interpretability**: SHAP values, feature importance, embeddings visualization
- **Time Series**: Forecasting with TabPFN
- **Causal Inference**: CATE estimation using TabPFN as base model

## License

[Add your license here]

## References

- TabPFN: [GitHub Repository](https://github.com/PriorLabs/tabpfn)
- TabPFN Client: [GitHub Repository](https://github.com/automl/tabpfn-client)

