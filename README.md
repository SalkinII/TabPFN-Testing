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

### Iterative Development (No Rebuilds Required)

For faster development cycles without rebuilding the container:

**Using PowerShell Helper Script (Recommended):**

```powershell
# Start development container with volume mounts
.\dev.ps1 start

# View logs in real-time
.\dev.ps1 logs

# Check container status
.\dev.ps1 status

# Stop container
.\dev.ps1 stop

# Restart container
.\dev.ps1 restart

# Clean old log files (older than 7 days)
.\dev.ps1 clean
```

**Using Docker Compose:**

```powershell
# Start development container
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop container
docker-compose -f docker-compose.dev.yml down
```

**Manual Docker Command:**

```powershell
# Run with volume mounts (code changes reflect immediately)
docker run -p 5006:5006 -v ${PWD}:/app -v ${PWD}/logs:/app/logs tabpfn-data-quality
```

**Benefits:**
- Code changes reflect immediately via volume mounts
- Logs accessible from host in `logs/dev/` folder
- Faster iteration - edit code locally, see changes instantly
- Structured logging with timestamps and context

### Running Tests

All tests should be run inside the Docker container where all dependencies are installed. No local dependency installation is required.

**Using PowerShell Helper Script (Recommended):**

```powershell
# Run container startup tests
.\dev.ps1 test
```

**Using Docker Directly:**

```powershell
# Run tests in running container
docker exec tabpfn-data-quality-dev python tests/test_container_startup.py

# Or start container and run tests
docker-compose -f docker-compose.dev.yml up -d
docker exec tabpfn-data-quality-dev python tests/test_container_startup.py
```

The test suite verifies:
- All required modules can be imported
- App initialization works correctly
- Required file paths exist
- Environment variables are set correctly
- Panel extensions are available

### Local Development (Optional)

If you want to run the application locally (not recommended for testing):

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
panel serve app.py --show
```

**Note:** For testing and development, using Docker is recommended as it ensures a consistent environment with all dependencies properly installed.

## Usage

1. **Upload CSV File**: Use the file upload widget in the sidebar to upload your clinical data CSV file
2. **Review Assessment**: The dashboard will automatically assess data quality and display:
   - Overall quality score (0-100)
   - Summary cards with key metrics
   - Missing values analysis
   - Outlier detection results
   - Anomaly scores
   - Column-level quality metrics
   - Clinical quality checks
   - Actionable recommendations

## Project Structure

```
.
├── app.py                    # Main Panel application
├── data_quality.py           # TabPFN-based quality assessment
├── visualizations.py         # Panel visualization components
├── clinical_quality.py       # Clinical-specific quality checks
├── corruption_framework.py   # Data corruption utilities (for testing)
├── corrupt_data.py           # Standalone CLI script for batch corruption
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
- Impossible values (e.g., age > 150)
- Temporal inconsistencies (e.g., discharge before admission)
- Referential integrity (missing/duplicate IDs)
- Clinical plausibility (e.g., BMI calculations)

## Logging

All operations are logged to the `logs/` directory (gitignored):
- **Development logs**: `logs/dev/` - Application startup, errors, file uploads, and performance metrics
- **Assessment logs**: `logs/` - Quality assessment runs and results
- **Corruption logs**: `logs/` - Data corruption operations (for testing)

Logs are stored as JSON files with timestamps for easy parsing and analysis. Development logs are automatically created when running in development mode.

## Testing with Corrupted Data

The corruption framework provides utilities for testing TabPFN's detection capabilities. Use the standalone `corrupt_data.py` script to corrupt CSV files for testing.

### Quick Start

```bash
# Corrupt all files in csvlate/ with 10% missing values
docker exec <container> python corrupt_data.py --source csvlate --corruption missing --level 10

# Corrupt single file with maximum corruption
docker exec <container> python corrupt_data.py --source csvlate/patients.csv --corruption maximum

# Corrupt with outliers at 5%
docker exec <container> python corrupt_data.py --source csv1k --corruption outliers --level 5
```

### Corruption Types

- `missing`: Introduce missing values (NaN)
- `outliers`: Introduce statistical outliers
- `duplicates`: Introduce duplicate rows
- `inconsistencies`: Introduce format inconsistencies
- `maximum`: Apply all corruption types at maximum levels

### Output

Corrupted files are saved to the `corrupt/` directory, preserving the folder structure:
- `csvlate/patients.csv` → `corrupt/csvlate/patients.csv`
- `csv1k/encounters.csv` → `corrupt/csv1k/encounters.csv`

### Documentation

For detailed usage instructions, see:
- **[Corruption Framework Guide](docs/Corruption_Framework_Guide.md)**: Complete API reference and usage examples
- **[Testing Guide](docs/Testing_Guide.md)**: Step-by-step testing workflows
- **[Logging Structure](docs/Logging_Structure.md)**: Understanding log files

### Python API

You can also use the corruption framework programmatically:

```python
from corruption_framework import DataCorruptor

corruptor = DataCorruptor(random_seed=42)

# Introduce missing values
corrupted_df, details = corruptor.introduce_missing_values(df, missing_percentage=10.0)

# Introduce outliers
corrupted_df, details = corruptor.introduce_outliers(df, outlier_percentage=5.0)

# Apply maximum corruption (all types)
corrupted_df, details = corruptor.apply_maximum_corruption(df)
```

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
- **[Findings Summary](docs/Findings_Summary.md)**: Key findings from experiments

### Testing & Corruption
- **[Corruption Framework Guide](docs/Corruption_Framework_Guide.md)**: Complete guide to using the corruption framework
- **[Testing Guide](docs/Testing_Guide.md)**: Step-by-step testing workflows and validation
- **[Logging Structure](docs/Logging_Structure.md)**: Understanding log files and log analysis

## Dependencies

- Panel >= 1.3.0 (BSD-3-Clause)
- TabPFN >= 6.0.0 (TABPFN-2.5 License)
- Pandas >= 2.0.0
- NumPy >= 1.24.0
- Plotly >= 5.17.0
- Matplotlib >= 3.7.0

## Contributing

Contributions are welcome! Please ensure that:
1. All code follows PEP 8 style guidelines
2. Tests are added for new features
3. Documentation is updated accordingly
4. License compliance is maintained

## References

- TabPFN: https://github.com/PriorLabs/tabpfn
- Panel: https://github.com/holoviz/panel
- TabPFN Documentation: https://docs.priorlabs.ai/models
