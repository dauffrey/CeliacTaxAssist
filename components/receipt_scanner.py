import streamlit as st
from utils.ocr_processor import extract_prices_from_image, ItemPrice
from PIL import Image
import io
from typing import List, Dict

def render_detected_items(items: List[ItemPrice]) -> Dict[str, Dict]:
    """
    Render detected items with checkboxes and return selected items
    """
    st.markdown("### Detected Items")
    
    selected_items = {}
    for idx, item in enumerate(items):
        with st.expander(f"{item.item_name} - ${item.final_price:.2f}", expanded=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if item.description:
                    st.text(f"Description: {item.description}")
                if item.discount:
                    st.text(f"Original: ${item.original_price:.2f}")
                    st.text(f"Discount: -${item.discount:.2f}")
                
                # Show GF confidence if any
                if item.gf_confidence and item.gf_confidence > 0:
                    confidence_color = (
                        "🟢" if item.gf_confidence > 0.8 else
                        "🟡" if item.gf_confidence > 0.4 else
                        "🟠"
                    )
                    st.text(f"GF Confidence: {confidence_color} {item.gf_confidence*100:.0f}%")
            
            with col2:
                is_gf = st.checkbox("Gluten-Free", key=f"gf_{idx}")
                is_regular = st.checkbox("Regular", key=f"reg_{idx}")
                
                if is_gf or is_regular:
                    selected_items[item.item_name] = {
                        "name": item.item_name,
                        "price": item.final_price,
                        "is_gf": is_gf,
                        "is_regular": is_regular
                    }
    
    return selected_items

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
                try:
                    # Process the image
                    detected_items = extract_prices_from_image(image_bytes)
                    
                    if not detected_items:
                        st.warning("🔍 No items or prices detected in the receipt. Please ensure:")
                        st.markdown("""
                            - The receipt image is clear and well-lit
                            - Text and prices are clearly visible
                            - Items and prices are in standard format
                        """)
                        return None
                    
                    # Display detected items and get user selection
                    selected_items = render_detected_items(detected_items)
                    
                    if selected_items:
                        # Find GF and regular pairs
                        gf_items = {name: item for name, item in selected_items.items() if item["is_gf"]}
                        regular_items = {name: item for name, item in selected_items.items() if item["is_regular"]}
                        
                        if gf_items and regular_items:
                            st.success("✅ Items selected successfully!")
                            
                            # Display comparison summary
                            st.markdown("### Price Comparison Summary")
                            for gf_name, gf_item in gf_items.items():
                                st.markdown(f"""
                                    **{gf_name}**
                                    - GF Price: ${gf_item['price']:.2f}
                                    - Regular Price: ${next(iter(regular_items.values()))['price']:.2f}
                                    - Difference: ${gf_item['price'] - next(iter(regular_items.values()))['price']:.2f}
                                """)
                            
                            if st.button("✅ Add Selected Items", type="primary"):
                                return {
                                    "items": [
                                        {
                                            "product_name": gf_name,
                                            "gf_price": gf_item["price"],
                                            "regular_price": next(iter(regular_items.values()))["price"]
                                        }
                                        for gf_name, gf_item in gf_items.items()
                                    ]
                                }
                        else:
                            st.info("Please mark at least one gluten-free and one regular item for comparison.")
                    
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
