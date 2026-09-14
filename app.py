
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Nassau Candy Profitability Dashboard",
    page_icon="🍫",
    layout="wide"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

.main-title {
    font-size: 36px;
    font-weight: 700;
    margin-bottom: 5px;
}

.subtitle {
    font-size: 17px;
    color: #666;
    margin-bottom: 25px;
}

.kpi-card {
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #ddd;
    background-color: #fafafa;
    text-align: center;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    df = pd.read_csv("df_clean.csv")

    df["Order Date"] = pd.to_datetime(
        df["Order Date"],
        errors="coerce"
    )

    df = df.dropna(subset=["Order Date"]).copy()

    return df


df = load_data()


# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="main-title">🍫 Nassau Candy Distributor</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Product Line Profitability & Margin Performance Analysis'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("🎛️ Dashboard Filters")

min_date = df["Order Date"].min().date()
max_date = df["Order Date"].max().date()

date_range = st.sidebar.date_input(
    "Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

divisions = sorted(
    df["Division"].dropna().unique()
)

selected_divisions = st.sidebar.multiselect(
    "Division",
    divisions,
    default=divisions
)

margin_threshold = st.sidebar.slider(
    "Margin Threshold (%)",
    min_value=0,
    max_value=100,
    value=50,
    step=1
)

product_search = st.sidebar.text_input(
    "🔎 Product Search",
    placeholder="Enter product name..."
)


# ============================================================
# FILTER DATA
# ============================================================

filtered_df = df.copy()

if isinstance(date_range, tuple) and len(date_range) == 2:

    start_date = pd.Timestamp(date_range[0])

    # Add one day so the selected end date is fully included
    end_date = (
        pd.Timestamp(date_range[1])
        + pd.Timedelta(days=1)
    )

    filtered_df = filtered_df[
        (filtered_df["Order Date"] >= start_date)
        &
        (filtered_df["Order Date"] < end_date)
    ]


if selected_divisions:

    filtered_df = filtered_df[
        filtered_df["Division"].isin(
            selected_divisions
        )
    ]


if filtered_df.empty:

    st.warning(
        "No data available for the selected filters."
    )

    st.stop()


# ============================================================
# OVERALL BUSINESS KPIs
# ============================================================

total_sales = filtered_df["Sales"].sum()
total_cost = filtered_df["Cost"].sum()
total_profit = filtered_df["Gross Profit"].sum()
total_units = filtered_df["Units"].sum()

if total_sales > 0:
    gross_margin = (
        total_profit / total_sales
    ) * 100
else:
    gross_margin = 0


# ============================================================
# MONTHLY MARGIN VOLATILITY
# ============================================================

monthly_margin = (
    filtered_df
    .assign(
        Month=lambda x:
        x["Order Date"]
        .dt
        .to_period("M")
        .astype(str)
    )
    .groupby(
        "Month",
        as_index=False
    )
    .agg(
        Sales=("Sales", "sum"),
        Gross_Profit=("Gross Profit", "sum")
    )
)

monthly_margin["Gross Margin %"] = np.where(
    monthly_margin["Sales"] > 0,
    (
        monthly_margin["Gross_Profit"]
        /
        monthly_margin["Sales"]
    ) * 100,
    0
)

if len(monthly_margin) > 1:
    margin_volatility = (
        monthly_margin["Gross Margin %"].std()
    )
else:
    margin_volatility = 0


# ============================================================
# KPI CARDS
# ============================================================

st.subheader("📌 Business Overview")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Total Sales",
        f"${total_sales:,.2f}"
    )

with col2:
    st.metric(
        "Total Cost",
        f"${total_cost:,.2f}"
    )

with col3:
    st.metric(
        "Gross Profit",
        f"${total_profit:,.2f}"
    )

with col4:
    st.metric(
        "Gross Margin",
        f"{gross_margin:.2f}%"
    )

with col5:
    st.metric(
        "Margin Volatility",
        f"{margin_volatility:.2f} pp"
    )

st.caption(
    f"Total Units Sold: {total_units:,.0f}"
)

st.divider()


# ============================================================
# PRODUCT PROFITABILITY
# ============================================================

st.header("📦 Product Profitability")


filtered_product = (
    filtered_df
    .groupby(
        [
            "Product ID",
            "Product Name",
            "Division"
        ],
        as_index=False
    )
    .agg(
        Sales=("Sales", "sum"),
        Units=("Units", "sum"),
        Cost=("Cost", "sum"),
        Gross_Profit=("Gross Profit", "sum")
    )
)

filtered_product = filtered_product.rename(
    columns={
        "Gross_Profit": "Gross Profit"
    }
)


# Gross Margin

filtered_product["Gross Margin %"] = np.where(
    filtered_product["Sales"] > 0,
    (
        filtered_product["Gross Profit"]
        /
        filtered_product["Sales"]
    ) * 100,
    0
)


# Profit Per Unit

filtered_product["Profit per Unit"] = np.where(
    filtered_product["Units"] > 0,
    (
        filtered_product["Gross Profit"]
        /
        filtered_product["Units"]
    ),
    0
)


# Revenue Contribution

total_product_sales = (
    filtered_product["Sales"].sum()
)

total_product_profit = (
    filtered_product["Gross Profit"].sum()
)


if total_product_sales > 0:

    filtered_product[
        "Revenue Contribution %"
    ] = (
        filtered_product["Sales"]
        /
        total_product_sales
    ) * 100

else:

    filtered_product[
        "Revenue Contribution %"
    ] = 0


# Profit Contribution

if total_product_profit > 0:

    filtered_product[
        "Profit Contribution %"
    ] = (
        filtered_product["Gross Profit"]
        /
        total_product_profit
    ) * 100

else:

    filtered_product[
        "Profit Contribution %"
    ] = 0


# ============================================================
# PRODUCT SEARCH
# ============================================================

if product_search:

    filtered_product = filtered_product[
        filtered_product["Product Name"]
        .str.contains(
            product_search,
            case=False,
            na=False
        )
    ]


col1, col2 = st.columns(2)


# ============================================================
# TOP PRODUCTS BY GROSS PROFIT
# ============================================================

with col1:

    top_profit = (
        filtered_product
        .sort_values(
            "Gross Profit",
            ascending=False
        )
        .head(10)
        .sort_values(
            "Gross Profit"
        )
    )

    if not top_profit.empty:

        fig_profit = px.bar(
            top_profit,
            x="Gross Profit",
            y="Product Name",
            orientation="h",
            title="Top 10 Products by Gross Profit",
            labels={
                "Gross Profit":
                "Gross Profit ($)"
            }
        )

        st.plotly_chart(
            fig_profit,
            use_container_width=True
        )


# ============================================================
# TOP PRODUCTS BY GROSS MARGIN
# ============================================================

with col2:

    top_margin = (
        filtered_product
        .sort_values(
            "Gross Margin %",
            ascending=False
        )
        .head(10)
        .sort_values(
            "Gross Margin %"
        )
    )

    if not top_margin.empty:

        fig_margin = px.bar(
            top_margin,
            x="Gross Margin %",
            y="Product Name",
            orientation="h",
            title="Top 10 Products by Gross Margin",
            labels={
                "Gross Margin %":
                "Gross Margin (%)"
            }
        )

        st.plotly_chart(
            fig_margin,
            use_container_width=True
        )


# ============================================================
# PRODUCT TABLE
# ============================================================

st.subheader(
    "📋 Product-Level Profitability"
)

display_product = filtered_product.copy()

for col in [
    "Sales",
    "Cost",
    "Gross Profit",
    "Gross Margin %",
    "Profit per Unit",
    "Revenue Contribution %",
    "Profit Contribution %"
]:

    if col in display_product.columns:

        display_product[col] = (
            display_product[col].round(2)
        )


st.dataframe(
    display_product.sort_values(
        "Gross Profit",
        ascending=False
    ),
    use_container_width=True,
    hide_index=True
)

st.divider()


# ============================================================
# DIVISION PERFORMANCE
# ============================================================

st.header("🏭 Division Performance")


filtered_division = (
    filtered_df
    .groupby(
        "Division",
        as_index=False
    )
    .agg(
        Sales=("Sales", "sum"),
        Cost=("Cost", "sum"),
        Units=("Units", "sum"),
        Gross_Profit=("Gross Profit", "sum")
    )
)

filtered_division = filtered_division.rename(
    columns={
        "Gross_Profit":
        "Gross Profit"
    }
)


filtered_division["Gross Margin %"] = np.where(
    filtered_division["Sales"] > 0,
    (
        filtered_division["Gross Profit"]
        /
        filtered_division["Sales"]
    ) * 100,
    0
)


division_total_profit = (
    filtered_division["Gross Profit"].sum()
)


if division_total_profit > 0:

    filtered_division[
        "Profit Contribution %"
    ] = (
        filtered_division["Gross Profit"]
        /
        division_total_profit
    ) * 100

else:

    filtered_division[
        "Profit Contribution %"
    ] = 0


col1, col2 = st.columns(2)


# Revenue vs Profit

with col1:

    fig_division = px.bar(
        filtered_division,
        x="Division",
        y=[
            "Sales",
            "Gross Profit"
        ],
        barmode="group",
        title="Revenue vs Gross Profit by Division"
    )

    st.plotly_chart(
        fig_division,
        use_container_width=True
    )


# Division Margin

with col2:

    fig_div_margin = px.bar(
        filtered_division,
        x="Division",
        y="Gross Margin %",
        title="Gross Margin by Division"
    )

    st.plotly_chart(
        fig_div_margin,
        use_container_width=True
    )


# Division Table

st.subheader(
    "Division-Level Performance Summary"
)

division_display = (
    filtered_division.copy()
)

for col in [
    "Sales",
    "Cost",
    "Gross Profit",
    "Gross Margin %",
    "Profit Contribution %"
]:

    if col in division_display.columns:

        division_display[col] = (
            division_display[col].round(2)
        )


st.dataframe(
    division_display,
    use_container_width=True,
    hide_index=True
)

st.divider()


# ============================================================
# COST & MARGIN DIAGNOSTICS
# ============================================================

st.header(
    "💰 Cost & Margin Diagnostics"
)

col1, col2 = st.columns(2)


# Sales vs Gross Profit

with col1:

    fig_scatter = px.scatter(
        filtered_product,
        x="Sales",
        y="Gross Profit",
        size="Units",
        hover_name="Product Name",
        color="Division",
        title="Sales vs Gross Profit"
    )

    st.plotly_chart(
        fig_scatter,
        use_container_width=True
    )


# Cost vs Sales

with col2:

    fig_cost = px.scatter(
        filtered_product,
        x="Sales",
        y="Cost",
        size="Units",
        hover_name="Product Name",
        color="Division",
        title="Cost vs Sales"
    )

    st.plotly_chart(
        fig_cost,
        use_container_width=True
    )


# ============================================================
# MARGIN RISK PRODUCTS
# ============================================================

st.subheader(
    "⚠️ Margin Risk Products"
)


risk_products = filtered_product[
    filtered_product["Gross Margin %"]
    < margin_threshold
].copy()


risk_products = risk_products.sort_values(
    "Sales",
    ascending=False
)


if len(risk_products) > 0:

    risk_display = risk_products[
        [
            "Product Name",
            "Division",
            "Sales",
            "Gross Profit",
            "Gross Margin %",
            "Profit per Unit"
        ]
    ].copy()


    for col in [
        "Sales",
        "Gross Profit",
        "Gross Margin %",
        "Profit per Unit"
    ]:

        risk_display[col] = (
            risk_display[col].round(2)
        )


    st.warning(
        f"{len(risk_display)} product(s) are "
        f"below the selected "
        f"{margin_threshold}% margin threshold."
    )


    st.dataframe(
        risk_display,
        use_container_width=True,
        hide_index=True
    )

else:

    st.success(
        "No products fall below the "
        "selected margin threshold."
    )


st.divider()


# ============================================================
# PROFIT & REVENUE CONCENTRATION
# ============================================================

st.header(
    "📊 Profit & Revenue Concentration Analysis"
)


pareto_dashboard = (
    filtered_product
    .sort_values(
        "Gross Profit",
        ascending=False
    )
    .reset_index(drop=True)
)


if not pareto_dashboard.empty:

    profit_denominator = (
        pareto_dashboard["Gross Profit"].sum()
    )

    revenue_denominator = (
        pareto_dashboard["Sales"].sum()
    )


    # ========================================================
    # CUMULATIVE PROFIT
    # ========================================================

    if profit_denominator > 0:

        pareto_dashboard[
            "Cumulative Profit %"
        ] = (
            pareto_dashboard[
                "Gross Profit"
            ].cumsum()
            /
            profit_denominator
        ) * 100

    else:

        pareto_dashboard[
            "Cumulative Profit %"
        ] = 0


    # ========================================================
    # REVENUE RANKING
    # ========================================================

    revenue_sorted = (
        filtered_product
        .sort_values(
            "Sales",
            ascending=False
        )
        .reset_index(drop=True)
    )


    if revenue_denominator > 0:

        revenue_sorted[
            "Cumulative Revenue %"
        ] = (
            revenue_sorted[
                "Sales"
            ].cumsum()
            /
            revenue_denominator
        ) * 100

    else:

        revenue_sorted[
            "Cumulative Revenue %"
        ] = 0


    # ========================================================
    # PRODUCTS REQUIRED FOR 80% PROFIT
    # ========================================================

    profit_crossing = (
        pareto_dashboard[
            pareto_dashboard[
                "Cumulative Profit %"
            ] >= 80
        ]
    )


    if not profit_crossing.empty:

        profit_80_count = (
            profit_crossing.index[0] + 1
        )

    else:

        profit_80_count = (
            len(pareto_dashboard)
        )


    profit_80_percentage = (
        profit_80_count
        /
        len(pareto_dashboard)
    ) * 100


    # ========================================================
    # PRODUCTS REQUIRED FOR 80% REVENUE
    # ========================================================

    revenue_crossing = (
        revenue_sorted[
            revenue_sorted[
                "Cumulative Revenue %"
            ] >= 80
        ]
    )


    if not revenue_crossing.empty:

        revenue_80_count = (
            revenue_crossing.index[0] + 1
        )

    else:

        revenue_80_count = (
            len(revenue_sorted)
        )


    revenue_80_percentage = (
        revenue_80_count
        /
        len(revenue_sorted)
    ) * 100


    # ========================================================
    # TOP 5 PROFIT DEPENDENCY
    # ========================================================

    top_5_profit = (
        pareto_dashboard
        .head(5)["Gross Profit"]
        .sum()
    )


    if total_product_profit > 0:

        top_5_profit_share = (
            top_5_profit
            /
            total_product_profit
        ) * 100

    else:

        top_5_profit_share = 0


    # ========================================================
    # PARETO KPIs
    # ========================================================

    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Products for 80% Profit",
            f"{profit_80_count}"
        )

        st.caption(
            f"{profit_80_percentage:.1f}% "
            "of products"
        )


    with col2:

        st.metric(
            "Products for 80% Revenue",
            f"{revenue_80_count}"
        )

        st.caption(
            f"{revenue_80_percentage:.1f}% "
            "of products"
        )


    with col3:

        st.metric(
            "Top 5 Profit Dependency",
            f"{top_5_profit_share:.2f}%"
        )


    # ========================================================
    # PROFIT PARETO
    # ========================================================

    fig_profit_pareto = px.bar(
        pareto_dashboard,
        x="Product Name",
        y="Gross Profit",
        title="Profit Concentration — Pareto by Product"
    )


    fig_profit_pareto.update_layout(
        xaxis_tickangle=-60,
        xaxis_title="Product",
        yaxis_title="Gross Profit ($)"
    )


    st.plotly_chart(
        fig_profit_pareto,
        use_container_width=True
    )


    # ========================================================
    # REVENUE PARETO
    # ========================================================

    fig_revenue_pareto = px.bar(
        revenue_sorted,
        x="Product Name",
        y="Sales",
        title="Revenue Concentration — Pareto by Product"
    )


    fig_revenue_pareto.update_layout(
        xaxis_tickangle=-60,
        xaxis_title="Product",
        yaxis_title="Sales ($)"
    )


    st.plotly_chart(
        fig_revenue_pareto,
        use_container_width=True
    )


    # ========================================================
    # CUMULATIVE PROFIT CURVE
    # ========================================================

    pareto_curve = (
        pareto_dashboard.copy()
    )


    pareto_curve["Product Rank"] = np.arange(
        1,
        len(pareto_curve) + 1
    )


    fig_cumulative = px.line(
        pareto_curve,
        x="Product Rank",
        y="Cumulative Profit %",
        markers=True,
        title="Cumulative Profit Contribution"
    )


    fig_cumulative.update_layout(
        xaxis_title="Number of Products",
        yaxis_title="Cumulative Profit (%)"
    )


    st.plotly_chart(
        fig_cumulative,
        use_container_width=True
    )


