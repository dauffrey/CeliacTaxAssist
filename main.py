import streamlit as st
import pandas as pd
from database.db_manager import DatabaseManager
from components.product_form import render_product_form
from components.product_list import render_product_list
from components.educational_content import render_educational_content
from components.receipt_scanner import render_receipt_scanner
from components.auth import render_auth
from components.price_comparison import render_price_comparison
from components.chat_assistant import render_chat_assistant
from utils.calculations import calculate_tax_credit
from utils.pdf_generator import generate_tax_report
from utils.tax_export import (
    generate_turbotax_csv,
    generate_quicken_qif,
    generate_json_export
)

# Page configuration with iOS-like styling
st.set_page_config(
    page_title="Celiac Tax Calculator",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
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

# Main app layout with iOS-style header
st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <h1 style='font-size: 2.5rem; font-weight: 700; margin-bottom: 0;'>Celiac Tax Calculator</h1>
        <p style='color: #8E8E93; font-size: 1.1rem; margin-top: 5px;'>Track your gluten-free expenses for tax purposes</p>
    </div>
""", unsafe_allow_html=True)

# Tabs with iOS-style icons
tabs = {
    "Products": "📱",
    "Price Comparison": "💰",
    "Scan Receipt": "📸",
    "Summary": "📊",
    "Guidelines": "📖",
    "Chat Assistant": "🤖"
}

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([f"{icon} {name}" for name, icon in tabs.items()])

with tab1:
    # Product management
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Product form
        product_data = render_product_form()
        if product_data:
            db.add_product(**product_data, user_id=user_id)
            st.success("✅ Product added successfully!")
            st.rerun()
    
    with col2:
        st.markdown("""
        <div style='background: var(--ios-info-background); color: var(--ios-info-text); padding: 16px; border-radius: 16px;'>
            <p style='margin: 0;'>
                <strong>📝 Quick Guide</strong><br>
                • Add your gluten-free products<br>
                • Enter regular counterpart prices<br>
                • Keep receipts for tax purposes
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Product list
    products = db.get_user_products(user_id)
    render_product_list(products)

with tab2:
    # Price comparison database
    render_price_comparison(db, user_id)

with tab3:
    # Receipt scanner with iOS-style camera UI
    st.markdown("""
        <div style='background: var(--ios-card); padding: 20px; border-radius: 16px; text-align: center;'>
            <span style='font-size: 2rem;'>📸</span>
            <p style='margin: 10px 0; color: var(--ios-text-secondary);'>
                Upload a receipt image to automatically extract prices
            </p>
        </div>
    """, unsafe_allow_html=True)
    
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
            st.success("✅ Product added successfully from receipt!")
            st.rerun()

with tab4:
    # Summary and calculations with iOS-style metrics
    if products := db.get_user_products(user_id):
        calculations = calculate_tax_credit(products)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Total Extra Cost", f"${calculations['total_difference']:.2f}")
        with col2:
            st.metric("📊 Products Tracked", calculations['product_count'])
        with col3:
            st.metric("💸 Estimated Tax Credit", f"${calculations['estimated_tax_credit']:.2f}")
        
        # Export options with iOS-style buttons
        st.subheader("Export Options")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            pdf_buffer = generate_tax_report(products, calculations)
            st.download_button(
                label="📑 PDF Report",
                data=pdf_buffer,
                file_name="celiac_tax_report.pdf",
                mime="application/pdf"
            )
        
        with col2:
            csv_data = generate_turbotax_csv(products, calculations)
            st.download_button(
                label="📊 TurboTax CSV",
                data=csv_data,
                file_name="celiac_tax_turbotax.csv",
                mime="text/csv"
            )
        
        with col3:
            qif_data = generate_quicken_qif(products)
            st.download_button(
                label="💳 Quicken QIF",
                data=qif_data,
                file_name="celiac_tax_quicken.qif",
                mime="text/plain"
            )
        
        with col4:
            json_data = generate_json_export(products, calculations)
            st.download_button(
                label="🔄 JSON Export",
                data=json_data,
                file_name="celiac_tax_data.json",
                mime="application/json"
            )
        
        st.markdown("""
        <div style='background: var(--ios-info-background); color: var(--ios-info-text); padding: 16px; border-radius: 16px;'>
            <p style='margin: 0;'>
                <strong>📱 Export Options</strong><br>
                • PDF Report: Complete tax report with calculations and summary<br>
                • TurboTax (CSV): Import directly into TurboTax as medical expenses<br>
                • Quicken (QIF): Import as categorized transactions in Quicken<br>
                • JSON: Full data export for custom processing
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background: var(--ios-info-background); color: var(--ios-info-text); padding: 16px; border-radius: 16px;'>
            <p style='margin: 0; text-align: center;'>
                📱 Add some products to see your tax summary!
            </p>
        </div>
        """, unsafe_allow_html=True)

with tab5:
    # Educational content with iOS-style formatting
    render_educational_content()

with tab6:
    # Chat Assistant with iOS-style interface
    render_chat_assistant()

# Add iOS-style footer
st.markdown("""
    <div style='text-align: center; padding: 20px 0; color: var(--ios-text-secondary); font-size: 0.9rem;'>
        Made with ❤️ for the Celiac community
    </div>
""", unsafe_allow_html=True)
