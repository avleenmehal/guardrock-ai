from consumer.valkey_consumer import ValkeyConsumer
from models.message import VideoMessage


def process_message(message: VideoMessage):
    """
    This is where your Twelve Labs processing will go
    For now, just simulate work
    """
    print(f"  Title: {message.title}")
    print(f"  URL: {message.url}")
    print(f"  Channel: {message.channel_name}")

    # Simulate processing
    import time
    print("  [Simulating indexing...]")
    time.sleep(2)
    print("  [Simulating analysis...]")
    time.sleep(1)
    print("  ✓ Done!")


def main():
    # Version A/B (REST API)
    consumer = ValkeyConsumer(
        base_url="http://localhost:8080/api/queue/video-ingestion",
        poll_interval=10
    )
    consumer.start(process_message)


if __name__ == "__main__":
    main()