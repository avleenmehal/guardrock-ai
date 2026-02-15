from twelvelabs import TwelveLabs
import time
import os
import glob
from typing import Optional, Dict, Any
from models.message import VideoMessage

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
            print(f"[TWELVE_LABS] Uploaded — task {task.id} ({task.status})")
            return task
        except Exception as e:
            print(f"[TWELVE_LABS] Upload failed: {e}")
            return None

    def wait_for_indexing(self, task: Any) -> Optional[str]:
        """Wait for video indexing to complete. Returns video_id."""
        print(f"[TWELVE_LABS] Waiting for indexing (task {task.id}) ...")
        start_time = time.time()

        try:
            def on_progress(t):
                print(f"[TWELVE_LABS]   [{int(time.time() - start_time)}s] {t.status}")

            task.wait_for_done(sleep_interval=10, callback=on_progress)

            if task.status == "ready":
                print(f"[TWELVE_LABS] Indexing done — video_id={task.video_id} ({int(time.time() - start_time)}s)")
                return task.video_id

            print(f"[TWELVE_LABS] Indexing ended with status: {task.status}")
            return None
        except Exception as e:
            print(f"[TWELVE_LABS] Indexing error: {e}")
            return None

    def analyze_video(self, video_id: str, prompt: str) -> Optional[str]:
        """Analyze an indexed video. Returns the analysis text."""
        print(f"[TWELVE_LABS] Analyzing video {video_id} ...")
        try:
            result = self.client.generate.text(video_id=video_id, prompt=prompt)
            print(f"[TWELVE_LABS] Analysis done ({len(result.data)} chars)")
            return result.data
        except Exception as e:
            print(f"[TWELVE_LABS] Analysis failed: {e}")
            return None

    def _find_video_file(self) -> Optional[str]:
        """Return the first video file found in the downloads folder."""
        for ext in ("*.mp4", "*.mov", "*.avi", "*.mkv", "*.webm"):
            matches = glob.glob(os.path.join(DOWNLOADS_DIR, ext))
            if matches:
                return matches[0]
        return None

    def process_message(self, message: VideoMessage) -> Optional[Dict]:
        """Index a local video file, wait for indexing, and analyze it."""
        print(f"\n{'=' * 60}")
        print(f"[TWELVE_LABS] Processing: {message.title} ({message.unique_id})")
        print(f"{'=' * 60}\n")

        # Step 1: Find the downloaded video file
        file_path = self._find_video_file()
        if not file_path:
            print(f"[TWELVE_LABS] No video file found in {DOWNLOADS_DIR}")
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
        return """Analyze this video for signs of manipulation and urgency that might indicate misinformation or misleading content.

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

1. **Manipulation Score (0-10):** Rate the overall level of manipulative tactics used
2. **Urgency Score (0-10):** Rate the level of urgency and time pressure
3. **Key Phrases:** List specific phrases or statements that demonstrate manipulation or urgency
4. **Summary:** Brief overview of the video's main argument or message
5. **Red Flags:** Any specific concerns that warrant fact-checking

Be specific and quote exact phrases from the video when possible."""