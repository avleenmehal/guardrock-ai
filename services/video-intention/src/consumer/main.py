import sys
import os

# Add src directory to path so imports work when run from any directory
_src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

import json
import requests
from clients.twelve_labs_client import TwelveLabsClient
from config import config
from consumer.valkey_consumer import ValkeyConsumer
from models.message import VideoMessage
from risk_analyser.risk_client import OpenAIClient


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

            # Call risk_analyser to get a risk summary via OpenAI
            openai_key = os.environ.get("OPENAI_API_KEY")
            if openai_key:
                openai_client = OpenAIClient(openai_key)
                risk_summary = openai_client.summarise(result)
                print("\n" + "=" * 60)
                print("RISK SUMMARY")
                print("=" * 60)
                print(json.dumps(risk_summary, indent=2))
                print("=" * 60 + "\n")

                # Push risk summary to endpoint
                if message.unique_id.startswith("supa-"):
                    # PATCH to Supabase
                    SUPABASE_URL = os.environ.get("SUPABASE_URL")
                    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
                    if SUPABASE_URL and SUPABASE_KEY:
                        patch_url = f"{SUPABASE_URL}/rest/v1/videos?unique_id=eq.{message.unique_id}"
                        patch_headers = {
                            "apikey": SUPABASE_KEY,
                            "Authorization": f"Bearer {SUPABASE_KEY}",
                            "Content-Type": "application/json",
                        }
                        patch_body = {
                            "summary": risk_summary.get("summary", ""),
                            "level": risk_summary.get("level", 0),
                        }
                        try:
                            patch_response = requests.patch(patch_url, headers=patch_headers, json=patch_body)
                            patch_response.raise_for_status()
                            print(f"✓ Risk summary patched to Supabase for {message.unique_id}")
                        except requests.RequestException as e:
                            print(f"✗ Failed to patch risk summary to Supabase: {e}")
                    else:
                        print("⚠ SUPABASE_URL or SUPABASE_KEY not set, skipping Supabase patch")
                else:
                    RISK_ENDPOINT = "http://152.7.177.184:3000/api/submit"
                    try:
                        post_response = requests.post(RISK_ENDPOINT, json=risk_summary)
                        post_response.raise_for_status()
                        print(f"✓ Risk summary pushed to {RISK_ENDPOINT}")
                    except requests.RequestException as e:
                        print(f"✗ Failed to push risk summary: {e}")
            else:
                print("⚠ OPENAI_API_KEY not set, skipping risk summary")
        else:
            print("\n✗ Failed to process video\n")

    # Start consuming messages
    try:
        valkey_consumer.start(message_callback)
    finally:
        valkey_consumer.stop()


if __name__ == "__main__":
    main()