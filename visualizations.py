"""
Panel visualization components for data quality metrics.
"""

import panel as pn
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional
from utils import format_quality_score


def create_quality_score_card(score: float, title: str = "Overall Quality Score") -> pn.pane.HTML:
    """
    Create a quality score card with color coding.
    
    Args:
        score: Quality score (0-100)
        title: Title for the card
        
    Returns:
        Panel HTML pane with the score card
    """
    formatted_score, color_class = format_quality_score(score)
    
    color_map = {
        'success': '#28a745',  # Green
        'warning': '#ffc107',  # Yellow
        'info': '#17a2b8',    # Blue
        'danger': '#dc3545'   # Red
    }
    
    color = color_map.get(color_class, '#6c757d')
    
    html = f"""
    <div style="text-align: center; padding: 20px; background: {color}20; border-radius: 8px; border: 2px solid {color};">
        <h3 style="margin: 0 0 10px 0; color: #333;">{title}</h3>
        <div style="font-size: 48px; font-weight: bold; color: {color}; margin: 10px 0;">
            {formatted_score}
        </div>
        <div style="font-size: 14px; color: #666;">out of 100</div>
    </div>
    """
    
    return pn.pane.HTML(html, sizing_mode='stretch_width')


def create_summary_cards(stats: Dict) -> pn.Row:
    """
    Create summary cards for key metrics.
    
    Args:
        stats: Dictionary with statistics
        
    Returns:
        Panel Row with summary cards
    """
    cards = []
    
    # Total Records Card
    cards.append(pn.indicators.Number(
        name='Total Records',
        value=stats.get('total_rows', 0),
        format='{value:,.0f}',
        colors=[(50, '#28a745')]
    ))
    
    # Missing Values Card
    missing_pct = stats.get('missing_percentage', 0)
    cards.append(pn.indicators.Number(
        name='Missing Values',
        value=missing_pct,
        format='{value:.1f}%',
        colors=[(5, '#28a745'), (20, '#ffc107'), (50, '#dc3545')]
    ))
    
    # Outlier Count Card
    outlier_count = stats.get('outlier_count', 0)
    cards.append(pn.indicators.Number(
        name='Outliers Detected',
        value=outlier_count,
        format='{value:,.0f}',
        colors=[(10, '#28a745'), (50, '#ffc107'), (100, '#dc3545')]
    ))
    
    # Duplicate Rows Card
    duplicate_pct = stats.get('duplicate_percentage', 0)
    cards.append(pn.indicators.Number(
        name='Duplicate Rows',
        value=duplicate_pct,
        format='{value:.1f}%',
        colors=[(5, '#28a745'), (10, '#ffc107'), (20, '#dc3545')]
    ))
    
    return pn.Row(*cards, sizing_mode='stretch_width')


