import pandas as pd
import datetime
import string

SPECIAL_EVENTS = [
    {
        "id": "red_cross_day",
        "name": "World Red Cross & Red Crescent Day",
        "date_str": "May 8",
        "month": 5,
        "day": 8,
        "default_message": "❤️ Happy World Red Cross Day, {name}! Today we celebrate your humanitarian spirit as a proud {blood_group} donor. Your support saves lives. Consider donating blood today! - Red Cross Society"
    },
    {
        "id": "world_donor_day",
        "name": "World Blood Donor Day",
        "date_str": "June 14",
        "month": 6,
        "day": 14,
        "default_message": "🩸 Happy World Blood Donor Day, {name}! As an essential {blood_group} donor in {location}, thank you for giving the gift of life. Your next donation can save 3 lives! - Red Cross Society"
    },
    {
        "id": "national_donation_day",
        "name": "National Voluntary Blood Donation Day",
        "date_str": "October 1",
        "month": 10,
        "day": 1,
        "default_message": "🎉 Today is National Voluntary Blood Donation Day! Dear {name}, as a valued {blood_group} donor, your voluntary contribution brings hope to patients in urgent need. Be a hero today! - Red Cross Society"
    }
]

DEFAULT_BIRTHDAY_MESSAGE = (
    "🎂 Happy Birthday, {name}! 🎁\n\n"
    "On your special day, the Red Cross Society wishes you joy, health, and happiness!\n"
    "Celebrate life by saving lives — as a {blood_group} donor, your blood donation is a priceless gift to someone in need. ❤️\n"
    "Wishing you a wonderful year ahead!"
)

DEFAULT_EMERGENCY_MESSAGE = (
    "🚨 URGENT BLOOD NEEDED! 🩸\n\n"
    "Dear {name},\n"
    "An urgent requirement for {blood_group} blood has been reported at {hospital} ({location}).\n"
    "Urgency Level: {urgency}\n\n"
    "If you are available to donate, please respond or contact: {contact_person}.\n"
    "Your timely help can save a life today! Thank you, Red Cross Society."
)

def get_days_until_event(month: int, day: int) -> int:
    """Calculate days remaining until specified month and day."""
    today = datetime.date.today()
    try:
        event_date = datetime.date(today.year, month, day)
    except ValueError:
        event_date = datetime.date(today.year, 2, 28)
        
    if event_date < today:
        try:
            event_date = datetime.date(today.year + 1, month, day)
        except ValueError:
            event_date = datetime.date(today.year + 1, 2, 28)
            
    return (event_date - today).days

def get_today_birthdays(df: pd.DataFrame) -> pd.DataFrame:
    """Find donors whose birthday (month and day) matches today."""
    if df is None or df.empty or 'dob_dt' not in df.columns:
        return pd.DataFrame()
    
    today = datetime.date.today()
    
    def is_birthday_today(dob):
        if pd.isna(dob) or not isinstance(dob, (pd.Timestamp, datetime.date, datetime.datetime)):
            return False
        return dob.month == today.month and dob.day == today.day
        
    birthday_df = df[df['dob_dt'].apply(is_birthday_today)].copy()
    return birthday_df

def get_upcoming_birthdays(df: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    """Find donors with birthdays in the next N days."""
    if df is None or df.empty or 'dob_dt' not in df.columns:
        return pd.DataFrame()
        
    today = datetime.date.today()
    upcoming_list = []
    
    for idx, row in df.iterrows():
        dob = row['dob_dt']
        if pd.isna(dob) or not isinstance(dob, (pd.Timestamp, datetime.date, datetime.datetime)):
            continue
        try:
            bday_this_year = datetime.date(today.year, dob.month, dob.day)
        except ValueError:
            bday_this_year = datetime.date(today.year, 2, 28)
            
        if bday_this_year < today:
            try:
                bday_this_year = datetime.date(today.year + 1, dob.month, dob.day)
            except ValueError:
                bday_this_year = datetime.date(today.year + 1, 2, 28)
                
        diff_days = (bday_this_year - today).days
        if 0 <= diff_days <= days:
            row_dict = row.to_dict()
            row_dict['days_until_bday'] = diff_days
            upcoming_list.append(row_dict)
            
    return pd.DataFrame(upcoming_list)

def format_message(template_str: str, donor_row: dict, extra_tags: dict = None) -> str:
    """Safe template formatting resilient against missing keys or malformed tags."""
    if not template_str:
        return ""
        
    tags = {
        'name': str(donor_row.get('name', 'Valued Donor')),
        'blood_group': str(donor_row.get('blood_group', 'Blood')),
        'phone': str(donor_row.get('phone', '')),
        'location': str(donor_row.get('location', 'your area')),
        'dob': str(donor_row.get('dob', '')),
        'last_donation': str(donor_row.get('last_donation', 'N/A')),
        'age': str(donor_row.get('age', 'N/A')),
        'hospital': 'Red Cross Emergency Center',
        'urgency': 'HIGH',
        'contact_person': 'Red Cross Helpline'
    }
    
    if extra_tags:
        tags.update(extra_tags)
        
    # Use string.Template for safe substitution
    try:
        # Convert {tag} format to $tag for Template class
        safe_tpl = template_str
        for k in tags.keys():
            safe_tpl = safe_tpl.replace(f"{{{k}}}", f"${k}")
        tpl = string.Template(safe_tpl)
        return tpl.safe_substitute(tags)
    except Exception:
        # Fallback manual string replacement
        result = template_str
        for k, v in tags.items():
            result = result.replace(f"{{{k}}}", str(v))
        return result
