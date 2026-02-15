# clients/twelve_labs.py
from twelvelabs import TwelveLabs
import time
import tempfile
import os
import shutil
import yt_dlp
from typing import Optional, Dict, Any
from models.message import VideoMessage


class TwelveLabsClient:
    """Client for Twelve Labs API using official SDK"""

    def __init__(self, api_key: str, index_id: str):
        """
        Initialize Twelve Labs client

        Args:
            api_key: Your Twelve Labs API key
            index_id: Existing index ID from Twelve Labs UI
        """
        self.client = TwelveLabs(api_key=api_key)
        self.index_id = index_id

        print("[TWELVE_LABS] Client initialized")
        print(f"[TWELVE_LABS] Using index: {index_id}")

    def index_youtube_video(self, youtube_url: str, video_uuid: str) -> Optional[Any]:
        """
        Submit a YouTube video URL for indexing

        The video is processed and stored on Twelve Labs server, then indexed.

        Args:
            youtube_url: YouTube video URL (e.g., https://www.youtube.com/watch?v=...)
            video_uuid: UUID to track this video

        Returns:
            Task object if successful, None otherwise
        """

        print(f"[TWELVE_LABS] Submitting YouTube video for indexing...")
        print(f"[TWELVE_LABS]   UUID: {video_uuid}")
        print(f"[TWELVE_LABS]   YouTube URL: {youtube_url}")

        tmp_path = None
        try:
            # Get a unique temp path, then delete the empty file so yt-dlp
            # can create it fresh (otherwise yt-dlp skips an already-existing file)
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                tmp_path = tmp.name
            os.remove(tmp_path)

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'best[ext=mp4]/best',
                'outtmpl': tmp_path,
                'cookiesfrombrowser': ('chrome',),  # use your logged-in Chrome session
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                title = info.get('title', 'unknown')

            file_size = os.path.getsize(tmp_path)
            print(f"[TWELVE_LABS]   Downloaded: {title}")
            print(f"[TWELVE_LABS]   File size: {file_size} bytes")

            if file_size == 0:
                raise ValueError("Downloaded file is empty")

            with open(tmp_path, 'rb') as video_file:
                task = self.client.tasks.create(
                    index_id=self.index_id,
                    video_file=video_file,
                )

            print(f"[TWELVE_LABS] ✓ YouTube video submitted successfully")
            print(f"[TWELVE_LABS]   Task ID: {task.id}")
            print(f"[TWELVE_LABS]   Status: {task.status}")

            return task

        except Exception as e:
            print(f"[TWELVE_LABS] ✗ Failed to submit YouTube video: {e}")
            print(f"[TWELVE_LABS]   Error type: {type(e).__name__}")
            return None

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
                print(f"[TWELVE_LABS]   Temp file cleaned up")

    def wait_for_indexing(self, task: Any, max_wait_seconds: int = 600) -> Optional[str]:
        """
        Wait for video indexing to complete

        Args:
            task: Task object from index_youtube_video
            max_wait_seconds: Maximum time to wait (default: 600s = 10min)

        Returns:
            video_id if successful, None if failed or timeout
        """
        print(f"[TWELVE_LABS] Waiting for indexing to complete...")
        print(f"[TWELVE_LABS]   Task ID: {task.id}")
        print(f"[TWELVE_LABS]   Max wait: {max_wait_seconds}s")

        start_time = time.time()

        try:
            # Define callback to show progress
            def progress_callback(t):
                elapsed = int(time.time() - start_time)
                print(f"[TWELVE_LABS]   [{elapsed}s] Status: {t.status}")

            # Wait for task to complete with progress updates
            task.wait_for_done(
                sleep_interval=10,
                callback=progress_callback
            )

            elapsed = int(time.time() - start_time)

            if task.status == "ready":
                video_id = task.video_id
                print(f"[TWELVE_LABS] ✓ Indexing completed!")
                print(f"[TWELVE_LABS]   Video ID: {video_id}")
                print(f"[TWELVE_LABS]   Total time: {elapsed}s")
                return video_id
            else:
                print(f"[TWELVE_LABS] ✗ Indexing failed with status: {task.status}")
                return None

        except Exception as e:
            print(f"[TWELVE_LABS] ✗ Error during indexing: {e}")
            print(f"[TWELVE_LABS]   Error type: {type(e).__name__}")
            return None

    def analyze_video(self, video_id: str, prompt: str) -> Optional[str]:
        """
        Analyze the indexed video using Twelve Labs generate endpoint

        Args:
            video_id: The Twelve Labs video ID
            prompt: Analysis prompt

        Returns:
            Analysis text from the model, None if failed
        """
        print(f"[TWELVE_LABS] Analyzing video...")
        print(f"[TWELVE_LABS]   Video ID: {video_id}")
        print(f"[TWELVE_LABS]   Prompt length: {len(prompt)} chars")

        try:
            result = self.client.generate.text(
                video_id=video_id,
                prompt=prompt
            )

            analysis_text = result.data

            print(f"[TWELVE_LABS] ✓ Analysis completed")
            print(f"[TWELVE_LABS]   Response length: {len(analysis_text)} chars")

            return analysis_text

        except Exception as e:
            print(f"[TWELVE_LABS] ✗ Failed to analyze video: {e}")
            print(f"[TWELVE_LABS]   Error type: {type(e).__name__}")
            return None

    def process_message(self, message: VideoMessage) -> Optional[Dict]:
        """
        Complete workflow for YouTube video analysis

        Args:
            message: VideoMessage from the queue containing YouTube URL

        Returns:
            Dict with analysis results, None if any step fails
        """
        print(f"\n{'=' * 60}")
        print(f"[TWELVE_LABS] Starting YouTube video processing")
        print(f"{'=' * 60}")
        print(f"  UUID: {message.unique_id}")
        print(f"  Title: {message.title}")
        print(f"  Channel: {message.channel_name}")
        print(f"  YouTube URL: {message.url}")
        print(f"  Timestamp: {message.timestamp}")
        print(f"{'=' * 60}\n")

        # Step 1: Submit YouTube video URL for indexing
        task = self.index_youtube_video(message.url, message.unique_id)
        if not task:
            print(f"[TWELVE_LABS] ✗ Failed to submit YouTube video for indexing")
            return None

        # Step 2: Wait for video to be downloaded, processed, and indexed
        video_id = self.wait_for_indexing(task, max_wait_seconds=600)
        if not video_id:
            print(f"[TWELVE_LABS] ✗ Video indexing did not complete successfully")
            return None

        # Step 3: Analyze the indexed video
        analysis_prompt = self._get_analysis_prompt()
        analysis_text = self.analyze_video(video_id, analysis_prompt)

        if not analysis_text:
            print(f"[TWELVE_LABS] ✗ Failed to analyze video")
            return None

        # Step 4: Return complete result
        result = {
            'video_uuid': message.unique_id,
            'video_id': video_id,
            'task_id': task.id,
            'youtube_url': message.url,
            'analysis_text': analysis_text,
            'metadata': {
                'title': message.title,
                'channel': message.channel_name,
                'description': message.description,
                'timestamp': str(message.timestamp)
            }
        }

        print(f"\n{'=' * 60}")
        print(f"[TWELVE_LABS] ✓ YouTube video processing completed successfully")
        print(f"{'=' * 60}\n")

        return result

    def _get_analysis_prompt(self) -> str:
        """
        Get the analysis prompt for intention detection

        Returns:
            Formatted prompt string
        """
        prompt = """Analyze this video for signs of manipulation and urgency that might indicate misinformation or misleading content.

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

        return prompt