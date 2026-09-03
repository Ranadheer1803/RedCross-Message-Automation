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

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Identify and map column names to standard fields."""
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
    
    # Ensure mandatory standard columns exist
    for std_key in ['name', 'phone', 'blood_group', 'dob', 'last_donation', 'location']:
        if std_key not in normalized_df.columns:
            normalized_df[std_key] = None
            
    # Clean phone numbers
    normalized_df['phone'] = normalized_df['phone'].apply(clean_phone_number)
    
    # Standardize Blood Group string
    normalized_df['blood_group'] = normalized_df['blood_group'].astype(str).str.strip().str.upper()
    normalized_df['blood_group'] = normalized_df['blood_group'].replace({'NONE': 'Unknown', 'NAN': 'Unknown', 'N/A': 'Unknown'})
    
    # Format DOB and Last Donation dates
    normalized_df['dob_dt'] = pd.to_datetime(normalized_df['dob'], errors='coerce')
    normalized_df['last_donation_dt'] = pd.to_datetime(normalized_df['last_donation'], errors='coerce')
    
    # Determine eligibility (>= 90 days since last donation or no donation history)
    today = pd.Timestamp.now().floor('d')
    normalized_df['days_since_donation'] = (today - normalized_df['last_donation_dt']).dt.days
    normalized_df['is_eligible'] = normalized_df['days_since_donation'].apply(
        lambda d: True if pd.isna(d) or d >= 90 else False
    )
    
    return normalized_df

def clean_phone_number(phone_raw) -> str:
    if pd.isna(phone_raw):
        return ""
    # Extract numbers only
    digits = re.sub(r'\D', '', str(phone_raw))
    if not digits:
        return ""
    # Add default country code (India +91) if 10 digits
    if len(digits) == 10:
        return f"+91{digits}"
    elif len(digits) > 10 and not str(phone_raw).startswith('+'):
        return f"+{digits}"
    elif str(phone_raw).startswith('+'):
        return f"+{digits}"
    return digits

def generate_sample_datasheet(file_path: str = "sample_donors.xlsx") -> str:
    """Generate a sample Excel datasheet with realistic Red Cross donor records."""
    today = datetime.date.today()
    
    donors_data = [
        {
            "Full Name": "Rahul Sharma",
            "Mobile Number": "9876543210",
            "Blood Group": "O+",
            "Date of Birth": (today - datetime.timedelta(days=25*365)).strftime("%Y-%m-%d"),
            "Last Donation Date": (today - datetime.timedelta(days=120)).strftime("%Y-%m-%d"),
            "Location": "Hyderabad",
            "Email": "rahul.sharma@example.com"
        },
        {
            "Full Name": "Priya Patel",
            "Mobile Number": "9812345678",
            "Blood Group": "A+",
            "Date of Birth": today.strftime("%Y-%m-%d"), # Birthday today!
            "Last Donation Date": (today - datetime.timedelta(days=100)).strftime("%Y-%m-%d"),
            "Location": "Secunderabad",
            "Email": "priya.patel@example.com"
        },
        {
            "Full Name": "Vikram Singh",
            "Mobile Number": "9765432109",
            "Blood Group": "O-", # Universal donor
            "Date of Birth": (today - datetime.timedelta(days=30*365 + 10)).strftime("%Y-%m-%d"),
            "Last Donation Date": (today - datetime.timedelta(days=45)).strftime("%Y-%m-%d"), # Ineligible (< 90 days)
            "Location": "Cyberabad",
            "Email": "vikram.s@example.com"
        },
        {
            "Full Name": "Ananya Reddy",
            "Mobile Number": "9654321098",
            "Blood Group": "B+",
            "Date of Birth": (today - datetime.timedelta(days=22*365)).strftime("%Y-%m-%d"),
            "Last Donation Date": (today - datetime.timedelta(days=150)).strftime("%Y-%m-%d"),
            "Location": "Hyderabad",
            "Email": "ananya.r@example.com"
        },
        {
            "Full Name": "Suresh Verma",
            "Mobile Number": "9543210987",
            "Blood Group": "AB+",
            "Date of Birth": (today - datetime.timedelta(days=28*365)).strftime("%Y-%m-%d"),
            "Last Donation Date": (today - datetime.timedelta(days=200)).strftime("%Y-%m-%d"),
            "Location": "Warangal",
            "Email": "suresh.v@example.com"
        },
        {
            "Full Name": "Sneha Kulkarni",
            "Mobile Number": "9432109876",
            "Blood Group": "O-",
            "Date of Birth": (today - datetime.timedelta(days=26*365)).strftime("%Y-%m-%d"),
            "Last Donation Date": (today - datetime.timedelta(days=110)).strftime("%Y-%m-%d"),
            "Location": "Hyderabad",
            "Email": "sneha.k@example.com"
        },
        {
            "Full Name": "Karthik Rao",
            "Mobile Number": "9321098765",
            "Blood Group": "A-",
            "Date of Birth": (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d"), # Birthday tomorrow!
            "Last Donation Date": (today - datetime.timedelta(days=95)).strftime("%Y-%m-%d"),
            "Location": "Nizamabad",
            "Email": "karthik.rao@example.com"
        },
        {
            "Full Name": "Meera Joshi",
            "Mobile Number": "9210987654",
            "Blood Group": "B-",
            "Date of Birth": (today - datetime.timedelta(days=24*365)).strftime("%Y-%m-%d"),
            "Last Donation Date": (today - datetime.timedelta(days=180)).strftime("%Y-%m-%d"),
            "Location": "Karimnagar",
            "Email": "meera.j@example.com"
        }
    ]
    
    df = pd.DataFrame(donors_data)
    df.to_excel(file_path, index=False, engine='openpyxl')
    return file_path
