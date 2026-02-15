# GuardRock AI

**Deployment URLs**

Frontend - http://152.7.178.231/

Video Upload service - http://152.7.178.231/upload.html


**Defending minds from manipulative content, one short video at a time.**

In the age of AI-generated content, short-form videos have become a powerful vehicle for manipulation. They create false urgency, exploit emotions, and push people toward impulsive decisions -- all within 60 seconds. GuardRock AI is a real-time  system that detects deceptive and manipulative patterns in short videos and warns users before they fall for it.

---

## The Problem

Short-form video platforms are flooded with content designed to manipulate. These videos use fear-based language, fake urgency, emotional triggers, and misleading claims to push viewers into action -- whether that's sharing misinformation, buying a scam product, or simply living in a state of manufactured panic.

The worst part? Most people don't realize they're being manipulated. The content feels real. It feels urgent. And by the time you think twice, you've already shared it.

---

## What GuardRock AI Does

We built **a web platform** where users can upload and browse videos through a content filter. You choose what risk level you're comfortable seeing -- safe, vulnerable, or risky -- and the platform only shows you content that matches your preference.

Also, we **extended** this to a **browser extension** that monitors your YouTube Shorts feed in real-time and overlays a risk assessment directly on the video you're watching. Think of it as a manipulation detector sitting right on your shoulder.


Behind both of these is a **distributed pipeline** that analyzes videos using Twelve Labs' multimodal video AI that actually processes the video, scores them for manipulation and urgency, and delivers results back to the user in seconds.

---

## How It Works (The Big Picture)

The system is a chain of services that talk to each other through message queues. Here's the human-readable version of what happens:

### When you're browsing YouTube Shorts (Extension Flow)

```
You watch a Short on YouTube
        |
        v
Browser extension detects you've been watching for 3+ seconds
        |
        v
It grabs the video's title, channel name, and ID
        |
        v
Sends it to our Ingestion Service
        |
        v
Ingestion checks: "Have we seen this before?"
   - Yes -> Skip (no duplicate work)
   - No  -> Drop it into the processing queue
        |
        v
Video Intention Service picks it up from the queue
        |
        v
Uploads it to Twelve Labs for deep video analysis
        |
        v
Twelve Labs returns a detailed breakdown:
manipulation tactics, urgency indicators, credibility concerns
        |
        v
We pass that analysis to OpenAI to generate a clean risk summary
with a score from 1-10
        |
        v
Result gets pushed to the Summary Service queue
        |
        v
Browser extension polls for results and overlays
the risk badge right on the YouTube page
        |
        v
You see: "⚠ High Risk (8/10)" or nothing if it's safe
```

### When you upload a video on the platform (Web App Flow)

