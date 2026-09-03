import pandas as pd
import datetime
import re
import os

COLUMN_MAPPINGS = {
    'name': ['name', 'full name', 'donor name', 'donor', 'person name', 'member name'],
    'phone': ['phone', 'mobile', 'phone number', 'contact', 'whatsapp', 'mobile number', 'contact number'],
    'blood_group': ['blood group', 'blood type', 'bg', 'group', 'b_group'],
    'dob': ['dob', 'date of birth', 'birth date', 'birthday', 'birth_date'],
    'last_donation': ['last donation date', 'last donation', 'donated on', 'last_donated', 'last donation_date'],
    'location': ['location', 'city', 'address', 'area', 'town', 'district'],
    'email': ['email', 'email address', 'mail']
}

def clean_phone_number(phone_raw) -> str:
    """Robustly clean and format phone numbers from strings, ints, floats, or NaNs."""
    if pd.isna(phone_raw) or phone_raw is None:
        return ""
        
    if isinstance(phone_raw, float):
        phone_str = f"{int(phone_raw)}" if phone_raw.is_integer() else str(phone_raw)
    else:
        phone_str = str(phone_raw).strip()
        
    if phone_str.endswith('.0'):
        phone_str = phone_str[:-2]
        
    digits = re.sub(r'\D', '', phone_str)
    if not digits:
        return ""
        
    if len(digits) == 10:
        return f"+91{digits}"
    elif len(digits) > 10:
        return f"+{digits}"
    return digits

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Identify, map, and standardize dataframe columns with error-resilient type casting."""
    if df is None or df.empty:
        return pd.DataFrame(columns=['name', 'phone', 'blood_group', 'dob', 'last_donation', 'location', 'email', 'dob_dt', 'last_donation_dt', 'age', 'days_since_donation', 'days_until_eligible', 'is_eligible', 'eligibility_status'])
        
    normalized_df = df.copy()
    col_rename_map = {}
    
    for original_col in df.columns:
        clean_col = str(original_col).strip().lower()
        mapped = False
        for std_key, aliases in COLUMN_MAPPINGS.items():
            if clean_col in aliases or any(alias in clean_col for alias in aliases):
                col_rename_map[original_col] = std_key
                mapped = True
                break
        if not mapped:
            col_rename_map[original_col] = original_col
            
    normalized_df = normalized_df.rename(columns=col_rename_map)
    
    for std_key in ['name', 'phone', 'blood_group', 'dob', 'last_donation', 'location', 'email']:
        if std_key not in normalized_df.columns:
            normalized_df[std_key] = ""
            
    normalized_df['name'] = normalized_df['name'].fillna("").astype(str).str.strip()
    normalized_df['location'] = normalized_df['location'].fillna("").astype(str).str.strip()
    normalized_df['email'] = normalized_df['email'].fillna("").astype(str).str.strip()
    
    normalized_df['phone'] = normalized_df['phone'].apply(clean_phone_number)
    
    normalized_df['blood_group'] = normalized_df['blood_group'].astype(str).str.strip().str.upper()
    valid_bgs = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
    normalized_df['blood_group'] = normalized_df['blood_group'].apply(
        lambda bg: bg if bg in valid_bgs else 'O+'
    )
    
    normalized_df['dob_dt'] = pd.to_datetime(normalized_df['dob'], errors='coerce')
    normalized_df['last_donation_dt'] = pd.to_datetime(normalized_df['last_donation'], errors='coerce')
    
    normalized_df['dob'] = normalized_df['dob_dt'].dt.strftime("%Y-%m-%d").fillna("")
    normalized_df['last_donation'] = normalized_df['last_donation_dt'].dt.strftime("%Y-%m-%d").fillna("")
    
    today = pd.Timestamp.now().floor('d')
    def calc_age(dob):
        if pd.isna(dob):
            return 25
        return max(18, int((today - dob).days // 365.25))
    normalized_df['age'] = normalized_df['dob_dt'].apply(calc_age)
    
    normalized_df['days_since_donation'] = (today - normalized_df['last_donation_dt']).dt.days
    
    def calc_days_until_eligible(days_since):
        if pd.isna(days_since) or days_since >= 90:
            return 0
        return int(90 - days_since)
        
    normalized_df['days_until_eligible'] = normalized_df['days_since_donation'].apply(calc_days_until_eligible)
    normalized_df['is_eligible'] = normalized_df['days_until_eligible'] == 0
    
    normalized_df['eligibility_status'] = normalized_df['days_until_eligible'].apply(
        lambda d: "Eligible Now" if d == 0 else f"Eligible in {d} days"
    )
    
    return normalized_df

def save_dataframe_to_excel(df: pd.DataFrame, file_path: str = "sample_donors.xlsx") -> bool:
    """Save normalized donor dataframe back into Excel datasheet file safely."""
    try:
        export_df = df.copy()
        export_cols = {
            'name': 'Full Name',
            'phone': 'Mobile Number',
            'blood_group': 'Blood Group',
            'dob': 'Date of Birth',
            'last_donation': 'Last Donation Date',
            'location': 'Location',
            'email': 'Email'
        }
        
        cols_to_keep = [c for c in export_cols.keys() if c in export_df.columns]
        export_df = export_df[cols_to_keep].rename(columns=export_cols)
        
        export_df.to_excel(file_path, index=False, engine='openpyxl')
        return True
    except Exception as e:
        print(f"Error saving to Excel file {file_path}: {e}")
        return False

def delete_donor_by_phone(df: pd.DataFrame, phone: str, file_path: str = "sample_donors.xlsx") -> pd.DataFrame:
    """Delete a donor record matching the phone number and save updated Excel."""
    clean_p = clean_phone_number(phone)
    updated_df = df[df['phone'] != clean_p].copy()
    save_dataframe_to_excel(updated_df, file_path)
    return updated_df

def generate_sample_datasheet(file_path: str = "sample_donors.xlsx") -> str:
    """Generate an empty Excel datasheet template with standard headers and 0 records."""
    columns = [
        "Full Name",
        "Mobile Number",
        "Blood Group",
        "Date of Birth",
        "Last Donation Date",
        "Location",
        "Email"
    ]
    df = pd.DataFrame(columns=columns)
    df.to_excel(file_path, index=False, engine='openpyxl')
    return file_path
