# 🩸 Red Cross Message Automation Dashboard

An interactive Python & Streamlit admin dashboard for **Red Cross Society** blood donation management. Automatically parse donor Excel/CSV datasheets, match donors by blood group during emergencies, dispatch targeted WhatsApp notifications, and send automated birthday greetings & awareness campaign messages.

---

## 🌟 Key Features

1. **📊 Excel Datasheet Manager**:
   - Supports `.xlsx`, `.xls`, and `.csv` files.
   - Automatic column recognition for `Name`, `Phone`, `Blood Group`, `Date of Birth`, `Last Donation Date`, and `Location`.
   - Built-in eligibility calculator (flags donors eligible if last donation was $\ge 90$ days ago).

2. **🚨 Emergency Blood Group Dispatcher**:
   - Select required blood group (`O-`, `O+`, `A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`).
   - Dynamic message template generator with live preview (`{name}`, `{blood_group}`, `{hospital}`, `{urgency}`, `{contact_person}`).
   - Instant 1-click WhatsApp deep-link buttons (`wa.me`) or automated bulk dispatchers.

3. **🎂 Birthday & Campaign Automation**:
   - Automatic identification of donors celebrating birthdays today and upcoming birthdays.
   - 1-Click WhatsApp birthday wishes encouraging blood donation.
   - Pre-configured awareness campaigns:
     - *World Red Cross & Red Crescent Day* (May 8)
     - *World Blood Donor Day* (June 14)
     - *National Voluntary Blood Donation Day* (October 1)

4. **📱 Multi-Mode WhatsApp Engines**:
   - **Direct WhatsApp Web Links (1-Click)** (Free, Universal, default)
   - **Automated Browser Dispatcher (PyWhatKit)**
   - **Twilio WhatsApp API Integration**

---

## 🚀 Quick Start Guide

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/Ranadheer1803/RedCross-Message-Automation.git
cd RedCross-Message-Automation

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch the Application

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## 📂 Project Structure

- `app.py`: Main Streamlit web application & user interface.
- `excel_handler.py`: Excel reader, column normalizer, eligibility logic, and sample datasheet builder.
- `whatsapp_engine.py`: WhatsApp deep link generator and multi-engine dispatchers.
- `campaigns.py`: Birthday detection, awareness day calendar, and message template formatter.
- `requirements.txt`: Project dependencies.
