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
    create_recommendations_panel,
    create_outlier_scatter_plot,
    create_missing_values_heatmap
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


def export_quality_report(results: dict, df: pd.DataFrame, format: str = 'json') -> bytes:
    """
    Export quality assessment results to a file with row indices and flagged values.
    
    Args:
        results: Quality assessment results dictionary
        df: Original DataFrame for value lookups
        format: Export format ('json' or 'csv')
        
    Returns:
        Bytes of the exported file
    """
    if format == 'json':
        # Enhanced JSON with flagged values and row indices
        export_data = {
            'summary': {
                'overall_score': results.get('quality_score', {}).get('overall_score', 0),
                'missing_percentage': results.get('missing_assessment', {}).get('missing_percentage', 0),
                'outlier_count': results.get('outlier_results', {}).get('outlier_count', 0),
                'anomaly_count': results.get('anomaly_results', {}).get('anomaly_count', 0),
                'clinical_issues': results.get('clinical_checks', {}).get('total_issues', 0),
                'total_rows': len(df) if df is not None else 0,
                'total_columns': len(df.columns) if df is not None else 0
            },
            'flagged_values': {
                'outliers': [],
                'missing': [],
                'anomalies': [],
                'clinical_issues': []
            }
        }
        
        # Add outlier details with values
        outlier_indices = results.get('outlier_results', {}).get('outlier_indices', [])
        for outlier_info in outlier_indices:
            row_idx = outlier_info.get('row_index', -1)
            if row_idx >= 0 and df is not None and row_idx < len(df):
                row_data = df.iloc[row_idx].to_dict()
                export_data['flagged_values']['outliers'].append({
                    'row_index': row_idx,
                    'outlier_score': outlier_info.get('outlier_score', 0),
                    'percentile_rank': outlier_info.get('percentile_rank', 0),
                    'values': {str(k): str(v) for k, v in row_data.items()}
                })
        
        # Add missing value details
        missing_locations = results.get('missing_assessment', {}).get('missing_value_locations', [])
        for missing_info in missing_locations:
            row_idx = missing_info.get('row_index', -1)
            col = missing_info.get('column', '')
            if row_idx >= 0 and df is not None and row_idx < len(df) and col in df.columns:
                export_data['flagged_values']['missing'].append({
                    'row_index': row_idx,
                    'column': col,
                    'value_type': 'missing',
                    'row_values': {str(k): str(v) for k, v in df.iloc[row_idx].to_dict().items()}
                })
        
        # Add anomaly details
        anomaly_indices = results.get('anomaly_results', {}).get('anomaly_indices', [])
        for anomaly_info in anomaly_indices:
            row_idx = anomaly_info.get('row_index', -1)
            if row_idx >= 0 and df is not None and row_idx < len(df):
                row_data = df.iloc[row_idx].to_dict()
                export_data['flagged_values']['anomalies'].append({
                    'row_index': row_idx,
                    'anomaly_score': anomaly_info.get('outlier_score', 0),  # Uses outlier score
                    'percentile_rank': anomaly_info.get('percentile_rank', 0),
                    'values': {str(k): str(v) for k, v in row_data.items()}
                })
        
        json_str = json.dumps(export_data, indent=2, default=str)
        return json_str.encode('utf-8')
    
    elif format == 'csv':
        # Create summary CSV
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


