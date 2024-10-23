import streamlit as st
from utils.ocr_processor import extract_prices_from_image, get_highest_prices

def render_receipt_scanner():
    st.subheader("Scan Receipt")
    
    uploaded_file = st.file_uploader("Upload receipt image", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file is not None:
        # Display the uploaded image
        st.image(uploaded_file, caption='Uploaded Receipt', use_column_width=True)
        
        # Process the image
        try:
            prices = extract_prices_from_image(uploaded_file.getvalue())
            
            if not prices:
                st.warning("No prices detected in the receipt. Please ensure the image is clear and contains visible price information.")
                return None
            
            gf_price, regular_price = get_highest_prices(prices)
            
            if gf_price is None or regular_price is None:
                st.warning("Could not detect enough prices. Please ensure the receipt shows both GF and regular product prices.")
                return None
            
            # Display detected prices
            st.success("Prices detected!")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Detected GF Price", f"${gf_price:.2f}")
            with col2:
                st.metric("Detected Regular Price", f"${regular_price:.2f}")
            
            # Allow user to confirm and use these prices
            if st.button("Use these prices"):
                return {
                    "gf_price": gf_price,
                    "regular_price": regular_price
                }
            
        except Exception as e:
            st.error(f"Error processing receipt: {str(e)}")
            return None
    
    return None
