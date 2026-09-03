const express = require('express');
const cors = require('cors');
const qrcode = require('qrcode-terminal');
const { Client, LocalAuth } = require('whatsapp-web.js');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

let isReady = false;
let latestQR = null;

// Initialize WhatsApp Web Client with LocalAuth session persistence
const client = new Client({
    authStrategy: new LocalAuth({ dataPath: './.wwebjs_auth' }),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu'
        ]
    }
});

// Display QR code for 1-time scanning
client.on('qr', (qr) => {
    latestQR = qr;
    isReady = false;
    console.log('\n=============================================================');
    console.log('🩸 RED CROSS WEST GODAVARI — WHATSAPP WEB.JS SCAN QR CODE');
    console.log('Scan the QR code below using WhatsApp on your phone (Linked Devices):');
    console.log('=============================================================\n');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    isReady = true;
    latestQR = null;
    console.log('\n=============================================================');
    console.log('🟢 RED CROSS WHATSAPP WEB.JS ENGINE IS LIVE & READY!');
    console.log('All emergency messages will be sent automatically with 0 clicks!');
    console.log('=============================================================\n');
});

client.on('authenticated', () => {
    console.log('✓ WhatsApp Client Authenticated Successfully!');
});

client.on('auth_failure', (msg) => {
    console.error('🔴 WhatsApp Authentication Failure:', msg);
});

client.on('disconnected', (reason) => {
    isReady = false;
    console.warn('⚠️ WhatsApp Client Disconnected:', reason);
    client.initialize();
});

// Start Client
client.initialize();

// REST API Endpoints
app.get('/status', (req, res) => {
    res.json({
        ready: isReady,
        has_qr: !!latestQR,
        user: isReady && client.info ? client.info.wid.user : null
    });
});

app.post('/send-message', async (req, res) => {
    const { phone, message } = req.body;

    if (!phone || !message) {
        return res.status(400).json({ status: 'error', message: 'phone and message are required' });
    }

    if (!isReady) {
        return res.status(503).json({ 
            status: 'error', 
            message: 'WhatsApp Web.js client is not ready yet. Please scan QR code.' 
        });
    }

    try {
        const cleanDigits = phone.replace(/\D/g, '');
        const chatId = cleanDigits.length === 10 ? `91${cleanDigits}@c.us` : `${cleanDigits}@c.us`;

        console.log(`Sending message to ${chatId}...`);
        const sentMsg = await client.sendMessage(chatId, message);

        res.json({
            status: 'success',
            message: `Message sent automatically to ${phone}!`,
            msg_id: sentMsg.id._serialized
        });
    } catch (err) {
        console.error('Error sending message via whatsapp-web.js:', err);
        res.status(500).json({ status: 'error', message: err.message });
    }
});

app.post('/send-bulk', async (req, res) => {
    const { recipients } = req.body; // Array of { phone, message, name }

    if (!recipients || !Array.isArray(recipients)) {
        return res.status(400).json({ status: 'error', message: 'recipients array required' });
    }

    if (!isReady) {
        return res.status(503).json({ 
            status: 'error', 
            message: 'WhatsApp Web.js client is not ready yet. Please scan QR code.' 
        });
    }

    const results = [];
    for (let i = 0; i < recipients.length; i++) {
        const item = recipients[i];
        try {
            const cleanDigits = item.phone.replace(/\D/g, '');
            const chatId = cleanDigits.length === 10 ? `91${cleanDigits}@c.us` : `${cleanDigits}@c.us`;

            console.log(`[${i + 1}/${recipients.length}] Auto-sending to ${item.name || cleanDigits} (${chatId})...`);
            const sentMsg = await client.sendMessage(chatId, item.message);

            results.append({
                name: item.name || 'Donor',
                phone: cleanDigits,
                status: 'SENT_AUTOMATICALLY',
                msg_id: sentMsg.id._serialized
            });

            // Small 1.5s delay between messages to prevent rate-limit
            await new Promise(r => setTimeout(r, 1500));
        } catch (err) {
            console.error(`Error sending to ${item.phone}:`, err.message);
            results.append({
                name: item.name || 'Donor',
                phone: item.phone,
                status: 'FAILED',
                error: err.message
            });
        }
    }

    res.json({
        status: 'success',
        message: `Processed ${results.length} emergency notifications!`,
        results: results
    });
});

app.listen(PORT, () => {
    console.log(`🚀 Red Cross WhatsApp-Web.js Service running on port ${PORT}`);
});
