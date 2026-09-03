// RED CROSS WEST GODAVARI - Frontend Application JavaScript

let currentEmergencyMatches = [];

document.addEventListener("DOMContentLoaded", () => {
    initDateDropdowns();
    loadStats();
    loadDonors();
    loadEvents();
    loadBirthdays();
});

// Initialize Instant Year / Month / Day Dropdowns
function initDateDropdowns() {
    const currentYear = new Date().getFullYear();
    
    // Years (Current year down to 1940)
    const dobYearSelect = document.getElementById('dob-year');
    const lastYearSelect = document.getElementById('last-year');
    dobYearSelect.innerHTML = '<option value="">Year</option>';
    lastYearSelect.innerHTML = '<option value="">Year</option>';
    
    for (let y = currentYear; y >= 1940; y--) {
        const opt1 = new Option(y, y);
        const opt2 = new Option(y, y);
        dobYearSelect.add(opt1);
        lastYearSelect.add(opt2);
    }
    dobYearSelect.value = 1998;
    lastYearSelect.value = currentYear;

    // Months (Jan - Dec)
    const months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const dobMonthSelect = document.getElementById('dob-month');
    const lastMonthSelect = document.getElementById('last-month');
    dobMonthSelect.innerHTML = '<option value="">Month</option>';
    lastMonthSelect.innerHTML = '<option value="">Month</option>';
    
    months.forEach((m, idx) => {
        const val = String(idx + 1).padStart(2, '0');
        dobMonthSelect.add(new Option(m, val));
        lastMonthSelect.add(new Option(m, val));
    });
    dobMonthSelect.value = "05";
    lastMonthSelect.value = "01";

    // Days (1 - 31)
    const dobDaySelect = document.getElementById('dob-day');
    const lastDaySelect = document.getElementById('last-day');
    dobDaySelect.innerHTML = '<option value="">Day</option>';
    lastDaySelect.innerHTML = '<option value="">Day</option>';
    
    for (let d = 1; d <= 31; d++) {
        const val = String(d).padStart(2, '0');
        dobDaySelect.add(new Option(d, val));
        lastDaySelect.add(new Option(d, val));
    }
    dobDaySelect.value = "15";
    lastDaySelect.value = "10";
}

// Tab Switching Logic
function switchTab(tabId) {
    document.querySelectorAll('.rc-tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.rc-tab-content').forEach(content => content.classList.remove('active'));

    event.target.classList.add('active');
    document.getElementById(tabId).classList.add('active');

    if (tabId === 'tab-registry') loadDonors();
    if (tabId === 'tab-campaigns') loadBirthdays();
}

// Fetch Global Metrics & Blood Group Inventory
async function loadStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();

        document.getElementById('metric-total').innerText = data.total_donors;
        document.getElementById('metric-eligible').innerText = data.eligible_count;
        document.getElementById('metric-birthdays').innerText = data.birthdays_today;
        document.getElementById('metric-neo4j').innerText = data.neo4j.person_count || 0;

        const bgGrid = document.getElementById('bg-inventory-grid');
        bgGrid.innerHTML = '';
        const allGroups = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"];
        
        allGroups.forEach(bg => {
            const count = data.blood_inventory[bg] || 0;
            bgGrid.innerHTML += `
                <div class="rc-bg-chip">
                    <div class="rc-bg-chip-type">${bg}</div>
                    <div class="rc-bg-chip-cnt">${count}</div>
                </div>
            `;
        });
    } catch (e) {
        console.error("Error loading stats:", e);
    }
}