def create_missing_values_chart(missing_stats: Dict) -> pn.pane.Plotly:
    """
    Create a bar chart showing missing values per column.
    
    Args:
        missing_stats: Dictionary with missing value statistics
        
    Returns:
        Panel Plotly pane
    """
    column_stats = missing_stats.get('column_missing_stats', {})
    
    if not column_stats:
        # Empty chart
        fig = go.Figure()
        fig.add_annotation(
            text="No missing values detected",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return pn.pane.Plotly(fig, sizing_mode='stretch_width')
    
    columns = list(column_stats.keys())
    percentages = [column_stats[col]['percentage'] for col in columns]
    
    fig = go.Figure(data=[
        go.Bar(
            x=columns,
            y=percentages,
            marker_color=['#dc3545' if p > 20 else '#ffc107' if p > 10 else '#28a745' for p in percentages],
            text=[f"{p:.1f}%" for p in percentages],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title='Missing Values by Column',
        xaxis_title='Column',
        yaxis_title='Missing Percentage (%)',
        height=400,
        showlegend=False
    )
    
    return pn.pane.Plotly(fig, sizing_mode='stretch_width')


def create_outlier_distribution_chart(outlier_scores: List[float]) -> pn.pane.Plotly:
    """
    Create a histogram showing outlier score distribution.
    
    Args:
        outlier_scores: List of outlier scores
        
    Returns:
        Panel Plotly pane
    """
    if not outlier_scores:
        fig = go.Figure()
        fig.add_annotation(
            text="No outlier scores available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return pn.pane.Plotly(fig, sizing_mode='stretch_width')
    
    fig = go.Figure(data=[
        go.Histogram(
            x=outlier_scores,
            nbinsx=50,
            marker_color='#17a2b8',
            opacity=0.7
        )
    ])
    
    # Add threshold line
    threshold = np.percentile(outlier_scores, 95)
    fig.add_vline(
        x=threshold,
        line_dash="dash",
        line_color="red",
        annotation_text=f"95th percentile ({threshold:.2f})"
    )
    
    fig.update_layout(
        title='Outlier Score Distribution',
        xaxis_title='Outlier Score',
        yaxis_title='Frequency',
        height=400,
        showlegend=False
    )
    
    return pn.pane.Plotly(fig, sizing_mode='stretch_width')


def create_quality_breakdown_chart(component_scores: Dict) -> pn.pane.Plotly:
    """
    Create a radar/spider chart showing component quality scores.
    
    Args:
        component_scores: Dictionary with component scores
        
    Returns:
        Panel Plotly pane
    """
    categories = list(component_scores.keys())
    values = [component_scores[cat] for cat in categories]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Quality Scores',
        line_color='#17a2b8'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=False,
        title='Quality Score Breakdown',
        height=400
    )
    
    return pn.pane.Plotly(fig, sizing_mode='stretch_width')


def create_column_quality_table(column_quality: Dict[str, Dict]) -> pn.widgets.Tabulator:
    """
    Create a table showing quality metrics for each column.
    
    Args:
        column_quality: Dictionary mapping column names to quality metrics
        
    Returns:
        Panel Tabulator widget
    """
    rows = []
    for col, metrics in column_quality.items():
        rows.append({
            'Column': col,
            'Quality Score': f"{metrics.get('quality_score', 0):.1f}",
            'Missing %': f"{metrics.get('missing_percentage', 0):.1f}",
            'Missing Count': metrics.get('missing_count', 0),
            'Data Type': metrics.get('data_type', 'unknown'),
            'Unique Values': metrics.get('unique_values', 0)
        })
    
    df = pd.DataFrame(rows)
    
    # Sort by quality score
    df = df.sort_values('Quality Score', ascending=False)
    
    return pn.widgets.Tabulator(
        df,
        pagination='remote',
        page_size=10,
        sizing_mode='stretch_width',
        height=400
    )


def create_anomaly_heatmap(anomaly_scores: List[float], n_rows: int = 100) -> pn.pane.Plotly:
    """
    Create a heatmap showing anomaly patterns.
    
    Args:
        anomaly_scores: List of anomaly scores
        n_rows: Number of rows to display
        
    Returns:
        Panel Plotly pane
    """
    if not anomaly_scores:
        fig = go.Figure()
        fig.add_annotation(
            text="No anomaly scores available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return pn.pane.Plotly(fig, sizing_mode='stretch_width')
    
    # Reshape scores into a grid for visualization
    scores_array = np.array(anomaly_scores[:n_rows])
    n_cols = min(10, len(scores_array))
    n_display_rows = len(scores_array) // n_cols + (1 if len(scores_array) % n_cols else 0)
    
    # Pad if necessary
    padded_scores = np.pad(
        scores_array,
        (0, n_display_rows * n_cols - len(scores_array)),
        mode='constant',
        constant_values=0
    )
    
    heatmap_data = padded_scores.reshape(n_display_rows, n_cols)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        colorscale='RdYlGn_r',  # Red-Yellow-Green reversed
        showscale=True,
        colorbar=dict(title="Anomaly Score")
    ))
    
    fig.update_layout(
        title='Anomaly Score Heatmap (First 100 Records)',
        xaxis_title='Column Group',
        yaxis_title='Row',
        height=400
    )
    
    return pn.pane.Plotly(fig, sizing_mode='stretch_width')


def create_recommendations_panel(quality_results: Dict) -> pn.pane.HTML:
    """
    Create a panel with actionable recommendations.
    
    Args:
        quality_results: Dictionary with quality assessment results
        
    Returns:
        Panel HTML pane with recommendations
    """
    recommendations = []
    
    overall_score = quality_results.get('quality_score', {}).get('overall_score', 100)
    
    if overall_score < 60:
        recommendations.append("⚠️ <strong>Critical:</strong> Data quality is below acceptable thresholds. Review and clean data before use.")
    
    missing_assessment = quality_results.get('missing_assessment', {})
    missing_pct = missing_assessment.get('missing_percentage', 0)
    if missing_pct > 20:
        recommendations.append(f"📊 <strong>Missing Values:</strong> {missing_pct:.1f}% of values are missing. Consider imputation or data collection review.")
    elif missing_pct > 10:
        recommendations.append(f"📊 <strong>Missing Values:</strong> {missing_pct:.1f}% missing values detected. Review patterns.")
    
    outlier_results = quality_results.get('outlier_results', {})
    outlier_count = outlier_results.get('outlier_count', 0)
    if outlier_count > 50:
        recommendations.append(f"🔍 <strong>Outliers:</strong> {outlier_count} outliers detected. Review for data entry errors or valid extreme values.")
    
    clinical_checks = quality_results.get('clinical_checks', {})
    if clinical_checks.get('has_issues', False):
        total_issues = clinical_checks.get('total_issues', 0)
        recommendations.append(f"🏥 <strong>Clinical Issues:</strong> {total_issues} clinical quality issues found. Review for impossible values and inconsistencies.")
    
    if not recommendations:
        recommendations.append("✅ <strong>Good:</strong> Data quality appears acceptable. Continue monitoring.")
    
    html = f"""
    <div style="padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #17a2b8;">
        <h4 style="margin-top: 0;">Recommendations</h4>
        <ul style="margin: 0; padding-left: 20px;">
            {''.join([f'<li style="margin: 8px 0;">{rec}</li>' for rec in recommendations])}
        </ul>
    </div>
    """
    
    return pn.pane.HTML(html, sizing_mode='stretch_width')

