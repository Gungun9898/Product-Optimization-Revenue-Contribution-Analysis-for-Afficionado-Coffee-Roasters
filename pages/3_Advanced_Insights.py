import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import base64
from pathlib import Path

# Streamlit page configuration
st.set_page_config(
    page_title="Pareto and Category",
    layout="wide"
)

# Project paths
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "coffee_roasters.db"

# Background image function
def get_base64_image(image_path):
    with open(image_path, "rb") as img:
        return base64.b64encode(img.read()).decode()

# Load background image
bg_image = get_base64_image(BASE_DIR / "rustic-bread-and-bakery.jpg")

st.markdown(f"""
<style>

[data-testid="stAppViewContainer"] {{
    background-image:
        linear-gradient(
            rgba(245,248,247,0.80),
            rgba(245,248,247,0.80)
        ),
        url("data:image/jpeg;base64,{bg_image}");

    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        rgba(0,98,65,0.95) 0%,
        rgba(30,58,138,0.95) 100%
    ) !important;
}
            

/* Sidebar labels */
[data-testid="stSidebar"] *{
    color:#D4A017 !important;
}

/* Main page */
.stApp{
    background: transparent;
}

/* Tabs */
button[data-baseweb="tab"]{
    font-size:16px;
    font-weight:600;
}

button[aria-selected="true"]{
    color:#1E3A8A !important;
    border-bottom:4px solid #006241 !important;
}

/* Dataframe */
[data-testid="stDataFrame"]{
    border-radius:15px;
}

/* Subheaders */
h2,h3{
    color:#1E3A8A;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="
background:rgba(255,255,255,0.75);
backdrop-filter:blur(10px);
padding:30px;
border-radius:20px;
box-shadow:0 8px 20px rgba(0,0,0,0.12);
margin-bottom:25px;
border-left:6px solid #1E3A8A;
">
<h1 style="
margin:0;
color:#1E3A8A;
font-size:48px;
font-weight:800;
">
Advanced Insights
</h1>

<p style="
color:#475569;
font-size:18px;
margin-top:10px;
">
ABC Product Analysis and Market Basket Analysis from the same SQLite database
</p>
</div>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    with sqlite3.connect(DB_PATH) as conn:

        product_df = pd.read_sql_query(
            "SELECT * FROM vw_product_kpi", conn
        )

        pareto_df = pd.read_sql_query(
            "SELECT * FROM vw_product_pareto", conn
        )

        product_df.columns = product_df.columns.str.lower().str.strip()
        pareto_df.columns = pareto_df.columns.str.lower().str.strip()

        basket_df = pd.DataFrame()
        basket_error = None

        basket_queries = []

        for query in basket_queries:
            try:
                basket_df = pd.read_sql_query(query, conn)
                basket_df.columns = basket_df.columns.str.lower().str.strip()
                basket_error = None
                break
            except Exception as e:
                basket_error = str(e)

    return product_df, pareto_df, basket_df, basket_error


product_df, pareto_df, basket_df, basket_error = load_data()


if not basket_df.empty:
    st.subheader("Sample Basket Data")
    st.dataframe(basket_df.head(10))

tabs = st.tabs(
    [
        "ABC Analysis",
        "Product Portfolio & Revenue Concentration"
    ]
)

def highlight_abc_row(row):
    if row["ABC Class"] == "A":
        return ["background-color: #dbeafe"] * len(row)
    elif row["ABC Class"] == "B":
        return ["background-color: #fef3c7"] * len(row)
    elif row["ABC Class"] == "C":
        return ["background-color: #dcfce7"] * len(row)
    return [""] * len(row)

with tabs[0]:
    st.subheader("ABC Product Analysis")

    abc_df = pareto_df.copy()

    if abc_df.empty:
        st.warning("No Pareto data found.")
    else:
        abc_df = abc_df.sort_values("total_revenue", ascending=False).reset_index(drop=True)

        if "cum_revenue_pct" not in abc_df.columns:
            abc_df["revenue_share_pct"] = (
                abc_df["total_revenue"] / abc_df["total_revenue"].sum()
            ) * 100
            abc_df["cum_revenue_pct"] = abc_df["revenue_share_pct"].cumsum()

        def classify_abc(x):
            if x <= 80:
                return "A"
            elif x <= 95:
                return "B"
            return "C"

        abc_df["abc_class"] = abc_df["cum_revenue_pct"].apply(classify_abc)

        category_options = ["All"] + sorted(
            abc_df["product_category"].dropna().unique().tolist()
        )

        selected_category = st.selectbox(
            "Filter ABC by Category",
            category_options,
            key="abc_category"
        )

        filtered_abc = abc_df.copy()
        if selected_category != "All":
            filtered_abc = filtered_abc[
                filtered_abc["product_category"] == selected_category
            ]

        abc_summary = filtered_abc.groupby("abc_class", as_index=False).agg(
            products=("product_id", "nunique"),
            revenue=("total_revenue", "sum")
        )

        total_products = filtered_abc["product_id"].nunique()
        a_products = filtered_abc[filtered_abc["abc_class"] == "A"]["product_id"].nunique()
        a_revenue = filtered_abc[filtered_abc["abc_class"] == "A"]["total_revenue"].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Products", f"{total_products}")
        c2.metric("A-Class Products", f"{a_products}")
        c3.metric("A-Class Revenue", f"${a_revenue:,.0f}")

        col1, col2 = st.columns(2)

        with col1:
            fig_abc_bar = px.bar(
                abc_summary,
                x="abc_class",
                y="revenue",
                color="abc_class",
                text="products",
                category_orders={"abc_class": ["A", "B", "C"]},
                color_discrete_map={"A": "#1d4ed8", "B": "#f59e0b", "C": "#94a3b8"}
            )
            fig_abc_bar.update_layout(
                title="Revenue by ABC Class",
                xaxis_title="ABC Class",
                yaxis_title="Total Revenue",
                height=420
            )
            st.plotly_chart(fig_abc_bar, use_container_width=True)
                        


        with col2:
            fig_abc_pie = px.pie(
                abc_summary,
                names="abc_class",
                values="products",
                color="abc_class",
                color_discrete_map={"A": "#1d4ed8", "B": "#f59e0b", "C": "#94a3b8"}
            )
            fig_abc_pie.update_layout(
                title="Product Count by ABC Class",
                height=420
            )
            st.plotly_chart(fig_abc_pie, use_container_width=True)
        

        st.markdown("### ABC Product Table")

        abc_display_cols = [
            "product_detail",
            "product_category",
            "product_type",
            "total_revenue",
            "revenue_share_pct",
            "cum_revenue_pct",
            "abc_class"
        ]

        abc_display_cols = [c for c in abc_display_cols if c in filtered_abc.columns]

        abc_table = filtered_abc[abc_display_cols].rename(columns={
            "product_detail": "Product",
            "product_category": "Category",
            "product_type": "Type",
            "total_revenue": "Revenue",
            "revenue_share_pct": "Revenue %",
            "cum_revenue_pct": "Cumulative Revenue %",
            "abc_class": "ABC Class"
        })

        styled_abc_table = (
            abc_table.style
            .apply(highlight_abc_row, axis=1)
            .format({
                "Revenue": "${:,.0f}",
                "Revenue %": "{:.2f}",
                "Cumulative Revenue %": "{:.2f}"
            })
        )

        st.dataframe(styled_abc_table, use_container_width=True)

        st.info(
            "A = top revenue-driving products up to 80% cumulative revenue, "
            "B = next 15%, C = remaining products."
        )


with tabs[1]:

    st.subheader("Product Portfolio Matrix")

    portfolio_df = product_df.copy()

    revenue_median = portfolio_df["total_revenue"].median()
    units_median = portfolio_df["units_sold"].median()

    def classify_product(row):

        if row["total_revenue"] >= revenue_median and row["units_sold"] >= units_median:
            return "Star"

        elif row["total_revenue"] >= revenue_median and row["units_sold"] < units_median:
            return "Premium"

        elif row["total_revenue"] < revenue_median and row["units_sold"] >= units_median:
            return "Volume Driver"

        return "Underperformer"

    portfolio_df["segment"] = portfolio_df.apply(
        classify_product,
        axis=1
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Stars",
        portfolio_df[portfolio_df["segment"] == "Star"].shape[0]
    )

    c2.metric(
        "Premium",
        portfolio_df[portfolio_df["segment"] == "Premium"].shape[0]
    )

    c3.metric(
        "Volume Drivers",
        portfolio_df[portfolio_df["segment"] == "Volume Driver"].shape[0]
    )

    c4.metric(
        "Underperformers",
        portfolio_df[portfolio_df["segment"] == "Underperformer"].shape[0]
    )

    fig_matrix = px.scatter(
        portfolio_df,
        x="units_sold",
        y="total_revenue",
        color="segment",
        size="revenue_share_pct",
        hover_name="product_detail",
        title="Revenue vs Volume Portfolio Matrix"
    )

    fig_matrix.add_vline(
        x=units_median,
        line_dash="dash"
    )

    fig_matrix.add_hline(
        y=revenue_median,
        line_dash="dash"
    )

    fig_matrix.update_layout(height=600)

    st.plotly_chart(
        fig_matrix,
        use_container_width=True
   )

    st.markdown("---")

    st.subheader("Revenue Concentration Analysis")

    concentration_df = pareto_df.sort_values(
        "revenue_rank"
    )

    products_80 = concentration_df[
        concentration_df["is_top_80pct"] == 1
    ].shape[0]

    total_products = concentration_df.shape[0]

    concentration_ratio = (
        products_80 / total_products
    ) * 100

    top10_revenue_pct = concentration_df.head(10)[
        "revenue_share_pct"
    ].sum()

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Products Driving 80% Revenue",
        products_80
    )

    c2.metric(
        "Total Products",
        total_products
    )

    c3.metric(
        "Top 10 Product Revenue %",
        f"{top10_revenue_pct:.1f}%"
    )

    fig_concentration = px.line(
        concentration_df,
        x="revenue_rank",
        y="cum_revenue_pct",
        markers=True,
        title="Revenue Concentration Curve"
    )

    fig_concentration.add_hline(
        y=80,
        line_dash="dash",
        line_color="red"
    )

    fig_concentration.update_layout(
        height=500
    )

    st.plotly_chart(
        fig_concentration,
        use_container_width=True
    )

    st.markdown("### Products Driving 80% Revenue")

    top80_products = concentration_df[
        concentration_df["is_top_80pct"] == 1
    ]

    st.dataframe(
        top80_products[
            [
                "product_detail",
                "product_category",
                "total_revenue",
                "cum_revenue_pct"
            ]
        ].rename(
            columns={
                "product_detail": "Product",
                "product_category": "Category",
                "total_revenue": "Revenue",
                "cum_revenue_pct": "Cumulative Revenue %"
            }
        ),
        use_container_width=True
    )

    st.success(
        f"{products_80} out of {total_products} products generate approximately 80% of total revenue."
    )


