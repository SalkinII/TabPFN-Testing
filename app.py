"""
Main Panel application for TabPFN Data Quality Assessment Dashboard.
"""

import panel as pn
import pandas as pd
import io
import json
from typing import Optional
import os

from data_quality import DataQualityAssessor
from clinical_quality import ClinicalQualityChecker
from visualizations import (
    create_quality_score_card,
    create_summary_cards,
    create_missing_values_chart,
    create_outlier_distribution_chart,
    create_quality_breakdown_chart,
    create_column_quality_table,
    create_anomaly_heatmap,
    create_recommendations_panel
)
from utils import calculate_basic_stats, log_operation, log_dev_event, log_error

# Configure Panel
pn.extension('plotly', 'tabulator', sizing_mode='stretch_width')

# Initialize components
try:
    log_dev_event('startup', 'Initializing TabPFN Data Quality Assessment Dashboard')
    
    # Set HuggingFace token if available (for TabPFN model authentication)
    hf_token = os.environ.get('HF_TOKEN')
    if hf_token:
        os.environ['HF_TOKEN'] = hf_token
        log_dev_event('startup', 'HuggingFace token found - TabPFN models will authenticate')
    else:
        log_dev_event('startup', 'No HuggingFace token found - TabPFN will use statistical fallback methods')
    
    assessor = DataQualityAssessor()
    clinical_checker = ClinicalQualityChecker()
    log_dev_event('startup', 'Components initialized successfully')
except Exception as e:
    log_error(e, {'context': 'initialization'})
    raise

# State
current_df: Optional[pd.DataFrame] = None
quality_results: dict = {}


