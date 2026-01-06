"""
Chart generation service using seaborn.
"""

import asyncio
import io
from typing import Any, Dict

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Set premium dark theme
plt.style.use("dark_background")
sns.set_theme(
    style="whitegrid",
    rc={
        "axes.facecolor": "#121212",
        "figure.facecolor": "#121212",
        "grid.color": "#2D2D2D",
        "grid.linestyle": "--",
        "axes.edgecolor": "#333333",
        "text.color": "white",
        "xtick.color": "#AAAAAA",
        "ytick.color": "#AAAAAA",
        "font.family": "sans-serif",
    },
)


class ChartService:
    """
    Service for generating elegant dark-mode charts.
    """

    @staticmethod
    async def generate_consumption_chart(
        data: Dict[str, Any],
        period: str,
        title: str,
        x_label: str = "Date",
        y_label: str = "Consumption (kWh)",
    ) -> io.BytesIO:
        """
        Generate consumption chart asynchronously.
        """
        return await asyncio.to_thread(
            ChartService._generate_chart_sync,
            data,
            period,
            title,
            x_label,
            y_label,
        )

    @staticmethod
    def _generate_chart_sync(
        data: Dict[str, Any],
        period: str,
        title: str,
        x_label: str,
        y_label: str,
    ) -> io.BytesIO:
        """
        Synchronous method to generate an elegant dark-mode chart.
        """
        labels = data.get("labels", [])
        values = data.get("values", [])

        if not labels or not values:
            df = pd.DataFrame({"x": [], "y": []})
            no_data = True
        else:
            df = pd.DataFrame({"x": labels, "y": values})
            no_data = False

        fig, ax = plt.subplots(figsize=(11, 7), facecolor="#121212")
        ax.set_facecolor("#121212")

        if no_data:
            ax.text(
                0.5,
                0.5,
                "No Data Available",
                horizontalalignment="center",
                verticalalignment="center",
                transform=ax.transAxes,
                color="#666666",
                fontsize=16,
            )
            ax.set_title(title, pad=20, fontsize=18, fontweight="bold", color="white")
        else:
            if period in ["today", "yearly"]:
                # Bar chart for single points or broad aggregates
                # Use a nice gradient-like color
                color = "#32E0C4" if period == "today" else "#00FF87"
                sns.barplot(
                    data=df,
                    x="x",
                    y="y",
                    ax=ax,
                    color=color,
                    alpha=0.9,
                    edgecolor=color,
                    linewidth=1,
                )

                # Add elegant value labels
                for container in ax.containers:
                    ax.bar_label(
                        container,
                        fmt="%.1f",
                        padding=5,
                        color="white",
                        fontweight="bold",
                        fontsize=12,
                    )
            else:
                # Line chart for time-series (weekly, monthly)
                # Vibrant blue with fill
                line_color = "#00D2FF"
                sns.lineplot(
                    data=df,
                    x="x",
                    y="y",
                    ax=ax,
                    marker="o",
                    linewidth=3,
                    markersize=10,
                    color=line_color,
                    markeredgecolor="white",
                    markeredgewidth=1.5,
                )

                # Fill under the line for elegance
                plt.fill_between(df["x"], df["y"], color=line_color, alpha=0.1)

            # Labels and Title
            ax.set_xlabel(x_label, labelpad=15, fontsize=13, color="#AAAAAA")
            ax.set_ylabel(y_label, labelpad=15, fontsize=13, color="#AAAAAA")
            ax.set_title(
                title.upper(),
                pad=30,
                fontsize=20,
                fontweight="bold",
                color="white",
            )

            # Axis formatting
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color("#333333")
            ax.spines["bottom"].set_color("#333333")

            # Tick markers
            plt.xticks(rotation=45, ha="right", fontsize=11)
            plt.yticks(fontsize=11)

        plt.tight_layout()

        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(
            buf, format="png", dpi=120, bbox_inches="tight", facecolor="#121212"
        )
        buf.seek(0)
        plt.close(fig)

        return buf
