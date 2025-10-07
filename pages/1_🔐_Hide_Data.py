"""
Hide Data Page - Encrypt and Embed Data in Images
"""

import streamlit as st
from pathlib import Path
import os
import io
from PIL import Image
from datetime import datetime

from utils.crypto_engine import CryptoEngine, quick_encrypt
from utils.stego_engine import StegoEngine
from utils.key_manager import KeyManager
from utils.analytics import Analytics

st.set_page_config(
    page_title="Hide Data - SecureStego",
    page_icon="🔐",
    layout="wide"
)

# Load CSS
def load_css():
    css_file = Path("styles/main.css")
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# Initialize
if 'uploads_dir' not in st.session_state:
    Path("uploads").mkdir(exist_ok=True)
    Path("output").mkdir(exist_ok=True)

st.markdown("""
<div class="stego-header">
    <h1>🔐 Hide Encrypted Data</h1>
    <p>Encrypt and embed your secret data into images</p>
</div>
""", unsafe_allow_html=True)

# Main Layout
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📸 Upload Cover Image")
    
    uploaded_image = st.file_uploader(
        "Choose a PNG/BMP image",
        type=['png', 'bmp', 'tiff'],
        help="Lossless formats work best for LSB steganography",
        key="cover_image"
    )
    
    if uploaded_image:
        # Save uploaded image
        image_path = Path("uploads") / uploaded_image.name
        with open(image_path, "wb") as f:
            f.write(uploaded_image.getbuffer())
        
        # Display image
        st.image(uploaded_image, caption="Cover Image")
        
        # Validate and show stats
        is_valid, msg, stats = StegoEngine.validate_image(str(image_path))
        
        if is_valid:
            st.success(msg)
            
            # Show capacity
            st.markdown("#### 📊 Image Capacity")
            capacity_col1, capacity_col2, capacity_col3 = st.columns(3)
            
            with capacity_col1:
                st.metric("Dimensions", f"{stats['width']}×{stats['height']}")
            with capacity_col2:
                st.metric("Format", stats['format'])
            with capacity_col3:
                st.metric("Max Capacity", f"{stats['capacity_kb']:.1f} KB")
            
        else:
            st.error(msg)
            st.stop()

with col2:
    st.markdown("### 🔑 Encryption Setup")
    
    # Key selection
    km = KeyManager()
    keys = km.list_keys()
    
    if keys:
        key_option = st.radio(
            "Select Key Method",
            ["Use Saved Key", "Enter Key Manually", "Generate New Key"],
            horizontal=True
        )
        
        if key_option == "Use Saved Key":
            key_names = [k['name'] for k in keys]
            selected_key_name = st.selectbox("Choose Key", key_names)
            
            if selected_key_name:
                encryption_key, key_meta = km.load_key(selected_key_name)
                st.info(f"🔑 Using key: **{selected_key_name}**\n\nFingerprint: `{key_meta['fingerprint']}`")
        
        elif key_option == "Enter Key Manually":
            key_input = st.text_input(
                "Enter Base64 Key",
                type="password",
                help="Paste your 256-bit key in base64 format"
            )
            if key_input:
                try:
                    encryption_key = km.string_to_key(key_input)
                    fingerprint = km.get_key_fingerprint(encryption_key)
                    st.success(f"✅ Valid key | Fingerprint: `{fingerprint}`")
                except Exception as e:
                    st.error(f"❌ Invalid key: {str(e)}")
                    st.stop()
        
        else:  # Generate New Key
            if st.button("🎲 Generate New Key", use_container_width=True):
                new_key = km.generate_key()
                key_name = f"Key_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                km.save_key(new_key, key_name, "Auto-generated for hide operation")
                encryption_key = new_key
                st.success(f"✅ Generated new key: **{key_name}**")
                st.info(f"Key saved to Key Manager")
    else:
        st.warning("No keys found. Generating a new key...")
        if st.button("🎲 Generate First Key", use_container_width=True):
            new_key = km.generate_key()
            key_name = "Default_Key"
            km.save_key(new_key, key_name, "First encryption key")
            encryption_key = new_key
            st.success(f"✅ Generated key: **{key_name}**")
            st.rerun()

st.markdown("---")

# Data Input Section
st.markdown("### 📝 Secret Data to Hide")

data_type = st.radio(
    "Data Type",
    ["Text Message", "Upload File"],
    horizontal=True
)

if data_type == "Text Message":
    secret_message = st.text_area(
        "Enter your secret message",
        height=150,
        placeholder="Type your confidential message here...",
        help="This will be encrypted before embedding"
    )
    
    if secret_message:
        data_bytes = secret_message.encode('utf-8')
        st.info(f"📏 Message size: **{len(data_bytes)} bytes** ({len(data_bytes)/1024:.2f} KB)")