st.divider()


# ============================================================
# PROFIT CONTRIBUTION
# ============================================================

st.header(
    "📈 Profit Contribution"
)


profit_chart = (
    filtered_product
    .sort_values(
        "Profit Contribution %",
        ascending=False
    )
)


if not profit_chart.empty:

    fig_contribution = px.bar(
        profit_chart,
        x="Product Name",
        y="Profit Contribution %",
        title="Product Contribution to Total Gross Profit"
    )


    fig_contribution.update_layout(
        xaxis_tickangle=-60
    )


    st.plotly_chart(
        fig_contribution,
        use_container_width=True
    )


st.divider()


# ============================================================
# MONTHLY GROSS MARGIN TREND
# ============================================================

st.header(
    "📅 Monthly Gross Margin Trend"
)


monthly_filtered = (
    filtered_df
    .assign(
        Month=lambda x:
        x["Order Date"]
        .dt
        .to_period("M")
        .astype(str)
    )
    .groupby(
        "Month",
        as_index=False
    )
    .agg(
        Sales=("Sales", "sum"),
        Cost=("Cost", "sum"),
        Gross_Profit=("Gross Profit", "sum")
    )
)


monthly_filtered = (
    monthly_filtered.rename(
        columns={
            "Gross_Profit":
            "Gross Profit"
        }
    )
)


