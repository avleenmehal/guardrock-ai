from twelvelabs import TwelveLabs
import time
import os
import sys
import requests
from typing import Optional, Dict, Any
from models.message import VideoMessage

# Add project root to path so we can import download_yt
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from download_yt import download_youtube_short

DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "downloads")


class TwelveLabsClient:
    """Client for Twelve Labs API using official SDK"""

    def __init__(self, api_key: str, index_id: str):
        self.client = TwelveLabs(api_key=api_key)
        self.index_id = index_id
        print(f"[TWELVE_LABS] Client initialized, index: {index_id}")

    def index_video_file(self, file_path: str) -> Optional[Any]:
        """Upload a local video file for indexing. Returns a Task object."""
        print(f"[TWELVE_LABS] Uploading {file_path} ...")

        if not os.path.isfile(file_path):
            print(f"[TWELVE_LABS] File not found: {file_path}")
            return None

        try:
            with open(file_path, 'rb') as video_file:
                task = self.client.tasks.create(
                    index_id=self.index_id,
                    video_file=video_file,
                )
            print(f"[TWELVE_LABS] Uploaded — task {task.id}")
            return task
        except Exception as e:
            print(f"[TWELVE_LABS] Upload failed: {e}")
            return None

    def wait_for_indexing(self, task: Any) -> Optional[str]:
        """Wait for video indexing to complete. Returns video_id."""
        task_id = task.id
        print(f"[TWELVE_LABS] Waiting for indexing (task {task_id}) ...")
        start_time = time.time()

        try:
            while True:
                updated = self.client.tasks.retrieve(task_id)
                status = updated.status
                print(f"[TWELVE_LABS]   [{int(time.time() - start_time)}s] {status}")

                if status == "ready":
                    video_id = updated.video_id
                    print(f"[TWELVE_LABS] Indexing done — video_id={video_id} ({int(time.time() - start_time)}s)")
                    return video_id

                if status == "failed":
                    print(f"[TWELVE_LABS] Indexing failed")
                    return None

                time.sleep(10)
        except Exception as e:
            print(f"[TWELVE_LABS] Indexing error: {e}")
            return None

    def analyze_video(self, video_id: str, prompt: str) -> Optional[str]:
        """Analyze an indexed video. Returns the analysis text."""
        print(f"[TWELVE_LABS] Analyzing video {video_id} ...")
        try:
            result = self.client.analyze(video_id=video_id, prompt=prompt)
            print(f"[TWELVE_LABS] Analysis done ({len(result.data)} chars)")
            return result.data
        except Exception as e:
            print(f"[TWELVE_LABS] Analysis failed: {e}")
            return None

    def _download_video(self, url: str, video_id: str) -> Optional[str]:
        """Download the video. Uses direct HTTP for supa- IDs, yt-dlp otherwise."""
        # Check if already downloaded
        for ext in ("mp4", "mov", "avi", "mkv", "webm"):
            path = os.path.join(DOWNLOADS_DIR, f"{video_id}.{ext}")
            if os.path.isfile(path):
                print(f"[TWELVE_LABS] Already downloaded: {path}")
                return path

        if video_id.startswith("supa-"):
            storage_url = f"https://mhzwvjyvhevawbrhmmtp.supabase.co/storage/v1/object/public/videos/{video_id}.mp4"                        
            return self._download_from_url(storage_url, video_id)   

        print(f"[TWELVE_LABS] Downloading {url} ...")
        result = download_youtube_short(url, output_path=DOWNLOADS_DIR, filename=video_id)
        if result and os.path.isfile(result):
            return result
        return None

    def _download_from_url(self, url: str, video_id: str) -> Optional[str]:
        """Download a video directly from a public URL."""
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)
        file_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.mp4")
        print(f"[TWELVE_LABS] Downloading from public URL: {url} ...")
        try:
            resp = requests.get(url, stream=True, timeout=120)
            resp.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"[TWELVE_LABS] Downloaded: {file_path}")
            return file_path
        except requests.RequestException as e:
            print(f"[TWELVE_LABS] Direct download failed: {e}")
            return None

    def process_message(self, message: VideoMessage) -> Optional[Dict]:
        """Download, index, and analyze a video."""
        print(f"\n{'=' * 60}")
        print(f"[TWELVE_LABS] Processing: {message.title} ({message.unique_id})")
        print(f"{'=' * 60}\n")

        # Step 1: Download the video from YouTube
        file_path = self._download_video(message.url, message.unique_id)
        if not file_path:
            print(f"[TWELVE_LABS] Failed to download video: {message.url}")
            return None

        # Step 2: Upload and index
        task = self.index_video_file(file_path)
        if not task:
            return None

        # Step 3: Wait for indexing
        video_id = self.wait_for_indexing(task)
        if not video_id:
            return None

        # Step 4: Analyze
        analysis_text = self.analyze_video(video_id, self._get_analysis_prompt())
        if not analysis_text:
            return None

        print(f"\n[TWELVE_LABS] Processing complete\n")

        return {
            'video_uuid': message.unique_id,
            'video_id': video_id,
            'task_id': task.id,
            'file_path': file_path,
            'analysis_text': analysis_text,
            'metadata': {
                'title': message.title,
                'channel': message.channel_name,
                'description': message.description,
                'timestamp': str(message.timestamp)
            }
        }

    def _get_analysis_prompt(self) -> str:
        return """ #Context:
        You are a video analyst specializing in detecting AI generated content, manipulation, urgency tactics, and deception in video content to prevent 
        users from taking sensitive action. AI generated content can be highly realistic and may use sophisticated techniques to mimic human speech, facial expressions, and mannerisms.
        At the same time, not all videos discuss sensitive topics or contain manipulation — many are safe and informative. Your task is to carefully
         analyze the video content, including the speaker's intent, language, tone, and visual cues, to determine if there are any signs of manipulation, misinformation, or urgent calls to action that might indicate the video is trying to mislead viewers or push them towards a harmful action.
         
        #Instruction: Your task is to analyze the video and look for any signs of manipulation, spreading misinformation, 
        or urgent calls to action that might indicate the video is trying to mislead viewers or push them towards a harmful action.
        If the video is not AI generated, you can mark it safe. 
        
        Before answering:
        1. Identify whether the speaker is real or synthetically generated through AI.
        2. Look for audio-video sync mismatches.
        3. Evaluate unnatural facial micro-expressions.
        4. Determine speaker intent (informational, persuasive, manipulative, threatening).
        5. Output scores from 0–10 and justification.

**Look for the following indicators:**

1. **Manipulation Tactics:**
   - Emotional appeals (fear, anger, shock, outrage)
   - Loaded or inflammatory language
   - One-sided arguments without acknowledging counterpoints
   - Misuse of authority ("experts say" without sources)
   - "Us vs. them" divisive rhetoric
   - Exaggerated claims or hyperbole
   - Cherry-picking facts or taking things out of context

2. **Urgency Indicators:**
   - Time pressure language ("act now", "limited time", "before it's too late")
   - Consequence threats ("if you don't act", "they're coming for you")
   - Breaking news framing or urgent calls to action
   - Immediacy language ("urgent", "critical", "must watch")

3. **Credibility Concerns:**
   - Unverified claims presented as facts
   - Missing or vague sources
   - Conspiracy theory language
   - Claims that "they don't want you to know this"

**Provide the following in your analysis:**

1. **AI Generation Indicators:** Note any signs that the speaker may be AI-generated (e.g., audio-video sync issues, unnatural expressions)
2. **Manipulation Score (0-10):** Rate the overall level of manipulative tactics used
3. **Urgency Score (0-10):** Rate the level of urgency and time pressure
4. **Key Phrases:** List specific phrases or statements that demonstrate manipulation or urgency
5. **Summary:** Brief overview of the video's main argument or message
6. **Red Flags:** Any specific concerns that warrant fact-checking

Be specific and quote exact phrases from the video when possible."""