from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import pandas as pd
import datetime
import os
import io
import logging
import webbrowser
import time

from excel_handler import (
    normalize_columns, generate_sample_datasheet, save_dataframe_to_excel, 
    delete_donor_by_phone, clean_phone_number
)
from whatsapp_engine import generate_whatsapp_web_url, generate_wa_me_link, dispatch_pywhatkit_message, dispatch_twilio_whatsapp
from campaigns import (
    SPECIAL_EVENTS, DEFAULT_BIRTHDAY_MESSAGE, DEFAULT_EMERGENCY_MESSAGE,
    get_today_birthdays, get_upcoming_birthdays, format_message, get_days_until_event
)
from neo4j_handler import Neo4jManager
from graph_engine import InMemGraphEngine

app = FastAPI(title="RED CROSS WEST GODAVARI REST API — Neo4j Powered", version="2.5")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ACTIVE_EXCEL_PATH = "sample_donors.xlsx"

# Connect to user's live local Neo4j instance "REDCROSS WG"
neo4j_mgr = Neo4jManager(uri="bolt://localhost:7687", user="neo4j", password="REDCROSS WG")
neo4j_connected = neo4j_mgr.connect()
logging.info(f"Neo4j REDCROSS WG Instance Connection: {neo4j_connected}")

graph_engine = InMemGraphEngine()

if not os.path.exists(ACTIVE_EXCEL_PATH):
    generate_sample_datasheet(ACTIVE_EXCEL_PATH)

def load_current_df() -> pd.DataFrame:
    if os.path.exists(ACTIVE_EXCEL_PATH):
        raw_df = pd.read_excel(ACTIVE_EXCEL_PATH)
        norm_df = normalize_columns(raw_df)
        
        graph_engine.clear()
        for idx, row in norm_df.iterrows():
            graph_engine.upsert_person(row.to_dict())
            
        return norm_df
    return normalize_columns(pd.DataFrame())

load_current_df()

