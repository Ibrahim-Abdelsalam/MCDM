"""Chart generation for MCDM analysis results."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from ..config import BASE_DIR


class ChartGenerator:
    """Generate visualizations for analysis results."""

    def __init__(self, output_dir: Path | None = None) -> None:
        """Initialize the chart generator with the output directory."""
        self.output_dir = output_dir or (BASE_DIR / "data" / "results")
        self.method_colors = {
            "AHP": "#4472C4",
            "TOPSIS": "#375623",
            "VIKOR": "#7030A0",
        }

    def _get_method_name(self, key: str) -> str:
        """Extract method name from key like 'AHP_scheme_name_Score'."""
        for method in self.method_colors.keys():
            if key.startswith(method):
                return method
        return "Unknown"

    def generate_top10_charts(
        self,
        analysis_results: dict[str, pd.DataFrame],
        entity_type: str,
    ) -> list[Path]:
        """Generate bar charts for top 10 per method per scheme."""
        chart_paths = []
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        for key, result_df in analysis_results.items():
            method = self._get_method_name(key)
            color = self.method_colors.get(method, "#4472C4")
            
            # Get top 10
            top_10 = result_df.nsmallest(10, "Rank").sort_values("Rank")
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            x_labels = [f"#{i}" for i in range(1, len(top_10) + 1)]
            bars = ax.bar(x_labels, top_10["Score"].values, color=color, edgecolor="black", linewidth=1.2)
            
            # Annotate bars with Company_ID and score
            for bar, (_, row) in zip(bars, top_10.iterrows()):
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 0.02,
                    f"{row['ID']}\n{height:.3f}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )
            
            ax.set_xlabel("Rank", fontsize=12, fontweight="bold")
            ax.set_ylabel("Score", fontsize=12, fontweight="bold")
            ax.set_ylim(0, 1.05)
            ax.set_title(f"Top 10 {entity_type.title()} - {method} - {key}", fontsize=14, fontweight="bold")
            ax.grid(axis="y", alpha=0.3)
            
            # Save chart
            chart_filename = f"top10_{method}_{key}.png"
            chart_path = self.output_dir / chart_filename
            fig.tight_layout()
            fig.savefig(chart_path, dpi=100, bbox_inches="tight")
            plt.close(fig)
            
            chart_paths.append(chart_path)
        
        return chart_paths

    def generate_scatter_charts(
        self,
        analysis_results: dict[str, pd.DataFrame],
        entity_type: str,
    ) -> list[Path]:
        """Generate scatter plots for cross-scheme comparison per method."""
        chart_paths = []
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        methods_data = {}
        
        # Aggregate data by method
        for key, result_df in analysis_results.items():
            method = self._get_method_name(key)
            if method not in methods_data:
                methods_data[method] = {}
            
            # Get top 10 for this scheme
            top_10 = result_df.nsmallest(10, "Rank")
            methods_data[method][key] = top_10
        
        # Create one scatter plot per method
        palette = sns.color_palette("husl", len(methods_data))
        
        for method_idx, (method, schemes_data) in enumerate(methods_data.items()):
            fig, ax = plt.subplots(figsize=(14, 8))
            
            color = palette[method_idx]
            x_pos = 0
            
            for scheme_key, top_10_df in schemes_data.items():
                x_positions = [x_pos + i * 0.05 for i in range(len(top_10_df))]
                ax.scatter(
                    x_positions,
                    top_10_df["Score"].values,
                    s=100,
                    alpha=0.7,
                    color=color,
                    edgecolors="black",
                    linewidth=1,
                )
                
                # Annotate points with Company_ID
                for x, y, company_id in zip(x_positions, top_10_df["Score"].values, top_10_df["ID"].values):
                    ax.text(x, y + 0.02, company_id, ha="center", va="bottom", fontsize=8)
                
                x_pos += 1
            
            ax.set_xlabel("Scheme", fontsize=12, fontweight="bold")
            ax.set_ylabel("Score", fontsize=12, fontweight="bold")
            ax.set_ylim(0, 1.05)
            ax.set_title(f"Cross-Scheme Comparison - {method} - {entity_type.title()}", fontsize=14, fontweight="bold")
            ax.grid(axis="y", alpha=0.3)
            
            # Save chart
            chart_filename = f"scatter_{method}_all_schemes.png"
            chart_path = self.output_dir / chart_filename
            fig.tight_layout()
            fig.savefig(chart_path, dpi=100, bbox_inches="tight")
            plt.close(fig)
            
            chart_paths.append(chart_path)
        
        return chart_paths

    def generate_all_charts(
        self,
        analysis_results: dict[str, pd.DataFrame],
        entity_type: str,
    ) -> list[Path]:
        """Generate all charts (bar and scatter)."""
        paths = []
        paths.extend(self.generate_top10_charts(analysis_results, entity_type))
        paths.extend(self.generate_scatter_charts(analysis_results, entity_type))
        return paths