monthly_filtered["Gross Margin %"] = np.where(
    monthly_filtered["Sales"] > 0,
    (
        monthly_filtered["Gross Profit"]
        /
        monthly_filtered["Sales"]
    ) * 100,
    0
)


fig_monthly = px.line(
    monthly_filtered,
    x="Month",
    y="Gross Margin %",
    markers=True,
    title="Monthly Gross Margin Trend"
)


fig_monthly.update_layout(
    xaxis_title="Month",
    yaxis_title="Gross Margin (%)"
)


st.plotly_chart(
    fig_monthly,
    use_container_width=True
)


# ============================================================
# EXECUTIVE INSIGHTS
# ============================================================

st.header(
    "💡 Key Business Insights"
)


if not filtered_product.empty:

    best_profit_product = (
        filtered_product
        .sort_values(
            "Gross Profit",
            ascending=False
        )
        .iloc[0]
    )


    best_margin_product = (
        filtered_product
        .sort_values(
            "Gross Margin %",
            ascending=False
        )
        .iloc[0]
    )


    worst_margin_product = (
        filtered_product
        .sort_values(
            "Gross Margin %"
        )
        .iloc[0]
    )


    st.markdown(
        f"""
        **🏆 Highest Gross Profit Product:**
        {best_profit_product['Product Name']} —
        Gross Profit: ${best_profit_product['Gross Profit']:,.2f}

        **📈 Highest Gross Margin Product:**
        {best_margin_product['Product Name']} —
        Gross Margin: {best_margin_product['Gross Margin %']:.2f}%

        **⚠️ Lowest Gross Margin Product:**
        {worst_margin_product['Product Name']} —
        Gross Margin: {worst_margin_product['Gross Margin %']:.2f}%

        **📊 Overall Gross Margin:**
        {gross_margin:.2f}%

        **📉 Margin Volatility:**
        {margin_volatility:.2f} percentage points
        """
    )