def load_csv_file(file_input) -> pd.DataFrame:
    """
    Load CSV file from Panel FileInput.
    
    Args:
        file_input: Panel FileInput.value (list of bytes) or bytes directly
        
    Returns:
        Loaded DataFrame
    """
    if file_input is None:
        log_dev_event('file_upload', 'No file input provided', {'file_input': str(file_input)})
        return None
    
    # Handle Panel FileInput.value format (list of bytes)
    if isinstance(file_input, list):
        if len(file_input) == 0:
            log_dev_event('file_upload', 'FileInput value is empty list')
            return None
        file_content = file_input[0]
    elif hasattr(file_input, '__len__') and len(file_input) == 0:
        log_dev_event('file_upload', 'FileInput value is empty')
        return None
    elif hasattr(file_input, 'content_bytes') or hasattr(file_input, 'content_string'):
        # Handle MockFileInput-like objects (for testing)
        if hasattr(file_input, 'content_bytes') and file_input.content_bytes:
            file_content = file_input.content_bytes
        elif hasattr(file_input, 'content_string') and file_input.content_string:
            file_content = file_input.content_string
        else:
            log_dev_event('file_upload', 'MockFileInput has no content')
            return None
    else:
        # Direct bytes or other format
        file_content = file_input
    
    try:
        
        # Log file input details for debugging
        file_type = type(file_content).__name__
        file_size = len(file_content) if hasattr(file_content, '__len__') else 'unknown'
        
        # Log first few characters for debugging (but not too much)
        if isinstance(file_content, bytes):
            preview = file_content[:100].decode('utf-8', errors='ignore')
        else:
            preview = str(file_content)[:100] if hasattr(file_content, '__str__') else 'N/A'
        
        log_dev_event('file_upload', f'Processing file input: type={file_type}, size={file_size}, preview_length={len(preview)}')
        
        # Panel FileInput typically returns bytes, but handle different cases
        if isinstance(file_content, bytes):
            # Most common case: bytes from FileInput
            if len(file_content) == 0:
                log_error(Exception("Empty bytes content"), {'context': 'load_csv_file', 'file_input_type': file_type})
                return None
            file_obj = io.BytesIO(file_content)
            df = pd.read_csv(file_obj, encoding='utf-8')
            log_dev_event('file_upload', f'Parsed CSV as bytes: {len(df)} rows, {len(df.columns)} columns')
        elif isinstance(file_content, str):
            # If it's a string, check if it looks like CSV content or a filename
            if len(file_content) == 0:
                log_error(Exception("Empty string content"), {'context': 'load_csv_file', 'file_input_type': file_type})
                return None
            if '\n' in file_content or ',' in file_content[:500]:
                # Looks like CSV content
                file_obj = io.StringIO(file_content)
                df = pd.read_csv(file_obj)
                log_dev_event('file_upload', f'Parsed CSV as string content: {len(df)} rows, {len(df.columns)} columns')
            else:
                # Might be a filename/path - this shouldn't happen with FileInput
                log_error(Exception("String appears to be filename, not content"), {
                    'context': 'load_csv_file', 
                    'file_input_type': file_type,
                    'preview': preview[:50]
                })
                return None
        else:
            # Try to convert to bytes
            try:
                if hasattr(file_content, 'read'):
                    # It's a file-like object
                    df = pd.read_csv(file_content)
                else:
                    file_obj = io.BytesIO(bytes(file_content))
                    df = pd.read_csv(file_obj, encoding='utf-8')
                log_dev_event('file_upload', f'Parsed CSV after conversion: {len(df)} rows, {len(df.columns)} columns')
            except Exception as conv_e:
                log_error(conv_e, {
                    'context': 'load_csv_file', 
                    'file_input_type': file_type, 
                    'conversion_error': str(conv_e),
                    'preview': preview[:50] if isinstance(preview, str) else 'N/A'
                })
                return None
        
        # Validate DataFrame
        if df is None:
            log_dev_event('file_upload', 'Error: DataFrame is None after parsing')
            return None
        elif len(df) == 0:
            log_dev_event('file_upload', 'Warning: DataFrame is empty after parsing')
            # Check if it's just headers
            if len(df.columns) > 0:
                log_dev_event('file_upload', f'DataFrame has {len(df.columns)} columns but 0 rows (headers-only CSV)')
        elif len(df.columns) == 0:
            log_dev_event('file_upload', 'Warning: DataFrame has no columns after parsing')
        
        return df
    except pd.errors.EmptyDataError as e:
        log_error(e, {
            'context': 'load_csv_file', 
            'error_type': 'EmptyDataError', 
            'file_input_type': str(type(file_input[0]) if file_input and len(file_input) > 0 else None)
        })
        print(f"Error loading CSV: File is empty - {e}")
        return None
    except pd.errors.ParserError as e:
        log_error(e, {
            'context': 'load_csv_file', 
            'error_type': 'ParserError', 
            'file_input_type': str(type(file_input[0]) if file_input and len(file_input) > 0 else None)
        })
        print(f"Error loading CSV: Parse error - {e}")
        return None
    except UnicodeDecodeError as e:
        # Try with different encoding
        try:
            file_content = file_input[0]
            if isinstance(file_content, bytes):
                file_obj = io.BytesIO(file_content)
                df = pd.read_csv(file_obj, encoding='latin-1')
                log_dev_event('file_upload', f'Parsed CSV with latin-1 encoding: {len(df)} rows, {len(df.columns)} columns')
                return df
        except:
            pass
        log_error(e, {
            'context': 'load_csv_file', 
            'error_type': 'UnicodeDecodeError'
        })
        print(f"Error loading CSV: Encoding error - {e}")
        return None
    except Exception as e:
        log_error(e, {
            'context': 'load_csv_file', 
            'file_input_type': str(type(file_input[0]) if file_input and len(file_input) > 0 else None),
            'error_details': str(e)
        })
        print(f"Error loading CSV: {e}")
        import traceback
        traceback.print_exc()
        return None


def assess_data_quality(df: pd.DataFrame) -> dict:
    """
    Perform comprehensive data quality assessment.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary with assessment results
    """
    global quality_results
    
    # Validate DataFrame is not empty
    if df is None or len(df) == 0:
        raise ValueError("Cannot assess quality of empty DataFrame")
    if len(df.columns) == 0:
        raise ValueError("Cannot assess quality of DataFrame with no columns")
    
    # Basic statistics
    basic_stats = calculate_basic_stats(df)
    
    # Missing value assessment
    missing_assessment = assessor.assess_missing_values(df)
    
    # Outlier detection
    outlier_results = assessor.detect_outliers(df)
    
    # Anomaly detection
    anomaly_results = assessor.detect_anomalies(df)
    
    # Overall quality score
    quality_score = assessor.calculate_quality_score(df)
    
    # Column-level quality
    column_quality = assessor.assess_column_quality(df)
    
    # Clinical quality checks
    clinical_checks = clinical_checker.run_all_checks(df)
    
    # Compile results
    quality_results = {
        'basic_stats': basic_stats,
        'missing_assessment': missing_assessment,
        'outlier_results': outlier_results,
        'anomaly_results': anomaly_results,
        'quality_score': quality_score,
        'column_quality': column_quality,
        'clinical_checks': clinical_checks
    }
    
    # Log assessment
    log_operation('assessment', {
        'file_name': 'uploaded_file',
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'overall_score': quality_score['overall_score'],
        'missing_percentage': missing_assessment['missing_percentage'],
        'outlier_count': outlier_results.get('outlier_count', 0),
        'clinical_issues': clinical_checks['total_issues']
    })
    
    return quality_results


