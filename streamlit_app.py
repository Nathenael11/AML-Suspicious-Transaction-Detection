"""
AML Suspicious Transaction Detection - Web Interface
A production-ready transaction monitoring tool for detecting potential money laundering patterns.

Author: Nathenael Ermias
Project:AML Detection System
"""

import streamlit as st
import pickle
import numpy as np
import pandas as pd
import sys
import os
from datetime import datetime

# Add the app directory to Python path for module imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# ============================================================================
# MODEL LOADING
# ============================================================================

@st.cache_resource
def load_aml_model():
    """
    Load the trained XGBoost model and feature list.
    Falls back to a demonstration mode if model files are missing.
    """
    try:
        with open('models/model.pkl', 'rb') as f:
            model = pickle.load(f)
        with open('models/feature_names.pkl', 'rb') as f:
            features = pickle.load(f)
        return model, features
    except Exception as e:
        st.warning(f"⚠️ Running in demonstration mode. Error: {e}")
        return None, None

# ============================================================================
# FEATURE ENGINEERING
# ============================================================================

def prepare_features(raw_transaction, feature_names):
    """
    Convert raw transaction input into the 56 features expected by the model.
    For single transaction analysis, graph features use default values since
    we don't have historical transaction data.
    """
    features = {}
    
    # --- Core Transaction Features ---
    amount_paid = float(raw_transaction.get('amount_paid', 0))
    amount_received = float(raw_transaction.get('amount_received', 0))
    
    # Log transformations help the model handle large value ranges
    features['log_amount_paid'] = np.log1p(max(amount_paid, 0))
    features['log_amount_received'] = np.log1p(max(amount_received, 0))
    features['amount_discrepancy'] = amount_paid - amount_received
    
    # --- Indicator Flags ---
    # Currency mismatch is a classic money laundering red flag
    features['currency_mismatch'] = 1 if raw_transaction.get('payment_currency') != raw_transaction.get('receiving_currency') else 0
    
    # Cross-bank transfers are generally safer than same-bank transfers
    features['cross_bank'] = 1 if raw_transaction.get('from_bank') != raw_transaction.get('to_bank') else 0
    
    # Self-loop (same sender and receiver account) - highly suspicious
    features['self_loop'] = 1 if raw_transaction.get('from_account') == raw_transaction.get('to_account') else 0
    
    # --- Temporal Features ---
    # Time-based patterns: criminals often work at unusual hours
    hour = int(raw_transaction.get('hour_of_day', 12))
    day = int(raw_transaction.get('day_of_week', 3))
    
    features['hour_of_day'] = hour
    features['day_of_week'] = day
    features['is_weekend'] = 1 if day in [5, 6] else 0
    
    # --- Payment Format One-Hot Encoding ---
    # Different payment methods carry different risk profiles
    payment_format = raw_transaction.get('payment_format', 'Unknown')
    format_options = ['Credit Card', 'Debit Card', 'ACH', 'Wire Transfer', 'Cheque', 'Reinvestment']
    for fmt in format_options:
        features[f'fmt_{fmt}'] = 1 if payment_format == fmt else 0
    
    # --- Currency One-Hot Encoding ---
    currency = raw_transaction.get('payment_currency', 'US Dollar')
    currency_options = ['US Dollar', 'Euro', 'GBP', 'Canadian Dollar', 'Australian Dollar', 'OTHER']
    for cur in currency_options:
        features[f'cur_{cur}'] = 1 if currency == cur else 0
    
    # --- Graph Features (Default Values) ---
    # For single transactions, we use average values from the training data
    # This is a limitation of single-transaction analysis
    graph_defaults = {
        'src_out_degree': 10.0,
        'src_in_degree': 8.0,
        'dst_out_degree': 10.0,
        'dst_in_degree': 8.0,
        'src_fan_out_unique': 5.0,
        'src_fan_in_unique': 4.0,
        'dst_fan_out_unique': 5.0,
        'dst_fan_in_unique': 4.0,
        'src_in_cycle': 0.0,
        'dst_in_cycle': 0.0,
        'src_is_fan_out_hub': 0.0,
        'src_is_fan_in_hub': 0.0,
        'dst_is_fan_out_hub': 0.0,
        'dst_is_fan_in_hub': 0.0,
        'src_velocity_count_24h': 5.0,
        'src_velocity_amount_24h': 1000.0,
        'amount_zscore_vs_src_history': 0.0,
        'src_in_out_ratio': 0.8,
        'dst_in_out_ratio': 0.8,
        'src_total_degree': 18.0,
        'dst_total_degree': 18.0,
    }
    
    for key, value in graph_defaults.items():
        features[key] = value
    
    # --- Ensure Correct Feature Order ---
    # The model expects features in a specific order
    result = {}
    for name in feature_names:
        result[name] = features.get(name, 0)
    
    return pd.DataFrame([result])

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="AML Shield - Transaction Detection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# CUSTOM STYLES
# ============================================================================

