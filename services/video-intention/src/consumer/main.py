import sys
import os

# Add src directory to path so imports work when run from any directory
_src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from clients.twelve_labs_client import TwelveLabsClient
from config import config
from consumer.valkey_consumer import ValkeyConsumer
from models.message import VideoMessage


def main():
    """Main entry point"""
    print("Starting Video Intention Service")
    print("=" * 60)

    # Initialize clients
    valkey_consumer = ValkeyConsumer(
        base_url="http://152.7.179.59:3001/api/consume",
        poll_interval=10
    )

    twelve_labs_client = TwelveLabsClient(api_key=config.twelve_labs.api_key,index_id="69911c19f20ac9cd89a7b61b")

    print("✓ Clients initialized")
    print("=" * 60 + "\n")

    # Define callback function for each message
    def message_callback(message: VideoMessage):
        result = twelve_labs_client.process_message(message)

        if result:
            print("\n" + "=" * 60)
            print("ANALYSIS RESULT")
            print("=" * 60)
            print(result['analysis_text'])
            print("=" * 60 + "\n")

            # TODO: Parse analysis, calculate scores, call fact-checker
        else:
            print("\n✗ Failed to process video\n")

    # Start consuming messages
    try:
        valkey_consumer.start(message_callback)
    finally:
        valkey_consumer.stop()


if __name__ == "__main__":
    main()