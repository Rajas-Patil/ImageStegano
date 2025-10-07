"""
Reveal Data Page - Extract and Decrypt Hidden Data
"""

import streamlit as st
from pathlib import Path
import io
from datetime import datetime

from utils.crypto_engine import CryptoEngine, quick_decrypt
from utils.stego_engine import StegoEngine
from utils.key_manager import KeyManager
from utils.analytics import Analytics

st.set_page_config(
    page_title="Reveal Data - SecureStego",
    page_icon="🔓",
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
Path("uploads").mkdir(exist_ok=True)

st.markdown("""
<div class="stego-header">
    <h1>🔓 Reveal Hidden Data</h1>
    <p>Extract and decrypt secret data from stego images</p>
</div>
""", unsafe_allow_html=True)

# Main Layout
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 🖼️ Upload Stego Image")
    
    stego_image = st.file_uploader(
        "Choose stego image with hidden data",
        type=['png', 'bmp', 'tiff'],
        help="Upload the image containing hidden encrypted data",
        key="stego_image"
    )
    
    if stego_image:
        # Save uploaded image
        stego_path = Path("uploads") / stego_image.name
        with open(stego_path, "wb") as f:
            f.write(stego_image.getbuffer())
        
        # Display image
        st.image(stego_image, caption="Stego Image")
        
        # Image info
        from PIL import Image
        img = Image.open(stego_path)
        width, height = img.size
        
        info_col1, info_col2, info_col3 = st.columns(3)
        with info_col1:
            st.metric("Width", f"{width}px")
        with info_col2:
            st.metric("Height", f"{height}px")
        with info_col3:
            st.metric("Format", img.format)

with col2:
    st.markdown("### 🔑 Decryption Key")
    
    # Key selection
    km = KeyManager()
    keys = km.list_keys()
    
    if keys:
        key_option = st.radio(
            "Key Input Method",
            ["Use Saved Key", "Enter Key Manually"],
            horizontal=True
        )
        
        if key_option == "Use Saved Key":
            key_names = [k['name'] for k in keys]
            selected_key_name = st.selectbox("Choose Key", key_names)
            
            if selected_key_name:
                decryption_key, key_meta = km.load_key(selected_key_name)
                st.info(f"🔑 Selected: **{selected_key_name}**\n\nFingerprint: `{key_meta['fingerprint']}`")
        
        else:  # Manual entry
            key_input = st.text_input(
                "Enter Base64 Key",
                type="password",
                help="Paste the encryption key used to hide the data"
            )
            if key_input:
                try:
                    decryption_key = km.string_to_key(key_input)
                    fingerprint = km.get_key_fingerprint(decryption_key)
                    st.success(f"✅ Valid key | Fingerprint: `{fingerprint}`")
                except Exception as e:
                    st.error(f"❌ Invalid key format: {str(e)}")
                    st.stop()
    else:
        st.warning("⚠️ No saved keys found")
        key_input = st.text_input(
            "Enter Base64 Key",
            type="password",
            help="Paste the encryption key"
        )
        if key_input:
            try:
                decryption_key = km.string_to_key(key_input)
                st.success("✅ Key accepted")
            except Exception as e:
                st.error(f"❌ Invalid key: {str(e)}")
                st.stop()

st.markdown("---")

# Reveal Button
st.markdown("### 🔍 Extract & Decrypt")

col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])

with col_btn2:
    reveal_button = st.button(
        "🔓 Reveal Data",
        use_container_width=True,
        type="primary"
    )