def create_method_badge(method: str, fallback: str = None) -> pn.pane.HTML:
    """
    Create a badge showing the detection method used.
    
    Args:
        method: Method name (e.g., 'tabpfn_unsupervised', 'statistical_fallback')
        fallback: Fallback method if applicable
        
    Returns:
        Panel HTML pane with method badge
    """
    if method == 'statistical_fallback' or fallback == 'statistical':
        badge_html = """
        <span style="display: inline-flex; align-items: center; padding: 4px 12px; 
                     background: rgba(245, 158, 11, 0.1); color: #f59e0b; 
                     border-radius: 12px; font-size: 12px; font-weight: 500; 
                     border: 1px solid rgba(245, 158, 11, 0.3);">
            <span style="margin-right: 4px;">⚠️</span>
            Statistical Method
        </span>
        """
    elif 'tabpfn' in method.lower():
        badge_html = """
        <span style="display: inline-flex; align-items: center; padding: 4px 12px; 
                     background: rgba(16, 185, 129, 0.1); color: #10b981; 
                     border-radius: 12px; font-size: 12px; font-weight: 500; 
                     border: 1px solid rgba(16, 185, 129, 0.3);">
            <span style="margin-right: 4px;">✓</span>
            TabPFN Model
        </span>
        """
    else:
        badge_html = f"""
        <span style="display: inline-flex; align-items: center; padding: 4px 12px; 
                     background: rgba(107, 114, 128, 0.1); color: var(--text-secondary); 
                     border-radius: 12px; font-size: 12px; font-weight: 500; 
                     border: 1px solid rgba(107, 114, 128, 0.3);">
            {method}
        </span>
        """
    
    return pn.pane.HTML(badge_html, sizing_mode='stretch_width')


