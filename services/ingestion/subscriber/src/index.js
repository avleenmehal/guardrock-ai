const express = require('express');
const Redis = require('ioredis');
const cors = require('cors');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

// Configuration
const PORT = process.env.PORT || 3001;
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

// GET /api/consume
app.get('/api/consume', async (req, res) => {
  try {
    // RPOP - get and remove from queue atomically
    const data = await valkey.rpop('message_queue');

    if (!data) {
      // Queue is empty
      return res.status(204).send();
    }

    // Parse and return the JSON
    const parsedData = JSON.parse(data);
    res.status(200).json(parsedData);
  } catch (error) {
    console.error('Error consuming message:', error);
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

// Get queue stats (optional, useful for debugging)
app.get('/api/stats', async (req, res) => {
  try {
    const queueLength = await valkey.llen('message_queue');
    res.json({ 
      queue_length: queueLength,
      status: 'active'
    });
  } catch (error) {
    console.error('Error getting stats:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`Subscriber API running on port ${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, closing server...');
  await valkey.quit();
  process.exit(0);
});