else:  # Upload File
    secret_file = st.file_uploader(
        "Upload file to hide",
        type=['txt', 'pdf', 'docx', 'jpg', 'png', 'zip', 'json'],
        help="Any file type supported"
    )
    
    if secret_file:
        data_bytes = secret_file.read()
        st.info(f"📄 File: **{secret_file.name}** | Size: **{len(data_bytes)} bytes** ({len(data_bytes)/1024:.2f} KB)")

st.markdown("---")

# Hide Button
st.markdown("### 🚀 Hide Data")

col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])

with col_btn2:
    hide_button = st.button(
        "🔐 Encrypt & Hide",
        use_container_width=True,
        type="primary"
    )

if hide_button:
    # Validation
    if not uploaded_image:
        st.error("❌ Please upload a cover image")
        st.stop()
    
    if 'encryption_key' not in locals():
        st.error("❌ Please select or generate an encryption key")
        st.stop()
    
    if 'data_bytes' not in locals():
        st.error("❌ Please enter data to hide")
        st.stop()
    
    # Check capacity
    is_valid, msg, stats = StegoEngine.validate_image(str(image_path))
    estimated_encrypted_size = len(data_bytes) * 2  # Rough estimate with encryption overhead
    
    if estimated_encrypted_size > stats['capacity_bytes']:
        st.error(f"❌ Data too large for image\n\nData: ~{estimated_encrypted_size} bytes\nCapacity: {stats['capacity_bytes']} bytes")
        st.stop()
    
    # Progress
    progress_bar = st.progress(0, text="Starting encryption...")
    
    try:
        # Step 1: Encrypt
        progress_bar.progress(25, text="🔒 Encrypting data with AES-256-GCM...")
        
        metadata = {
            'filename': uploaded_image.name if data_type == "Upload File" else "message.txt",
            'type': data_type
        }
        
        encrypted_bundle = quick_encrypt(encryption_key, data_bytes, metadata)
        
        progress_bar.progress(50, text="📦 Encrypted! Now embedding in image...")
        
        # Step 2: Embed
        output_filename = f"stego_{Path(uploaded_image.name).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        output_path = Path("output") / output_filename
        
        hide_stats = StegoEngine.hide(
            str(image_path),
            encrypted_bundle,
            str(output_path)
        )
        
        progress_bar.progress(75, text="✅ Embedded! Finalizing...")
        
        # Step 3: Log analytics
        Analytics.log_operation('hide', {
            'cover_image': uploaded_image.name,
            'payload_bytes': len(data_bytes),
            'payload_kb': len(data_bytes) / 1024,
            'capacity_used': hide_stats['capacity_used_percent'],
            'output_file': output_filename
        })
        
        progress_bar.progress(100, text="✅ Complete!")
        
        # Success!
        st.balloons()
        st.success("🎉 **Successfully hidden encrypted data in image!**")
        
        # Show results
        st.markdown("#### 📊 Operation Summary")
        
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        
        with summary_col1:
            st.metric("Original Data", f"{len(data_bytes)} bytes")
        
        with summary_col2:
            st.metric("Encrypted Payload", f"{len(encrypted_bundle)} bytes")
        
        with summary_col3:
            st.metric("Capacity Used", f"{hide_stats['capacity_used_percent']:.1f}%")
        
        # Display stego image
        st.markdown("#### 🖼️ Stego Image")
        stego_img = Image.open(output_path)
        st.image(stego_img, caption="Stego Image (with hidden data)")
        
        # Download button
        with open(output_path, "rb") as file:
            st.download_button(
                label="📥 Download Stego Image",
                data=file,
                file_name=output_filename,
                mime="image/png",
                use_container_width=True
            )
        
        # Security tips
        st.markdown("---")
        st.markdown("#### 🛡️ Security Tips")
        st.info("""
        ✅ **Your data is safe!** It's encrypted with AES-256-GCM before embedding.
        
        🔑 **Keep your key safe!** Store it separately from the image.
        
        📤 **Safe to share:** You can send this image over insecure channels (email, social media).
        
        ⚠️ **Don't modify:** Editing the image may corrupt hidden data.
        """)
        
    except Exception as e:
        st.error(f"❌ Error during operation: {str(e)}")
        progress_bar.empty()

# Sidebar info
with st.sidebar:
    st.markdown("### 💡 How It Works")
    st.markdown("""
    **Encryption Layer:**
    1. Generate random 96-bit nonce
    2. Encrypt data with AES-256-GCM
    3. Generate 128-bit auth tag
    4. Bundle nonce + ciphertext + tag
    
    **Steganography Layer:**
    5. Encode bundle as base64
    6. Embed in image LSBs
    7. Save as lossless PNG
    
    **Security:** Even if steganography is detected, encrypted data remains confidential.
    """)
    
    st.markdown("---")
    
    st.markdown("### 📚 Algorithms Used")
    st.markdown("""
    - **AES-256-GCM**: Authenticated encryption
    - **LSB**: Least Significant Bit substitution
    - **CSPRNG**: Secure key generation
    """)