def create_flagged_values_tab(results: dict, df: pd.DataFrame) -> pn.Tabs:
    """
    Create a tabbed interface for inspecting flagged values.
    
    Args:
        results: Quality assessment results dictionary
        df: Original DataFrame
        
    Returns:
        Panel Tabs widget with flagged value tables
    """
    tabs = []
    
    # Outliers tab
    outlier_indices = results.get('outlier_results', {}).get('outlier_indices', [])
    if outlier_indices and df is not None:
        outlier_data = []
        for outlier_info in outlier_indices:
            row_idx = outlier_info.get('row_index', -1)
            if 0 <= row_idx < len(df):
                row_data = df.iloc[row_idx].to_dict()
                outlier_data.append({
                    'Row Index': row_idx,
                    'Outlier Score': f"{outlier_info.get('outlier_score', 0):.3f}",
                    'Percentile Rank': f"{outlier_info.get('percentile_rank', 0):.1f}%",
                    **{str(k): str(v) for k, v in row_data.items()}
                })
        
        if outlier_data:
            outlier_df = pd.DataFrame(outlier_data)
            outlier_table = pn.widgets.Tabulator(
                outlier_df,
                pagination='remote',
                page_size=20,
                sizing_mode='stretch_width',
                height=500
            )
            tabs.append(('Outliers', outlier_table))
    
    # Missing values tab
    missing_locations = results.get('missing_assessment', {}).get('missing_value_locations', [])
    if missing_locations and df is not None:
        missing_data = []
        for missing_info in missing_locations:
            row_idx = missing_info.get('row_index', -1)
            col = missing_info.get('column', '')
            if 0 <= row_idx < len(df) and col in df.columns:
                row_data = df.iloc[row_idx].to_dict()
                missing_data.append({
                    'Row Index': row_idx,
                    'Column': col,
                    'Value Type': 'Missing',
                    **{str(k): str(v) if not pd.isna(v) else 'NaN' for k, v in row_data.items()}
                })
        
        if missing_data:
            missing_df = pd.DataFrame(missing_data)
            missing_table = pn.widgets.Tabulator(
                missing_df,
                pagination='remote',
                page_size=20,
                sizing_mode='stretch_width',
                height=500
            )
            tabs.append(('Missing Values', missing_table))
    
    # Anomalies tab
    anomaly_indices = results.get('anomaly_results', {}).get('anomaly_indices', [])
    if anomaly_indices and df is not None:
        anomaly_data = []
        for anomaly_info in anomaly_indices:
            row_idx = anomaly_info.get('row_index', -1)
            if 0 <= row_idx < len(df):
                row_data = df.iloc[row_idx].to_dict()
                anomaly_data.append({
                    'Row Index': row_idx,
                    'Anomaly Score': f"{anomaly_info.get('outlier_score', 0):.3f}",
                    'Percentile Rank': f"{anomaly_info.get('percentile_rank', 0):.1f}%",
                    **{str(k): str(v) for k, v in row_data.items()}
                })
        
        if anomaly_data:
            anomaly_df = pd.DataFrame(anomaly_data)
            anomaly_table = pn.widgets.Tabulator(
                anomaly_df,
                pagination='remote',
                page_size=20,
                sizing_mode='stretch_width',
                height=500
            )
            tabs.append(('Anomalies', anomaly_table))
    
    # Clinical issues tab
    clinical_checks = results.get('clinical_checks', {})
    if clinical_checks.get('has_issues', False) and df is not None:
        clinical_data = []
        # Extract clinical issues (simplified - would need to track row indices in clinical_quality.py)
        for check_type, check_results in clinical_checks.items():
            if isinstance(check_results, dict) and check_results.get('has_issues'):
                issue_count = check_results.get('total_issues', 0)
                if issue_count > 0:
                    clinical_data.append({
                        'Issue Type': check_type.replace('_', ' ').title(),
                        'Count': issue_count,
                        'Details': str(check_results.get('details', ''))[:100]
                    })
        
        if clinical_data:
            clinical_df = pd.DataFrame(clinical_data)
            clinical_table = pn.widgets.Tabulator(
                clinical_df,
                pagination='remote',
                page_size=20,
                sizing_mode='stretch_width',
                height=500
            )
            tabs.append(('Clinical Issues', clinical_table))
    
    # If no tabs created, show message
    if not tabs:
        no_data_pane = pn.pane.HTML(
            '<div class="dashboard-card" style="padding: 24px; text-align: center; color: var(--text-secondary);">No flagged values found.</div>',
            sizing_mode='stretch_width'
        )
        return pn.Tabs([('No Data', no_data_pane)])
    
    return pn.Tabs(*tabs)


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
    
    # Outlier distribution (histogram)
    outlier_scores = results['outlier_results'].get('outlier_scores', [])
    outlier_chart = create_outlier_distribution_chart(outlier_scores)
    
    # Outlier scatter plot (new visualization)
    outlier_scatter = create_outlier_scatter_plot(results['outlier_results'], df)
    
    # Missing values heatmap (new visualization)
    missing_heatmap = create_missing_values_heatmap(results['missing_assessment'], df)
    
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
    json_data = export_quality_report(results, df, format='json')
    csv_data = export_quality_report(results, df, format='csv')
    
    # Create FileDownload widgets with proper configuration
    export_json_file = pn.widgets.FileDownload(
        file=io.BytesIO(json_data),
        filename='quality_report.json',
        button_type='primary',
        auto=False
    )
    
    export_csv_file = pn.widgets.FileDownload(
        file=io.BytesIO(csv_data),
        filename='quality_report.csv',
        button_type='primary',
        auto=False
    )
    
    export_panel = pn.Row(
        pn.pane.HTML('<h3 class="section-heading">Export Quality Report</h3>', sizing_mode='stretch_width'),
        export_json_file,
        export_csv_file,
        sizing_mode='stretch_width'
    )
    
    # Flagged values inspection tab
    flagged_values_tab = create_flagged_values_tab(results, df)
    
    # Clinical quality issues
    clinical_issues_html = ""
    if results['clinical_checks']['has_issues']:
        issues_list = []
        for check_type, check_results in results['clinical_checks'].items():
            if isinstance(check_results, dict) and check_results.get('has_issues'):
                issues_list.append(f"<li><strong>{check_type.replace('_', ' ').title()}:</strong> {check_results.get('total_issues', 0)} issues</li>")
        
        clinical_issues_html = f"""
        <div class="dashboard-card" style="padding: 15px; border-left: 4px solid var(--warning-color);">
            <h4 class="section-heading" style="margin-top: 0;">Clinical Quality Issues</h4>
            <ul style="margin: 0; padding-left: 20px; color: var(--text-primary);">
                {''.join(issues_list)}
            </ul>
        </div>
        """
    
    clinical_pane = pn.pane.HTML(clinical_issues_html, sizing_mode='stretch_width') if clinical_issues_html else pn.pane.HTML("", height=0)
    
    # Layout with improved spacing and theme-aware styling
    dashboard = pn.Column(
        pn.pane.HTML(
            '<h1 class="section-heading" style="font-size: 28px; font-weight: 700; margin-bottom: 8px;">📊 Data Quality Assessment Dashboard</h1>',
            sizing_mode='stretch_width'
        ),
        pn.Spacer(height=16),
        pn.Column(
            score_card,
            css_classes=['dashboard-card'],
            sizing_mode='stretch_width'
        ),
        pn.Spacer(height=32),
        pn.Column(
            summary_cards,
            css_classes=['dashboard-card'],
            sizing_mode='stretch_width'
        ),
        pn.Spacer(height=32),
        pn.Row(
            pn.Column(
                pn.pane.HTML('<h3 class="section-heading">Missing Values Analysis</h3>', sizing_mode='stretch_width'),
                pn.Column(missing_chart, css_classes=['dashboard-card'], sizing_mode='stretch_width'),
                sizing_mode='stretch_width',
                margin=(0, 8, 0, 0)
            ),
            pn.Column(
                pn.pane.HTML('<h3 class="section-heading">Quality Score Breakdown</h3>', sizing_mode='stretch_width'),
                pn.Column(breakdown_chart, css_classes=['dashboard-card'], sizing_mode='stretch_width'),
                sizing_mode='stretch_width',
                margin=(0, 0, 0, 8)
            ),
            sizing_mode='stretch_width'
        ),
        pn.Spacer(height=32),
        pn.Row(
            pn.Column(
                pn.Row(
                    pn.pane.HTML('<h3 class="section-heading">Outlier Distribution (Histogram)</h3>', sizing_mode='stretch_width'),
                    create_method_badge(
                        results['outlier_results'].get('method', 'unknown'),
                        results['outlier_results'].get('fallback')
                    ),
                    sizing_mode='stretch_width'
                ),
                pn.Column(outlier_chart, css_classes=['dashboard-card'], sizing_mode='stretch_width'),
                sizing_mode='stretch_width',
                margin=(0, 8, 0, 0)
            ),
            pn.Column(
                pn.Row(
                    pn.pane.HTML('<h3 class="section-heading">Anomaly Heatmap</h3>', sizing_mode='stretch_width'),
                    create_method_badge(
                        results['anomaly_results'].get('method', 'unknown'),
                        results['anomaly_results'].get('fallback')
                    ),
                    sizing_mode='stretch_width'
                ),
                pn.Column(anomaly_heatmap, css_classes=['dashboard-card'], sizing_mode='stretch_width'),
                sizing_mode='stretch_width',
                margin=(0, 0, 0, 8)
            ),
            sizing_mode='stretch_width'
        ),
        pn.Spacer(height=32),
        pn.Column(
            pn.Row(
                pn.pane.HTML('<h3 class="section-heading">Outlier Scatter Plot</h3>', sizing_mode='stretch_width'),
                create_method_badge(
                    results['outlier_results'].get('method', 'unknown'),
                    results['outlier_results'].get('fallback')
                ),
                sizing_mode='stretch_width'
            ),
            pn.pane.HTML('<p class="section-subheading">Outlier scores by row index, colored by percentile rank</p>', sizing_mode='stretch_width'),
            pn.Column(outlier_scatter, css_classes=['dashboard-card'], sizing_mode='stretch_width'),
            sizing_mode='stretch_width'
        ),
        pn.Spacer(height=32),
        pn.Column(
            pn.pane.HTML('<h3 class="section-heading">Missing Values Heatmap</h3>', sizing_mode='stretch_width'),
            pn.pane.HTML('<p class="section-subheading">Condensed view of missing value patterns across rows and columns</p>', sizing_mode='stretch_width'),
            pn.Column(missing_heatmap, css_classes=['dashboard-card'], sizing_mode='stretch_width'),
            sizing_mode='stretch_width'
        ),
        pn.Spacer(height=32),
        pn.Column(
            pn.pane.HTML('<h3 class="section-heading">Column-Level Quality Metrics</h3>', sizing_mode='stretch_width'),
            pn.Column(column_table, css_classes=['dashboard-card'], sizing_mode='stretch_width'),
            sizing_mode='stretch_width'
        ),
        pn.Spacer(height=32),
        pn.Column(
            pn.pane.HTML('<h3 class="section-heading">Flagged Values Inspection</h3>', sizing_mode='stretch_width'),
            pn.pane.HTML('<p class="section-subheading">Inspect specific rows and values that were flagged as outliers, missing, anomalies, or clinical issues</p>', sizing_mode='stretch_width'),
            pn.Column(flagged_values_tab, css_classes=['dashboard-card'], sizing_mode='stretch_width'),
            sizing_mode='stretch_width'
        ),
        pn.Spacer(height=32),
        pn.Column(
            recommendations,
            css_classes=['dashboard-card'],
            sizing_mode='stretch_width'
        ),
        pn.Column(
            clinical_pane,
            css_classes=['dashboard-card'],
            sizing_mode='stretch_width'
        ) if clinical_issues_html else pn.Spacer(height=0),
        pn.Spacer(height=32),
        pn.Column(
            export_panel,
            css_classes=['dashboard-card'],
            sizing_mode='stretch_width'
        ),
        sizing_mode='stretch_width',
        scroll=True,
        margin=(0, 24, 24, 24)
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
            f'<div class="dashboard-card" style="padding: 24px; border-left: 4px solid var(--danger-color);"><h3 style="margin-top: 0; color: var(--text-primary);">Error</h3><p style="color: var(--text-primary);">{str(e)}</p></div>', 
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

# Create dashboard pane - will be updated reactively
dashboard_pane = pn.Column(sizing_mode='stretch_width', scroll=True)

# Custom CSS for modern styling with dark mode support
custom_css = """
<style>
    /* Light mode CSS variables */
    :root {
        --primary-color: #2563eb;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
        --bg-color: #f9fafb;
        --bg-secondary: #ffffff;
        --text-primary: #1f2937;
        --text-secondary: #6b7280;
        --text-tertiary: #9ca3af;
        --border-color: #e5e7eb;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --spacing-xs: 4px;
        --spacing-sm: 8px;
        --spacing-md: 16px;
        --spacing-lg: 24px;
        --spacing-xl: 32px;
        --spacing-2xl: 48px;
    }
    
    /* Dark mode CSS variables */
    [data-theme="dark"], 
    .dark-mode,
    .bk-root[data-theme="dark"] {
        --primary-color: #3b82f6;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
        --bg-color: #111827;
        --bg-secondary: #1f2937;
        --text-primary: #f9fafb;
        --text-secondary: #d1d5db;
        --text-tertiary: #9ca3af;
        --border-color: #374151;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3);
    }
    
    /* Base styling */
    .bk-panel-widget {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Dashboard spacing utilities */
    .dashboard-section {
        margin-bottom: var(--spacing-xl);
        padding: var(--spacing-lg);
        background: var(--bg-secondary);
        border-radius: 12px;
        border: 1px solid var(--border-color);
        box-shadow: var(--shadow-sm);
    }
    
    .dashboard-header {
        margin-bottom: var(--spacing-lg);
    }
    
    /* Status messages with theme support */
    .status-message {
        padding: 12px 16px;
        border-radius: 8px;
        margin: 12px 0;
        font-size: 14px;
        line-height: 1.5;
        transition: all 0.2s ease;
    }
    
    .status-success {
        background-color: rgba(16, 185, 129, 0.1);
        color: var(--success-color);
        border-left: 4px solid var(--success-color);
    }
    
    [data-theme="dark"] .status-success,
    .dark-mode .status-success {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34d399;
    }
    
    .status-warning {
        background-color: rgba(245, 158, 11, 0.1);
        color: var(--warning-color);
        border-left: 4px solid var(--warning-color);
    }
    
    [data-theme="dark"] .status-warning,
    .dark-mode .status-warning {
        background-color: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
    }
    
    .status-error {
        background-color: rgba(239, 68, 68, 0.1);
        color: var(--danger-color);
        border-left: 4px solid var(--danger-color);
    }
    
    [data-theme="dark"] .status-error,
    .dark-mode .status-error {
        background-color: rgba(239, 68, 68, 0.15);
        color: #f87171;
    }
    
    .status-info {
        background-color: rgba(37, 99, 235, 0.1);
        color: var(--primary-color);
        border-left: 4px solid var(--primary-color);
    }
    
    [data-theme="dark"] .status-info,
    .dark-mode .status-info {
        background-color: rgba(59, 130, 246, 0.15);
        color: #60a5fa;
    }
    
    /* Theme-aware headings */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary);
        transition: color 0.2s ease;
    }
    
    /* Tabulator table styling */
    .tabulator {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        border-radius: 8px;
        overflow: hidden;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
    }
    
    .tabulator .tabulator-header {
        background: var(--bg-color);
        border-bottom: 2px solid var(--border-color);
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .tabulator .tabulator-header .tabulator-col {
        background: var(--bg-color);
        color: var(--text-primary);
        border-right: 1px solid var(--border-color);
    }
    
    .tabulator .tabulator-header .tabulator-col:hover {
        background: var(--bg-secondary);
    }
    
    .tabulator .tabulator-tableHolder {
        background: var(--bg-secondary);
    }
    
    .tabulator .tabulator-table {
        background: var(--bg-secondary);
    }
    
    .tabulator .tabulator-row {
        background: var(--bg-secondary);
        color: var(--text-primary);
        border-bottom: 1px solid var(--border-color);
        transition: background-color 0.15s ease;
    }
    
    .tabulator .tabulator-row:hover {
        background: var(--bg-color);
    }
    
    .tabulator .tabulator-cell {
        color: var(--text-primary);
        border-right: 1px solid var(--border-color);
        padding: 12px 16px;
    }
    
    /* Custom scrollbar styling for Tabulator */
    .tabulator .tabulator-tableHolder::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    .tabulator .tabulator-tableHolder::-webkit-scrollbar-track {
        background: var(--bg-color);
        border-radius: 5px;
    }
    
    .tabulator .tabulator-tableHolder::-webkit-scrollbar-thumb {
        background: var(--text-tertiary);
        border-radius: 5px;
        transition: background 0.2s ease;
    }
    
    .tabulator .tabulator-tableHolder::-webkit-scrollbar-thumb:hover {
        background: var(--text-secondary);
    }
    
    /* Firefox scrollbar */
    .tabulator .tabulator-tableHolder {
        scrollbar-width: thin;
        scrollbar-color: var(--text-tertiary) var(--bg-color);
    }
    
    /* Pagination styling */
    .tabulator .tabulator-footer {
        background: var(--bg-color);
        border-top: 1px solid var(--border-color);
        color: var(--text-primary);
    }
    
    .tabulator .tabulator-page {
        color: var(--text-primary);
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        margin: 0 2px;
        padding: 6px 12px;
        transition: all 0.2s ease;
    }
    
    .tabulator .tabulator-page:hover {
        background: var(--bg-color);
        border-color: var(--primary-color);
    }
    
    .tabulator .tabulator-page.active {
        background: var(--primary-color);
        color: white;
        border-color: var(--primary-color);
    }
    
    /* Improved spacing for dashboard sections */
    .dashboard-card {
        padding: var(--spacing-lg);
        margin-bottom: var(--spacing-lg);
        background: var(--bg-secondary);
        border-radius: 12px;
        border: 1px solid var(--border-color);
        box-shadow: var(--shadow-sm);
        transition: box-shadow 0.2s ease;
    }
    
    .dashboard-card:hover {
        box-shadow: var(--shadow-md);
    }
    
    /* Section headings */
    .section-heading {
        font-size: 18px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: var(--spacing-md);
        margin-top: 0;
    }
    
    .section-subheading {
        font-size: 13px;
        color: var(--text-secondary);
        margin-bottom: var(--spacing-sm);
        margin-top: 0;
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

# Watch for theme changes and restore dashboard if DataFrame exists
def on_theme_change(event):
    """Restore dashboard when theme changes if we have data."""
    global current_df
    if current_df is not None and len(dashboard_pane.objects) == 0:
        # Theme changed and dashboard was cleared, recreate it
        try:
            dashboard = create_dashboard(current_df)
            dashboard_pane.objects = [dashboard]
        except Exception as e:
            log_error(e, {'context': 'theme_change_restore', 'df_rows': len(current_df) if current_df is not None else 0})

# Watch the app's theme parameter for changes
app.param.watch(on_theme_change, 'theme')

# Make servable
app.servable()

if __name__ == "__main__":
    app.show(port=5006)