```
User uploads a video through the web app
        |
        v
Video file goes to Supabase Storage
Metadata goes to Supabase Database
        |
        v
Metadata also gets sent to the Ingestion Service
        |
        v
Same pipeline kicks in -- download, analyze, score
        |
        v
Results get written back to Supabase directly
        |
        v
Web app displays the video with its risk level
Users can filter by: Safe (0-3) | Vulnerable (4-7) | Risky (8-10)
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          GUARDROCK AI                                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐         ┌─────────────────────────────────────┐    │
│  │   Browser    │ POST    │         INGESTION SERVICE           │    │
│  │  Extension   │--------→│  Producer ──→ [Valkey Queue] ──→ Sub│    │
│  │  (Chrome)    │         └──────────────────────┬──────────────┘    │
│  └──────┬───────┘                                │                   │
│         │                                        │ polls             │
│         │                                        v                   │
│         │                        ┌───────────────────────────────┐   │
│         │                        │    VIDEO INTENTION SERVICE     │   │
│         │                        │                               │   │
│         │                        │  1. Upload to Twelve Labs     │   │
│         │                        │  2. Wait for AI analysis      │   │
│         │                        │  3. Get risk score (OpenAI)   │   │
│         │                        └──────────────┬────────────────┘   │
│         │                                       │                    │
│         │                    ┌──────────────────┬┴────────────────┐  │
│         │                    │ YouTube IDs      │ Uploaded Videos  │  │
│         │                    v                  v                  │  │
│         │    ┌──────────────────────┐   ┌──────────────┐         │  │
│         │    │   SUMMARY SERVICE    │   │   Supabase    │         │  │
│         │    │ Producer→[Valkey]→Sub│   │  (Database +  │         │  │
│  polls  │    └──────────┬───────────┘   │   Storage)    │         │  │
│         │               │               └──────┬───────┘         │  │
│         v               v                      │                  │  │
│  ┌──────────────┐  ┌────────┐                  │                  │  │
│  │  Risk Badge   │  │Overlay │           ┌─────┴──────┐          │  │
│  │  on YouTube   │  │ on UI  │           │  Web App    │          │  │
│  └──────────────┘  └────────┘           │  (Filter +  │          │  │
│                                          │  Upload)    │          │  │
│                                          └────────────┘          │  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Services Breakdown

### `/services/extension` -- Browser Extension (Chrome)
The eyes of the system. A Manifest V3 Chrome extension that runs on YouTube Shorts pages. It watches what you watch -- after 3 seconds on a Short, it extracts metadata and ships it to the backend. It also continuously polls for analysis results and renders a sleek overlay card showing the risk level, summary, and channel info right on top of YouTube.

### `/services/ingestion` -- Ingestion Service (Node.js + Valkey)
The front door. Two components -- a **Producer** that accepts video metadata and queues it, and a **Subscriber** that lets downstream services consume from the queue. It uses Valkey (Redis-compatible in-memory store) as the message broker. Has a built-in LRU cache to avoid processing the same video twice.

### `/services/video-intention` -- Video Intention Service (Python)
The brain. This is where the real analysis happens. It polls the ingestion queue, uploads it to **Twelve Labs** for multimodal video understanding (the AI literally watches the video -- analyzing speech, visuals, text overlays, tone, everything), then takes that rich analysis and passes it to **OpenAI** to distill it into a clean risk summary with a 1-10 score. Results are routed either back to the summary queue (for extension users) or directly to Supabase (for platform uploads).

### `/services/summary` -- Summary Service (Node.js + Valkey)
The delivery system. Same producer-subscriber pattern as ingestion, but for outbound results. The browser extension polls this service to pick up analyzed risk summaries and display them to the user.

### `/services/application` -- Web Application (Vanilla JS + Supabase)
The platform. A clean, mobile-first web app where users can browse analyzed videos in a vertical scrolling feed (think TikTok-style). Videos are tagged with risk levels and users can filter by safety preference. Also includes an upload page for submitting new videos to the analysis pipeline.

### `/services/fact-checker` -- Fact Checker (Foundation)
Groundwork for a future fact-checking layer that cross-references claims made in videos against trusted sources.

---

## Why Twelve Labs?

Most "video analysis" tools just look at titles and thumbnails. That's surface-level. **Twelve Labs provides multimodal video understanding** -- it processes the actual video content including speech, on-screen text, visual cues, tone of voice, and scene context. This is critical because manipulative content often *looks* legitimate in its metadata but reveals itself through emotional speech patterns, urgent visual cues, and misleading on-screen text.

Our analysis prompt instructs Twelve Labs to look for:
- **Manipulation tactics**: emotional appeals, loaded language, "us vs. them" rhetoric, misuse of authority
- **Urgency indicators**: time pressure language, consequence threats, "breaking news" framing
- **Credibility concerns**: unverified claims presented as facts, conspiracy language, missing sources

This is the kind of analysis you can only do by actually watching the video.

---

## Why Valkey?

We use **Valkey** (an open-source Redis-compatible in-memory data store) as the backbone for inter-service communication. Two separate Valkey instances power two independent message queues:

1. **Ingestion Queue**: Buffers incoming video metadata between the extension/platform and the analysis pipeline
2. **Summary Queue**: Buffers completed risk assessments for delivery back to the extension

Valkey gives us:
- **Decoupled services**: The extension doesn't wait for analysis to finish. It fires and forgets. Results arrive asynchronously.
- **LRU caching**: The ingestion producer maintains a least-recently-used cache so duplicate videos are detected and skipped instantly.
- **Atomic operations**: LPUSH/RPOP gives us reliable FIFO queue behavior without race conditions.
- **Speed**: In-memory operations mean sub-millisecond queue operations, which matters when you're processing videos in real-time as someone scrolls.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Browser Extension | Chrome Manifest V3, Vanilla JS |
| Message Queues | Valkey (Redis-compatible) |
| Ingestion & Summary Services | Node.js, Express, ioredis |
| Video Analysis | Twelve Labs (multimodal video AI) |
| Risk Scoring | OpenAI GPT-4o-mini |
| Database & Storage | Supabase (PostgreSQL + Object Storage) |
| Frontend | Vanilla JS, CSS (mobile-first) |
| Containerization | Docker, Docker Compose |

---

## Project Structure

```
guardrock-ai/
├── services/
│   ├── extension/          # Chrome browser extension
│   │   ├── manifest.json
│   │   ├── background.js   # Message relay & API communication
│   │   ├── content.js      # YouTube DOM scraping & overlay UI
│   │   └── popup.html/js   # Extension toggle UI
│   │
│   ├── ingestion/          # Video metadata intake & queuing
│   │   ├── producer/       # Accepts submissions, manages LRU cache
│   │   ├── subscriber/     # Serves queued messages to consumers
│   │   └── docker-compose.yml
│   │
│   ├── video-intention/    # Core analysis engine
│   │   ├── src/
│   │   │   ├── clients/    # Twelve Labs SDK integration
│   │   │   ├── consumer/   # Valkey queue consumer + main pipeline
│   │   │   ├── models/     # Message data models
│   │   │   └── risk_analyser/  # OpenAI risk scoring
│   │   └── Dockerfile
│   │
│   ├── summary/            # Risk summary delivery & queuing
│   │   ├── producer/       # Accepts analyzed results
│   │   ├── subscriber/     # Serves results to extension
│   │   └── docker-compose.yml
│   │
│   ├── application/        # Web platform (video feed + upload)
│   │   ├── index.html      # Filtered video feed
│   │   ├── upload.html     # Video submission page
│   │   └── config.js       # Supabase configuration
│   │
│   └── fact-checker/       # Future fact-checking integration
│
├── LICENSE
└── README.md
```

---

## Team

Built by **Avleen Singh Mehal**, **Dhruv Soni**, and **Sweekar Burji**.

---

## License

MIT