def export_quality_report(results: dict, format: str = 'json') -> bytes:
    """
    Export quality assessment results to a file.
    
    Args:
        results: Quality assessment results dictionary
        format: Export format ('json' or 'csv')
        
    Returns:
        Bytes of the exported file
    """
    if format == 'json':
        json_str = json.dumps(results, indent=2, default=str)
        return json_str.encode('utf-8')
    elif format == 'csv':
        # Create a summary CSV
        rows = []
        rows.append(['Metric', 'Value'])
        rows.append(['Overall Score', results.get('quality_score', {}).get('overall_score', 0)])
        rows.append(['Missing Percentage', results.get('missing_assessment', {}).get('missing_percentage', 0)])
        rows.append(['Outlier Count', results.get('outlier_results', {}).get('outlier_count', 0)])
        rows.append(['Anomaly Count', results.get('anomaly_results', {}).get('anomaly_count', 0)])
        rows.append(['Clinical Issues', results.get('clinical_checks', {}).get('total_issues', 0)])
        
        df_export = pd.DataFrame(rows[1:], columns=rows[0])
        csv_str = df_export.to_csv(index=False)
        return csv_str.encode('utf-8')
    else:
        raise ValueError(f"Unsupported format: {format}")


def create_dashboard(df: pd.DataFrame) -> pn.Column:
    """
    Create the main dashboard with all visualizations.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Panel Column with dashboard
    """
    # Validate DataFrame is not empty
    if df is None or len(df) == 0:
        raise ValueError("Cannot create dashboard for empty DataFrame")
    if len(df.columns) == 0:
        raise ValueError("Cannot create dashboard for DataFrame with no columns")
    
    # Assess data quality
    results = assess_data_quality(df)
    
    # Overall quality score card
    overall_score = results['quality_score']['overall_score']
    score_card = create_quality_score_card(overall_score, "Overall Data Quality Score")
    
    # Summary cards
    stats = results['basic_stats']
    stats['outlier_count'] = results['outlier_results'].get('outlier_count', 0)
    summary_cards = create_summary_cards(stats)
    
    # Missing values chart
    missing_chart = create_missing_values_chart(results['missing_assessment'])
    
    # Outlier distribution
    outlier_scores = results['outlier_results'].get('outlier_scores', [])
    outlier_chart = create_outlier_distribution_chart(outlier_scores)
    
    # Quality breakdown
    component_scores = results['quality_score']['component_scores']
    breakdown_chart = create_quality_breakdown_chart(component_scores)
    
    # Column quality table
    column_table = create_column_quality_table(results['column_quality'])
    
    # Anomaly heatmap
    anomaly_scores = results['anomaly_results'].get('anomaly_scores', [])
    anomaly_heatmap = create_anomaly_heatmap(anomaly_scores)
    
    # Recommendations
    recommendations = create_recommendations_panel(results)
    
    # Export functionality
    json_data = export_quality_report(results, format='json')
    csv_data = export_quality_report(results, format='csv')
    
    export_json_file = pn.widgets.FileDownload(
        file='quality_report.json',
        button_type='primary',
        filename='quality_report.json',
        auto=True
    )
    export_json_file.file = json_data
    
    export_csv_file = pn.widgets.FileDownload(
        file='quality_report.csv',
        button_type='primary',
        filename='quality_report.csv',
        auto=True
    )
    export_csv_file.file = csv_data
    
    export_panel = pn.Row(
        pn.pane.Markdown("### Export Quality Report"),
        export_json_file,
        export_csv_file,
        sizing_mode='stretch_width'
    )
    
    # Clinical quality issues
    clinical_issues_html = ""
    if results['clinical_checks']['has_issues']:
        issues_list = []
        for check_type, check_results in results['clinical_checks'].items():
            if isinstance(check_results, dict) and check_results.get('has_issues'):
                issues_list.append(f"<li><strong>{check_type.replace('_', ' ').title()}:</strong> {check_results.get('total_issues', 0)} issues</li>")
        
        clinical_issues_html = f"""
        <div style="padding: 15px; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107; margin: 10px 0;">
            <h4 style="margin-top: 0;">Clinical Quality Issues</h4>
            <ul style="margin: 0; padding-left: 20px;">
                {''.join(issues_list)}
            </ul>
        </div>
        """
    
    clinical_pane = pn.pane.HTML(clinical_issues_html, sizing_mode='stretch_width') if clinical_issues_html else pn.pane.HTML("", height=0)
    
    # Layout with improved spacing
    dashboard = pn.Column(
        pn.pane.HTML(
            '<h1 style="font-size: 28px; font-weight: 700; color: #1f2937; margin-bottom: 8px;">📊 Data Quality Assessment Dashboard</h1>',
            sizing_mode='stretch_width'
        ),
        pn.Spacer(height=8),
        score_card,
        pn.Spacer(height=24),
        summary_cards,
        pn.Spacer(height=24),
        pn.Row(
            pn.Column(
                pn.pane.HTML('<h3 style="font-size: 18px; font-weight: 600; color: #1f2937;">Missing Values Analysis</h3>', sizing_mode='stretch_width'),
                missing_chart,
                sizing_mode='stretch_width'
            ),
            pn.Column(
                pn.pane.HTML('<h3 style="font-size: 18px; font-weight: 600; color: #1f2937;">Quality Score Breakdown</h3>', sizing_mode='stretch_width'),
                breakdown_chart,
                sizing_mode='stretch_width'
            ),
            sizing_mode='stretch_width'
        ),
        pn.Spacer(height=24),
        pn.Row(
            pn.Column(
                pn.pane.HTML('<h3 style="font-size: 18px; font-weight: 600; color: #1f2937;">Outlier Distribution</h3>', sizing_mode='stretch_width'),
                outlier_chart,
                sizing_mode='stretch_width'
            ),
            pn.Column(
                pn.pane.HTML('<h3 style="font-size: 18px; font-weight: 600; color: #1f2937;">Anomaly Heatmap</h3>', sizing_mode='stretch_width'),
                anomaly_heatmap,
                sizing_mode='stretch_width'
            ),
            sizing_mode='stretch_width'
        ),
        pn.Spacer(height=24),
        pn.pane.HTML('<h3 style="font-size: 18px; font-weight: 600; color: #1f2937;">Column-Level Quality Metrics</h3>', sizing_mode='stretch_width'),
        column_table,
        pn.Spacer(height=24),
        recommendations,
        clinical_pane,
        pn.Spacer(height=24),
        export_panel,
        sizing_mode='stretch_width',
        scroll=True,
        margin=(0, 20, 20, 20)
    )
    
    return dashboard


