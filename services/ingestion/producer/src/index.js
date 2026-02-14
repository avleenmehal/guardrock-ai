const express = require('express');
const Redis = require('ioredis');
require('dotenv').config();

const app = express();
app.use(express.json());

// Configuration
const PORT = process.env.PORT || 3000;
const MAX_CACHE_SIZE = parseInt(process.env.MAX_CACHE_SIZE || '10', 10);
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
  const { url, channel_name, title, description, unique_id } = req.body;
  
  if (!url || !channel_name || !title || !description || !unique_id) {
    return res.status(400).json({ 
      error: 'Missing required fields',
      required: ['url', 'channel_name', 'title', 'description', 'unique_id']
    });
  }
  
  next();
};

// POST /api/submit
app.post('/api/submit', validateSubmission, async (req, res) => {
  try {
    const { url } = req.body;
    const jsonData = JSON.stringify(req.body);
    const cacheKey = `cache:${url}`;
    const timestamp = Date.now();

    // Check if URL exists in cache
    const exists = await valkey.exists(cacheKey);

    if (exists) {
      // CACHE HIT - Update LRU timestamp
      await valkey.zadd('cache_lru', timestamp, url);
      return res.status(201).json({ status: 'accepted' });
    }

    // CACHE MISS - Proceed with caching and queuing
    const cacheSize = await valkey.zcard('cache_lru');

    // Evict oldest if cache is full
    if (cacheSize >= MAX_CACHE_SIZE) {
      const oldest = await valkey.zpopmin('cache_lru', 1);
      if (oldest && oldest.length > 0) {
        const oldestUrl = oldest[0];
        await valkey.del(`cache:${oldestUrl}`);
        console.log(`Evicted from cache: ${oldestUrl}`);
      }
    }

    // Add to cache and LRU tracker
    await valkey.set(cacheKey, jsonData);
    await valkey.zadd('cache_lru', timestamp, url);

    // Add to message queue
    await valkey.lpush('message_queue', jsonData);

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
  console.log(`Max cache size: ${MAX_CACHE_SIZE}`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, closing server...');
  await valkey.quit();
  process.exit(0);
});