import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, callback, dash_table, dcc, html

from data_loader import load_data, load_production_raw

df_full = load_data()
prod_raw = load_production_raw()

# ── helpers ────────────────────────────────────────────────────────────────────

def kpi_card(title: str, value: str) -> html.Div:
    return html.Div(
        [html.P(title, className="kpi-title"), html.H3(value, className="kpi-value")],
        className="kpi-card",
    )


def sorted_opts(series: pd.Series) -> list[dict]:
    vals = sorted(series.dropna().unique())
    return [{"label": v, "value": v} for v in vals]


# ── layout ─────────────────────────────────────────────────────────────────────

app = Dash(__name__, title="NY Wells Dashboard")
server = app.server  # expose for gunicorn

COUNTIES = sorted_opts(df_full["County"])
WELL_TYPES = sorted_opts(df_full["Well Type"])
WELL_STATUSES = sorted_opts(df_full["Well Status"])

MIN_YEAR = int(df_full["Spud Year"].min()) if df_full["Spud Year"].notna().any() else 1800
MAX_YEAR = int(df_full["Spud Year"].max()) if df_full["Spud Year"].notna().any() else 2026

app.layout = html.Div(
    [
        html.Header(
            html.H1("New York State Oil & Gas Wells"),
            className="app-header",
        ),
        html.Div(
            [
                # ── sidebar ────────────────────────────────────────────────────
                html.Aside(
                    [
                        html.H2("Filters"),
                        html.Label("County"),
                        dcc.Dropdown(
                            id="filter-county",
                            options=COUNTIES,
                            multi=True,
                            placeholder="All counties",
                            className="dropdown",
                        ),
                        html.Label("Spud Year Range"),
                        dcc.RangeSlider(
                            id="filter-year",
                            min=MIN_YEAR,
                            max=MAX_YEAR,
                            step=1,
                            value=[MIN_YEAR, MAX_YEAR],
                            marks={
                                y: str(y)
                                for y in range(
                                    (MIN_YEAR // 20) * 20,
                                    MAX_YEAR + 1,
                                    20,
                                )
                            },
                            tooltip={"placement": "bottom", "always_visible": True},
                            className="year-slider",
                        ),
                        html.Label("Well Type"),
                        dcc.RadioItems(
                            id="type-radio",
                            options=[
                                {"label": "All", "value": "all"},
                                {"label": "Customize", "value": "custom"},
                            ],
                            value="all",
                            className="status-radio",
                            inputClassName="radio-input",
                            labelClassName="radio-label",
                        ),
                        html.Div(
                            dcc.Dropdown(
                                id="filter-type",
                                options=WELL_TYPES,
                                multi=True,
                                placeholder="Select types…",
                                className="dropdown",
                            ),
                            id="type-custom-box",
                            style={"display": "none"},
                        ),
                        html.Label("Well Status"),
                        dcc.RadioItems(
                            id="status-radio",
                            options=[
                                {"label": "All", "value": "all"},
                                {"label": "Active only", "value": "active"},
                                {"label": "Customize", "value": "custom"},
                            ],
                            value="all",
                            className="status-radio",
                            inputClassName="radio-input",
                            labelClassName="radio-label",
                        ),
                        html.Div(
                            dcc.Dropdown(
                                id="filter-status",
                                options=WELL_STATUSES,
                                multi=True,
                                placeholder="Select statuses…",
                                className="dropdown",
                            ),
                            id="status-custom-box",
                            style={"display": "none"},
                        ),
                    ],
                    className="sidebar",
                ),
                # ── main content ───────────────────────────────────────────────
                html.Main(
                    [
                        html.Div(id="kpi-row", className="kpi-row"),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        dcc.Graph(id="map-wells", className="graph map-graph"),
                                        dcc.Graph(id="chart-hover-county", className="graph hover-graph"),
                                    ],
                                    className="card card-wide map-card",
                                ),
                            ],
                            className="chart-row",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    dcc.Graph(id="chart-timeline", className="graph"),
                                    className="card",
                                ),
                                html.Div(
                                    dcc.Graph(id="chart-status", className="graph"),
                                    className="card",
                                ),
                            ],
                            className="chart-row",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    dcc.Graph(id="chart-type", className="graph"),
                                    className="card",
                                ),
                                html.Div(
                                    dcc.Graph(id="chart-production", className="graph"),
                                    className="card",
                                ),
                            ],
                            className="chart-row",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    dcc.Graph(id="chart-depth", className="graph"),
                                    className="card card-wide",
                                ),
                            ],
                            className="chart-row",
                        ),
                        html.Div(
                            html.Div(
                                [
                                    html.H2("Well Records", className="table-heading"),
                                    dash_table.DataTable(
                                        id="well-table",
                                        columns=[
                                            {"name": "API Well Number", "id": "API Well Number"},
                                            {"name": "Well Name", "id": "Well Name"},
                                            {"name": "Company Name", "id": "Company Name"},
                                            {"name": "County", "id": "County"},
                                            {"name": "Well Type", "id": "Well Type"},
                                            {"name": "Well Status", "id": "Well Status"},
                                            {"name": "Spud Year", "id": "Spud Year"},
                                            {"name": "True Vertical Depth (ft)", "id": "True Vertical Depth"},
                                            {"name": "Well Orientation", "id": "Well Orientation"},
                                            {"name": "Producing Formation", "id": "Producing Formation"},
                                        ],
                                        page_action="none",
                                        fixed_rows={"headers": True},
                                        sort_action="native",
                                        filter_action="native",
                                        style_table={"height": "400px", "overflowY": "auto"},
                                        style_header={
                                            "backgroundColor": "#1e3a5f",
                                            "color": "white",
                                            "fontWeight": "600",
                                            "fontSize": "0.8rem",
                                            "padding": "10px 12px",
                                            "border": "none",
                                        },
                                        style_cell={
                                            "fontSize": "0.8rem",
                                            "padding": "8px 12px",
                                            "textAlign": "left",
                                            "border": "1px solid #e2e8f0",
                                            "whiteSpace": "normal",
                                            "overflow": "hidden",
                                            "textOverflow": "ellipsis",
                                            "maxWidth": "200px",
                                        },
                                        style_data_conditional=[
                                            {
                                                "if": {"row_index": "odd"},
                                                "backgroundColor": "#f8fafc",
                                            },
                                            {
                                                "if": {"filter_query": '{Well Status} = "Active"'},
                                                "color": "#059669",
                                                "fontWeight": "500",
                                            },
                                            {
                                                "if": {"filter_query": '{Well Status} contains "Plugged"'},
                                                "color": "#dc2626",
                                            },
                                        ],
                                        style_filter={
                                            "backgroundColor": "#f1f5f9",
                                            "fontSize": "0.75rem",
                                        },
                                    ),
                                ],
                                className="card card-wide table-card",
                            ),
                            className="chart-row",
                        ),
                    ],
                    className="main-content",
                ),
            ],
            className="body-layout",
        ),
    ],
    className="app-container",
)

