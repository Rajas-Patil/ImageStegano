"""
Key Manager Page - Manage Encryption Keys
"""

import streamlit as st
from pathlib import Path
from datetime import datetime
import io

from utils.key_manager import KeyManager

st.set_page_config(
    page_title="Key Manager - SecureStego",
    page_icon="🔑",
    layout="wide"
)

# Load CSS
def load_css():
    css_file = Path("styles/main.css")
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

st.markdown("""
<div class="stego-header">
    <h1>🔑 Key Manager</h1>
    <p>Manage your encryption keys securely</p>
</div>
""", unsafe_allow_html=True)

# Initialize
km = KeyManager()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📋 All Keys", "➕ Generate New", "📥 Import", "📤 Export"])

# Tab 1: All Keys
with tab1:
    st.markdown("### 🔑 Your Encryption Keys")
    
    keys = km.list_keys()
    
    if not keys:
        st.info("📭 No keys found. Generate your first key in the 'Generate New' tab.")
    else:
        st.success(f"✅ **{len(keys)} keys** stored securely")
        
        # Display keys as cards
        for i, key in enumerate(keys):
            with st.expander(f"🔑 {key['name']}", expanded=(i == 0)):
                key_col1, key_col2 = st.columns([2, 1])
                
                with key_col1:
                    st.markdown(f"""
                    **Name:** {key['name']}  
                    **Fingerprint:** `{key['fingerprint']}`  
                    **Algorithm:** {key['algorithm']}  
                    **Created:** {key['created'].split('T')[0] if 'T' in key['created'] else key['created']}  
                    **Description:** {key.get('description', 'No description')}
                    """)
                
                with key_col2:
                    # Actions
                    if st.button("🔍 View Key", key=f"view_{i}"):
                        key_bytes, meta = km.load_key(key['name'])
                        key_str = km.key_to_string(key_bytes)
                        st.code(key_str, language=None)
                        st.caption("⚠️ Keep this key secret! Anyone with this key can decrypt your data.")
                    
                    if st.button("📤 Export", key=f"export_{i}"):
                        try:
                            export_path = Path("keys") / f"export_{key['name']}.json"
                            km.export_key(key['name'], str(export_path))
                            
                            with open(export_path, 'r') as f:
                                export_data = f.read()
                            
                            st.download_button(
                                label="Download Key File",
                                data=export_data,
                                file_name=f"{key['name']}.key.json",
                                mime="application/json",
                                key=f"download_{i}"
                            )
                            
                            # Clean up
                            export_path.unlink()
                        except Exception as e:
                            st.error(f"Export failed: {str(e)}")
                    
                    if st.button("🗑️ Delete", key=f"delete_{i}", type="secondary"):
                        if st.session_state.get(f'confirm_delete_{i}'):
                            if km.delete_key(key['name']):
                                st.success(f"Deleted {key['name']}")
                                st.rerun()
                            else:
                                st.error("Delete failed")
                        else:
                            st.session_state[f'confirm_delete_{i}'] = True
                            st.warning("Click again to confirm deletion")

# Tab 2: Generate New Key
with tab2:
    st.markdown("### ➕ Generate New Encryption Key")
    
    st.info("""
    **🔐 Secure Key Generation**
    
    Keys are generated using Python's `secrets.token_bytes()` which provides:
    - Cryptographically secure random numbers
    - 256-bit (32-byte) key size for AES-256
    - Suitable for production use
    """)
    
    with st.form("generate_key_form"):
        key_name = st.text_input(
            "Key Name *",
            placeholder="e.g., Project_Alpha, Personal_2025",
            help="Descriptive name to identify this key"
        )
        
        key_description = st.text_area(
            "Description (Optional)",
            placeholder="e.g., Key for confidential project documents",
            height=100
        )
        
        submit_generate = st.form_submit_button("🎲 Generate Key", use_container_width=True, type="primary")
        
        if submit_generate:
            if not key_name:
                st.error("❌ Please provide a key name")
            else:
                try:
                    # Generate key
                    new_key = km.generate_key()
                    fingerprint = km.get_key_fingerprint(new_key)
                    
                    # Save
                    filepath = km.save_key(new_key, key_name, key_description)
                    
                    # Success
                    st.success(f"✅ **Key generated successfully!**")
                    
                    st.markdown(f"""
                    **Name:** {key_name}  
                    **Fingerprint:** `{fingerprint}`  
                    **File:** {filepath.name}
                    """)
                    
                    # Show key (with warning)
                    with st.expander("🔍 View Generated Key (Click to expand)"):
                        key_str = km.key_to_string(new_key)
                        st.code(key_str, language=None)
                        st.error("⚠️ **IMPORTANT:** Save this key in a secure location. You'll need it to decrypt your data!")
                    
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Generation failed: {str(e)}")

