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
    Create a quality score card with color coding and modern styling.
    
    Args:
        score: Quality score (0-100)
        title: Title for the card
        
    Returns:
        Panel HTML pane with the score card
    """
    formatted_score, color_class = format_quality_score(score)
    
    # Modern color palette
    color_map = {
        'success': '#10b981',  # Modern green
        'warning': '#f59e0b',  # Amber
        'info': '#2563eb',     # Professional blue
        'danger': '#ef4444'    # Modern red
    }
    
    bg_color_map = {
        'success': '#d1fae5',  # Light green background
        'warning': '#fef3c7',  # Light amber background
        'info': '#dbeafe',     # Light blue background
        'danger': '#fee2e2'    # Light red background
    }
    
    color = color_map.get(color_class, '#6b7280')
    bg_color = bg_color_map.get(color_class, '#f3f4f6')
    
    html = f"""
    <div style="text-align: center; padding: 32px 24px; background: {bg_color}; border-radius: 12px; border: 2px solid {color}; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); transition: transform 0.2s;">
        <h3 style="margin: 0 0 16px 0; color: #1f2937; font-size: 18px; font-weight: 600; letter-spacing: -0.025em;">{title}</h3>
        <div style="font-size: 56px; font-weight: 700; color: {color}; margin: 16px 0; letter-spacing: -0.05em;">
            {formatted_score}
        </div>
        <div style="font-size: 14px; color: #6b7280; font-weight: 500;">out of 100</div>
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
    Create a bar chart showing missing values per column with modern styling.
    
    Args:
        missing_stats: Dictionary with missing value statistics
        
    Returns:
        Panel Plotly pane
    """
    column_stats = missing_stats.get('column_missing_stats', {})
    
    if not column_stats:
        # Empty chart with modern styling
        fig = go.Figure()
        fig.add_annotation(
            text="No missing values detected",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#6b7280")
        )
        fig.update_layout(
            plot_bgcolor='#f9fafb',
            paper_bgcolor='#ffffff',
            height=400
        )
        return pn.pane.Plotly(fig, sizing_mode='stretch_width')
    
    columns = list(column_stats.keys())
    percentages = [column_stats[col]['percentage'] for col in columns]
    
    # Modern color scheme
    colors = ['#ef4444' if p > 20 else '#f59e0b' if p > 10 else '#10b981' for p in percentages]
    
    fig = go.Figure(data=[
        go.Bar(
            x=columns,
            y=percentages,
            marker_color=colors,
            text=[f"{p:.1f}%" for p in percentages],
            textposition='outside',
            textfont=dict(size=11, color="#374151"),
            marker_line_color='#ffffff',
            marker_line_width=1.5,
            opacity=0.9
        )
    ])
    
    fig.update_layout(
        title=dict(
            text='Missing Values by Column',
            font=dict(size=18, color="#1f2937", family="Inter, system-ui, sans-serif")
        ),
        xaxis=dict(
            title=dict(text='Column', font=dict(size=13, color="#6b7280")),
            tickfont=dict(size=11, color="#6b7280"),
            gridcolor='#e5e7eb',
            gridwidth=1
        ),
        yaxis=dict(
            title=dict(text='Missing Percentage (%)', font=dict(size=13, color="#6b7280")),
            tickfont=dict(size=11, color="#6b7280"),
            gridcolor='#e5e7eb',
            gridwidth=1
        ),
        height=400,
        showlegend=False,
        plot_bgcolor='#f9fafb',
        paper_bgcolor='#ffffff',
        margin=dict(l=20, r=20, t=50, b=50)
    )
    
    return pn.pane.Plotly(fig, sizing_mode='stretch_width')


def create_outlier_distribution_chart(outlier_scores: List[float]) -> pn.pane.Plotly:
    """
    Create a histogram showing outlier score distribution with modern styling.
    
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
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#6b7280")
        )
        fig.update_layout(
            plot_bgcolor='#f9fafb',
            paper_bgcolor='#ffffff',
            height=400
        )
        return pn.pane.Plotly(fig, sizing_mode='stretch_width')
    
    fig = go.Figure(data=[
        go.Histogram(
            x=outlier_scores,
            nbinsx=50,
            marker_color='#2563eb',
            marker_line_color='#ffffff',
            marker_line_width=1,
            opacity=0.8
        )
    ])
    
    # Add threshold line with modern styling
    threshold = np.percentile(outlier_scores, 95)
    fig.add_vline(
        x=threshold,
        line_dash="dash",
        line_color="#ef4444",
        line_width=2,
        annotation_text=f"95th percentile ({threshold:.2f})",
        annotation_position="top",
        annotation_font_size=11,
        annotation_font_color="#ef4444"
    )
    
    fig.update_layout(
        title=dict(
            text='Outlier Score Distribution',
            font=dict(size=18, color="#1f2937", family="Inter, system-ui, sans-serif")
        ),
        xaxis=dict(
            title=dict(text='Outlier Score', font=dict(size=13, color="#6b7280")),
            tickfont=dict(size=11, color="#6b7280"),
            gridcolor='#e5e7eb',
            gridwidth=1
        ),
        yaxis=dict(
            title=dict(text='Frequency', font=dict(size=13, color="#6b7280")),
            tickfont=dict(size=11, color="#6b7280"),
            gridcolor='#e5e7eb',
            gridwidth=1
        ),
        height=400,
        showlegend=False,
        plot_bgcolor='#f9fafb',
        paper_bgcolor='#ffffff',
        margin=dict(l=20, r=20, t=50, b=50)
    )
    
    return pn.pane.Plotly(fig, sizing_mode='stretch_width')