os.makedirs("static", exist_ok=True)
os.makedirs("assets", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

class DonorCreate(BaseModel):
    name: str
    phone: str
    blood_group: str
    dob: str
    last_donation: str
    location: Optional[str] = "Eluru, West Godavari"
    email: Optional[str] = ""

class AutoDispatchReq(BaseModel):
    blood_group: str
    hospital: str = "Government General Hospital, Eluru"
    urgency: str = "HIGH"

@app.get("/api/stats")
def get_stats():
    df = load_current_df()
    total_donors = len(df)
    eligible_count = len(df[df['is_eligible'] == True]) if not df.empty else 0
    bday_df = get_today_birthdays(df)
    
    all_bgs = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
    bg_breakdown = {}
    if not df.empty:
        df['clean_bg'] = df['blood_group'].astype(str).str.strip().str.upper()
        for bg in all_bgs:
            bg_breakdown[bg] = len(df[df['clean_bg'] == bg])
    else:
        for bg in all_bgs:
            bg_breakdown[bg] = 0
            
    n_stats = neo4j_mgr.get_neo4j_stats()
    
    return {
        "total_donors": total_donors,
        "eligible_count": eligible_count,
        "birthdays_today": len(bday_df),
        "blood_inventory": bg_breakdown,
        "neo4j": n_stats,
        "graph_node_count": n_stats['person_count'] if neo4j_mgr.connected else len(graph_engine.person_nodes)
    }

@app.get("/api/donors")
def get_donors(search: Optional[str] = "", blood_group: Optional[str] = "ALL", eligibility: Optional[str] = "ALL"):
    df = load_current_df()
    if df.empty:
        return []
        
    filtered = df.copy()
    if search:
        filtered = filtered[
            filtered['name'].astype(str).str.contains(search, case=False, na=False) |
            filtered['phone'].astype(str).str.contains(search, case=False, na=False) |
            filtered['location'].astype(str).str.contains(search, case=False, na=False)
        ]
    if blood_group and blood_group != "ALL":
        filtered['clean_bg'] = filtered['blood_group'].astype(str).str.strip().str.upper()
        filtered = filtered[filtered['clean_bg'] == blood_group.strip().upper()]
    if eligibility == "ELIGIBLE":
        filtered = filtered[filtered['is_eligible'] == True]
    elif eligibility == "INELIGIBLE":
        filtered = filtered[filtered['is_eligible'] == False]
        
    return filtered.to_dict(orient="records")

@app.post("/api/donors")
def add_donor(donor: DonorCreate):
    df = load_current_df()
    new_dict = donor.dict()
    new_row = normalize_columns(pd.DataFrame([new_dict]))
    
    updated_df = pd.concat([df, new_row], ignore_index=True)
    save_dataframe_to_excel(updated_df, ACTIVE_EXCEL_PATH)
    
    graph_engine.upsert_person(new_row.iloc[0].to_dict())
    
    neo4j_synced = False
    if neo4j_mgr.connected:
        neo4j_synced = neo4j_mgr.upsert_donor(new_row.iloc[0].to_dict())
        
    return {"status": "success", "message": f"Added donor {donor.name}", "neo4j_synced": neo4j_synced}

@app.put("/api/donors/{phone}")
def update_donor(phone: str, donor: DonorCreate):
    df = load_current_df()
    clean_p = clean_phone_number(phone)
    
    if df.empty or clean_p not in df['phone'].values:
        raise HTTPException(status_code=404, detail="Donor not found")
        
    idx = df[df['phone'] == clean_p].index[0]
    df.at[idx, 'name'] = donor.name
    df.at[idx, 'phone'] = clean_phone_number(donor.phone)
    df.at[idx, 'blood_group'] = donor.blood_group
    df.at[idx, 'dob'] = donor.dob
    df.at[idx, 'last_donation'] = donor.last_donation
    df.at[idx, 'location'] = donor.location
    df.at[idx, 'email'] = donor.email
    
    updated_df = normalize_columns(df)
    save_dataframe_to_excel(updated_df, ACTIVE_EXCEL_PATH)
    
    graph_engine.upsert_person(updated_df.loc[idx].to_dict())
    
    if neo4j_mgr.connected:
        neo4j_mgr.upsert_donor(updated_df.loc[idx].to_dict())
        
    return {"status": "success", "message": f"Updated donor {donor.name}"}

@app.delete("/api/donors/{phone}")
def delete_donor(phone: str):
    df = load_current_df()
    clean_p = clean_phone_number(phone)
    
    updated_df = delete_donor_by_phone(df, clean_p, ACTIVE_EXCEL_PATH)
    graph_engine.delete_person(clean_p)
    
    if neo4j_mgr.connected:
        neo4j_mgr.delete_donor(clean_p)
        
    return {"status": "success", "message": f"Deleted donor with phone {phone}"}

@app.get("/api/emergency")
def match_emergency(blood_group: str, hospital: Optional[str] = "GGH Eluru", urgency: Optional[str] = "HIGH"):
    clean_bg = blood_group.strip().upper()
    
    if neo4j_mgr.connected:
        matched = neo4j_mgr.get_compatible_donors_graph(clean_bg)
        engine_type = "NEO4J_REDCROSS_WG_INSTANCE"
    else:
        matched = graph_engine.query_compatible_donors(clean_bg)
        engine_type = "NEO4J_LOCAL_GRAPH_ENGINE"
        
    for donor in matched:
        msg = format_message(
            DEFAULT_EMERGENCY_MESSAGE,
            donor,
            extra_tags={'hospital': hospital, 'urgency': urgency, 'contact_person': 'Red Cross West Godavari (9876543210)'}
        )
        donor['wa_message'] = msg
        donor['wa_url'] = generate_whatsapp_web_url(donor.get('phone', ''), msg)
        
    return {
        "required_blood_group": clean_bg,
        "engine_used": engine_type,
        "count": len(matched),
        "donors": matched
    }

@app.post("/api/emergency/auto-dispatch")
def auto_dispatch_emergency(req: AutoDispatchReq):
    clean_bg = req.blood_group.strip().upper()
    
    if neo4j_mgr.connected:
        matched = neo4j_mgr.get_compatible_donors_graph(clean_bg)
    else:
        matched = graph_engine.query_compatible_donors(clean_bg)
        
    dispatched_count = 0
    for donor in matched:
        msg = format_message(
            DEFAULT_EMERGENCY_MESSAGE,
            donor,
            extra_tags={'hospital': req.hospital, 'urgency': req.urgency, 'contact_person': 'Red Cross West Godavari (9876543210)'}
        )
        wa_url = generate_whatsapp_web_url(donor.get('phone', ''), msg)
        
        webbrowser.open(wa_url)
        time.sleep(0.8)
        dispatched_count += 1
        
    return {
        "status": "success",
        "message": f"Successfully launched WhatsApp dispatches for all {dispatched_count} donors!",
        "dispatched_count": dispatched_count
    }

@app.get("/api/neo4j/seed")
def download_cypher_seed():
    load_current_df()
    cypher_file = graph_engine.generate_neo4j_cypher_seed_script("redcross_neo4j_seed.cypher")
    return FileResponse(cypher_file, filename="redcross_neo4j_seed.cypher", media_type="text/plain")

@app.get("/api/birthdays")
def get_birthdays():
    df = load_current_df()
    today_bdays = get_today_birthdays(df).to_dict(orient="records") if not df.empty else []
    upcoming_bdays = get_upcoming_birthdays(df, days=7).to_dict(orient="records") if not df.empty else []
    
    for donor in today_bdays:
        msg = format_message(DEFAULT_BIRTHDAY_MESSAGE, donor)
        donor['wa_message'] = msg
        donor['wa_url'] = generate_whatsapp_web_url(donor.get('phone', ''), msg)
        
    return {
        "today": today_bdays,
        "upcoming": upcoming_bdays
    }

@app.get("/api/events")
def get_events():
    events_data = []
    for ev in SPECIAL_EVENTS:
        days_rem = get_days_until_event(ev['month'], ev['day'])
        ev_copy = dict(ev)
        ev_copy['days_remaining'] = days_rem
        events_data.append(ev_copy)
    return events_data

@app.post("/api/excel/upload")
async def upload_excel(file: UploadFile = File(...)):
    contents = await file.read()
    if file.filename.endswith('.csv'):
        raw_df = pd.read_csv(io.BytesIO(contents))
    else:
        raw_df = pd.read_excel(io.BytesIO(contents))
        
    df = normalize_columns(raw_df)
    save_dataframe_to_excel(df, ACTIVE_EXCEL_PATH)
    
    load_current_df()
    
    if neo4j_mgr.connected:
        neo4j_mgr.sync_dataframe(df)
        
    return {"status": "success", "message": f"Uploaded {len(df)} donor records"}

@app.get("/api/excel/download")
def download_excel():
    if os.path.exists(ACTIVE_EXCEL_PATH):
        return FileResponse(ACTIVE_EXCEL_PATH, filename="RedCross_WestGodavari_Donors.xlsx")
    raise HTTPException(status_code=404, detail="Excel file not found")
