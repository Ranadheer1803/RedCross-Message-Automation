// RED CROSS WEST GODAVARI - Frontend Application JavaScript

document.addEventListener("DOMContentLoaded", () => {
    loadStats();
    loadDonors();
    loadEvents();
    loadBirthdays();
});

// Tab Switching Logic
function switchTab(tabId) {
    document.querySelectorAll('.rc-tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.rc-tab-content').forEach(content => content.classList.remove('active'));

    event.target.classList.add('active');
    document.getElementById(tabId).classList.add('active');

    if (tabId === 'tab-registry') loadDonors();
    if (tabId === 'tab-emergency') matchEmergencyDonors();
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

        // Render Blood Group Inventory Chips
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

// Load Donors Table
async function loadDonors() {
    const search = document.getElementById('search-input').value;
    const bg = document.getElementById('filter-bg').value;
    const eligibility = document.getElementById('filter-eligibility').value;

    const query = new URLSearchParams({ search, blood_group: bg, eligibility });
    try {
        const res = await fetch(`/api/donors?${query}`);
        const donors = await res.json();

        const tbody = document.getElementById('donors-table-body');
        tbody.innerHTML = '';

        if (!donors || donors.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" style="text-align: center; padding: 32px; color: #64748B;">
                        No donors registered yet. Click <b>➕ Add First / New Member</b> above to register!
                    </td>
                </tr>
            `;
            return;
        }

        donors.forEach(d => {
            const waUrl = `https://api.whatsapp.com/send?phone=${d.phone.replace(/\D/g, '')}&text=${encodeURIComponent(`Hello ${d.name}, Red Cross West Godavari Branch greeting!`)}`;
            tbody.innerHTML += `
                <tr>
                    <td><b>${d.name}</b></td>
                    <td><code>${d.phone}</code></td>
                    <td><b style="color: #D32F2F;">${d.blood_group}</b></td>
                    <td>${d.age || 'N/A'}</td>
                    <td>${d.dob || '-'}</td>
                    <td>${d.last_donation || '-'}</td>
                    <td><span class="rc-values-pill" style="font-size: 11px;">${d.eligibility_status}</span></td>
                    <td>${d.location || 'General'}</td>
                    <td>
                        <button class="rc-btn rc-btn-outline" style="padding: 4px 10px; font-size: 12px;" onclick="openEditModal('${d.phone}')">✏️ Edit</button>
                        <button class="rc-btn rc-btn-outline" style="padding: 4px 10px; font-size: 12px; color: #D32F2F;" onclick="deleteDonor('${d.phone}', '${d.name}')">🗑️ Delete</button>
                        <a href="${waUrl}" target="_blank" class="rc-btn rc-btn-red" style="padding: 4px 10px; font-size: 12px;">💬 WhatsApp</a>
                    </td>
                </tr>
            `;
        });
    } catch (e) {
        console.error("Error loading donors:", e);
    }
}

// Modal Form Handlers
function openAddModal() {
    document.getElementById('modal-title').innerText = "➕ Add Member Record";
    document.getElementById('donor-form').reset();
    document.getElementById('edit-original-phone').value = "";
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
            document.getElementById('form-dob').value = d.dob || "";
            document.getElementById('form-last-donation').value = d.last_donation || "";
            document.getElementById('form-location').value = d.location || "Eluru, West Godavari";
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
    const donorData = {
        name: document.getElementById('form-name').value,
        phone: document.getElementById('form-phone').value,
        blood_group: document.getElementById('form-bg').value,
        dob: document.getElementById('form-dob').value,
        last_donation: document.getElementById('form-last-donation').value,
        location: document.getElementById('form-location').value,
        email: ""
    };

    try {
        let res;
        if (originalPhone) {
            // Update
            res = await fetch(`/api/donors/${originalPhone}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(donorData)
            });
        } else {
            // Create
            res = await fetch('/api/donors', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(donorData)
            });
        }
        
        if (res.ok) {
            closeModal();
            loadStats();
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

// Match Emergency Donors
async function matchEmergencyDonors() {
    const bg = document.getElementById('em-bg-select').value;
    const hospital = document.getElementById('em-hospital').value;
    const urgency = document.getElementById('em-urgency').value;

    try {
        const res = await fetch(`/api/emergency?blood_group=${bg}&hospital=${encodeURIComponent(hospital)}&urgency=${urgency}`);
        const data = await res.json();

        document.getElementById('em-matched-count').innerText = data.count;
        const listDiv = document.getElementById('em-matched-list');
        listDiv.innerHTML = '';

        if (!data.donors || data.donors.length === 0) {
            listDiv.innerHTML = `<div class="rc-card"><p class="text-muted">No matching donors registered for blood group ${bg}.</p></div>`;
            return;
        }

        data.donors.forEach(d => {
            listDiv.innerHTML += `
                <div class="rc-donor-item" style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 18px; font-weight: 800;">👤 ${d.name} <span style="color: #64748B; font-size: 13px;">(Age: ${d.age || 'N/A'})</span></div>
                        <div style="font-size: 13px; color: #475569; margin-top: 4px;">
                            🩸 Blood Group: <b style="color: #D32F2F;">${d.blood_group}</b> | 📍 Location: <b>${d.location || 'General'}</b> | ⏳ Status: <code>${d.eligibility_status || 'Eligible'}</code>
                        </div>
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
