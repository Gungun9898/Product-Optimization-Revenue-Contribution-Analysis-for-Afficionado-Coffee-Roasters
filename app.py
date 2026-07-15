import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st
import base64
from pathlib import Path

def get_base64_image(image_path):
    with open(image_path, "rb") as img:
        return base64.b64encode(img.read()).decode()
        
BASE_DIR = Path(__file__).parent

bg_image = get_base64_image(BASE_DIR / "front_page.jpg")

DB_PATH = BASE_DIR / "coffee_roasters.db"

#st.write("Image loaded:", len(bg_image))    


st.set_page_config(page_title="Coffee Roasters KPI App", layout="wide")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}         

/* Background */
.stApp {{
    background-image: url("data:image/jpeg;base64,{bg_image}");
    background-size: cover;
    background-repeat: no-repeat;
    background-position: center;
}}

.stApp::before {{
    content: "";
    position: fixed;
    inset: 0;

    background-image: url("data:image/jpeg;base64,{bg_image}");
    background-repeat: repeat;
    background-size: 500px;

    opacity: 0.04;

    pointer-events: none;
    z-index: -1;
}}

.stApp::after {{
    content: "";
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.35);
    pointer-events: none;
    z-index: -1;
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: linear-gradient(
        180deg,
        rgba(0,98,65,0.95) 0%,
        rgba(30,58,138,0.95) 100%
    ) !important;
}}

/* KPI Cards */
[data-testid="stMetric"] {{
    background: rgba(255,255,255,0.92);
    backdrop-filter: blur(8px);
    border-radius: 16px;
    padding: 20px;
    border-left: 6px solid #006241;
    box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}}

/* Main Title */
h1 {{
    color: #0F172A;
    font-size: 52px;
    font-weight: 800;
    letter-spacing: -1px;
}}

/* Subheaders */
h2 {{
    font-size: 42px;
    font-weight: 700;
    color: #1E3A8A;
}}

/* Metric Values */
div[data-testid="stMetricValue"] {{
    color: #006241;
    font-size: 40px;
    font-weight: 800;
}}

/* Metric Labels */
div[data-testid="stMetricLabel"] {{
    color: #64748B;
}}

/* Tables */
[data-testid="stDataFrame"] {{
    border-radius: 12px;
}}

/* Select Boxes */
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {{
    background-color: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.25);
    color: white;
}}

/* Slider */
[data-testid="stSidebar"] .stSlider label {{
    color: white !important;
}}

/* Sidebar Labels */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div {{
    color: #D4A017 !important;
}}

</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)

    product_df = pd.read_sql_query(
        "SELECT * FROM vw_product_kpi", conn
    )

    category_df = pd.read_sql_query(
        "SELECT * FROM vw_category_kpi", conn
    )

    pareto_df = pd.read_sql_query(
        "SELECT * FROM vw_product_pareto", conn
    )

    conn.close()

    return product_df, category_df, pareto_df

product_df, category_df, pareto_df = load_data()


# Standardize column names
product_df.columns = product_df.columns.str.lower().str.strip()
category_df.columns = category_df.columns.str.lower().str.strip()
pareto_df.columns = pareto_df.columns.str.lower().str.strip()


st.title("Coffee Roasters KPI App")
st.caption("Streamlit front-end powered by SQLite KPI views")


st.markdown("""
<div style="
background: rgba(255,255,255,0.82);
backdrop-filter: blur(10px);
border:1px solid rgba(255,255,255,0.3);
padding:25px;
border-radius:20px;
margin-bottom:20px;
box-shadow:0 8px 32px rgba(0,0,0,0.08);
">
<h2 style="color:#1E3A8A;margin:0;">
    Coffee Roasters Performance Dashboard
</h2>
<p style="color:#475569;">
Monitor product performance, revenue contribution,
category trends and strategic insights.
</p>
</div>
""", unsafe_allow_html=True)



st.sidebar.markdown("""
<div style="
background: linear-gradient(135deg,#006241,#1E3A8A);
padding:12px;
border-radius:12px;
text-align:center;
margin-bottom:15px;
box-shadow:0 4px 10px rgba(0,0,0,0.1);
">
<h3 style="
color:#D4A017;
margin:0;
font-size:22px;
font-weight:700;
letter-spacing:0.3px;
">
    Dashboard Filters
</h3>
                    

</div>
                    

                    
                                        
""", unsafe_allow_html=True)



