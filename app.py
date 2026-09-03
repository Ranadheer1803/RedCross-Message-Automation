import streamlit as st
import pandas as pd
import datetime
import os
import io

# Custom imports
from excel_handler import normalize_columns, generate_sample_datasheet
from whatsapp_engine import generate_whatsapp_web_url, generate_wa_me_link, dispatch_pywhatkit_message, dispatch_twilio_whatsapp
from campaigns import (
    SPECIAL_EVENTS, DEFAULT_BIRTHDAY_MESSAGE, DEFAULT_EMERGENCY_MESSAGE,
    get_today_birthdays, get_upcoming_birthdays, format_message
)

# Set Streamlit page config
st.set_page_config(
    page_title="Red Cross Message Automation Dashboard",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich aesthetics
st.markdown("""
<style>
    /* Dark glassmorphic theme styling */
    .stApp {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F172A 100%);
        color: #F8FAFC;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Header Card */
    .header-card {
        background: rgba(225, 29, 72, 0.12);
        border: 1px solid rgba(225, 29, 72, 0.3);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px 0 rgba(225, 29, 72, 0.1);
        display: flex;
        align-items: center;
        gap: 20px;
    }
    
    .header-title {
        font-size: 28px;
        font-weight: 800;
        color: #FFFFFF;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .header-subtitle {
        color: #94A3B8;
        font-size: 14px;
        margin-top: 4px;
    }
    
    /* Metric Cards */
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px 22px;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(225, 29, 72, 0.4);
    }
    
    .metric-label {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        color: #94A3B8;
        letter-spacing: 0.5px;
    }
    
    .metric-val {
        font-size: 32px;
        font-weight: 800;
        color: #F8FAFC;
        margin-top: 4px;
    }

    .blood-badge {
        background: #E11D48;
        color: white;
        padding: 4px 10px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 14px;
        display: inline-block;
    }
    
    .wa-button {
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
        color: white !important;
        padding: 8px 16px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
        font-size: 13px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        box-shadow: 0 4px 12px rgba(37, 211, 102, 0.3);
        transition: all 0.2s ease;
    }
    .wa-button:hover {
        transform: scale(1.03);
        box-shadow: 0 6px 16px rgba(37, 211, 102, 0.4);
    }

    /* Tabs override */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: rgba(15, 23, 42, 0.6);
        padding: 8px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #94A3B8;
        font-weight: 600;
        padding: 10px 20px;
    }

    .stTabs [aria-selected="true"] {
        background-color: #E11D48 !important;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'df' not in st.session_state:
    # Generate sample Excel if none exists
    sample_file = "sample_donors.xlsx"
    if not os.path.exists(sample_file):
        generate_sample_datasheet(sample_file)
    sample_df = pd.read_excel(sample_file)
    st.session_state['df'] = normalize_columns(sample_df)

if 'dispatch_logs' not in st.session_state:
    st.session_state['dispatch_logs'] = []

# Header Section
st.markdown("""
<div class="header-card">
    <div style="font-size: 42px;">🩸</div>
    <div>
        <div class="header-title">Red Cross Message Automation</div>
        <div class="header-subtitle">Smart Blood Donor Emergency Dispatcher & Campaign Automation Platform</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/red-cross.png", width=64)
    st.header("📋 Datasheet Controls")
    
    uploaded_file = st.file_uploader("Upload Donor Excel / CSV", type=["xlsx", "xls", "csv"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                raw_df = pd.read_csv(uploaded_file)
            else:
                raw_df = pd.read_excel(uploaded_file)
            st.session_state['df'] = normalize_columns(raw_df)
            st.success(f"Loaded {len(st.session_state['df'])} records from {uploaded_file.name}")
        except Exception as e:
            st.error(f"Error reading file: {e}")
            
    st.divider()
    
    # Download sample datasheet button
    st.subheader("💡 Need a Test File?")
    sample_path = "sample_donors.xlsx"
    if not os.path.exists(sample_path):
        generate_sample_datasheet(sample_path)
    with open(sample_path, "rb") as f:
        st.download_button(
            label="📥 Download Sample Excel Datasheet",
            data=f,
            file_name="RedCross_Sample_Donors.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    st.divider()
    st.subheader("⚙️ Dispatch Method")
    dispatch_mode = st.radio(
        "Select Messaging Engine",
        ["Direct WhatsApp Web Link (1-Click)", "Automated Browser (PyWhatKit)", "Twilio WhatsApp API"],
        index=0
    )
    
    if dispatch_mode == "Twilio WhatsApp API":
        twilio_sid = st.text_input("Twilio Account SID", type="password")
        twilio_token = st.text_input("Twilio Auth Token", type="password")
        twilio_from = st.text_input("Twilio From Number (e.g. +14155238886)")
    else:
        twilio_sid, twilio_token, twilio_from = None, None, None

# Current dataset reference
df = st.session_state['df']

# Top Metrics Row
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Donors</div>
        <div class="metric-val">{len(df)}</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    eligible_count = len(df[df['is_eligible'] == True]) if 'is_eligible' in df.columns else 0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Eligible Donors (≥90 days)</div>
        <div class="metric-val" style="color: #4ADE80;">{eligible_count}</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    bday_df = get_today_birthdays(df)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Birthdays Today</div>
        <div class="metric-val" style="color: #FACC15;">{len(bday_df)}</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    unique_bg = len(df['blood_group'].unique()) if 'blood_group' in df.columns else 0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Blood Group Varieties</div>
        <div class="metric-val" style="color: #F43F5E;">{unique_bg}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Navigation Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Donor Registry", 
    "🚨 Emergency Request", 
    "🎂 Birthdays & Campaigns", 
    "📜 Activity Logs"
])

# ==================== TAB 1: DONOR REGISTRY ====================
with tab1:
    st.subheader("📋 Donor Registry Datasheet")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        search_query = st.text_input("🔍 Search Donor Name or Phone")
    with col_f2:
        bg_options = ["ALL"] + sorted(list(df['blood_group'].dropna().unique()))
        selected_bg = st.selectbox("🩸 Filter by Blood Group", bg_options)
    with col_f3:
        eligibility_filter = st.selectbox("⏳ Filter Eligibility", ["All Donors", "Eligible Only (≥ 90 Days)", "Recently Donated (< 90 Days)"])
        
    filtered_df = df.copy()
    if search_query:
        filtered_df = filtered_df[
            filtered_df['name'].astype(str).str.contains(search_query, case=False, na=False) |
            filtered_df['phone'].astype(str).str.contains(search_query, case=False, na=False)
        ]
    if selected_bg != "ALL":
        filtered_df = filtered_df[filtered_df['blood_group'] == selected_bg]
    if eligibility_filter == "Eligible Only (≥ 90 Days)":
        filtered_df = filtered_df[filtered_df['is_eligible'] == True]
    elif eligibility_filter == "Recently Donated (< 90 Days)":
        filtered_df = filtered_df[filtered_df['is_eligible'] == False]
        
    st.write(f"Showing **{len(filtered_df)}** matching donor records:")
    
    # Display table columns clean view
    display_cols = ['name', 'phone', 'blood_group', 'dob', 'last_donation', 'location', 'is_eligible']
    display_cols = [c for c in display_cols if c in filtered_df.columns]
    
    st.dataframe(filtered_df[display_cols], use_container_width=True)
    
    # Add new donor record manually
    with st.expander("➕ Add New Donor Record"):
        with st.form("new_donor_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                n_name = st.text_input("Full Name")
                n_phone = st.text_input("Mobile Number")
            with c2:
                n_bg = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
                n_loc = st.text_input("Location / City")
            with c3:
                n_dob = st.date_input("Date of Birth", value=datetime.date(2000, 1, 1))
                n_last = st.date_input("Last Donation Date", value=datetime.date.today() - datetime.timedelta(days=100))
                
            submitted = st.form_submit_button("Save Donor Record")
            if submitted and n_name and n_phone:
                new_row = pd.DataFrame([{
                    'name': n_name,
                    'phone': n_phone,
                    'blood_group': n_bg,
                    'dob': n_dob.strftime("%Y-%m-%d"),
                    'last_donation': n_last.strftime("%Y-%m-%d"),
                    'location': n_loc
                }])
                norm_new_row = normalize_columns(new_row)
                st.session_state['df'] = pd.concat([st.session_state['df'], norm_new_row], ignore_index=True)
                st.success(f"Added new donor: {n_name}")
                st.rerun()

# ==================== TAB 2: EMERGENCY REQUEST ====================
with tab2:
    st.subheader("🚨 Emergency Blood Dispatcher")
    st.info("Select the required blood group. The system will match donors from the datasheet and prepare WhatsApp notifications.")
    
    col_e1, col_e2 = st.columns([1, 2])
    
    with col_e1:
        req_bg = st.selectbox("🎯 Required Blood Group", ["O- (Universal)", "O+", "A+", "A-", "B+", "B-", "AB+", "AB-"])
        clean_req_bg = req_bg.split(" ")[0]
        
        urgency_level = st.select_slider("🔥 Urgency Level", options=["NORMAL", "HIGH", "CRITICAL"])
        hospital_name = st.text_input("🏥 Hospital / Location Name", value="Apollo Hospital, Hyderabad")
        contact_person = st.text_input("📞 Emergency Contact Person", value="Red Cross Helpline (9876543210)")
        
        only_eligible = st.checkbox("Only include eligible donors (≥90 days since last donation)", value=True)
        
        # Filter matching donors
        match_df = df[df['blood_group'] == clean_req_bg].copy()
        if only_eligible:
            match_df = match_df[match_df['is_eligible'] == True]
            
        st.markdown(f"**Found <span style='color:#F43F5E; font-size:20px;'>{len(match_df)}</span> matching donors for {clean_req_bg}**", unsafe_allow_html=True)

    with col_e2:
        st.markdown("##### 📝 Message Template Editor")
        msg_template = st.text_area(
            "Customize WhatsApp Emergency Message",
            value=DEFAULT_EMERGENCY_MESSAGE,
            height=200
        )
        
        # Preview formatted message with sample donor
        if not match_df.empty:
            sample_donor = match_df.iloc[0].to_dict()
            sample_preview = format_message(
                msg_template, 
                sample_donor, 
                extra_tags={'hospital': hospital_name, 'urgency': urgency_level, 'contact_person': contact_person}
            )
            with st.expander("👁️ Live Message Preview (Sample Donor)"):
                st.code(sample_preview, language="text")
                
    st.divider()
    st.subheader("📤 Target Donors & Dispatch")
    
    if match_df.empty:
        st.warning(f"No matching donors found for blood group {clean_req_bg}.")
    else:
        # Action controls
        col_act1, col_act2 = st.columns([2, 1])
        
        with col_act1:
            st.write(f"Matching donors list ({len(match_df)} donors):")
            
        with col_act2:
            if dispatch_mode == "Automated Browser (PyWhatKit)":
                if st.button("🚀 Trigger Bulk Dispatch via PyWhatKit"):
                    progress_bar = st.progress(0)
                    for i, (idx, donor) in enumerate(match_df.iterrows()):
                        donor_msg = format_message(msg_template, donor.to_dict(), extra_tags={'hospital': hospital_name, 'urgency': urgency_level, 'contact_person': contact_person})
                        res = dispatch_pywhatkit_message(donor['phone'], donor_msg)
                        st.session_state['dispatch_logs'].append({
                            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "donor": donor['name'],
                            "phone": donor['phone'],
                            "type": "Emergency Request",
                            "status": res['status'],
                            "detail": res.get('message', '')
                        })
                        progress_bar.progress((i + 1) / len(match_df))
                    st.success("Completed automated dispatch sequence!")
                    
            elif dispatch_mode == "Twilio WhatsApp API":
                if st.button("🚀 Send Bulk WhatsApp via Twilio API"):
                    if not (twilio_sid and twilio_token and twilio_from):
                        st.error("Please enter Twilio Account SID, Auth Token, and From Number in the sidebar.")
                    else:
                        for idx, donor in match_df.iterrows():
                            donor_msg = format_message(msg_template, donor.to_dict(), extra_tags={'hospital': hospital_name, 'urgency': urgency_level, 'contact_person': contact_person})
                            res = dispatch_twilio_whatsapp(donor['phone'], donor_msg, twilio_sid, twilio_token, twilio_from)
                            st.session_state['dispatch_logs'].append({
                                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "donor": donor['name'],
                                "phone": donor['phone'],
                                "type": "Emergency Request (Twilio)",
                                "status": res['status'],
                                "detail": res.get('message', 'Delivered')
                            })
                        st.success("Dispatched all messages via Twilio API!")

        # Donor Table with 1-Click WhatsApp buttons
        for idx, donor in match_df.iterrows():
            d_name = donor['name']
            d_phone = donor['phone']
            d_bg = donor['blood_group']
            d_loc = donor['location']
            
            donor_msg = format_message(
                msg_template, 
                donor.to_dict(), 
                extra_tags={'hospital': hospital_name, 'urgency': urgency_level, 'contact_person': contact_person}
            )
            wa_url = generate_whatsapp_web_url(d_phone, donor_msg)
            
            c_d1, c_d2, c_d3, c_d4 = st.columns([2, 2, 2, 2])
            with c_d1:
                st.markdown(f"**{d_name}**")
            with c_d2:
                st.markdown(f"🩸 `{d_bg}` | 📍 {d_loc}")
            with c_d3:
                st.markdown(f"📞 `{d_phone}`")
            with c_d4:
                st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-button">💬 Send WhatsApp</a>', unsafe_allow_html=True)
            st.divider()

# ==================== TAB 3: BIRTHDAYS & CAMPAIGNS ====================
with tab3:
    st.subheader("🎂 Birthday Celebrations & Donor Appreciation")
    
    bday_today_df = get_today_birthdays(df)
    bday_upcoming_df = get_upcoming_birthdays(df, days=7)
    
    col_b1, col_b2 = st.columns(2)
    
    with col_b1:
        st.markdown("#### 🎉 Donors Celebrating Birthday Today")
        if bday_today_df.empty:
            st.info("No donors have birthdays today.")
        else:
            for idx, donor in bday_today_df.iterrows():
                b_msg = format_message(DEFAULT_BIRTHDAY_MESSAGE, donor.to_dict())
                b_wa_url = generate_whatsapp_web_url(donor['phone'], b_msg)
                
                st.markdown(f"""
                <div style="background: rgba(234, 179, 8, 0.1); border: 1px solid rgba(234, 179, 8, 0.3); border-radius: 12px; padding: 16px; margin-bottom: 12px;">
                    <div style="font-weight: 700; font-size: 18px; color: #FACC15;">🎈 {donor['name']}</div>
                    <div style="font-size: 14px; color: #CBD5E1; margin: 4px 0;">Blood Group: <b>{donor['blood_group']}</b> | Phone: <code>{donor['phone']}</code></div>
                    <a href="{b_wa_url}" target="_blank" class="wa-button" style="margin-top: 8px;">🎂 Send Birthday Wishes & Donor Reminder</a>
                </div>
                """, unsafe_allow_html=True)
                
    with col_b2:
        st.markdown("#### 📅 Upcoming Birthdays (Next 7 Days)")
        if bday_upcoming_df.empty:
            st.info("No birthdays coming up in the next 7 days.")
        else:
            for idx, donor in bday_upcoming_df.iterrows():
                st.markdown(f"• **{donor['name']}** ({donor['blood_group']}) - Birthday in **{donor['days_until_bday']}** days")
                
    st.divider()
    st.subheader("📅 Awareness Days & Red Cross Campaigns")
    
    selected_event = st.selectbox("Select Awareness Campaign Day", [e['name'] for e in SPECIAL_EVENTS])
    event_info = next(e for e in SPECIAL_EVENTS if e['name'] == selected_event)
    
    st.markdown(f"**Date**: `{event_info['date_str']}`")
    camp_msg_template = st.text_area("Campaign Message Template", value=event_info['default_message'], height=120)
    
    if st.button(f"📢 Broadcast '{event_info['name']}' Message to All Donors"):
        st.success(f"Prepared campaign messages for all {len(df)} donors!")
        for idx, donor in df.iterrows():
            c_msg = format_message(camp_msg_template, donor.to_dict())
            st.session_state['dispatch_logs'].append({
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "donor": donor['name'],
                "phone": donor['phone'],
                "type": event_info['name'],
                "status": "Prepared Link",
                "detail": "Campaign URL Generated"
            })

# ==================== TAB 4: ACTIVITY LOGS ====================
with tab4:
    st.subheader("📜 Activity & Dispatch Logs")
    
    if not st.session_state['dispatch_logs']:
        st.info("No messaging activity logged yet in this session.")
    else:
        logs_df = pd.DataFrame(st.session_state['dispatch_logs'])
        st.dataframe(logs_df, use_container_width=True)
        
        # Download logs button
        csv_buffer = io.StringIO()
        logs_df.to_csv(csv_buffer, index=False)
        st.download_button(
            "📥 Export Logs to CSV",
            data=csv_buffer.getvalue(),
            file_name=f"RedCross_Dispatch_Logs_{datetime.date.today()}.csv",
            mime="text/csv"
        )