def create_quality_breakdown_chart(component_scores: Dict) -> pn.pane.Plotly:
    """
    Create a radar/spider chart showing component quality scores with modern styling.
    
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
        line_color='#2563eb',
        fillcolor='rgba(37, 99, 235, 0.2)',
        line_width=3,
        marker=dict(size=8, color='#2563eb')
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=11, color="#6b7280"),
                gridcolor='#e5e7eb',
                linecolor='#d1d5db'
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color="#374151")
            )
        ),
        showlegend=False,
        title=dict(
            text='Quality Score Breakdown',
            font=dict(size=18, color="#1f2937", family="Inter, system-ui, sans-serif")
        ),
        height=400,
        paper_bgcolor='#ffffff',
        plot_bgcolor='#f9fafb'
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
    Create a heatmap showing anomaly patterns with modern styling.
    
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
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#6b7280")
        )
        fig.update_layout(
            plot_bgcolor='#f9fafb',
            paper_bgcolor='#ffffff',
            height=400
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
        colorscale=[[0, '#10b981'], [0.5, '#f59e0b'], [1, '#ef4444']],  # Green-Yellow-Red
        showscale=True,
        colorbar=dict(
            title=dict(text="Anomaly Score", font=dict(size=12, color="#6b7280")),
            tickfont=dict(size=10, color="#6b7280")
        ),
        hovertemplate='Row: %{y}<br>Column: %{x}<br>Score: %{z:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text='Anomaly Score Heatmap (First 100 Records)',
            font=dict(size=18, color="#1f2937", family="Inter, system-ui, sans-serif")
        ),
        xaxis=dict(
            title=dict(text='Column Group', font=dict(size=13, color="#6b7280")),
            tickfont=dict(size=11, color="#6b7280"),
            gridcolor='#e5e7eb'
        ),
        yaxis=dict(
            title=dict(text='Row', font=dict(size=13, color="#6b7280")),
            tickfont=dict(size=11, color="#6b7280"),
            gridcolor='#e5e7eb'
        ),
        height=400,
        plot_bgcolor='#f9fafb',
        paper_bgcolor='#ffffff',
        margin=dict(l=20, r=20, t=50, b=50)
    )
    
    return pn.pane.Plotly(fig, sizing_mode='stretch_width')


def create_recommendations_panel(quality_results: Dict) -> pn.pane.HTML:
    """
    Create a panel with actionable recommendations and modern styling.
    
    Args:
        quality_results: Dictionary with quality assessment results
        
    Returns:
        Panel HTML pane with recommendations
    """
    recommendations = []
    
    overall_score = quality_results.get('quality_score', {}).get('overall_score', 100)
    
    if overall_score < 60:
        recommendations.append(("Critical", "Data quality is below acceptable thresholds. Review and clean data before use.", "#ef4444"))
    
    missing_assessment = quality_results.get('missing_assessment', {})
    missing_pct = missing_assessment.get('missing_percentage', 0)
    if missing_pct > 20:
        recommendations.append(("Missing Values", f"{missing_pct:.1f}% of values are missing. Consider imputation or data collection review.", "#f59e0b"))
    elif missing_pct > 10:
        recommendations.append(("Missing Values", f"{missing_pct:.1f}% missing values detected. Review patterns.", "#2563eb"))
    
    outlier_results = quality_results.get('outlier_results', {})
    outlier_count = outlier_results.get('outlier_count', 0)
    if outlier_count > 50:
        recommendations.append(("Outliers", f"{outlier_count} outliers detected. Review for data entry errors or valid extreme values.", "#f59e0b"))
    
    clinical_checks = quality_results.get('clinical_checks', {})
    if clinical_checks.get('has_issues', False):
        total_issues = clinical_checks.get('total_issues', 0)
        recommendations.append(("Clinical Issues", f"{total_issues} clinical quality issues found. Review for impossible values and inconsistencies.", "#ef4444"))
    
    if not recommendations:
        recommendations.append(("Good", "Data quality appears acceptable. Continue monitoring.", "#10b981"))
    
    # Build recommendation items with modern styling
    items_html = ""
    for title, message, color in recommendations:
        items_html += f"""
        <li style="margin: 12px 0; padding: 12px; background: #ffffff; border-radius: 8px; border-left: 4px solid {color}; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);">
            <strong style="color: {color}; font-size: 14px; display: block; margin-bottom: 4px;">{title}</strong>
            <span style="color: #374151; font-size: 13px; line-height: 1.5;">{message}</span>
        </li>
        """
    
    html = f"""
    <div style="padding: 24px; background: #f9fafb; border-radius: 12px; border: 1px solid #e5e7eb; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);">
        <h4 style="margin: 0 0 16px 0; color: #1f2937; font-size: 18px; font-weight: 600;">Recommendations</h4>
        <ul style="margin: 0; padding-left: 0; list-style: none;">
            {items_html}
        </ul>
    </div>
    """
    
    return pn.pane.HTML(html, sizing_mode='stretch_width')

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


def create_outlier_scatter_plot(outlier_results: Dict, df: pd.DataFrame) -> pn.pane.Plotly:
    """
    Create a scatter plot showing outlier scores with percentile-based coloring.
    
    Args:
        outlier_results: Dictionary with outlier detection results
        df: Original DataFrame for value lookups
        
    Returns:
        Panel Plotly pane with scatter plot
    """
    outlier_scores = outlier_results.get('outlier_scores', [])
    percentile_ranks = outlier_results.get('percentile_ranks', [])
    outlier_indices = outlier_results.get('outlier_indices', [])
    
    if not outlier_scores or not percentile_ranks:
        fig = go.Figure()
        fig.add_annotation(
            text="No outlier data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#6b7280")
        )
        fig.update_layout(
            plot_bgcolor='#f9fafb',
            paper_bgcolor='#ffffff',
            height=400
        )
        return pn.pane.Plotly(fig, sizing_mode='stretch_width')
    
    # Create row indices (0 to n-1)
    row_indices = list(range(len(outlier_scores)))
    
    # Color mapping based on percentile rank
    colors = []
    for rank in percentile_ranks:
        if rank < 50:
            colors.append('#10b981')  # Green
        elif rank < 90:
            colors.append('#f59e0b')  # Yellow/Amber
        elif rank < 95:
            colors.append('#f97316')  # Orange
        else:
            colors.append('#ef4444')  # Red
    
    # Create scatter plot
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=row_indices,
        y=outlier_scores,
        mode='markers',
        marker=dict(
            color=colors,
            size=8,
            opacity=0.7,
            line=dict(width=1, color='white')
        ),
        hovertemplate='<b>Row Index:</b> %{x}<br>' +
                      '<b>Outlier Score:</b> %{y:.3f}<br>' +
                      '<b>Percentile Rank:</b> %{customdata:.1f}%<extra></extra>',
        customdata=percentile_ranks,
        name='Outliers'
    ))
    
    # Add threshold line at 95th percentile
    threshold = np.percentile(outlier_scores, 95)
    fig.add_hline(
        y=threshold,
        line_dash="dash",
        line_color="#ef4444",
        line_width=2,
        annotation_text=f"95th percentile ({threshold:.2f})",
        annotation_position="right",
        annotation_font_size=11,
        annotation_font_color="#ef4444"
    )
    
    fig.update_layout(
        title=dict(
            text='Outlier Distribution by Row Index',
            font=dict(size=18, color="#1f2937", family="Inter, system-ui, sans-serif")
        ),
        xaxis=dict(
            title=dict(text='Row Index', font=dict(size=13, color="#6b7280")),
            tickfont=dict(size=11, color="#6b7280"),
            gridcolor='#e5e7eb',
            gridwidth=1
        ),
        yaxis=dict(
            title=dict(text='Outlier Score', font=dict(size=13, color="#6b7280")),
            tickfont=dict(size=11, color="#6b7280"),
            gridcolor='#e5e7eb',
            gridwidth=1
        ),
        height=400,
        showlegend=False,
        plot_bgcolor='#f9fafb',
        paper_bgcolor='#ffffff',
        margin=dict(l=20, r=20, t=50, b=50)
    )
    
    return pn.pane.Plotly(fig, sizing_mode='stretch_width')


def create_missing_values_heatmap(missing_assessment: Dict, df: pd.DataFrame) -> pn.pane.Plotly:
    """
    Create a condensed heatmap showing missing value patterns.
    
    Args:
        missing_assessment: Dictionary with missing value assessment results
        df: Original DataFrame
        
    Returns:
        Panel Plotly pane with heatmap
    """
    columns_with_missing = missing_assessment.get('columns_with_missing', [])
    
    if not columns_with_missing or df is None or len(df) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No missing values found",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#6b7280")
        )
        fig.update_layout(
            plot_bgcolor='#f9fafb',
            paper_bgcolor='#ffffff',
            height=400
        )
        return pn.pane.Plotly(fig, sizing_mode='stretch_width')
    
    # Sample rows if dataset is too large (>1000 rows)
    if len(df) > 1000:
        # Take first 500 and last 500 rows
        first_500 = df.head(500)
        last_500 = df.tail(500)
        sample_df = pd.concat([first_500, last_500])
        row_labels = [f"Row {idx}" for idx in list(first_500.index) + list(last_500.index)]
    else:
        sample_df = df
        row_labels = [f"Row {idx}" for idx in df.index]
    
    # Create binary matrix: 0 = present, 1 = missing
    missing_matrix = []
    for idx, row in sample_df.iterrows():
        row_data = []
        for col in columns_with_missing:
            row_data.append(1 if pd.isna(row[col]) else 0)
        missing_matrix.append(row_data)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=missing_matrix,
        x=columns_with_missing,
        y=row_labels,
        colorscale=[[0, '#ffffff'], [1, '#ef4444']],  # White to red
        showscale=True,
        colorbar=dict(
            title=dict(text="Missing", side="right"),
            tickmode="array",
            tickvals=[0, 1],
            ticktext=["Present", "Missing"]
        ),
        hovertemplate='<b>Row:</b> %{y}<br>' +
                      '<b>Column:</b> %{x}<br>' +
                      '<b>Status:</b> %{customdata}<extra></extra>',
        customdata=[["Missing" if val == 1 else "Present" for val in row] for row in missing_matrix]
    ))
    
    fig.update_layout(
        title=dict(
            text='Missing Values Heatmap',
            font=dict(size=18, color="#1f2937", family="Inter, system-ui, sans-serif")
        ),
        xaxis=dict(
            title=dict(text='Column', font=dict(size=13, color="#6b7280")),
            tickfont=dict(size=10, color="#6b7280"),
            tickangle=-45
        ),
        yaxis=dict(
            title=dict(text='Row', font=dict(size=13, color="#6b7280")),
            tickfont=dict(size=10, color="#6b7280")
        ),
        height=min(600, max(400, len(sample_df) * 2)),
        plot_bgcolor='#f9fafb',
        paper_bgcolor='#ffffff',
        margin=dict(l=20, r=20, t=50, b=100)
    )
    
    return pn.pane.Plotly(fig, sizing_mode='stretch_width')

