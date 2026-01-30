"""Visualization module for paper clustering results.

This module provides Plotly-based interactive scatter plots for visualizing
paper clusters in 2D space with hover information.

WHY: Interactive visualization helps explore cluster structure and identify
     key papers within each theme.
HOW: Creates Plotly scatter plots with color-coded clusters and hover tooltips
     showing paper details (title, year, citations, cluster ID).
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from plotly.graph_objects import Figure

    from papernavigator.cluster import ClusteringResult


# Color palette for clusters (colorblind-friendly)
CLUSTER_COLORS = [
    "#1f77b4",  # blue
    "#ff7f0e",  # orange
    "#2ca02c",  # green
    "#d62728",  # red
    "#9467bd",  # purple
    "#8c564b",  # brown
    "#e377c2",  # pink
    "#7f7f7f",  # gray
    "#bcbd22",  # olive
    "#17becf",  # cyan
]

# Color for noise points (HDBSCAN -1 label)
NOISE_COLOR = "#cccccc"


def create_cluster_plot(
    papers: list[dict[str, Any]],
    coords: np.ndarray,
    labels: np.ndarray,
    title: str = "Paper Clusters",
) -> "Figure":
    """Create an interactive Plotly scatter plot of clustered papers.
    
    Each point represents a paper, colored by cluster assignment.
    Hover shows: title, year, citations, cluster ID.
    
    Args:
        papers: List of paper dictionaries with 'title', 'year', 'citation_count'
        coords: 2D coordinates from dimensionality reduction (n_papers, 2)
        labels: Cluster labels (n_papers,)
        title: Plot title
        
    Returns:
        Plotly Figure object
    """
    import plotly.graph_objects as go

    # Get unique labels
    unique_labels = sorted(set(labels))

    traces = []

    for label in unique_labels:
        # Get indices for this cluster
        mask = labels == label
        indices = np.where(mask)[0]

        # Get data for this cluster
        x = coords[mask, 0]
        y = coords[mask, 1]

        # Build hover text
        hover_texts = []
        for idx in indices:
            paper = papers[idx]
            paper_title = paper.get("title", "Unknown")
            # Truncate long titles
            if len(paper_title) > 80:
                paper_title = paper_title[:77] + "..."

            year = paper.get("year", "N/A")
            citations = paper.get("citation_count", 0)

            hover_text = (
                f"<b>{paper_title}</b><br>"
                f"Year: {year}<br>"
                f"Citations: {citations}<br>"
                f"Cluster: {label if label != -1 else 'Noise'}"
            )
            hover_texts.append(hover_text)

        # Determine color
        if label == -1:
            color = NOISE_COLOR
            name = "Noise"
        else:
            color = CLUSTER_COLORS[label % len(CLUSTER_COLORS)]
            name = f"Cluster {label}"

        # Create trace
        trace = go.Scatter(
            x=x,
            y=y,
            mode="markers",
            name=name,
            marker=dict(
                size=10,
                color=color,
                opacity=0.7,
                line=dict(width=1, color="white"),
            ),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hover_texts,
        )
        traces.append(trace)

    # Create figure
    fig = go.Figure(data=traces)

    # Update layout
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor="center",
            font=dict(size=20),
        ),
        xaxis=dict(
            title="Dimension 1",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.1)",
            zeroline=False,
        ),
        yaxis=dict(
            title="Dimension 2",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.1)",
            zeroline=False,
        ),
        legend=dict(
            title="Clusters",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.02,
        ),
        hovermode="closest",
        template="plotly_white",
        width=1000,
        height=700,
    )

    return fig


def create_cluster_plot_from_result(
    result: "ClusteringResult",
    title: str | None = None,
) -> "Figure":
    """Create scatter plot directly from ClusteringResult.
    
    Convenience wrapper around create_cluster_plot.
    
    Args:
        result: ClusteringResult from ClusteringEngine.run_full_pipeline
        title: Optional custom title
        
    Returns:
        Plotly Figure object
    """
    plot_title = title or f"Paper Clusters ({result.method.upper()}, {result.n_clusters} clusters)"

    return create_cluster_plot(
        papers=result.papers,
        coords=result.coords_2d,
        labels=result.labels,
        title=plot_title,
    )


def save_html(fig: "Figure", path: str | Path) -> None:
    """Save Plotly figure as interactive HTML file.
    
    Args:
        fig: Plotly Figure object
        path: Output file path
    """
    path = Path(path)
    fig.write_html(
        str(path),
        include_plotlyjs="cdn",
        full_html=True,
    )


def save_cluster_visualization(
    result: "ClusteringResult",
    html_path: str | Path,
    title: str | None = None,
) -> None:
    """One-step function to create and save cluster visualization.
    
    Args:
        result: ClusteringResult from clustering pipeline
        html_path: Output HTML file path
        title: Optional custom title
    """
    fig = create_cluster_plot_from_result(result, title)
    save_html(fig, html_path)


def create_timeline_visualization(
    timeline_data: dict[str, Any],
    title: str = "Paper Timeline",
) -> "Figure":
    """Create an interactive timeline visualization.
    
    Args:
        timeline_data: Timeline data dictionary with 'timeline' array
        title: Plot title
        
    Returns:
        Plotly Figure object
    """
    import plotly.graph_objects as go

    timeline = timeline_data.get("timeline", [])
    if not timeline:
        # Empty timeline
        fig = go.Figure()
        fig.update_layout(title=title)
        return fig

    # Extract years and counts
    years = [entry["year"] for entry in timeline]
    counts = [entry["count"] for entry in timeline]

    # Build hover text
    hover_texts = []
    for entry in timeline:
        year = entry["year"]
        count = entry["count"]
        # Get top papers by citations
        papers = entry.get("papers", [])[:5]  # Top 5
        paper_titles = [p.get("title", "Unknown")[:60] for p in papers]
        hover_text = (
            f"<b>{year}</b><br>"
            f"Papers: {count}<br>"
            f"Top papers:<br>" + "<br>".join(f"• {t}" for t in paper_titles)
        )
        hover_texts.append(hover_text)

    # Create bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=years,
            y=counts,
            text=counts,
            textposition="outside",
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hover_texts,
            marker=dict(
                color=counts,
                colorscale="Blues",
                showscale=True,
                colorbar=dict(title="Papers"),
            ),
        )
    ])

    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor="center",
            font=dict(size=20),
        ),
        xaxis=dict(
            title="Year",
            type="category",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.1)",
        ),
        yaxis=dict(
            title="Number of Papers",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.1)",
        ),
        template="plotly_white",
        width=1000,
        height=600,
    )

    return fig


def save_timeline_visualization(
    timeline_data: dict[str, Any],
    html_path: str | Path,
    title: str | None = None,
) -> None:
    """Create and save timeline visualization.
    
    Args:
        timeline_data: Timeline data dictionary
        html_path: Output HTML file path
        title: Optional custom title
    """
    plot_title = title or f"Paper Timeline: {timeline_data.get('query', 'Unknown')}"
    fig = create_timeline_visualization(timeline_data, plot_title)
    save_html(fig, html_path)


def create_graph_visualization(
    graph_data: dict[str, Any],
    title: str = "Citation Graph",
) -> "Figure":
    """Create an interactive network graph visualization.
    
    Args:
        graph_data: Graph data dictionary with 'nodes' and 'edges'
        title: Plot title
        
    Returns:
        Plotly Figure object
    """
    import plotly.graph_objects as go

    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    if not nodes:
        # Empty graph
        fig = go.Figure()
        fig.update_layout(title=title)
        return fig

    # Create node positions using a simple layout (could use networkx for better layout)
    # For now, use a simple circular or force-directed-like layout
    import numpy as np

    n_nodes = len(nodes)
    if n_nodes == 1:
        node_x = [0]
        node_y = [0]
    else:
        # Circular layout
        angles = np.linspace(0, 2 * np.pi, n_nodes, endpoint=False)
        node_x = np.cos(angles).tolist()
        node_y = np.sin(angles).tolist()

    # Build node trace
    node_texts = []
    node_sizes = []
    for node in nodes:
        title = node.get("title", "Unknown")
        if len(title) > 50:
            title = title[:47] + "..."
        year = node.get("year", "N/A")
        citations = node.get("citation_count", 0)
        node_texts.append(f"<b>{title}</b><br>Year: {year}<br>Citations: {citations}")
        # Size based on citations (min 10, max 30)
        node_sizes.append(max(10, min(30, 10 + citations / 10)))

    # Create edge traces
    edge_traces = []
    node_map = {node["id"]: i for i, node in enumerate(nodes)}

    # Group edges by type for different colors
    cite_edges = []
    cited_by_edges = []

    for edge in edges:
        source_id = edge["source"]
        target_id = edge["target"]
        if source_id in node_map and target_id in node_map:
            source_idx = node_map[source_id]
            target_idx = node_map[target_id]

            edge_data = {
                "x": [node_x[source_idx], node_x[target_idx], None],
                "y": [node_y[source_idx], node_y[target_idx], None],
            }

            if edge.get("type") == "cites":
                cite_edges.append(edge_data)
            else:
                cited_by_edges.append(edge_data)

    # Add edge traces
    if cite_edges:
        cite_x = []
        cite_y = []
        for edge in cite_edges:
            cite_x.extend(edge["x"])
            cite_y.extend(edge["y"])

        edge_trace_cites = go.Scatter(
            x=cite_x,
            y=cite_y,
            mode="lines",
            line=dict(width=1, color="#888"),
            hoverinfo="none",
            showlegend=True,
            name="Cites",
        )
        edge_traces.append(edge_trace_cites)

    if cited_by_edges:
        cited_x = []
        cited_y = []
        for edge in cited_by_edges:
            cited_x.extend(edge["x"])
            cited_y.extend(edge["y"])

        edge_trace_cited = go.Scatter(
            x=cited_x,
            y=cited_y,
            mode="lines",
            line=dict(width=1, color="#aaa"),
            hoverinfo="none",
            showlegend=True,
            name="Cited by",
        )
        edge_traces.append(edge_trace_cited)

    # Create node trace
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        name="Papers",
        marker=dict(
            size=node_sizes,
            color="#1f77b4",
            line=dict(width=2, color="white"),
        ),
        text=[node.get("title", "Unknown")[:30] for node in nodes],
        textposition="middle center",
        textfont=dict(size=8),
        hovertemplate="%{customdata}<extra></extra>",
        customdata=node_texts,
    )

    # Combine all traces
    fig = go.Figure(data=edge_traces + [node_trace])

    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor="center",
            font=dict(size=20),
        ),
        showlegend=True,
        hovermode="closest",
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        template="plotly_white",
        width=1200,
        height=800,
    )

    return fig


def save_graph_visualization(
    graph_data: dict[str, Any],
    html_path: str | Path,
    title: str | None = None,
) -> None:
    """Create and save graph visualization.
    
    Args:
        graph_data: Graph data dictionary
        html_path: Output HTML file path
        title: Optional custom title
    """
    plot_title = title or f"Citation Graph: {graph_data.get('query', 'Unknown')}"
    fig = create_graph_visualization(graph_data, plot_title)
    save_html(fig, html_path)