# ── styles injected via assets/ (see assets/style.css) ────────────────────────

# ── callbacks ──────────────────────────────────────────────────────────────────

@callback(
    Output("status-custom-box", "style"),
    Input("status-radio", "value"),
)
def toggle_status_custom(radio_val):
    return {"display": "block"} if radio_val == "custom" else {"display": "none"}


@callback(
    Output("type-custom-box", "style"),
    Input("type-radio", "value"),
)
def toggle_type_custom(radio_val):
    return {"display": "block"} if radio_val == "custom" else {"display": "none"}


def apply_filters(counties, type_radio, custom_types, status_radio, custom_statuses, year_range):
    dff = df_full.copy()
    if counties:
        dff = dff[dff["County"].isin(counties)]
    if type_radio == "custom" and custom_types:
        dff = dff[dff["Well Type"].isin(custom_types)]
    if status_radio == "active":
        dff = dff[dff["Well Status"] == "Active"]
    elif status_radio == "custom" and custom_statuses:
        dff = dff[dff["Well Status"].isin(custom_statuses)]
    if year_range:
        lo, hi = year_range
        mask = dff["Spud Year"].isna() | dff["Spud Year"].between(lo, hi)
        dff = dff[mask]
    return dff


@callback(
    Output("kpi-row", "children"),
    Output("map-wells", "figure"),
    Output("chart-timeline", "figure"),
    Output("chart-status", "figure"),
    Output("chart-type", "figure"),
    Output("chart-production", "figure"),
    Output("chart-depth", "figure"),
    Input("filter-county", "value"),
    Input("type-radio", "value"),
    Input("filter-type", "value"),
    Input("status-radio", "value"),
    Input("filter-status", "value"),
    Input("filter-year", "value"),
)
def update_all(counties, type_radio, custom_types, status_radio, custom_statuses, year_range):
    dff = apply_filters(counties, type_radio, custom_types, status_radio, custom_statuses, year_range)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total = len(dff)
    active = (dff["Well Status"] == "Active").sum()
    plugged = dff["Well Status"].str.contains("Plugged", na=False).sum()
    avg_depth = dff["True Vertical Depth"].replace(0, pd.NA).mean()
    avg_depth_str = f"{avg_depth:,.0f} ft" if pd.notna(avg_depth) else "N/A"

    kpis = [
        kpi_card("Total Wells", f"{total:,}"),
        kpi_card("Active", f"{active:,}"),
        kpi_card("Plugged & Abandoned", f"{plugged:,}"),
        kpi_card("Avg. True Vertical Depth", avg_depth_str),
    ]

    # ── Map ───────────────────────────────────────────────────────────────────
    map_df = dff.dropna(subset=["Surface Latitude", "Surface Longitude"])
    fig_map = px.scatter_mapbox(
        map_df,
        lat="Surface Latitude",
        lon="Surface Longitude",
        color="Well Type",
        hover_name="Well Name",
        hover_data={"County": True, "Well Status": True, "Company Name": True,
                    "Surface Latitude": False, "Surface Longitude": False},
        custom_data=["County", "API Well Number"],
        zoom=6,
        center={"lat": 42.9, "lon": -76.0},
        height=450,
        title="Well Locations",
    )
    fig_map.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        legend_title_text="Well Type",
    )

    # ── Timeline ──────────────────────────────────────────────────────────────
    timeline = (
        dff.dropna(subset=["Spud Year"])
        .groupby("Spud Year")
        .size()
        .reset_index(name="Count")
    )
    fig_timeline = px.bar(
        timeline,
        x="Spud Year",
        y="Count",
        title="Wells Spudded per Year",
        labels={"Spud Year": "Year", "Count": "Wells Drilled"},
        color_discrete_sequence=["#2563eb"],
    )
    fig_timeline.update_layout(margin={"t": 40, "b": 40})

    # ── Status breakdown ──────────────────────────────────────────────────────
    status_counts = dff["Well Type"].value_counts().reset_index()
    status_counts.columns = ["Well Type", "Count"]
    fig_status = px.pie(
        status_counts,
        names="Well Type",
        values="Count",
        title="Wells by Type",
        hole=0.4,
    )
    fig_status.update_layout(margin={"t": 40, "b": 10})

    # ── Type breakdown ────────────────────────────────────────────────────────
    type_counts = dff["Well Type"].value_counts().nlargest(10).reset_index()
    type_counts.columns = ["Well Type", "Count"]
    fig_type = px.bar(
        type_counts,
        x="Count",
        y="Well Type",
        orientation="h",
        title="Top 10 Well Types",
        color_discrete_sequence=["#7c3aed"],
    )
    fig_type.update_layout(yaxis={"categoryorder": "total ascending"}, margin={"t": 40})

    # ── County breakdown ──────────────────────────────────────────────────────
    county_counts = dff["County"].value_counts().nlargest(15).reset_index()
    county_counts.columns = ["County", "Count"]
    fig_county = px.bar(
        county_counts,
        x="Count",
        y="County",
        orientation="h",
        title="Top 15 Counties by Well Count",
        color_discrete_sequence=["#059669"],
    )
    fig_county.update_layout(yaxis={"categoryorder": "total ascending"}, margin={"t": 40})

    # ── Depth distribution ────────────────────────────────────────────────────
    depth_df = dff[dff["True Vertical Depth"] > 0]["True Vertical Depth"].dropna()
    fig_depth = go.Figure(
        go.Histogram(
            x=depth_df,
            nbinsx=60,
            marker_color="#d97706",
            name="True Vertical Depth",
        )
    )
    fig_depth.update_layout(
        title="Distribution of True Vertical Depth (ft)",
        xaxis_title="Depth (ft)",
        yaxis_title="Well Count",
        margin={"t": 40},
    )

    return kpis, fig_map, fig_timeline, fig_status, fig_type, fig_county, fig_depth