// Search & Load Donors
async function loadDonors() {
    const search = document.getElementById('search-input').value.trim();
    const bg = document.getElementById('filter-bg').value;
    const eligibility = document.getElementById('filter-eligibility').value;

    const cardsContainer = document.getElementById('donors-cards-container');
    const resultsTitle = document.getElementById('search-results-title');

    if (!search && bg === 'ALL' && eligibility === 'ALL') {
        resultsTitle.style.display = "none";
        cardsContainer.innerHTML = `
            <div class="rc-card" style="text-align: center; padding: 48px 24px;">
                <div style="font-size: 44px; color: #D32F2F; margin-bottom: 12px;">🔍</div>
                <h3 style="font-size: 20px; font-weight: 800;">Search Registered Donor Members</h3>
                <p class="text-muted" style="max-width: 480px; margin: 8px auto 20px;">
                    Enter a donor name, phone number, or city in the search bar above to query member records, or click below to register a new member.
                </p>
                <button class="rc-btn rc-btn-red" onclick="openAddModal()">➕ Add New Member</button>
            </div>
        `;
        return;
    }

    resultsTitle.style.display = "block";

    const query = new URLSearchParams({ search, blood_group: bg, eligibility });
    try {
        const res = await fetch(`/api/donors?${query}`);
        const donors = await res.json();

        cardsContainer.innerHTML = '';

        if (!donors || donors.length === 0) {
            cardsContainer.innerHTML = `
                <div class="rc-card" style="text-align: center; padding: 32px;">
                    <p class="text-muted">No donor records matched your search query '${search}'.</p>
                    <button class="rc-btn rc-btn-red" onclick="openAddModal()">➕ Register '${search}' as New Member</button>
                </div>
            `;
            return;
        }

        donors.forEach(d => {
            const waUrl = `https://api.whatsapp.com/send?phone=${d.phone.replace(/\D/g, '')}&text=${encodeURIComponent(`Hello ${d.name}, Red Cross West Godavari Branch greeting!`)}`;
            cardsContainer.innerHTML += `
                <div class="rc-donor-item" style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 20px; font-weight: 800; color: #0F172A;">👤 ${d.name} <span style="font-size: 14px; font-weight: 600; color: #64748B;">(Age: ${d.age || 'N/A'})</span></div>
                        <div style="font-size: 14px; color: #475569; margin-top: 4px;">
                            🩸 Blood Group: <b style="color:#D32F2F;">${d.blood_group}</b> | 📍 Location: <b>${d.location || 'General'}</b> | ⏳ Status: <code>${d.eligibility_status || 'Eligible'}</code>
                        </div>
                        <div style="font-size: 13px; color: #94A3B8; margin-top: 2px;">Phone: <code>${d.phone}</code> | DOB: <b>${d.dob || '-'}</b> | Last Donation: <b>${d.last_donation || '-'}</b></div>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <button class="rc-btn rc-btn-outline" style="padding: 8px 14px; font-size: 13px;" onclick="openEditModal('${d.phone}')">✏️ Edit</button>
                        <button class="rc-btn rc-btn-outline" style="padding: 8px 14px; font-size: 13px; color: #D32F2F;" onclick="deleteDonor('${d.phone}', '${d.name}')">🗑️ Delete</button>
                        <a href="${waUrl}" target="_blank" class="rc-wa-button">💬 WhatsApp</a>
                    </div>
                </div>
            `;
        });
    } catch (e) {
        console.error("Error searching donors:", e);
    }
}

// Modal Form Handlers
function openAddModal() {
    document.getElementById('modal-title').innerText = "➕ Add Member Record";
    document.getElementById('donor-form').reset();
    document.getElementById('edit-original-phone').value = "";
    
    document.getElementById('dob-year').value = "1998";
    document.getElementById('dob-month').value = "05";
    document.getElementById('dob-day').value = "15";
    
    const currentYear = new Date().getFullYear();
    document.getElementById('last-year').value = currentYear;
    document.getElementById('last-month').value = "01";
    document.getElementById('last-day').value = "10";
    
    document.getElementById('donor-modal').classList.add('active');
}

async function openEditModal(phone) {
    try {
        const res = await fetch(`/api/donors?search=${phone}`);
        const donors = await res.json();
        if (donors && donors.length > 0) {
            const d = donors[0];
            document.getElementById('modal-title').innerText = "✏️ Edit Member Record";
            document.getElementById('edit-original-phone').value = d.phone;
            document.getElementById('form-name').value = d.name;
            document.getElementById('form-phone').value = d.phone;
            document.getElementById('form-bg').value = d.blood_group;
            document.getElementById('form-location').value = d.location || "Eluru, West Godavari";
            
            if (d.dob && d.dob.includes('-')) {
                const parts = d.dob.split('-');
                document.getElementById('dob-year').value = parts[0];
                document.getElementById('dob-month').value = parts[1];
                document.getElementById('dob-day').value = parts[2];
            }
            
            if (d.last_donation && d.last_donation.includes('-')) {
                const parts = d.last_donation.split('-');
                document.getElementById('last-year').value = parts[0];
                document.getElementById('last-month').value = parts[1];
                document.getElementById('last-day').value = parts[2];
            }

            document.getElementById('donor-modal').classList.add('active');
        }
    } catch (e) {
        console.error("Error opening edit modal:", e);
    }
}

