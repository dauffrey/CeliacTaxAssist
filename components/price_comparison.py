import streamlit as st
import pandas as pd
from datetime import datetime

def render_price_comparison(db, user_id):
    st.subheader("Price Comparison Database")
    
    # Store Management Section
    with st.expander("Manage Stores"):
        col1, col2 = st.columns(2)
        with col1:
            store_name = st.text_input("Store Name")
            location = st.text_input("Location (optional)")
            if st.button("Add Store"):
                if store_name:
                    if db.add_store(store_name, location):
                        st.success(f"Store '{store_name}' added successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to add store. It might already exist.")
                else:
                    st.error("Please enter a store name.")
        
        with col2:
            stores = db.get_stores()
            if stores:
                st.write("Current Stores:")
                stores_df = pd.DataFrame(stores)
                st.dataframe(stores_df[['store_name', 'location']], hide_index=True)

    # Price Comparison Entry Form
    st.subheader("Add Price Comparison")
    with st.form("price_comparison_form"):
        col1, col2 = st.columns(2)
        with col1:
            product_name = st.text_input("Product Name")
            store = st.selectbox("Store", options=[s['store_name'] for s in stores], key="store_select")
            price_date = st.date_input("Price Date", datetime.now().date())
        
        with col2:
            gf_price = st.number_input("Gluten-Free Price ($)", min_value=0.0, step=0.01)
            regular_price = st.number_input("Regular Price ($)", min_value=0.0, step=0.01)
        
        submitted = st.form_submit_button("Add Price Comparison")
        
        if submitted:
            if not product_name or not store:
                st.error("Please fill in all required fields.")
            else:
                store_id = next(s['id'] for s in stores if s['store_name'] == store)
                if db.add_price_comparison(product_name, store_id, gf_price, regular_price, user_id, price_date):
                    st.success("Price comparison added successfully!")
                    st.rerun()
                else:
                    st.error("Failed to add price comparison. A comparison for this product at this store on this date might already exist.")

    # Price Comparison Display
    st.subheader("Price Comparisons")
    comparisons = db.get_price_comparisons()
    
    if comparisons:
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(comparisons)
        df['difference'] = df['gf_price'] - df['regular_price']
        df['price_date'] = pd.to_datetime(df['price_date']).dt.date
        
        # Group by product and find best deals
        best_deals = df.loc[df.groupby('product_name')['gf_price'].idxmin()]
        
        # Display best deals
        st.write("🏷️ Best Deals for Gluten-Free Products:")
        best_deals_display = best_deals[['product_name', 'store_name', 'gf_price', 'regular_price', 'difference', 'price_date']]
        best_deals_display.columns = ['Product', 'Store', 'GF Price ($)', 'Regular Price ($)', 'Difference ($)', 'Date']
        st.dataframe(best_deals_display, hide_index=True)
        
        # Allow filtering by product
        st.write("📊 Detailed Price Comparison:")
        unique_products = sorted(df['product_name'].unique())
        selected_product = st.selectbox("Select Product", ["All Products"] + list(unique_products))
        
        if selected_product != "All Products":
            filtered_df = df[df['product_name'] == selected_product]
        else:
            filtered_df = df
        
        # Display detailed comparison
        comparison_display = filtered_df[['product_name', 'store_name', 'location', 'gf_price', 'regular_price', 'difference', 'price_date']]
        comparison_display.columns = ['Product', 'Store', 'Location', 'GF Price ($)', 'Regular Price ($)', 'Difference ($)', 'Date']
        st.dataframe(comparison_display, hide_index=True)
    else:
        st.info("No price comparisons available yet. Add some above!")
