import streamlit as st
import pandas as pd
from database.db_manager import DatabaseManager
from components.product_form import render_product_form
from components.product_list import render_product_list
from components.educational_content import render_educational_content
from components.receipt_scanner import render_receipt_scanner
from components.auth import render_auth
from utils.calculations import calculate_tax_credit
from utils.pdf_generator import generate_tax_report

# Page configuration
st.set_page_config(
    page_title="Celiac Tax Calculator",
    page_icon="🌾",
    layout="wide"
)

# Load custom CSS
with open("assets/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize database
@st.cache_resource
def get_database():
    return DatabaseManager()

db = get_database()

# Authentication
user_id = render_auth(db)

# Main app layout
st.title("Celiac Tax Calculator")
st.markdown("Track your gluten-free expenses for tax purposes")

# Tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["Products", "Scan Receipt", "Summary", "Guidelines"])

with tab1:
    # Product management
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Product form
        product_data = render_product_form()
        if product_data:
            db.add_product(**product_data, user_id=user_id)
            st.success("Product added successfully!")
    
    with col2:
        st.info("""
        📝 Add your gluten-free products and their regular counterparts to track the price difference.
        Keep your receipts for tax purposes!
        """)
    
    # Product list
    products = db.get_user_products(user_id)
    render_product_list(products)

with tab2:
    # Receipt scanner
    st.info("""
    📸 Upload a receipt image to automatically extract prices.
    Make sure the receipt shows both gluten-free and regular product prices.
    """)
    
    price_data = render_receipt_scanner()
    if price_data:
        product_name = st.text_input("Product Name")
        if product_name and st.button("Add Product"):
            db.add_product(
                product_name=product_name,
                gf_price=price_data["gf_price"],
                regular_price=price_data["regular_price"],
                user_id=user_id
            )
            st.success("Product added successfully from receipt!")

with tab3:
    # Summary and calculations
    if products := db.get_user_products(user_id):
        calculations = calculate_tax_credit(products)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Extra Cost", f"${calculations['total_difference']:.2f}")
        with col2:
            st.metric("Products Tracked", calculations['product_count'])
        with col3:
            st.metric("Estimated Tax Credit", f"${calculations['estimated_tax_credit']:.2f}")
        
        # Generate report
        if st.button("Generate Tax Report"):
            pdf_buffer = generate_tax_report(products, calculations)
            st.download_button(
                label="Download Tax Report",
                data=pdf_buffer,
                file_name="celiac_tax_report.pdf",
                mime="application/pdf"
            )
    else:
        st.info("Add some products to see your tax summary!")

with tab4:
    # Educational content
    render_educational_content()
