import streamlit as st

def render_product_form():
    with st.form("product_form"):
        st.subheader("Add New Product")
        product_name = st.text_input("Product Name")
        col1, col2 = st.columns(2)
        with col1:
            gf_price = st.number_input("Gluten-Free Price ($)", min_value=0.0, step=0.01)
        with col2:
            regular_price = st.number_input("Regular Price ($)", min_value=0.0, step=0.01)
        
        submitted = st.form_submit_button("Add Product")
        
        if submitted:
            if not product_name:
                st.error("Please enter a product name")
                return None
            if gf_price <= 0 or regular_price <= 0:
                st.error("Prices must be greater than 0")
                return None
            return {
                "product_name": product_name,
                "gf_price": gf_price,
                "regular_price": regular_price
            }
    return None
