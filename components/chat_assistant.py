import streamlit as st

# Knowledge base for CRA-related information
CRA_KNOWLEDGE_BASE = {
    "guidelines": [
        "The CRA allows individuals with celiac disease to claim the incremental cost of gluten-free products as a medical expense.",
        "A medical practitioner's certification of celiac disease is required.",
        "The incremental cost is the difference between gluten-free products and regular products.",
    ],
    "eligible_expenses": [
        "Gluten-free bread, muffins, and cereals",
        "Gluten-free pasta and flour",
        "Gluten-free baked goods",
        "Other specialized gluten-free products",
    ],
    "calculations": [
        "Calculate the difference between gluten-free and regular product prices",
        "Keep all receipts and price comparisons",
        "Track purchases throughout the tax year",
        "Sum up the total incremental costs",
    ],
    "documentation": [
        "Medical diagnosis documentation",
        "Receipts for gluten-free products",
        "Price comparisons with regular products",
        "Annual summary of incremental costs",
    ],
}

def get_response(query):
    """Simple response generator based on keywords"""
    query = query.lower()
    
    if any(word in query for word in ["guideline", "rule", "allow"]):
        return "\n• " + "\n• ".join(CRA_KNOWLEDGE_BASE["guidelines"])
    elif any(word in query for word in ["eligible", "expense", "product"]):
        return "\n• " + "\n• ".join(CRA_KNOWLEDGE_BASE["eligible_expenses"])
    elif any(word in query for word in ["calculate", "math", "cost"]):
        return "\n• " + "\n• ".join(CRA_KNOWLEDGE_BASE["calculations"])
    elif any(word in query for word in ["document", "receipt", "proof"]):
        return "\n• " + "\n• ".join(CRA_KNOWLEDGE_BASE["documentation"])
    else:
        return "I can help you with CRA guidelines, eligible expenses, calculations, and required documentation. Please ask a specific question about any of these topics."

def render_chat_assistant():
    st.markdown("""
        <div style='background: var(--ios-card); padding: 20px; border-radius: 16px; text-align: center; margin-bottom: 20px;'>
            <span style='font-size: 2rem;'>🤖</span>
            <p style='margin: 10px 0; color: var(--ios-text-secondary);'>
                Ask me anything about CRA guidelines for celiac disease tax claims
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history with iOS-style bubbles
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
                <div style='margin: 10px 0; text-align: right;'>
                    <div style='display: inline-block; background: var(--ios-primary); color: white; 
                         padding: 10px 15px; border-radius: 20px; border-bottom-right-radius: 5px;
                         max-width: 80%; text-align: left; animation: slideLeft 0.3s ease-out;'>
                        {message["content"]}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style='margin: 10px 0;'>
                    <div style='display: inline-block; background: var(--ios-background); color: var(--ios-text);
                         padding: 10px 15px; border-radius: 20px; border-bottom-left-radius: 5px;
                         max-width: 80%; animation: slideRight 0.3s ease-out;'>
                        {message["content"]}
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # Chat input
    if prompt := st.chat_input("Ask about CRA guidelines..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        response = get_response(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    # Add animation styles
    st.markdown("""
        <style>
            @keyframes slideLeft {
                from { transform: translateX(20px); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideRight {
                from { transform: translateX(-20px); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        </style>
    """, unsafe_allow_html=True)
