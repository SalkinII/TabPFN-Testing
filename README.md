# TabPFN Data Quality Assessment Dashboard

A lightweight, containerized Panel-based web application for assessing data quality in clinical medicine CSV files using TabPFN (Prior-Data Fitted Networks).

## Features

- **TabPFN-Based Quality Assessment**: Uses TabPFN's unsupervised learning capabilities for outlier detection, anomaly detection, and missing value pattern analysis
- **Clinical Quality Checks**: Validates clinical data for impossible values, temporal inconsistencies, referential integrity, and clinical plausibility
- **Interactive Visualizations**: Real-time quality metrics with pragmatic, understandable visualizations
- **Comprehensive Scoring**: Overall and component-level quality scores (0-100 scale)
- **Actionable Recommendations**: Provides specific recommendations for data quality improvements
- **Lightweight Container**: Easy deployment with Docker

## Quick Start

### Using Docker (Recommended)

```bash
# Build the container
docker build -t tabpfn-data-quality .

# Run the container
docker run -p 5006:5006 tabpfn-data-quality
```

Then open your browser to `http://localhost:5006`

### Using Docker Compose

For production deployments, you can use Docker Compose:

```bash
# Start the application
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop the application
docker-compose -f docker-compose.prod.yml down
```

### Environment Variables

The application supports the following environment variables:

- `HF_TOKEN`: (Optional) Hugging Face token for TabPFN model access. If not provided, TabPFN will use statistical fallback methods.
- `PYTHONUNBUFFERED`: (Optional) Set to `1` for unbuffered Python output (useful for logging)

Example with environment variables:

```bash
docker run -p 5006:5006 -e HF_TOKEN=your_token_here tabpfn-data-quality
```

## Usage

1. **Upload CSV File**: Use the file upload widget in the sidebar to upload your CSV file
2. **Review Assessment**: The dashboard will automatically assess data quality and display:
   - Overall quality score (0-100)
   - Summary cards with key metrics
   - Missing values analysis
   - Outlier detection results
   - Anomaly scores
   - Column-level quality metrics
   - Clinical quality checks (for clinical data)
   - Actionable recommendations

### Supported File Formats

- CSV files with standard delimiters (comma, semicolon, tab)
- UTF-8 encoding (other encodings may be auto-detected)
- Headers in first row
- Any number of rows and columns

## Project Structure

```
.
├── app.py                    # Main Panel application
├── data_quality.py           # TabPFN-based quality assessment
├── visualizations.py          # Panel visualization components
├── clinical_quality.py        # Clinical-specific quality checks
├── utils.py                  # Helper functions
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container definition
├── .dockerignore             # Docker ignore file
├── LICENSE                   # Project license
└── README.md                 # This file
```

## Data Quality Metrics

### Overall Quality Score (0-100)

Composite score based on:
- Missing values (30% weight)
- Outliers (30% weight)
- Anomalies (20% weight)
- Consistency (20% weight)

### Component Scores

- **Missing Score**: Penalizes missing values
- **Outlier Score**: Penalizes statistical outliers
- **Anomaly Score**: Penalizes anomalous records
- **Consistency Score**: Penalizes duplicate rows and data inconsistencies

### Clinical Quality Checks

For clinical medicine data, the application performs additional checks:
- Impossible values (e.g., age > 150)
- Temporal inconsistencies (e.g., discharge before admission)
- Referential integrity (missing/duplicate IDs)
- Clinical plausibility (e.g., BMI calculations)

## Logging

All operations are logged to the `logs/` directory:
- **Assessment logs**: Quality assessment runs and results
- **Error logs**: Application errors and exceptions
- **Operation logs**: File uploads and processing events

Logs are stored as JSON files with timestamps for easy parsing and analysis. The logs directory structure is automatically created when the application starts.

## Configuration

### Docker Deployment

For production deployments, consider:

1. **Volume Mounts**: Mount the `logs/` directory to persist logs:
   ```bash
   docker run -p 5006:5006 -v /path/to/logs:/app/logs tabpfn-data-quality
   ```

2. **Environment Variables**: Set via `-e` flag or `.env` file:
   ```bash
   docker run -p 5006:5006 -e HF_TOKEN=your_token tabpfn-data-quality
   ```

3. **Resource Limits**: Set appropriate CPU and memory limits:
   ```bash
   docker run -p 5006:5006 --memory="2g" --cpus="2" tabpfn-data-quality
   ```

### Port Configuration

The application runs on port 5006 by default. To use a different port:

```bash
docker run -p 8080:5006 tabpfn-data-quality
```

Then access at `http://localhost:8080`

## License

This project is licensed under the BSD 3-Clause License. See LICENSE file for details.

### Third-Party Licenses

- **Panel**: BSD-3-Clause License (https://github.com/holoviz/panel)
- **TabPFN**: TABPFN-2.5 License v1.0 (https://docs.priorlabs.ai/models)
  - Note: For production/commercial use, a commercial license is required from PriorLabs

## Documentation

Comprehensive documentation is available in the `docs/` folder:

### User Documentation
- **[User Guide](docs/User_Guide.md)**: How to use the Panel dashboard application
- **[Pipeline Workflow](docs/Pipeline_Workflow.md)**: Operational workflow documentation

### Technical Documentation
- **[TabPFN Data Quality Factors](docs/TabPFN_DataQuality_Factors.md)**: Crucial factors about TabPFN's data quality aspects
- **[Logging Structure](docs/Logging_Structure.md)**: Understanding log files and log analysis

## Dependencies

- Panel >= 1.3.0 (BSD-3-Clause)
- TabPFN >= 6.0.0 (TABPFN-2.5 License)
- Pandas >= 2.0.0
- NumPy >= 1.24.0
- Plotly >= 5.17.0
- Matplotlib >= 3.7.0

## Support

For issues, questions, or contributions, please refer to the project repository or contact the maintainers.

## References

- TabPFN: https://github.com/PriorLabs/tabpfn
- Panel: https://github.com/holoviz/panel
- TabPFN Documentation: https://docs.priorlabs.ai/models