category_options = ["All"] + sorted(
    product_df["product_category"].dropna().unique().tolist()
)

selected_category = st.sidebar.selectbox(
    "Category",
    category_options
)

if selected_category == "All":
    available_types = product_df
else:
    available_types = product_df[
        product_df["product_category"] == selected_category
    ]

type_options = ["All"] + sorted(
    available_types["product_type"].dropna().unique().tolist()
)

selected_type = st.sidebar.selectbox(
    "Product Type",
    type_options
)

if selected_category == "All":
    max_products = len(product_df)
else:
    max_products = len(
        product_df[
            product_df["product_category"] == selected_category
        ]
    )

top_n = st.sidebar.slider(
    "Top-N Products",
    min_value=5,
    max_value=30,
    value=10
)

if top_n > max_products:
    st.sidebar.warning(
        f"You selected Top {top_n}, but only {max_products} products exist for the current filters."
    )
else:
    st.sidebar.caption(
        f"Selected category contains {max_products} products."
    )

filtered_product = product_df.copy()

if selected_category != "All":
    filtered_product = filtered_product[
    filtered_product["product_category"] == selected_category
]

if selected_category != "All":
    filtered_product = filtered_product[
        filtered_product["product_category"] == selected_category
    ]

if selected_type != "All":
    filtered_product = filtered_product[
        filtered_product["product_type"] == selected_type
    ]

total_revenue = filtered_product["total_revenue"].sum()
total_units = filtered_product["units_sold"].sum()
product_count = filtered_product["product_id"].nunique()
avg_revenue = filtered_product["total_revenue"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue", f"${total_revenue:,.0f}")
c2.metric("Units Sold", f"{total_units:,.0f}")
c3.metric("Products", f"{product_count}")
c4.metric("Avg Revenue", f"${avg_revenue:,.0f}")

st.markdown("## Top Revenue Generating Products")

display_cols = [
    "product_detail",
    "product_category",
    "product_type",
    "units_sold",
    "total_revenue",
    "revenue_share_pct"
]

display_cols = [
    c for c in display_cols
    if c in filtered_product.columns
]

top_products = (
    filtered_product.sort_values("total_revenue", ascending=False)
    .head(top_n)[display_cols]
)

st.dataframe(
    top_products.rename(
        columns={
            "product_detail": "Product",
            "product_category": "Category",
            "product_type": "Type",
            "units_sold": "Units Sold",
            "total_revenue": "Revenue",
            "revenue_share_pct": "Revenue %"
        }
    ),
    use_container_width=True
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Top Products by Revenue")
    category_colors = {
        "Coffee": "#006241",              # Starbucks Green
        "Tea": "#1E3A8A",                 # Executive Navy
        "Drinking Chocolate": "#D4A017", # Gold
        "Bakery": "#8B5E3C",             # Coffee Brown
        "Coffee beans": "#0F766E",       # Teal
        "Branded": "#7C3AED",            # Purple
        "Flavours": "#DC2626",           # Red
        "Loose Tea": "#16A34A",          # Green
        "Packaged Chocolate": "#F97316" # Orange
    }
    fig_bar = px.bar(
        top_products.sort_values("total_revenue", ascending=True),
        x="total_revenue",
        y="product_detail",
        color="product_category",
        orientation="h",
        color_discrete_map=category_colors
    )
    fig_bar.update_layout(height=450, yaxis_title="", xaxis_title="Total Revenue")
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.subheader("Popularity vs Revenue")
    category_colors = {
        "Coffee": "#006241",              # Starbucks Green
        "Tea": "#1E3A8A",                 # Executive Navy
        "Drinking Chocolate": "#D4A017", # Gold
        "Bakery": "#8B5E3C",             # Coffee Brown
        "Coffee beans": "#0F766E",       # Teal
        "Branded": "#7C3AED",            # Purple
        "Flavours": "#DC2626",           # Red
        "Loose Tea": "#16A34A",          # Green
        "Packaged Chocolate": "#F97316" # Orange
    }
    
    fig_scatter = px.scatter(
        filtered_product,
        x="units_sold",
        y="total_revenue",
        color="product_category",
        hover_name="product_detail",
        size="revenue_share_pct",
        color_discrete_map=category_colors
    )
   
    fig_scatter.update_layout(height=450)
    st.plotly_chart(fig_scatter, use_container_width=True)
