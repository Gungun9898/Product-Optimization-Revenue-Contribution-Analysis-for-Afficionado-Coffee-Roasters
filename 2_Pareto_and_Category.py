import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import base64


st.set_page_config(page_title="Pareto and Category", layout="wide")

def get_base64_image(image_path):
    with open(image_path, "rb") as img:
        return base64.b64encode(img.read()).decode()

bg_image = get_base64_image(r"C:\Users\gunja\Documents\Unified_portal\E-commerce\python\pages\bakery-coffee-shop.jpg")

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

DB_PATH = "coffee_roasters.db"

@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    category_df = pd.read_sql_query("SELECT * FROM vw_category_kpi", conn)
    pareto_df = pd.read_sql_query("SELECT * FROM vw_product_pareto", conn)
    conn.close()
    return category_df, pareto_df

category_df, pareto_df = load_data()

category_df.columns = category_df.columns.str.strip().str.lower()
pareto_df.columns = pareto_df.columns.str.strip().str.lower()

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
Pareto & Category Analysis
</h1>

<p style="
color:#475569;
font-size:18px;
margin-top:10px;
">
Identify revenue concentration, top-performing products and category contribution trends.
</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div style="
background:linear-gradient(135deg,#006241,#1E3A8A);
padding:14px;
border-radius:14px;
text-align:center;
margin-bottom:20px;
box-shadow:0 4px 12px rgba(0,0,0,0.15);
">
<h3 style="
margin:0;
color:white;
font-size:22px;
">
Dashboard Filters
</h3>
</div>
""", unsafe_allow_html=True)

category_options = ["All"] + sorted(pareto_df["product_category"].dropna().unique().tolist())
selected_category = st.sidebar.selectbox("Category", category_options)
if selected_category == "All":
    max_ranks = len(pareto_df)
else:
    max_ranks = len(
        pareto_df[
            pareto_df["product_category"] == selected_category
        ]
    )

top_n = st.sidebar.slider(
    "Top-N Ranks",
    min_value=1,
    max_value=max_ranks,
    value=min(50, max_ranks)
)

st.sidebar.caption(
    f"Selected category contains {max_ranks} ranked products."
)

if max_ranks < 50:
    st.sidebar.info(
        f"Only {max_ranks} ranked products available in this category."
    )
filtered_pareto = pareto_df.copy()

if selected_category != "All":
    filtered_pareto = filtered_pareto[filtered_pareto["product_category"] == selected_category]

filtered_pareto = filtered_pareto.sort_values("revenue_rank").head(top_n)

filtered_pareto = filtered_pareto.reset_index(drop=True)
filtered_pareto["display_rank"] = range(
    1,
    len(filtered_pareto) + 1
)

if filtered_pareto.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

tab1, tab2 = st.tabs(["Pareto View", "Category Distribution"])

with tab1:
    st.subheader("Pareto Analysis")

    top80_count = filtered_pareto["is_top_80pct"].sum()

    c1,c2,c3 = st.columns(3)

    c1.metric(
        "Products Driving 80%",
        f"{top80_count}"
    )

    c2.metric(
        "Products Selected",
        f"{len(filtered_pareto)}"
    )

    c3.metric(
        "Revenue Coverage",
        f"{filtered_pareto['cum_revenue_pct'].max():.1f}%"
    )

    fig = go.Figure()

    st.markdown("""
        <div style="
        background:white;
        padding:20px;
        border-radius:20px;
        box-shadow:0 6px 16px rgba(0,0,0,0.08);
        ">
        """, unsafe_allow_html=True)

    fig.add_trace(
        go.Bar(
            x=filtered_pareto["display_rank"],
            y=filtered_pareto["total_revenue"],
            name="Total Revenue",
            marker_color="#006241"
        )
    )
    fig.add_trace(
        go.Scatter(
            x=filtered_pareto["display_rank"],
            y=filtered_pareto["cum_revenue_pct"],
            name="Cum Revenue %",
            yaxis="y2",
            mode="lines",
            line=dict(
    color="#1E3A8A",
    width=4
)
        )
    )

    fig.update_layout(
        height=500,
        xaxis=dict(title="Revenue Rank"),
        yaxis=dict(title="Total Revenue"),
        yaxis2=dict(
            title="Cum Revenue %",
            overlaying="y",
            side="right",
            range=[0, 100]
        ),
        legend=dict(orientation="h")
    )

    fig.add_hline(
    y=80,
    line_dash="dash",
    line_color="#D4A017",
    line_width=3,
    yref="y2"
)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    top80 = filtered_pareto[
    filtered_pareto["is_top_80pct"] == 1
    ][
        ["product_detail","product_category","revenue_rank","total_revenue","revenue_share_pct","cum_revenue_pct"]
    ]
    st.subheader("Products Contributing to Top 80% of Revenue")
    st.dataframe(top80, use_container_width=True)

with tab2:
    st.subheader("Category Distribution")

    fig_cat = px.bar(
    category_df.sort_values("total_revenue", ascending=False),
    x="product_category",
    y="total_revenue",
    color="product_category",
    text="category_revenue_share_pct",
    color_discrete_sequence=[
        "#006241",
        "#1E3A8A",
        "#D4A017",
        "#0B4F71",
        "#34A853",
        "#4F46E5",
        "#A16207"
    ]
)
    fig_cat.update_layout(height=450, xaxis_title="", yaxis_title="Total Revenue", showlegend=False)
    st.plotly_chart(fig_cat, use_container_width=True)

    st.dataframe(
    category_df[
        [
            "product_category",
            "units_sold",
            "total_revenue",
            "category_revenue_share_pct"
        ]
    ],
    use_container_width=True
)