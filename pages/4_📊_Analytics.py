"""
Analytics Page - View Usage Statistics
"""

import streamlit as st
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd

from utils.analytics import Analytics
from utils.key_manager import KeyManager

st.set_page_config(
    page_title="Analytics - SecureStego",
    page_icon="📊",
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
    <h1>📊 Analytics Dashboard</h1>
    <p>Usage statistics and insights</p>
</div>
""", unsafe_allow_html=True)

# Get statistics
stats = Analytics.get_statistics()
km = KeyManager()
keys = km.list_keys()

# Overview Metrics
st.markdown("### 📈 Overview")

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

with metric_col1:
    st.metric(
        "Total Operations",
        stats['total_operations'],
        help="Total hide + reveal operations"
    )

with metric_col2:
    st.metric(
        "Data Hidden",
        f"{stats['total_data_hidden_mb']:.2f} MB",
        help="Total data encrypted and hidden"
    )

with metric_col3:
    st.metric(
        "Active Keys",
        len(keys),
        help="Number of encryption keys"
    )

with metric_col4:
    st.metric(
        "Avg Payload",
        f"{stats['avg_payload_size_kb']:.1f} KB",
        help="Average payload size per operation"
    )

st.markdown("---")

# Operations Breakdown
if stats['total_operations'] > 0:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔐 Operations Breakdown")
        
        # Pie chart
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Hide Operations', 'Reveal Operations'],
            values=[stats['hide_operations'], stats['reveal_operations']],
            hole=0.4,
            marker=dict(colors=['#6366f1', '#8b5cf6'])
        )])
        
        fig_pie.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=300
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.markdown("### 📊 Operation Details")
        
        detail_data = pd.DataFrame({
            'Operation': ['Hide Data', 'Reveal Data'],
            'Count': [stats['hide_operations'], stats['reveal_operations']],
            'Percentage': [
                f"{(stats['hide_operations']/stats['total_operations']*100):.1f}%",
                f"{(stats['reveal_operations']/stats['total_operations']*100):.1f}%"
            ]
        })
        
        st.dataframe(detail_data, hide_index=True, use_container_width=True)
        
        st.markdown("---")
        
        st.metric("Hide Operations", stats['hide_operations'])
        st.metric("Reveal Operations", stats['reveal_operations'])

st.markdown("---")

# Recent Operations
st.markdown("### 🕒 Recent Operations")

if stats['recent_operations']:
    for op in stats['recent_operations'][:10]:
        timestamp = op['timestamp'].split('T')
        date = timestamp[0]
        time = timestamp[1].split('.')[0] if len(timestamp) > 1 else ''
        
        op_type = op['type']
        details = op['details']
        
        icon = "🔐" if op_type == "hide" else "🔓"
        
        with st.expander(f"{icon} {op_type.upper()} - {date} {time}"):
            cols = st.columns(4)
            
            if op_type == 'hide':
                with cols[0]:
                    st.metric("Cover Image", details.get('cover_image', 'Unknown'))
                with cols[1]:
                    st.metric("Payload", f"{details.get('payload_kb', 0):.2f} KB")
                with cols[2]:
                    st.metric("Capacity Used", f"{details.get('capacity_used', 0):.1f}%")
                with cols[3]:
                    st.metric("Output", details.get('output_file', 'Unknown')[:20] + "...")
            else:
                with cols[0]:
                    st.metric("Stego Image", details.get('stego_image', 'Unknown'))
                with cols[1]:
                    st.metric("Data Size", f"{details.get('data_size_kb', 0):.2f} KB")
                with cols[2]:
                    st.metric("Status", "✅ Success")
else:
    st.info("📭 No operations recorded yet. Start hiding or revealing data!")

st.markdown("---")

# Key Statistics
st.markdown("### 🔑 Key Statistics")

if keys:
    key_df = pd.DataFrame(keys)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Keys by Creation Date")
        
        # Parse dates
        key_dates = []
        for key in keys:
            created = key.get('created', '')
            if created and 'T' in created:
                date = created.split('T')[0]
                key_dates.append(date)
        
        if key_dates:
            date_counts = pd.Series(key_dates).value_counts().sort_index()
            
            fig_line = go.Figure(data=[go.Scatter(
                x=date_counts.index,
                y=date_counts.values,
                mode='lines+markers',
                line=dict(color='#6366f1', width=3),
                marker=dict(size=8)
            )])
            
            fig_line.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Date",
                yaxis_title="Keys Created",
                height=300
            )
            
            st.plotly_chart(fig_line, use_container_width=True)
    
    with col2:
        st.markdown("#### All Keys")
        
        display_keys = []
        for key in keys:
            display_keys.append({
                'Name': key['name'],
                'Fingerprint': key['fingerprint'][:12] + "...",
                'Algorithm': key['algorithm']
            })
        
        st.dataframe(display_keys, hide_index=True, use_container_width=True)

else:
    st.info("📭 No keys found. Generate your first key to start!")

# Sidebar
with st.sidebar:
    st.markdown("### 🎯 Quick Actions")
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
    
    if st.button("🗑️ Clear Analytics", use_container_width=True):
        if st.session_state.get('confirm_clear'):
            Analytics.ANALYTICS_FILE.unlink(missing_ok=True)
            st.success("Analytics cleared!")
            st.rerun()
        else:
            st.session_state['confirm_clear'] = True
            st.warning("Click again to confirm")
    
    st.markdown("---")
    
    st.markdown("### 📈 Insights")
    
    if stats['total_operations'] > 0:
        ratio = stats['hide_operations'] / stats['reveal_operations'] if stats['reveal_operations'] > 0 else 0
        
        if ratio > 1.5:
            st.info("💡 You're hiding more than revealing. Good for security!")
        elif ratio < 0.5:
            st.info("💡 You're revealing more than hiding. Extracting old data?")
        else:
            st.success("✅ Balanced hide/reveal ratio")
    
    st.markdown("---")
    
    st.markdown("### 🔍 Data Quality")
    
    if stats['avg_payload_size_kb'] > 0:
        if stats['avg_payload_size_kb'] < 10:
            st.info("📝 Small payloads (text messages)")
        elif stats['avg_payload_size_kb'] < 100:
            st.info("📄 Medium payloads (documents)")
        else:
            st.info("📦 Large payloads (files)")
