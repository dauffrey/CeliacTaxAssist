import streamlit as st
from utils.ocr_processor import extract_prices_from_image, get_highest_prices
from PIL import Image
import io

def render_receipt_scanner():
    st.subheader("Scan Receipt")
    
    # File uploader with clear format instructions
    st.markdown("""
        <div style='background: var(--ios-info-background); padding: 10px; border-radius: 10px; margin-bottom: 15px;'>
            <p style='margin: 0; color: var(--ios-info-text);'>
                📸 <strong>Supported formats:</strong> JPEG, PNG, BMP, TIFF<br>
                💡 <strong>Tips for best results:</strong>
                • Ensure good lighting<br>
                • Keep receipt flat<br>
                • Make sure prices are clearly visible
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Upload receipt image",
        type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
        help="Upload a clear image of your receipt showing both gluten-free and regular product prices"
    )
    
    if uploaded_file is not None:
        try:
            # Read file content
            image_bytes = uploaded_file.getvalue()
            
            # Display the uploaded image with max width
            image = Image.open(io.BytesIO(image_bytes))
            
            # Calculate display width (max 600px while maintaining aspect ratio)
            max_width = 600
            if image.width > max_width:
                ratio = max_width / image.width
                display_size = (max_width, int(image.height * ratio))
            else:
                display_size = (image.width, image.height)
            
            # Display image with caption
            st.image(image, caption='Uploaded Receipt', use_column_width=False, width=display_size[0])
            
            with st.spinner("Processing receipt..."):
                # Process the image
                try:
                    prices = extract_prices_from_image(image_bytes)
                    
                    if not prices:
                        st.warning("🔍 No prices detected in the receipt. Please ensure:")
                        st.markdown("""
                            - The receipt image is clear and well-lit
                            - Prices are clearly visible
                            - Prices are in standard format (e.g., $XX.XX)
                        """)
                        return None
                    
                    gf_price, regular_price = get_highest_prices(prices)
                    
                    if gf_price is None or regular_price is None:
                        st.warning("⚠️ Could not identify both gluten-free and regular prices. Please ensure both prices are visible in the receipt.")
                        return None
                    
                    # Display detected prices in a more appealing way
                    st.success("✅ Prices detected successfully!")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Detected GF Price", f"${gf_price:.2f}")
                    with col2:
                        st.metric("Detected Regular Price", f"${regular_price:.2f}")
                    
                    # Show price difference
                    price_difference = gf_price - regular_price
                    st.metric("Price Difference", f"${price_difference:.2f}")
                    
                    # Allow user to confirm and use these prices
                    if st.button("✅ Use these prices", type="primary"):
                        return {
                            "gf_price": gf_price,
                            "regular_price": regular_price
                        }
                    
                except Exception as e:
                    st.error(f"❌ Error processing receipt: {str(e)}")
                    st.markdown("""
                        Please make sure:
                        - The image is not corrupted
                        - The file format is supported
                        - The image is clear and readable
                    """)
                    return None
                
        except Exception as e:
            st.error(f"❌ Error loading image: {str(e)}")
            return None
    
    return None