function closeModal() {
    document.getElementById('donor-modal').classList.remove('active');
}

async function handleFormSubmit(e) {
    e.preventDefault();
    const originalPhone = document.getElementById('edit-original-phone').value;
    
    const dobY = document.getElementById('dob-year').value;
    const dobM = document.getElementById('dob-month').value;
    const dobD = document.getElementById('dob-day').value;
    const dobStr = (dobY && dobM && dobD) ? `${dobY}-${dobM}-${dobD}` : "";

    const lastY = document.getElementById('last-year').value;
    const lastM = document.getElementById('last-month').value;
    const lastD = document.getElementById('last-day').value;
    const lastStr = (lastY && lastM && lastD) ? `${lastY}-${lastM}-${lastD}` : "";

    const donorData = {
        name: document.getElementById('form-name').value,
        phone: document.getElementById('form-phone').value,
        blood_group: document.getElementById('form-bg').value,
        dob: dobStr,
        last_donation: lastStr,
        location: document.getElementById('form-location').value,
        email: ""
    };

    try {
        let res;
        if (originalPhone) {
            res = await fetch(`/api/donors/${originalPhone}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(donorData)
            });
        } else {
            res = await fetch('/api/donors', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(donorData)
            });
        }
        
        if (res.ok) {
            closeModal();
            loadStats();
            document.getElementById('search-input').value = donorData.name;
            loadDonors();
        }
    } catch (err) {
        console.error("Error submitting form:", err);
    }
}

async function deleteDonor(phone, name) {
    if (confirm(`Are you sure you want to delete donor ${name} (${phone})?`)) {
        try {
            await fetch(`/api/donors/${phone}`, { method: 'DELETE' });
            loadStats();
            loadDonors();
        } catch (e) {
            console.error("Error deleting donor:", e);
        }
    }
}

// Emergency Matching Triggered on FIND MATCHING DONORS Button Click!
async function matchEmergencyDonors() {
    const bg = document.getElementById('em-bg-select').value;
    const hospital = document.getElementById('em-hospital').value;
    const urgency = document.getElementById('em-urgency').value;

    const listDiv = document.getElementById('em-matched-list');
    const reqAllContainer = document.getElementById('request-all-container');
    
    listDiv.innerHTML = `<div class="rc-card"><p class="text-muted">Searching database for compatible ${bg} donors...</p></div>`;

    try {
        const res = await fetch(`/api/emergency?blood_group=${bg}&hospital=${encodeURIComponent(hospital)}&urgency=${urgency}`);
        const data = await res.json();

        currentEmergencyMatches = data.donors || [];
        document.getElementById('em-matched-count').innerText = data.count;
        listDiv.innerHTML = '';

        if (!data.donors || data.donors.length === 0) {
            reqAllContainer.style.display = "none";
            listDiv.innerHTML = `<div class="rc-card" style="text-align: center; padding: 32px;"><p class="text-muted">No matching donors registered for blood group ${bg}.</p></div>`;
            return;
        }

        // Show REQUEST ALL button
        reqAllContainer.style.display = "block";

        data.donors.forEach(d => {
            listDiv.innerHTML += `
                <div class="rc-donor-item" style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 18px; font-weight: 800; color: #0F172A;">👤 ${d.name} <span style="font-size: 13px; color: #64748B;">(Age: ${d.age || 'N/A'})</span></div>
                        <div style="font-size: 13px; color: #475569; margin-top: 4px;">
                            🩸 Blood Group: <b style="color: #D32F2F;">${d.blood_group}</b> | 📍 Location: <b>${d.location || 'General'}</b> | ⏳ Status: <code>${d.eligibility_status || 'Eligible'}</code>
                        </div>
                        <div style="font-size: 13px; color: #94A3B8; margin-top: 2px;">Phone: <code>${d.phone}</code></div>
                    </div>
                    <div>
                        <a href="${d.wa_url}" target="_blank" class="rc-wa-button">💬 Send WhatsApp Message</a>
                    </div>
                </div>
            `;
        });
    } catch (e) {
        console.error("Error matching emergency donors:", e);
    }
}

// REQUEST ALL (Broadcast to Everyone on WhatsApp)
function requestAllEmergencyWhatsApp() {
    if (!currentEmergencyMatches || currentEmergencyMatches.length === 0) {
        alert("No matched donors available to notify.");
        return;
    }

    const broadcastList = document.getElementById('broadcast-list');
    broadcastList.innerHTML = '';

    currentEmergencyMatches.forEach(d => {
        broadcastList.innerHTML += `
            <div class="rc-donor-item" style="display: flex; justify-content: space-between; align-items: center; padding: 14px 20px; margin-bottom: 10px;">
                <div>
                    <b>👤 ${d.name}</b> (${d.blood_group}) - <code>${d.phone}</code>
                </div>
                <div>
                    <a href="${d.wa_url}" target="_blank" class="rc-wa-button" style="padding: 6px 14px; font-size: 12px;">💬 Notify on WhatsApp</a>
                </div>
            </div>
        `;
    });

    document.getElementById('broadcast-modal').classList.add('active');
}

function closeBroadcastModal() {
    document.getElementById('broadcast-modal').classList.remove('active');
}

// Load Birthdays & Campaigns
async function loadBirthdays() {
    try {
        const res = await fetch('/api/birthdays');
        const data = await res.json();

        const todayDiv = document.getElementById('bday-today-list');
        todayDiv.innerHTML = '';
        if (!data.today || data.today.length === 0) {
            todayDiv.innerHTML = `<p class="text-muted">No donors have birthdays today.</p>`;
        } else {
            data.today.forEach(d => {
                todayDiv.innerHTML += `
                    <div style="background: #FFF8E1; border: 1px solid #FFE082; border-radius: 14px; padding: 16px; margin-bottom: 12px;">
                        <div style="font-weight: 800; font-size: 18px; color: #F57F17;">🎈 ${d.name}</div>
                        <div style="font-size: 13px; color: #424242; margin: 4px 0;">Blood Group: <b style="color:#D32F2F;">${d.blood_group}</b> | Location: <b>${d.location}</b></div>
                        <a href="${d.wa_url}" target="_blank" class="rc-wa-button" style="margin-top: 8px;">🎂 Send Birthday Wishes</a>
                    </div>
                `;
            });
        }

        const upcomingDiv = document.getElementById('bday-upcoming-list');
        upcomingDiv.innerHTML = '';
        if (!data.upcoming || data.upcoming.length === 0) {
            upcomingDiv.innerHTML = `<p class="text-muted">No upcoming birthdays in the next 7 days.</p>`;
        } else {
            data.upcoming.forEach(d => {
                upcomingDiv.innerHTML += `<p>• <b>${d.name}</b> (${d.blood_group}) - Birthday in <b>${d.days_until_bday}</b> days</p>`;
            });
        }
    } catch (e) {
        console.error("Error loading birthdays:", e);
    }
}

async function loadEvents() {
    try {
        const res = await fetch('/api/events');
        const events = await res.json();
        const grid = document.getElementById('campaigns-grid');
        grid.innerHTML = '';
        events.forEach(ev => {
            grid.innerHTML += `
                <div class="rc-card" style="text-align: center;">
                    <div style="font-size: 12px; color: #64748B; font-weight: 700;">${ev.name}</div>
                    <div style="font-size: 28px; font-weight: 900; color: #0284C7; margin: 6px 0;">${ev.days_remaining} days</div>
                    <div style="font-size: 11px; color: #94A3B8;">(${ev.date_str})</div>
                </div>
            `;
        });
    } catch (e) {
        console.error("Error loading events:", e);
    }
}

// Neo4j & File Upload Handlers
async function connectNeo4j() {
    const uri = document.getElementById('neo-uri').value;
    const user = document.getElementById('neo-user').value;
    const password = document.getElementById('neo-pwd').value;

    const msgDiv = document.getElementById('neo-status-msg');
    try {
        const res = await fetch('/api/neo4j/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ uri, user, password })
        });
        const data = await res.json();
        if (res.ok) {
            msgDiv.innerHTML = `<span style="color: green; font-weight: bold;">🟢 ${data.message}</span>`;
            loadStats();
        } else {
            msgDiv.innerHTML = `<span style="color: red;">🔴 ${data.message}</span>`;
        }
    } catch (e) {
        msgDiv.innerHTML = `<span style="color: red;">🔴 Error connecting: ${e.message}</span>`;
    }
}

async function uploadExcelFile() {
    const fileInput = document.getElementById('upload-file-input');
    if (!fileInput.files || fileInput.files.length === 0) {
        alert("Please select a file to upload.");
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const res = await fetch('/api/excel/upload', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (res.ok) {
            alert(data.message);
            loadStats();
            loadDonors();
        }
    } catch (e) {
        console.error("Error uploading excel:", e);
    }
}
