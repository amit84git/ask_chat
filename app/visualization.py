"""
Visualization Module.
Generates HTML graph visualizations (Pyvis) and data charts (Matplotlib/Altair).
"""
import io
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from app.config import settings

logger = logging.getLogger(__name__)


class VisualizationService:
    """Generates interactive visualizations for query results and schema graphs."""

    def __init__(self):
        self.output_dir = Path(settings.vis_output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_data_chart(self, data: List[Dict[str, Any]], chart_type: str = "bar",
                            title: str = "Query Results", x_col: Optional[str] = None,
                            y_col: Optional[str] = None) -> str:
        """
        Generate an HTML chart from query result data using Altair.
        
        Returns:
            HTML string containing the chart
        """
        if not data:
            return "<p>No data to visualize</p>"

        try:
            import altair as alt
            df = pd.DataFrame(data)

            # Auto-detect columns if not specified
            if not x_col or not y_col:
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                text_cols = df.select_dtypes(include=["object"]).columns.tolist()

                if not y_col and numeric_cols:
                    y_col = numeric_cols[0]
                elif not y_col:
                    y_col = df.columns[0]

                if not x_col:
                    x_col = text_cols[0] if text_cols else df.columns[0]

            # Create chart based on type
            if chart_type == "bar":
                chart = alt.Chart(df).mark_bar().encode(
                    x=alt.X(x_col, sort="-y"),
                    y=alt.Y(y_col),
                    tooltip=[x_col, y_col],
                ).properties(title=title, width=600, height=400)

            elif chart_type == "line":
                chart = alt.Chart(df).mark_line(point=True).encode(
                    x=x_col,
                    y=y_col,
                    tooltip=[x_col, y_col],
                ).properties(title=title, width=600, height=400)

            elif chart_type == "scatter":
                chart = alt.Chart(df).mark_circle().encode(
                    x=x_col,
                    y=y_col,
                    tooltip=[x_col, y_col],
                ).properties(title=title, width=600, height=400)

            elif chart_type == "pie":
                chart = alt.Chart(df).mark_arc().encode(
                    theta=alt.Theta(field=y_col, type="quantitative"),
                    color=alt.Color(field=x_col, type="nominal"),
                    tooltip=[x_col, y_col],
                ).properties(title=title, width=400, height=400)

            else:
                chart = alt.Chart(df).mark_bar().encode(
                    x=x_col,
                    y=y_col,
                ).properties(title=title)

            return chart.to_html()

        except ImportError:
            logger.warning("Altair not available, falling back to Matplotlib")
            return self._matplotlib_chart_to_html(data, chart_type, title, x_col, y_col)

    def _matplotlib_chart_to_html(self, data: List[Dict[str, Any]], chart_type: str,
                                  title: str, x_col: Optional[str], y_col: Optional[str]) -> str:
        """Fallback chart generation using Matplotlib."""
        df = pd.DataFrame(data)

        if not x_col or not y_col:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            text_cols = df.select_dtypes(include=["object"]).columns.tolist()
            y_col = y_col or (numeric_cols[0] if numeric_cols else df.columns[0])
            x_col = x_col or (text_cols[0] if text_cols else df.columns[0])

        fig, ax = plt.subplots(figsize=(8, 5))

        if chart_type == "bar":
            df.plot(kind="bar", x=x_col, y=y_col, ax=ax, legend=False)
        elif chart_type == "line":
            df.plot(kind="line", x=x_col, y=y_col, ax=ax, marker="o")
        elif chart_type == "scatter":
            df.plot(kind="scatter", x=x_col, y=y_col, ax=ax)
        elif chart_type == "pie":
            df.set_index(x_col)[y_col].plot(kind="pie", ax=ax)
        else:
            df.plot(kind="bar", x=x_col, y=y_col, ax=ax)

        ax.set_title(title)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        plt.tight_layout()

        # Convert to HTML img tag with embedded SVG
        buf = io.BytesIO()
        fig.savefig(buf, format="svg", bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        svg_data = buf.getvalue().decode()

        html = f"""<div style="text-align:center;">
            <h3>{title}</h3>
            {svg_data}
        </div>"""
        return html

    def generate_graph_html(self, graph_dict: Dict[str, Any]) -> str:
        """
        Generate an interactive graph visualization from exported graph data.
        Falls back to a simple static visualization if Pyvis is not available.
        """
        try:
            import networkx as nx
            from pyvis.network import Network

            G = nx.MultiDiGraph()
            for node in graph_dict.get("nodes", []):
                G.add_node(
                    node["id"],
                    label=node.get("label", node["id"]),
                    title=node.get("label", node["id"]),
                    group=node.get("metadata", {}).get("node_type", "unknown"),
                )
            for edge in graph_dict.get("edges", []):
                G.add_edge(edge["source"], edge["target"],
                          title=edge.get("relationship", "connected"))

            net = Network(height="600px", width="100%", bgcolor="#1a1a2e", font_color="white")
            net.from_nx(G)
            net.show_buttons(filter_=["physics"])

            html = net.generate_html()
            return html

        except ImportError:
            logger.warning("Pyvis/NetworkX not available, generating static HTML")
            return self._static_graph_html(graph_dict)

    def _static_graph_html(self, graph_dict: Dict[str, Any]) -> str:
        """Generate a simple static graph visualization."""
        nodes = graph_dict.get("nodes", [])
        edges = graph_dict.get("edges", [])

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Schema Graph</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #1a1a2e; color: #eee; padding: 20px; }}
        .node {{ display: inline-block; padding: 10px 20px; margin: 5px; border-radius: 8px; font-size: 14px; }}
        .table {{ background: #00aaff; color: white; }}
        .column {{ background: #ffaa00; color: black; }}
        .keyword {{ background: #ff5500; color: white; }}
        .edge {{ color: #888; margin: 5px 0; font-size: 12px; }}
        h3 {{ margin-bottom: 10px; }}
    </style>
</head>
<body>
    <h2>Schema Graph</h2>
    <p>{len(nodes)} nodes, {len(edges)} edges</p>
    <div>
"""
        for node in nodes:
            ntype = node.get("metadata", {}).get("node_type", "unknown")
            css_class = {"table": "table", "column": "column", "keyword": "keyword"}.get(ntype, "")
            html += f'        <span class="node {css_class}">{node.get("label", node["id"])}</span>\n'

        html += "    </div>\n    <h3>Relationships</h3>\n    <ul>\n"
        for edge in edges:
            rel = edge.get("relationship", "connected")
            html += f'        <li class="edge">{edge["source"]} --[{rel}]--> {edge["target"]}</li>\n'

        html += """    </ul>
</body>
</html>"""
        return html

    def save_html(self, html_content: str, filename: str) -> str:
        """Save HTML content to file and return the file path."""
        filepath = self.output_dir / filename
        filepath.write_text(html_content, encoding="utf-8")
        logger.info(f"Saved visualization to {filepath}")
        return str(filepath)


# Singleton
vis_service = VisualizationService()