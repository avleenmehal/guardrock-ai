import json
import os
from risk_client import OpenAIClient


def main():
    # Sample structured data matching what the video-intention service produces
    analysis_data = {
        "video_uuid": "243567897",
        "video_id": "tl-video-001",
        "task_id": "tl-task-001",
        "file_path": "/tmp/videos/243567897.mp4",
        "analysis_text": (
            "Manipulation Score: 7/10\n"
            "Urgency Score: 8/10\n"
            "Key Phrases: 'Act now before it's too late', 'They don't want you to know this'\n"
            "Summary: The video uses fear-based tactics to promote an unverified health supplement, "
            "claiming mainstream medicine is hiding a cure.\n"
            "Red Flags: Unsubstantiated medical claims, appeal to conspiracy, artificial urgency"
        ),
        "metadata": {
            "title": "Unit Test Video",
            "channel": "unit-test-channel-crocs",
            "description": "This is a test video message for unit testing.",
            "timestamp": "2024-06-01T12:00:00Z",
        },
    }

    # OpenAI
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        openai = OpenAIClient(openai_key)
        print("Sending analysis data to OpenAI...\n")
        risk_result = openai.summarise(analysis_data)
        print("=== OpenAI Risk Summary ===")
        print(json.dumps(risk_result, indent=2))
        print()

    if not openai_key:
        print("Error: Set OPENAI_API_KEY environment variables.")


if __name__ == "__main__":
    main()