TABLE_COLS = [
    "API Well Number", "Well Name", "Company Name", "County",
    "Well Type", "Well Status", "Spud Year", "True Vertical Depth",
    "Well Orientation", "Producing Formation",
]


@callback(
    Output("well-table", "data"),
    Input("filter-county", "value"),
    Input("type-radio", "value"),
    Input("filter-type", "value"),
    Input("status-radio", "value"),
    Input("filter-status", "value"),
    Input("filter-year", "value"),
)
def update_table(counties, type_radio, custom_types, status_radio, custom_statuses, year_range):
    dff = apply_filters(counties, type_radio, custom_types, status_radio, custom_statuses, year_range)
    tbl = dff[TABLE_COLS].copy()
    tbl["Spud Year"] = tbl["Spud Year"].astype("Int64").astype(str).replace("<NA>", "")
    tbl["True Vertical Depth"] = tbl["True Vertical Depth"].apply(
        lambda x: f"{x:,.0f}" if pd.notna(x) and x > 0 else ""
    )
    return tbl.head(20).to_dict("records")


@callback(
    Output("chart-hover-county", "figure"),
    Input("map-wells", "hoverData"),
    Input("filter-county", "value"),
    Input("type-radio", "value"),
    Input("filter-type", "value"),
    Input("status-radio", "value"),
    Input("filter-status", "value"),
    Input("filter-year", "value"),
)
def update_hover_chart(hover_data, counties, type_radio, custom_types, status_radio, custom_statuses, year_range):
    def empty_fig(msg):
        fig = go.Figure()
        fig.update_layout(
            title="Well Production Over Time",
            xaxis={"visible": False},
            yaxis={"visible": False},
            annotations=[{
                "text": msg,
                "xref": "paper", "yref": "paper",
                "x": 0.5, "y": 0.5,
                "showarrow": False,
                "font": {"size": 14, "color": "#94a3b8"},
            }],
            margin={"t": 40, "b": 20},
            height=450,
        )
        return fig

    if hover_data is None:
        return empty_fig("Hover over a well to see its production over time")

    try:
        api = hover_data["points"][0]["customdata"][1]
    except (KeyError, IndexError, TypeError):
        return empty_fig("Hover over a well to see its production over time")

    well_prod = prod_raw[prod_raw["API Well Number"] == api].dropna(subset=["Year"])
    if well_prod.empty:
        return empty_fig("No production data for this well")

    well_name = well_prod["Well Name"].iloc[0] or api

    all_years = pd.RangeIndex(
        int(prod_raw["Year"].min()), int(prod_raw["Year"].max()) + 1
    )
    well_prod = (
        well_prod.set_index("Year")
        .reindex(all_years, fill_value=0)
        .reset_index()
        .rename(columns={"index": "Year"})
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=well_prod["Year"], y=well_prod["OIL (Bbls)"],
        name="Oil (Bbls)", mode="lines+markers", line={"color": "#d97706"},
    ))
    fig.add_trace(go.Scatter(
        x=well_prod["Year"], y=well_prod["GAS (Mcf)"],
        name="Gas (Mcf)", mode="lines+markers", line={"color": "#2563eb"},
        yaxis="y2",
    ))
    fig.add_trace(go.Scatter(
        x=well_prod["Year"], y=well_prod["WATER (Bbls)"],
        name="Water (Bbls)", mode="lines+markers", line={"color": "#06b6d4", "dash": "dot"},
    ))
    fig.update_layout(
        title=f"Production — {well_name}",
        xaxis={"title": "Year", "dtick": 1},
        yaxis={"title": "Oil / Water (Bbls)"},
        yaxis2={"title": "Gas (Mcf)", "overlaying": "y", "side": "right", "showgrid": False},
        legend={"orientation": "h", "y": -0.2},
        margin={"t": 40, "b": 60},
        height=450,
    )
    return fig




if __name__ == "__main__":
    app.run(debug=True)
