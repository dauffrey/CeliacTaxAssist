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

# Page configuration with Canadian branding
st.set_page_config(
    page_title="Canadian Celiac Tax Calculator",
    page_icon="🍁",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/about-your-tax-return/tax-return/completing-a-tax-return/deductions-credits-expenses/lines-33099-33199-eligible-medical-expenses-you-claim-on-your-tax-return.html',
        'Report a bug': "mailto:support@example.com",
        'About': "Canadian Celiac Tax Calculator helps you track and calculate medical expense tax credits for gluten-free products."
    }
)

# Load custom CSS
with open("assets/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Skip Navigation Link for Keyboard Users
st.markdown("""
    <a href="#main-content" class="skip-link">
        Skip to main content
    </a>
""", unsafe_allow_html=True)

# Initialize database
@st.cache_resource
def get_database():
    return DatabaseManager()

db = get_database()

# Authentication
user_id = render_auth(db)

# Main app layout with Canadian branding
st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <div style='font-size: 2.5rem; margin-bottom: 10px;'>
            🍁 <span style='color: var(--canada-red);'>Canadian</span> Celiac Tax Calculator
        </div>
        <p style='color: var(--text-secondary); font-size: 1.1rem; margin-top: 5px;'>
            Track your gluten-free expenses for CRA medical expense claims
        </p>
    </div>
    <div id="main-content" aria-label="Main content" role="main"></div>
""", unsafe_allow_html=True)

# Accessible tabs with Canadian-themed icons
tabs = {
    "Products": "🍁",
    "Price Comparison": "💰",
    "Scan Receipt": "📸",
    "Summary": "📊",
    "Guidelines": "📖",
    "Chat Assistant": "🤖"
}

# Create tabs with ARIA labels
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    f"{icon} {name}" for name, icon in tabs.items()
])

with tab1:
    st.markdown("""
        <div role="region" aria-label="Product Management">
            <h2>Track Your Gluten-Free Products</h2>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        product_data = render_product_form()
        if product_data:
            db.add_product(**product_data, user_id=user_id)
            st.success("✅ Product added successfully!")
            st.rerun()
    
    with col2:
        st.markdown("""
        <div role="complementary" aria-label="Quick Guide" 
             style='background: var(--background-secondary); padding: 16px; border-radius: 16px;'>
            <h3 style='color: var(--canada-red);'>🍁 Quick Guide</h3>
            <ul style='margin: 0; padding-left: 20px;'>
                <li>Add your gluten-free products</li>
                <li>Enter regular counterpart prices</li>
                <li>Keep receipts for CRA purposes</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    products = db.get_user_products(user_id)
    render_product_list(products)

with tab2:
    render_price_comparison(db, user_id)

with tab3:
    st.markdown("""
        <div role="region" aria-label="Receipt Scanner">
            <div style='background: var(--background-primary); padding: 20px; border-radius: 16px; text-align: center;'>
                <span aria-hidden="true" style='font-size: 2rem;'>📸</span>
                <h2>Scan Your Receipt</h2>
                <p>Upload a receipt image to automatically extract prices</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    price_data = render_receipt_scanner()
    if price_data and price_data.get("items"):
        for item in price_data["items"]:
            db.add_product(
                product_name=item["product_name"],
                gf_price=item["gf_price"],
                regular_price=item["regular_price"],
                user_id=user_id
            )
        st.success(f"✅ {len(price_data['items'])} products added successfully from receipt!")
        st.rerun()

with tab4:
    if products := db.get_user_products(user_id):
        calculations = calculate_tax_credit(products)
        
        st.markdown("""
            <div role="region" aria-label="Tax Summary">
                <h2>Tax Summary</h2>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Total Extra Cost", f"${calculations['total_difference']:.2f}", 
                     help="Total difference between GF and regular products")
        with col2:
            st.metric("📊 Products Tracked", calculations['product_count'],
                     help="Number of products tracked")
        with col3:
            st.metric("💸 Estimated Tax Credit", f"${calculations['estimated_tax_credit']:.2f}",
                     help="Estimated tax credit based on CRA guidelines")
        
        st.subheader("Export Options")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            pdf_buffer = generate_tax_report(products, calculations)
            st.download_button(
                label="📑 CRA Report (PDF)",
                data=pdf_buffer,
                file_name="celiac_tax_report.pdf",
                mime="application/pdf",
                help="Download a detailed PDF report for CRA submission"
            )
        
        with col2:
            csv_data = generate_turbotax_csv(products, calculations)
            st.download_button(
                label="📊 TurboTax Import",
                data=csv_data,
                file_name="celiac_tax_turbotax.csv",
                mime="text/csv",
                help="Export data for TurboTax import"
            )
        
        with col3:
            qif_data = generate_quicken_qif(products)
            st.download_button(
                label="💳 Quicken Import",
                data=qif_data,
                file_name="celiac_tax_quicken.qif",
                mime="text/plain",
                help="Export data for Quicken import"
            )
        
        with col4:
            json_data = generate_json_export(products, calculations)
            st.download_button(
                label="🔄 JSON Export",
                data=json_data,
                file_name="celiac_tax_data.json",
                mime="application/json",
                help="Export raw data in JSON format"
            )

with tab5:
    render_educational_content()

with tab6:
    render_chat_assistant()

# Accessible footer with Canadian branding
st.markdown("""
    <footer role="contentinfo" style='text-align: center; padding: 20px 0; color: var(--text-secondary);'>
        <div style='margin-bottom: 10px;'>
            <span aria-hidden="true">🍁</span> Made in Canada for the Celiac Community
        </div>
        <div style='font-size: 0.9rem;'>
            <a href="https://www.canada.ca/en/revenue-agency.html" target="_blank" rel="noopener noreferrer"
               style='color: var(--link-color); text-decoration: underline;'>
                CRA Guidelines
            </a> |
            <a href="#" style='color: var(--link-color); text-decoration: underline;'>
                Accessibility Statement
            </a> |
            <a href="#" style='color: var(--link-color); text-decoration: underline;'>
                Privacy Policy
            </a>
        </div>
    </footer>
""", unsafe_allow_html=True)