# Tab 3: Import Key
with tab3:
    st.markdown("### 📥 Import Encryption Key")
    
    st.info("""
    **Import Options:**
    1. Upload a `.key.json` file exported from SecureStego
    2. Paste a base64 key string manually
    """)
    
    import_method = st.radio(
        "Import Method",
        ["Upload Key File", "Paste Key String"],
        horizontal=True
    )
    
    if import_method == "Upload Key File":
        uploaded_key_file = st.file_uploader(
            "Choose key file (.key.json)",
            type=['json'],
            help="Upload exported key file"
        )
        
        if uploaded_key_file:
            try:
                # Save temporarily
                temp_path = Path("keys") / "temp_import.json"
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_key_file.getbuffer())
                
                # Import
                key_name = km.import_key(str(temp_path))
                
                # Clean up
                temp_path.unlink()
                
                st.success(f"✅ **Successfully imported key:** {key_name}")
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Import failed: {str(e)}")
    
    else:  # Paste Key String
        with st.form("import_key_form"):
            new_key_name = st.text_input(
                "Key Name",
                placeholder="Name for this imported key"
            )
            
            key_string_input = st.text_area(
                "Base64 Key String",
                placeholder="Paste your base64-encoded key here",
                height=100,
                help="The key should be 44 characters long (256-bit base64)"
            )
            
            import_desc = st.text_input(
                "Description (Optional)",
                placeholder="e.g., Imported from backup"
            )
            
            submit_import = st.form_submit_button("📥 Import Key", use_container_width=True)
            
            if submit_import:
                if not new_key_name or not key_string_input:
                    st.error("❌ Please provide both name and key string")
                else:
                    try:
                        # Validate and convert
                        key_bytes = km.string_to_key(key_string_input.strip())
                        fingerprint = km.get_key_fingerprint(key_bytes)
                        
                        # Save
                        filepath = km.save_key(key_bytes, new_key_name, import_desc)
                        
                        st.success(f"✅ **Key imported successfully!**")
                        st.markdown(f"""
                        **Name:** {new_key_name}  
                        **Fingerprint:** `{fingerprint}`  
                        **File:** {filepath.name}
                        """)
                        
                    except Exception as e:
                        st.error(f"❌ Invalid key: {str(e)}")

# Tab 4: Export Keys
with tab4:
    st.markdown("### 📤 Export Encryption Keys")
    
    st.warning("""
    **⚠️ Security Warning**
    
    Exported keys contain sensitive cryptographic material. Handle with care:
    - Store in encrypted storage (password manager, encrypted drive)
    - Never share over insecure channels
    - Keep backups in multiple secure locations
    """)
    
    keys = km.list_keys()
    
    if not keys:
        st.info("No keys available to export")
    else:
        export_key_name = st.selectbox(
            "Select Key to Export",
            [k['name'] for k in keys]
        )
        
        if export_key_name:
            key_bytes, meta = km.load_key(export_key_name)
            
            col_exp1, col_exp2 = st.columns(2)
            
            with col_exp1:
                st.markdown("#### 📄 Export as File")
                
                import json
                export_data = {
                    'key': km.key_to_string(key_bytes),
                    'metadata': meta
                }
                
                export_json = json.dumps(export_data, indent=2)
                
                st.download_button(
                    label="📥 Download Key File",
                    data=export_json,
                    file_name=f"{export_key_name}.key.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col_exp2:
                st.markdown("#### 📋 Copy Key String")
                
                key_str = km.key_to_string(key_bytes)
                st.code(key_str, language=None)
                
                st.caption(f"Fingerprint: `{meta['fingerprint']}`")

# Sidebar
with st.sidebar:
    st.markdown("### 📊 Key Statistics")
    
    keys = km.list_keys()
    st.metric("Total Keys", len(keys))
    
    if keys:
        # Count by algorithm
        algorithms = {}
        for key in keys:
            algo = key.get('algorithm', 'Unknown')
            algorithms[algo] = algorithms.get(algo, 0) + 1
        
        st.markdown("**By Algorithm:**")
        for algo, count in algorithms.items():
            st.markdown(f"- {algo}: {count}")
    
    st.markdown("---")
    
    st.markdown("### 🛡️ Best Practices")
    st.markdown("""
    1. **Unique keys** for each project
    2. **Regular backups** in secure storage
    3. **Never share** keys over email/chat
    4. **Rotate keys** periodically
    5. **Delete unused** keys promptly
    """)