if reveal_button:
    # Validation
    if not stego_image:
        st.error("❌ Please upload a stego image")
        st.stop()
    
    if 'decryption_key' not in locals():
        st.error("❌ Please provide decryption key")
        st.stop()
    
    # Progress
    progress_bar = st.progress(0, text="Starting extraction...")
    
    try:
        # Step 1: Extract
        progress_bar.progress(25, text="📤 Extracting hidden data from image...")
        
        encrypted_bundle = StegoEngine.reveal(str(stego_path))
        
        progress_bar.progress(50, text="🔓 Decrypting with AES-256-GCM...")
        
        # Step 2: Decrypt
        decrypted_data, metadata = quick_decrypt(decryption_key, encrypted_bundle)
        
        progress_bar.progress(75, text="✅ Decrypted! Verifying integrity...")
        
        # Step 3: Log analytics
        Analytics.log_operation('reveal', {
            'stego_image': stego_image.name,
            'data_size_bytes': len(decrypted_data),
            'data_size_kb': len(decrypted_data) / 1024
        })
        
        progress_bar.progress(100, text="✅ Complete!")
        
        # Success!
        st.success("🎉 **Successfully extracted and decrypted hidden data!**")
        
        # Show metadata
        st.markdown("#### 📋 Data Metadata")
        
        meta_col1, meta_col2, meta_col3 = st.columns(3)
        
        with meta_col1:
            st.metric("Data Size", f"{len(decrypted_data)} bytes")
        
        with meta_col2:
            encrypted_at = metadata.get('timestamp', 'Unknown')
            if encrypted_at != 'Unknown':
                encrypted_at = encrypted_at.split('T')[0]
            st.metric("Encrypted", encrypted_at)
        
        with meta_col3:
            original_size = metadata.get('size', len(decrypted_data))
            st.metric("Original Size", f"{original_size} bytes")
        
        st.markdown("---")
        
        # Display data
        st.markdown("#### 💾 Decrypted Data")
        
        # Try to decode as text
        try:
            decoded_text = decrypted_data.decode('utf-8')
            
            # Show as text
            st.text_area(
                "Decrypted Message",
                value=decoded_text,
                height=200,
                help="Copy this text or download below"
            )
            
            # Download as text
            st.download_button(
                label="📥 Download as Text",
                data=decoded_text,
                file_name=f"revealed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        except UnicodeDecodeError:
            # Binary data
            st.info("📦 **Binary data detected** (not text)")
            
            st.code(f"Size: {len(decrypted_data)} bytes\nFirst 100 bytes (hex):\n{decrypted_data[:100].hex()}")
            
            # Download as binary
            original_filename = metadata.get('filename', 'revealed_data.bin')
            
            st.download_button(
                label=f"📥 Download {original_filename}",
                data=decrypted_data,
                file_name=original_filename,
                use_container_width=True
            )
        
        # Security verification
        st.markdown("---")
        st.markdown("#### ✅ Security Verification")
        
        verify_col1, verify_col2 = st.columns(2)
        
        with verify_col1:
            st.success("""
            **✅ Authentication Tag Verified**
            
            Data integrity confirmed. No tampering detected.
            """)
        
        with verify_col2:
            key_hash = metadata.get('key_hash', 'Unknown')
            st.info(f"""
            **🔑 Key Verification**
            
            Key fingerprint: `{key_hash}`
            """)
        
    except ValueError as e:
        progress_bar.empty()
        st.error(f"❌ **Decryption Failed**\n\n{str(e)}")
        
        st.markdown("#### 🔍 Troubleshooting")
        st.warning("""
        **Possible causes:**
        
        1. **Wrong Key**: The key doesn't match the one used for encryption
        2. **Tampered Image**: The image has been modified (cropped, compressed, edited)
        3. **No Hidden Data**: This image doesn't contain hidden data
        4. **Corrupted File**: File corruption during transfer
        
        **What to do:**
        - Verify you have the correct encryption key
        - Ensure the image hasn't been modified
        - Try downloading the original stego image again
        """)
    
    except Exception as e:
        progress_bar.empty()
        st.error(f"❌ Unexpected error: {str(e)}")

# Sidebar info
with st.sidebar:
    st.markdown("### 💡 How It Works")
    st.markdown("""
    **Extraction Process:**
    1. Read LSBs from pixels
    2. Reconstruct byte stream
    3. Decode base64 bundle
    
    **Decryption Process:**
    4. Parse nonce + ciphertext + tag
    5. Verify authentication tag
    6. Decrypt with AES-256-GCM
    7. Return original data
    
    **Security:** Tag verification ensures data wasn't tampered with.
    """)
    
    st.markdown("---")
    
    st.markdown("### 🛡️ Security Notes")
    st.markdown("""
    - Authentication tag verifies integrity
    - Wrong key = decryption failure
    - Any image modification = failure
    - Zero tolerance for tampering
    """)