def process_file(event):
    """
    Process uploaded file and update dashboard.
    
    Args:
        event: Panel Event object from param.watch()
    """
    global current_df
    
    # Extract file value from Event object
    # event.new contains the new value, event.obj is the widget
    if event is None:
        status_pane.object = "⚠️ Please upload a CSV file."
        dashboard_pane.objects = []
        return
    
    # Get the actual file value from the event
    if hasattr(event, 'new'):
        file_input = event.new
    elif hasattr(event, 'obj') and hasattr(event.obj, 'value'):
        file_input = event.obj.value
    else:
        # Fallback: treat event as the value directly (for backwards compatibility)
        file_input = event
    
    if file_input is None or (hasattr(file_input, '__len__') and len(file_input) == 0):
        status_pane.object = '<div class="status-message status-warning">⚠️ Please upload a CSV file.</div>'
        dashboard_pane.objects = []
        return
    
    # Load CSV
    df = load_csv_file(file_input)
    
    if df is None:
        status_pane.object = '<div class="status-message status-error">❌ Error loading CSV file. Please check the file format.</div>'
        dashboard_pane.objects = []
        return
    
    # Validate DataFrame is not empty
    if len(df) == 0:
        status_pane.object = '<div class="status-message status-error">❌ Error: CSV file is empty (0 rows). Please upload a file with data.</div>'
        dashboard_pane.objects = []
        log_error(Exception("Empty DataFrame"), {'context': 'process_file', 'file_input_type': str(type(file_input[0]) if file_input and len(file_input) > 0 else None)})
        return
    
    if len(df.columns) == 0:
        status_pane.object = '<div class="status-message status-error">❌ Error: CSV file has no columns. Please check the file format.</div>'
        dashboard_pane.objects = []
        log_error(Exception("No columns"), {'context': 'process_file', 'file_rows': len(df)})
        return
    
    current_df = df
    
    # Update status
    status_pane.object = f'<div class="status-message status-info">✅ File loaded successfully! {len(df)} rows, {len(df.columns)} columns. Assessing data quality...</div>'
    
    # Create dashboard
    try:
        log_dev_event('file_upload', f"Processing file: {len(df)} rows, {len(df.columns)} columns")
        dashboard = create_dashboard(df)
        dashboard_pane.objects = [dashboard]
        score = quality_results.get('quality_score', {}).get('overall_score', 0)
        status_class = 'status-success' if score >= 70 else 'status-warning' if score >= 60 else 'status-error'
        status_pane.object = f'<div class="status-message {status_class}">✅ Assessment complete! Overall quality score: {score:.1f}/100</div>'
        log_dev_event('assessment_complete', f"Quality score: {score:.1f}/100")
    except Exception as e:
        log_error(e, {'context': 'dashboard_creation', 'file_rows': len(df) if df is not None else 0})
        status_pane.object = f'<div class="status-message status-error">❌ Error during assessment: {str(e)}</div>'
        error_html = pn.pane.HTML(
            f'<div style="padding: 24px; background: #fee2e2; border-radius: 12px; border-left: 4px solid #ef4444; color: #991b1b;"><h3 style="margin-top: 0;">Error</h3><p>{str(e)}</p></div>', 
            sizing_mode='stretch_width'
        )
        dashboard_pane.objects = [error_html]


