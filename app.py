import streamlit as st
import pandas as pd
import datetime
import os
import io
import json

# Custom imports
from excel_handler import normalize_columns, generate_sample_datasheet, save_dataframe_to_excel, delete_donor_by_phone
from whatsapp_engine import generate_whatsapp_web_url, generate_wa_me_link, dispatch_pywhatkit_message, dispatch_twilio_whatsapp
from campaigns import (
    SPECIAL_EVENTS, DEFAULT_BIRTHDAY_MESSAGE, DEFAULT_EMERGENCY_MESSAGE,
    get_today_birthdays, get_upcoming_birthdays, format_message, get_days_until_event
)
from neo4j_handler import Neo4jManager

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
    .stApp {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F172A 100%);
        color: #F8FAFC;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
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

    .blood-chip {
        background: rgba(225, 29, 72, 0.15);
        border: 1px solid rgba(225, 29, 72, 0.3);
        border-radius: 10px;
        padding: 10px 14px;
        text-align: center;
    }
    .blood-chip-title {
        font-size: 16px;
        font-weight: 800;
        color: #F43F5E;
    }
    .blood-chip-val {
        font-size: 20px;
        font-weight: 700;
        color: #FFFFFF;
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

ACTIVE_EXCEL_PATH = "sample_donors.xlsx"

if 'df' not in st.session_state:
    if not os.path.exists(ACTIVE_EXCEL_PATH):
        generate_sample_datasheet(ACTIVE_EXCEL_PATH)
    sample_df = pd.read_excel(ACTIVE_EXCEL_PATH)
    st.session_state['df'] = normalize_columns(sample_df)

if 'dispatch_logs' not in st.session_state:
    st.session_state['dispatch_logs'] = []

if 'neo4j' not in st.session_state:
    st.session_state['neo4j'] = Neo4jManager()

if 'custom_events' not in st.session_state:
    st.session_state['custom_events'] = []

neo4j_mgr: Neo4jManager = st.session_state['neo4j']

# Header Section
st.markdown("""
<div class="header-card">
    <div style="font-size: 42px;">🩸</div>
    <div>
        <div class="header-title">Red Cross Message Automation</div>
        <div class="header-subtitle">Refined Blood Donor Dispatcher, Excel Sync & Neo4j Automation System</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/red-cross.png", width=64)
    st.header("📋 Datasheet & Persistence")
    
    uploaded_file = st.file_uploader("Upload Excel / CSV Datasheet", type=["xlsx", "xls", "csv"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                raw_df = pd.read_csv(uploaded_file)
            else:
                raw_df = pd.read_excel(uploaded_file)
            st.session_state['df'] = normalize_columns(raw_df)
            save_dataframe_to_excel(st.session_state['df'], ACTIVE_EXCEL_PATH)
            
            if neo4j_mgr.connected:
                synced = neo4j_mgr.sync_dataframe(st.session_state['df'])
                st.success(f"Loaded {len(st.session_state['df'])} records & synced {synced} to Neo4j!")
            else:
                st.success(f"Loaded {len(st.session_state['df'])} records from {uploaded_file.name}")
        except Exception as e:
            st.error(f"Error reading file: {e}")
            
    st.divider()
    
    st.subheader("💡 Export / Downloads")
    if os.path.exists(ACTIVE_EXCEL_PATH):
        with open(ACTIVE_EXCEL_PATH, "rb") as f:
            st.download_button(
                label="📥 Download Excel Sheet (.xlsx)",
                data=f,
                file_name="RedCross_Current_Donors.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    st.divider()
    
    st.subheader("🌐 Neo4j Graph DB Connection")
    n_uri = st.text_input("Neo4j URI", value="bolt://localhost:7687")
    n_user = st.text_input("Username", value="neo4j")
    n_pwd = st.text_input("Password", value="password", type="password")
    
    c_n1, c_n2 = st.columns(2)
    with c_n1:
        if st.button("🔌 Connect Neo4j"):
            neo4j_mgr.uri = n_uri
            neo4j_mgr.user = n_user
            neo4j_mgr.password = n_pwd
            if neo4j_mgr.connect():
                st.success("Connected!")
                synced_cnt = neo4j_mgr.sync_dataframe(st.session_state['df'])
                st.info(f"Synced {synced_cnt} records!")
            else:
                st.error(f"Failed: {neo4j_mgr.error_message}")
                
    with c_n2:
        if neo4j_mgr.connected:
            st.markdown("🟢 **Neo4j Connected**")
        else:
            st.markdown("🔴 **Neo4j Offline** (Excel mode active)")
            
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
        twilio_from = st.text_input("Twilio From Number")
    else:
        twilio_sid, twilio_token, twilio_from = None, None, None

df = st.session_state['df']

# Top Metrics Row
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Donors (Excel)</div>
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
    n_stats = neo4j_mgr.get_neo4j_stats()
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Neo4j Nodes</div>
        <div class="metric-val" style="color: #38BDF8;">{n_stats['person_count']}</div>
    </div>
    """, unsafe_allow_html=True)

# Blood Group Breakdown Cards
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("##### 🩸 Blood Group Inventory Breakdown")
bg_cols = st.columns(8)
all_groups = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
for i, bg_type in enumerate(all_groups):
    count = len(df[df['blood_group'] == bg_type]) if 'blood_group' in df.columns else 0
    with bg_cols[i]:
        st.markdown(f"""
        <div class="blood-chip">
            <div class="blood-chip-title">{bg_type}</div>
            <div class="blood-chip-val">{count}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Donor Registry", 
    "🚨 Emergency Request", 
    "🎂 Birthdays & Campaigns", 
    "🌐 Neo4j & Activity Logs"
])

# ==================== TAB 1: DONOR REGISTRY ====================
with tab1:
    st.subheader("📋 Donor Registry Datasheet & Management")
    st.info("Adding, editing, or deleting donor records automatically updates the Excel file on disk and syncs with Neo4j.")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        search_query = st.text_input("🔍 Search Donor Name, Phone, or City")
    with col_f2:
        bg_options = ["ALL"] + all_groups
        selected_bg = st.selectbox("🩸 Filter by Blood Group", bg_options)
    with col_f3:
        eligibility_filter = st.selectbox("⏳ Filter Eligibility", ["All Donors", "Eligible Only (≥ 90 Days)", "Recently Donated (< 90 Days)"])
        
    filtered_df = df.copy()
    if search_query:
        filtered_df = filtered_df[
            filtered_df['name'].astype(str).str.contains(search_query, case=False, na=False) |
            filtered_df['phone'].astype(str).str.contains(search_query, case=False, na=False) |
            filtered_df['location'].astype(str).str.contains(search_query, case=False, na=False)
        ]
    if selected_bg != "ALL":
        filtered_df = filtered_df[filtered_df['blood_group'] == selected_bg]
    if eligibility_filter == "Eligible Only (≥ 90 Days)":
        filtered_df = filtered_df[filtered_df['is_eligible'] == True]
    elif eligibility_filter == "Recently Donated (< 90 Days)":
        filtered_df = filtered_df[filtered_df['is_eligible'] == False]
        
    st.write(f"Showing **{len(filtered_df)}** matching donor records:")
    
    display_cols = ['name', 'phone', 'blood_group', 'age', 'dob', 'last_donation', 'eligibility_status', 'location']
    display_cols = [c for c in display_cols if c in filtered_df.columns]
    
    st.dataframe(filtered_df[display_cols], use_container_width=True)
    
    # Export Options
    exp_c1, exp_c2, exp_c3 = st.columns(3)
    with exp_c1:
        csv_data = filtered_df.to_csv(index=False)
        st.download_button("📥 Export Filtered View to CSV", csv_data, "filtered_donors.csv", "text/csv")
    with exp_c2:
        json_data = filtered_df.to_json(orient="records", indent=2)
        st.download_button("📥 Export Filtered View to JSON", json_data, "filtered_donors.json", "application/json")
        
    st.divider()
    col_e1, col_e2, col_e3 = st.columns(3)
    
    # --- Add New Donor Form ---
    with col_e1:
        with st.expander("➕ Add New Donor Record", expanded=True):
            with st.form("new_donor_form"):
                n_name = st.text_input("Full Name *")
                n_phone = st.text_input("Mobile Number *")
                n_bg = st.selectbox("Blood Group", all_groups)
                n_loc = st.text_input("Location / City", value="Hyderabad")
                n_dob = st.date_input("Date of Birth", value=datetime.date(1998, 5, 15))
                n_last = st.date_input("Last Donation Date", value=datetime.date.today() - datetime.timedelta(days=100))
                
                submitted = st.form_submit_button("💾 Save to Excel & Neo4j")
                if submitted:
                    if not n_name or not n_phone:
                        st.error("Please provide Name and Phone number.")
                    else:
                        new_dict = {
                            'name': n_name,
                            'phone': n_phone,
                            'blood_group': n_bg,
                            'dob': n_dob.strftime("%Y-%m-%d"),
                            'last_donation': n_last.strftime("%Y-%m-%d"),
                            'location': n_loc
                        }
                        new_row_df = normalize_columns(pd.DataFrame([new_dict]))
                        st.session_state['df'] = pd.concat([st.session_state['df'], new_row_df], ignore_index=True)
                        save_dataframe_to_excel(st.session_state['df'], ACTIVE_EXCEL_PATH)
                        
                        neo4j_status = ""
                        if neo4j_mgr.connected:
                            neo4j_mgr.upsert_donor(new_row_df.iloc[0].to_dict())
                            neo4j_status = " & Neo4j"
                                
                        st.success(f"✅ Added '{n_name}' to Excel{neo4j_status}!")
                        st.rerun()

    # --- Edit Existing Donor Form ---
    with col_e2:
        with st.expander("✏️ Edit Existing Donor", expanded=True):
            donor_to_edit = st.selectbox("Select Donor to Edit", ["-- Choose --"] + list(df['name'].dropna().unique()))
            if donor_to_edit != "-- Choose --":
                donor_row = df[df['name'] == donor_to_edit].iloc[0]
                with st.form("edit_donor_form"):
                    ed_name = st.text_input("Full Name", value=str(donor_row['name']))
                    ed_phone = st.text_input("Mobile Number", value=str(donor_row['phone']))
                    ed_bg = st.selectbox("Blood Group", all_groups, index=all_groups.index(donor_row['blood_group']) if donor_row['blood_group'] in all_groups else 0)
                    ed_loc = st.text_input("Location", value=str(donor_row['location']))
                    
                    edit_submitted = st.form_submit_button("🔄 Update Member Record")
                    if edit_submitted:
                        idx_to_update = df[df['name'] == donor_to_edit].index[0]
                        st.session_state['df'].at[idx_to_update, 'name'] = ed_name
                        st.session_state['df'].at[idx_to_update, 'phone'] = ed_phone
                        st.session_state['df'].at[idx_to_update, 'blood_group'] = ed_bg
                        st.session_state['df'].at[idx_to_update, 'location'] = ed_loc
                        
                        st.session_state['df'] = normalize_columns(st.session_state['df'])
                        save_dataframe_to_excel(st.session_state['df'], ACTIVE_EXCEL_PATH)
                        
                        neo_msg = ""
                        if neo4j_mgr.connected:
                            updated_dict = st.session_state['df'].loc[idx_to_update].to_dict()
                            neo4j_mgr.upsert_donor(updated_dict)
                            neo_msg = " & Neo4j"
                            
                        st.success(f"✅ Updated '{ed_name}' in Excel{neo_msg}!")
                        st.rerun()

    # --- Delete Donor Form ---
    with col_e3:
        with st.expander("🗑️ Delete Donor Record", expanded=True):
            donor_to_del = st.selectbox("Select Donor to Delete", ["-- Choose --"] + list(df['name'].dropna().unique()))
            if donor_to_del != "-- Choose --":
                donor_del_row = df[df['name'] == donor_to_del].iloc[0]
                st.warning(f"Are you sure you want to remove **{donor_to_del}** (`{donor_del_row['phone']}`)?")
                if st.button(f"❌ Delete {donor_to_del} Permanently"):
                    phone_del = donor_del_row['phone']
                    st.session_state['df'] = delete_donor_by_phone(st.session_state['df'], phone_del, ACTIVE_EXCEL_PATH)
                    
                    neo_del_msg = ""
                    if neo4j_mgr.connected:
                        neo4j_mgr.delete_donor(phone_del)
                        neo_del_msg = " & Neo4j"
                        
                    st.success(f"Deleted '{donor_to_del}' from Excel{neo_del_msg}!")
                    st.rerun()

# ==================== TAB 2: EMERGENCY REQUEST ====================
with tab2:
    st.subheader("🚨 Emergency Blood Dispatcher")
    st.info("Select the required blood group. You can query matching donors using standard Excel filter or Neo4j Graph Traversal (`CAN_DONATE_TO`).")
    
    col_e1, col_e2 = st.columns([1, 2])
    
    with col_e1:
        req_bg = st.selectbox("🎯 Required Recipient Blood Group", ["O-", "O+", "A+", "A-", "B+", "B-", "AB+", "AB-"])
        clean_req_bg = req_bg.strip()
        
        query_engine = st.radio("Search Engine", ["Excel Datasheet Engine", "Neo4j Graph Traversal (:CAN_DONATE_TO)"])
        
        urgency_level = st.select_slider("🔥 Urgency Level", options=["NORMAL", "HIGH", "CRITICAL"])
        hospital_name = st.text_input("🏥 Hospital / Location Name", value="Apollo Hospital, Hyderabad")
        contact_person = st.text_input("📞 Emergency Contact Person", value="Red Cross Helpline (9876543210)")
        
        only_eligible = st.checkbox("Only include eligible donors (≥90 days since last donation)", value=True)
        
        if query_engine == "Neo4j Graph Traversal (:CAN_DONATE_TO)" and neo4j_mgr.connected:
            neo_results = neo4j_mgr.get_compatible_donors_graph(clean_req_bg)
            match_df = pd.DataFrame(neo_results)
            if not match_df.empty and only_eligible:
                match_df = match_df[match_df['is_eligible'] == True]
            st.success("Queried via Neo4j Graph Cypher!")
        else:
            match_df = df[df['blood_group'] == clean_req_bg].copy()
            if only_eligible:
                match_df = match_df[match_df['is_eligible'] == True]
                
        st.markdown(f"**Found <span style='color:#F43F5E; font-size:20px;'>{len(match_df)}</span> donors who can donate to {clean_req_bg}**", unsafe_allow_html=True)

    with col_e2:
        st.markdown("##### 📝 Message Template Editor")
        msg_template = st.text_area(
            "Customize WhatsApp Emergency Message",
            value=DEFAULT_EMERGENCY_MESSAGE,
            height=200
        )
        
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
                        st.error("Please enter Twilio credentials in sidebar.")
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
            d_status = donor.get('eligibility_status', 'Eligible')
            
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
                st.markdown(f"🩸 `{d_bg}` | 📍 {d_loc} | `{d_status}`")
            with c_d3:
                st.markdown(f"📞 `{d_phone}`")
            with c_d4:
                st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-button">💬 Send WhatsApp</a>', unsafe_allow_html=True)
            st.divider()

# ==================== TAB 3: BIRTHDAYS & CAMPAIGNS ====================
with tab3:
    st.subheader("🎂 Birthday Celebrations & Campaign Automation")
    
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
    st.subheader("📅 Awareness Days & Custom Campaign Builder")
    
    all_events = SPECIAL_EVENTS + st.session_state['custom_events']
    
    # Event countdown badges
    ev_cols = st.columns(len(all_events))
    for i, ev in enumerate(all_events):
        days_rem = get_days_until_event(ev['month'], ev['day'])
        with ev_cols[i % len(ev_cols)]:
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 12px; text-align: center;">
                <div style="font-size: 12px; color: #94A3B8; font-weight: 700;">{ev['name']}</div>
                <div style="font-size: 22px; font-weight: 800; color: #38BDF8; margin-top: 4px;">{days_rem} days</div>
                <div style="font-size: 11px; color: #64748B;">({ev['date_str']})</div>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
    selected_event_name = st.selectbox("Select Campaign Event", [e['name'] for e in all_events])
    event_info = next(e for e in all_events if e['name'] == selected_event_name)
    
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
            
    with st.expander("➕ Add Custom Awareness Campaign"):
        with st.form("custom_campaign_form"):
            c_name = st.text_input("Campaign Name (e.g. District College Blood Drive)")
            c_month = st.number_input("Month (1-12)", min_value=1, max_value=12, value=10)
            c_day = st.number_input("Day (1-31)", min_value=1, max_value=31, value=15)
            c_template = st.text_area("Default Campaign Message", value="📢 Dear {name}, join our upcoming Red Cross Blood Drive! Your donation matters.")
            
            if st.form_submit_button("Save Campaign"):
                if c_name:
                    st.session_state['custom_events'].append({
                        "id": c_name.lower().replace(" ", "_"),
                        "name": c_name,
                        "date_str": f"Month {c_month}, Day {c_day}",
                        "month": int(c_month),
                        "day": int(c_day),
                        "default_message": c_template
                    })
                    st.success(f"Added custom campaign '{c_name}'!")
                    st.rerun()

# ==================== TAB 4: NEO4J & LOGS ====================
with tab4:
    st.subheader("🌐 Neo4j Graph Database & Activity Logs")
    
    col_n1, col_n2 = st.columns(2)
    with col_n1:
        st.markdown("#### 📊 Neo4j Database Status")
        if neo4j_mgr.connected:
            n_stats = neo4j_mgr.get_neo4j_stats()
            st.success("🟢 Neo4j Database Connected")
            st.write(f"- **Person Nodes**: `{n_stats['person_count']}`")
            st.write(f"- **Total Relationships**: `{n_stats['rel_count']}`")
            
            if st.button("🔄 Sync Entire Excel Datasheet to Neo4j Now"):
                synced = neo4j_mgr.sync_dataframe(df)
                st.success(f"Synced {synced} donor nodes to Neo4j!")
        else:
            st.warning("🔴 Neo4j Disconnected. Enter credentials in sidebar to connect.")
            st.info("When Neo4j is disconnected, all additions, edits, & deletions automatically persist to the Excel sheet.")

    with col_n2:
        st.markdown("#### 📜 Messaging Logs")
        if not st.session_state['dispatch_logs']:
            st.info("No messaging activity logged yet.")
        else:
            logs_df = pd.DataFrame(st.session_state['dispatch_logs'])
            st.dataframe(logs_df, use_container_width=True)
            
            csv_buffer = io.StringIO()
            logs_df.to_csv(csv_buffer, index=False)
            st.download_button(
                "📥 Export Logs to CSV",
                data=csv_buffer.getvalue(),
                file_name=f"RedCross_Dispatch_Logs_{datetime.date.today()}.csv",
                mime="text/csv"
            )
