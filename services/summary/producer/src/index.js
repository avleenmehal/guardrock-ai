const express = require('express');
const Redis = require('ioredis');
const cors = require('cors');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

// Configuration
const PORT = process.env.PORT || 3000;
const VALKEY_HOST = process.env.VALKEY_HOST || 'localhost';
const VALKEY_PORT = parseInt(process.env.VALKEY_PORT || '6379', 10);

// Valkey client
const valkey = new Redis({
  host: VALKEY_HOST,
  port: VALKEY_PORT,
  retryStrategy: (times) => {
    const delay = Math.min(times * 50, 2000);
    return delay;
  }
});

valkey.on('error', (err) => console.error('Valkey Error:', err));
valkey.on('connect', () => console.log('Connected to Valkey'));

// Validation middleware
const validateSubmission = (req, res, next) => {
  const { channel_name, title, unique_id, summary } = req.body;
  
  console.log('Received:', req.body);
  
  if (!channel_name || !title || !unique_id || !summary) {
    return res.status(400).json({ 
      error: 'Missing required fields',
      required: ['channel_name', 'title', 'unique_id', 'summary']
    });
  }
  
  next();
};

// POST /api/submit
app.post('/api/submit', validateSubmission, async (req, res) => {
  try {
    const jsonData = JSON.stringify(req.body);

    // Add to message queue
    await valkey.lpush('message_queue', jsonData);

    console.log('Message queued:', req.body.unique_id);
    res.status(201).json({ status: 'accepted' });
  } catch (error) {
    console.error('Error processing submission:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Health check
app.get('/health', async (req, res) => {
  try {
    await valkey.ping();
    res.json({ status: 'healthy', valkey: 'connected' });
  } catch (error) {
    res.status(503).json({ status: 'unhealthy', valkey: 'disconnected' });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`Producer API running on port ${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, closing server...');
  await valkey.quit();
  process.exit(0);
});