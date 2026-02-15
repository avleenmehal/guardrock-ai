import time
from typing import Optional, Callable

import requests

from models.message import VideoMessage

class ValkeyConsumer:
    """
    State-based consumer with WAIT and PROCESS states
    Supports manual message acknowledgement
    """

    def __init__(self, base_url: str, poll_interval: int = 10):
        self.base_url = base_url
        self.poll_interval = poll_interval
        self.state = "WAIT"
        self.running = False

    def _peek_message(self) -> Optional[VideoMessage]:
        """
        Peek at next message without removing from queue
        """
        url = f"{self.base_url}"

        try:
            # response = requests.get(url, timeout=5)
            response = {
                "title": "Unit Test Video",
                "uuid": "243567897",
                "url": "http://example.com/video.mp4",
                "channel_name": "unit-test-channel",
                "timestamp": "2024-06-01T12:00:00Z",
                "description": "This is a test video message for unit testing."
            }
            return VideoMessage.from_dict(response)
            if response.status_code == 200:
                data = response.json()
                return VideoMessage.from_dict(data)

            elif response.status_code == 204:
                return None

            else:
                print(f"✗ Unexpected status: {response.status_code}")
                return None

        except Exception as e:
            print(f"✗ Error peeking message: {e}")
            return None

    def _wait_state(self):
        """
        WAIT state: Poll endpoint every 10 seconds
        """
        print(f"[WAIT] Polling endpoint...")

        message = self._peek_message()

        if message:
            print(f"[WAIT] ✓ Message found: {message.uuid}")
            print(f"[WAIT] → Switching to PROCESS state")
            self.state = "PROCESS"
            return message
        else:
            print(f"[WAIT] Queue empty, waiting {self.poll_interval}s...")
            return None

    def _process_state(self, message: VideoMessage, callback: Callable):
        """
        PROCESS state: Execute callback and acknowledge
        """
        print(f"[PROCESS] Processing message: {message.uuid}")

        processing_success = False

        try:
            # Execute the processing callback
            callback(message)
            processing_success = True
            print(f"[PROCESS] ✓ Processing completed")

        except Exception as e:
            print(f"[PROCESS] ✗ Processing failed: {e}")
            processing_success = False

        finally:
            # Return to WAIT state
            print(f"[PROCESS] → Switching to WAIT state\n")
            self.state = "WAIT"

    def start(self, process_callback: Callable[[VideoMessage], None]):
        """
        Start the consumer loop

        Args:
            process_callback: Function to call when processing message
        """
        print("=" * 60)
        print("Starting Consumer")
        print(f"Poll Interval: {self.poll_interval}s")
        print("=" * 60 + "\n")

        self.running = True
        self.state = "WAIT"

        try:
            while self.running:
                if self.state == "WAIT":
                    message = self._wait_state()

                    if message:
                        # Process the message
                        self._process_state(message, process_callback)
                    # For this implementation, we will call the callback directly in the WAIT state
                    else:
                        # Sleep before next poll
                        time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            print("\n[CONSUMER] ✓ Shutting down gracefully...")
            self.running = False

    def stop(self):
        """Stop the consumer"""
        self.running = False