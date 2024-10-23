import streamlit as st
import pandas as pd

def render_product_list(products):
    if not products:
        st.info("No products added yet. Add your first product above!")
        return
    
    df = pd.DataFrame(products)
    df['date_added'] = pd.to_datetime(df['date_added']).dt.date
    
    st.subheader("Your Products")
    
    # Format the DataFrame for display
    display_df = df.copy()
    display_df['gf_price'] = display_df['gf_price'].apply(lambda x: f"${x:.2f}")
    display_df['regular_price'] = display_df['regular_price'].apply(lambda x: f"${x:.2f}")
    display_df['difference'] = display_df['difference'].apply(lambda x: f"${x:.2f}")
    
    st.dataframe(
        display_df[['product_name', 'gf_price', 'regular_price', 'difference', 'date_added']],
        use_container_width=True,
        hide_index=True,
    )
