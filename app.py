"""
SecureStego - Production Steganography Application
Main Dashboard
"""

import streamlit as st
from pathlib import Path
import base64

# Page config
st.set_page_config(
    page_title="ImageStegano",
    page_icon="🔐",
    layout="wide",  
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    css_file = Path("styles/main.css")
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.current_key = None
    st.session_state.key_name = None

# Header
st.markdown("""
<div class="stego-header">
    <h1>🔐ImageStegano</h1>
    
</div>
""", unsafe_allow_html=True)

# Welcome Section
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="stego-card">
        <h2>🛡️ Military-Grade Security</h2>
        <p>AES-256-GCM encryption with authenticated encryption ensures your data remains confidential and tamper-proof.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="stego-card">
        <h2>👁️ Invisible Hiding</h2>
        <p>LSB steganography embeds data in images with imperceptible visual changes. Perfect for covert communication.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="stego-card">
        <h2>⚡ Production Ready</h2>
        <p>Enterprise-grade key management, analytics, and error handling. Ready to deploy and monetize.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Quick Start Guide
st.markdown("## 🚀 Quick Start Guide")

tab1, tab2, tab3 = st.tabs(["📝 Hide Data", "🔍 Reveal Data", "🔑 Manage Keys"])

with tab1:
    st.markdown("""
    ### Hide Encrypted Data in Images
    
    1. **Generate Key**: Go to Key Manager and create a new encryption key
    2. **Upload Image**: Select a PNG/BMP image (minimum 100x100 pixels)
    3. **Enter Data**: Type message or upload file to hide
    4. **Hide**: Click "Hide Data" and download your stego image
    
    **Supported Formats:** PNG, BMP, TIFF  
    **Max Capacity:** Depends on image size (~3 bits per pixel)
    """)

with tab2:
    st.markdown("""
    ### Extract Hidden Data from Images
    
    1. **Upload Stego Image**: Select image with hidden data
    2. **Enter Key**: Provide encryption key or load from Key Manager
    3. **Reveal**: Extract and decrypt hidden data automatically
    4. **Download**: Save extracted data as text or file
    
    **Security:** Authentication tag verifies data integrity
    """)

with tab3:
    st.markdown("""
    ### Secure Key Management
    
    1. **Generate**: Create cryptographically secure 256-bit keys
    2. **Store**: Save keys with descriptive names and metadata
    3. **Import/Export**: Transfer keys securely between systems
    4. **Delete**: Remove keys you no longer need
    
    **Fingerprint:** Each key has unique SHA-256 fingerprint
    """)

st.markdown("---")

# Features
st.markdown("## ✨ Enterprise Features")

feature_col1, feature_col2 = st.columns(2)

with feature_col1:
    st.markdown("""
    ### 🔒 Security Features
    - **AES-256-GCM** authenticated encryption
    - **PBKDF2** key derivation (600K iterations)
    - **CSPRNG** key generation via `secrets.token_bytes()`
    - **Tamper detection** with authentication tags
    - **Key fingerprinting** for verification
    - **Metadata stripping** to prevent leaks
    """)

with feature_col2:
    st.markdown("""
    ### 🎨 User Experience
    - **Modern UI** with custom CSS styling
    - **Progress indicators** for long operations
    - **Image comparison** (PSNR calculation)
    - **Capacity calculator** for payload sizing
    - **Analytics dashboard** with operation history
    - **Export capabilities** for keys and data
    """)

st.markdown("---")

# Statistics
st.markdown("## 📊 Platform Statistics")

from utils.analytics import Analytics
from utils.key_manager import KeyManager

stats = Analytics.get_statistics()
km = KeyManager()
keys = km.list_keys()

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

with metric_col1:
    st.metric("Total Operations", stats['total_operations'])

with metric_col2:
    st.metric("Data Hidden", f"{stats['total_data_hidden_mb']} MB")

with metric_col3:
    st.metric("Active Keys", len(keys))

with metric_col4:
    st.metric("Avg Payload", f"{stats['avg_payload_size_kb']:.1f} KB")

st.markdown("---")

# Navigation
st.markdown("## 🧭 Navigation")

nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)

with nav_col1:
    st.page_link("app.py", label="🏠 Home", use_container_width=True)
    st.page_link("pages/1_🔐_Hide_Data.py", label="🔐 Hide Data", use_container_width=True)

with nav_col2:
    st.page_link("pages/2_🔓_Reveal_Data.py", label="🔓 Reveal Data", use_container_width=True)

with nav_col3:
    st.page_link("pages/3_🔑_Key_Manager.py", label="🔑 Key Manager", use_container_width=True)

with nav_col4:
    st.page_link("pages/4_📊_Analytics.py", label="📊 Analytics", use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #94a3b8; padding: 2rem 0;'>
    <p><strong>ImageStegano</strong>  </p>
    <p> |
    ] AES-256-GCM + LSB Algorithm |</p>
</div>
""", unsafe_allow_html=True)
