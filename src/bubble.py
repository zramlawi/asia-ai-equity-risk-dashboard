from __future__ import annotations

import pandas as pd
import plotly.express as px


def peer_comparison_chart(frame: pd.DataFrame):
    """Plot peer fundamentals and liquidity without disguising missing coverage."""
    plot_data = frame.copy()
    plot_data["percentile_label"] = plot_data["percentile"].map(
        lambda value: f"{value:.0f}" if pd.notna(value) else "Insufficient coverage"
    )
    plot_data["freshness_label"] = plot_data["is_fresh"].map(
        {True: "Fresh", False: "Stale or unavailable"}
    ).fillna("Unavailable")
    plot_data["bubble_size"] = pd.to_numeric(
        plot_data.get("market_cap"), errors="coerce"
    ).fillna(1)

    return px.scatter(
        plot_data,
        x="liquidity_score",
        y="fundamental_score",
        size="bubble_size",
        color="coverage",
        hover_name="ticker",
        hover_data={
            "overall_score": ":.1f",
            "coverage": ":.0%",
            "percentile_label": True,
            "freshness_label": True,
            "bubble_size": False,
        },
        labels={
            "liquidity_score": "Liquidity score",
            "fundamental_score": "Fundamental score",
            "coverage": "Evidence coverage",
        },
        title="Peer comparison: fundamentals, liquidity, and evidence coverage",
        size_max=60,
    )