st.markdown("""
<style>
    /* Main Header */
    .main-header {
        background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3e 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #00cc44;
        margin-bottom: 2rem;
    }
    
    /* Risk Indicators */
    .risk-high { 
        color: #ff4444; 
        font-weight: 700; 
        font-size: 1.5rem; 
        padding: 0.5rem 1rem;
        background: rgba(255, 68, 68, 0.1);
        border-radius: 8px;
        border-left: 4px solid #ff4444;
    }
    .risk-low { 
        color: #00cc44; 
        font-weight: 700; 
        font-size: 1.5rem; 
        padding: 0.5rem 1rem;
        background: rgba(0, 204, 68, 0.1);
        border-radius: 8px;
        border-left: 4px solid #00cc44;
    }
    .risk-medium {
        color: #ffaa00;
        font-weight: 700;
        font-size: 1.5rem;
        padding: 0.5rem 1rem;
        background: rgba(255, 170, 0, 0.1);
        border-radius: 8px;
        border-left: 4px solid #ffaa00;
    }
    
    /* Metric Cards */
    .metric-card {
        background: #1e1e2f;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #2a2a3e;
        text-align: center;
    }
    
    .stButton button {
        background: #00cc44;
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 8px;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background: #00b33a;
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0, 204, 68, 0.3);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem 0 1rem 0;
        color: #666;
        border-top: 1px solid #1e1e2f;
        margin-top: 2rem;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER
# ============================================================================

st.markdown("""
<div class="main-header">
    <h1 style="color: #fff; margin: 0; font-weight: 700;">
        🛡️ AML Shield
    </h1>
    <p style="color: #88aacc; margin: 0.5rem 0 0 0;">
        Suspicious Transaction Detection System
    </p>
    <p style="color: #556677; margin: 0.25rem 0 0 0; font-size: 0.85rem;">
        XGBoost Model • 56 Features • Threshold: 0.50
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# LOAD MODEL
# ============================================================================

model, feature_names = load_aml_model()

if model:
    st.success(f"✅ Model loaded successfully | {len(feature_names)} features active")
else:
    st.info("ℹ️ Running in demonstration mode with mock predictions")

# ============================================================================
# APPLICATION TABS
# ============================================================================

tab_single, tab_batch = st.tabs([
    "📊 Single Transaction Analysis",
    "📁 Batch Upload (CSV)"
])

# ============================================================================
# TAB 1: SINGLE TRANSACTION ANALYSIS
# ============================================================================

with tab_single:
    st.markdown("### Enter Transaction Details")
    st.markdown("Fill in the fields below to analyze a single transaction.")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("**Payment Information**")
        
        amount_paid = st.number_input(
            "Amount Paid ($)",
            min_value=0.0,
            value=100.0,
            step=1.0,
            help="The amount being sent in the transaction"
        )
        
        amount_received = st.number_input(
            "Amount Received ($)",
            min_value=0.0,
            value=100.0,
            step=1.0,
            help="The amount being received (may differ due to currency conversion)"
        )
        
        payment_currency = st.selectbox(
            "Payment Currency",
            ["US Dollar", "Euro", "GBP", "Canadian Dollar", "Australian Dollar", "OTHER"],
            help="The currency being used for payment"
        )
        
        receiving_currency = st.selectbox(
            "Receiving Currency",
            ["US Dollar", "Euro", "GBP", "Canadian Dollar", "Australian Dollar", "OTHER"],
            help="The currency being received"
        )
    
    with col_right:
        st.markdown("**Account Information**")
        
        from_bank = st.text_input(
            "From Bank",
            value="001",
            help="Sender's bank identifier"
        )
        
        to_bank = st.text_input(
            "To Bank",
            value="002",
            help="Recipient's bank identifier"
        )
        
        from_account = st.text_input(
            "From Account",
            value="8000F4580",
            help="Sender's account number"
        )
        
        to_account = st.text_input(
            "To Account",
            value="8000F5340",
            help="Recipient's account number"
        )
        
        payment_format = st.selectbox(
            "Payment Format",
            ["Credit Card", "Debit Card", "ACH", "Wire Transfer", "Cheque", "Reinvestment"],
            help="The method of payment"
        )
        
        col_time1, col_time2 = st.columns(2)
        with col_time1:
            hour_of_day = st.slider(
                "Hour of Day",
                min_value=0,
                max_value=23,
                value=14,
                help="24-hour format (0 = midnight, 14 = 2 PM)"
            )
        with col_time2:
            day_of_week = st.slider(
                "Day of Week (Mon=0)",
                min_value=0,
                max_value=6,
                value=3,
                help="0 = Monday, 6 = Sunday"
            )
    
    # --- Analyze Button ---
    st.markdown("---")
    if st.button("🔍 Analyze Transaction", type="primary"):
        with st.spinner("Analyzing transaction patterns..."):
            
            # Prepare input data
            transaction_data = {
                'amount_paid': amount_paid,
                'amount_received': amount_received,
                'payment_currency': payment_currency,
                'receiving_currency': receiving_currency,
                'from_bank': from_bank,
                'to_bank': to_bank,
                'from_account': from_account,
                'to_account': to_account,
                'payment_format': payment_format,
                'hour_of_day': hour_of_day,
                'day_of_week': day_of_week
            }
            
            # Get prediction
            if model and feature_names:
                try:
                    feature_vector = prepare_features(transaction_data, feature_names)
                    risk_score = model.predict_proba(feature_vector)[0][1]
                    risk_score = max(0.0, min(1.0, risk_score))
                except Exception as e:
                    risk_score = 0.5
                    st.warning(f"⚠️ Prediction error: {e}")
            else:
                # Demo mode
                risk_score = 0.85 if amount_paid > 5000 else 0.05
            
            # --- Display Results ---
            st.markdown("---")
            st.markdown("### 📊 Analysis Results")
            
            col_result1, col_result2, col_result3 = st.columns(3)
            
            with col_result1:
                st.markdown("""
                <div class="metric-card">
                    <p style="color: #88aacc; margin: 0; font-size: 0.85rem;">Risk Score</p>
                    <p style="font-size: 2rem; margin: 0.5rem 0; font-weight: 700;">{:.4f}</p>
                </div>
                """.format(risk_score), unsafe_allow_html=True)
            
            with col_result2:
                if risk_score >= 0.50:
                    st.markdown('<p class="risk-high">🚨 SUSPICIOUS</p>', unsafe_allow_html=True)
                else:
                    st.markdown('<p class="risk-low">✅ NORMAL</p>', unsafe_allow_html=True)
            
            with col_result3:
                if risk_score >= 0.50:
                    st.warning("⚠️ HIGH RISK - Immediate review required")
                else:
                    st.success("✅ LOW RISK - No action required")
            
            # Recommendation
            st.info(
                "📌 **Recommended Action:** " +
                ("Immediate investigation required. Transaction matches patterns associated with money laundering."
                 if risk_score >= 0.50 else
                 "Transaction appears normal. No further action required at this time.")
            )

# ============================================================================
# TAB 2: BATCH UPLOAD
# ============================================================================

with tab_batch:
    st.markdown("### Batch Transaction Analysis")
    st.markdown("Upload a CSV file containing multiple transactions for bulk analysis.")
    
    st.info("""
    **CSV Format Requirements:**
    - Required columns: `amount_paid`, `amount_received`, `payment_currency`, `receiving_currency`, 
      `from_bank`, `to_bank`, `from_account`, `to_account`, `payment_format`, `hour_of_day`, `day_of_week`
    - First row must contain column headers
    """)
    
    # --- Sample CSV Download ---
    sample_data = """amount_paid,amount_received,payment_currency,receiving_currency,from_bank,to_bank,from_account,to_account,payment_format,hour_of_day,day_of_week
45.50,45.50,US Dollar,US Dollar,001,002,8000F4580,8000F5340,Credit Card,14,3
9999.99,9999.99,US Dollar,Euro,010,010,8000EBD30,8000EBD30,Reinvestment,3,6
150.00,150.00,US Dollar,US Dollar,001,002,8000F4580,8000F5340,ACH,10,2"""
    
    st.download_button(
        label="📥 Download Sample CSV Template",
        data=sample_data,
        file_name="sample_transactions.csv",
        mime="text/csv",
        help="Download a sample CSV file with the correct format"
    )
    
    st.markdown("---")
    
    # --- File Upload ---
    uploaded_file = st.file_uploader(
        "Choose CSV file",
        type=['csv'],
        help="Upload a CSV file with transaction data"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ Successfully loaded {len(df)} transactions")
            
            # Preview
            with st.expander("Preview First 5 Transactions"):
                st.dataframe(df.head(5), use_container_width=True)
            
            # --- Process Batch ---
            if st.button("🚀 Process Batch", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                results = []
                total = len(df)
                
                for idx, row in df.iterrows():
                    status_text.text(f"Processing transaction {idx + 1} of {total}...")
                    
                    transaction_data = row.to_dict()
                    
                    if model and feature_names:
                        try:
                            feature_vector = prepare_features(transaction_data, feature_names)
                            risk_score = model.predict_proba(feature_vector)[0][1]
                            risk_score = max(0.0, min(1.0, risk_score))
                        except:
                            risk_score = 0.5
                    else:
                        # Demo mode
                        risk_score = 0.85 if float(row.get('amount_paid', 0)) > 5000 else 0.05
                    
                    results.append({
                        'risk_score': round(risk_score, 4),
                        'prediction': 'SUSPICIOUS' if risk_score >= 0.50 else 'NORMAL',
                        'alert_level': 'HIGH' if risk_score >= 0.50 else ('MEDIUM' if risk_score >= 0.30 else 'LOW')
                    })
                    
                    progress_bar.progress((idx + 1) / total)
                
                status_text.text("✅ Batch processing complete!")
                
                # --- Display Results ---
                st.markdown("---")
                st.markdown("### 📊 Batch Results")
                
                result_df = pd.DataFrame(results)
                
                # Summary metrics
                col_sum1, col_sum2, col_sum3 = st.columns(3)
                with col_sum1:
                    st.metric("📊 Total Processed", len(result_df))
                with col_sum2:
                    suspicious_count = len(result_df[result_df['prediction'] == 'SUSPICIOUS'])
                    st.metric("🚨 Suspicious Found", suspicious_count)
                with col_sum3:
                    avg_score = result_df['risk_score'].mean()
                    st.metric("📈 Average Risk Score", f"{avg_score:.3f}")
                
                st.dataframe(result_df, use_container_width=True)
                
                # Download results
                csv_result = result_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Results",
                    data=csv_result,
                    file_name=f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
        except Exception as e:
            st.error(f"❌ Error processing file: {e}")
            st.info("Please ensure your CSV file has the correct format.")


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("""
<div class="footer">
    🛡️ AML Shield by Nathenael © 2026 &nbsp;|&nbsp; 
    XGBoost v2.0 &nbsp;|&nbsp;
   
</div>
""", unsafe_allow_html=True)