# Create UI components
file_input = pn.widgets.FileInput(
    accept='.csv',
    multiple=False,
    name='Upload CSV File',
    sizing_mode='stretch_width'
)

file_input.param.watch(process_file, 'value')

status_pane = pn.pane.HTML(
    '<div class="status-message status-info">📁 Please upload a CSV file to begin assessment.</div>', 
    sizing_mode='stretch_width'
)
dashboard_pane = pn.Column(sizing_mode='stretch_width', scroll=True)

# Custom CSS for modern styling
custom_css = """
<style>
    :root {
        --primary-color: #2563eb;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
        --bg-color: #f9fafb;
        --text-primary: #1f2937;
        --text-secondary: #6b7280;
    }
    
    .bk-panel-widget {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    .dashboard-header {
        margin-bottom: 24px;
    }
    
    .status-message {
        padding: 12px 16px;
        border-radius: 8px;
        margin: 12px 0;
        font-size: 14px;
        line-height: 1.5;
    }
    
    .status-success {
        background-color: #d1fae5;
        color: #065f46;
        border-left: 4px solid var(--success-color);
    }
    
    .status-warning {
        background-color: #fef3c7;
        color: #92400e;
        border-left: 4px solid var(--warning-color);
    }
    
    .status-error {
        background-color: #fee2e2;
        color: #991b1b;
        border-left: 4px solid var(--danger-color);
    }
    
    .status-info {
        background-color: #dbeafe;
        color: #1e40af;
        border-left: 4px solid var(--primary-color);
    }
</style>
"""

# Main layout with modern styling
app = pn.template.FastListTemplate(
    title="TabPFN Data Quality Assessment",
    sidebar=[
        pn.pane.HTML(custom_css),
        pn.pane.Markdown("""
        ## 📊 Instructions
        
        1. Upload a CSV file using the file input below
        2. Wait for the assessment to complete
        3. Review the quality metrics and recommendations
        
        ---
        
        ## ✨ Features
        
        - **Outlier Detection**: Uses TabPFN to detect statistical outliers
        - **Missing Value Analysis**: Analyzes missing value patterns
        - **Anomaly Detection**: Identifies anomalous records
        - **Clinical Quality Checks**: Validates clinical data plausibility
        - **Quality Scoring**: Overall and component-level quality scores
        
        ---
        
        ## 🧪 Testing
        
        To test with corrupted data, use the `corrupt_data.py` script in Docker:
        
        ```bash
        docker exec <container> python corrupt_data.py --source csvlate --corruption missing --level 10
        ```
        
        See `docs/Corruption_Framework_Guide.md` for details.
        """),
        file_input,
        status_pane
    ],
    main=[
        dashboard_pane
    ],
    header_background='#2563eb',
    accent='#2563eb',
    header_color='white',
    sidebar_width=320
)

# Make servable
app.servable()

if __name__ == "__main__":
    app.show(port=5006)