# ============================================================
# MANAGEMENT RECOMMENDATIONS
# ============================================================

st.header(
    "💼 Management Recommendations"
)


recommendations = [

    (
        "Protect high-profit core products",
        "Prioritize availability, reliable sourcing, "
        "competitive pricing, and margin monitoring "
        "for the leading profit-generating products."
    ),

    (
        "Investigate Kazookles margin risk",
        "Review procurement cost, selling price, "
        "discounts, supplier terms, and overall "
        "product economics because Kazookles has "
        "the lowest margin."
    ),

    (
        "Improve high-sales / low-margin products",
        "Evaluate price optimization, supplier "
        "negotiation, cost reduction, and discount "
        "control before considering product "
        "rationalization."
    ),

    (
        "Scale high-margin / low-sales products",
        "Test targeted marketing, cross-selling, "
        "bundling, and improved product visibility "
        "for products with attractive margins but "
        "limited volume."
    ),

    (
        "Reduce profit concentration risk",
        "Develop additional profitable products so "
        "the business is less dependent on a small "
        "number of core products."
    ),

    (
        "Review low-sales / low-margin products",
        "Consider pricing, cost reduction, "
        "repositioning, or rationalization for "
        "products with both weak sales and weak margins."
    )
]


for title, recommendation in recommendations:

    st.markdown(
        f"**{title}:** {recommendation}"
    )


# ============================================================
# DOWNLOAD ANALYSIS
# ============================================================

st.divider()

st.header(
    "📥 Download Analysis"
)


download_product = (
    filtered_product.copy()
)

download_division = (
    filtered_division.copy()
)

download_monthly = (
    monthly_filtered.copy()
)


product_csv = (
    download_product
    .to_csv(index=False)
    .encode("utf-8")
)


division_csv = (
    download_division
    .to_csv(index=False)
    .encode("utf-8")
)


monthly_csv = (
    download_monthly
    .to_csv(index=False)
    .encode("utf-8")
)


col1, col2, col3 = st.columns(3)


with col1:

    st.download_button(
        label="⬇️ Product Profitability CSV",
        data=product_csv,
        file_name="product_profitability_filtered.csv",
        mime="text/csv"
    )


with col2:

    st.download_button(
        label="⬇️ Division Performance CSV",
        data=division_csv,
        file_name="division_profitability_filtered.csv",
        mime="text/csv"
    )


with col3:

    st.download_button(
        label="⬇️ Monthly Profitability CSV",
        data=monthly_csv,
        file_name="monthly_profitability_filtered.csv",
        mime="text/csv"
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Nassau Candy Distributor | "
    "Product Line Profitability & Margin Performance Analysis"
)
