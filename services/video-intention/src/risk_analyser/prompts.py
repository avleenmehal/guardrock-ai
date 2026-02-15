def build_risk_summary_prompt(analysis_data: dict) -> str:
    metadata = analysis_data['metadata']
    return (
        "# Context: You are a risk analyst specializing in detecting AI generated content, manipulation, urgency tactics, "
        "and deception in video content to prevent users from taking sensitive action. You are provided with metadata that has some scores based on AI generated content, manipulation, urgency tactics.\n\n"
        
        "## Metadata (use this to assess context, credibility, and intent):\n"
        f"- Title: {metadata['title']}\n"
        f"- Channel: {metadata['channel']}\n"
        f"- Description: {metadata['description']}\n"
        f"- Timestamp: {metadata['timestamp']}\n\n"
        f"- Video UUID: {analysis_data['video_uuid']}\n\n"
        "## Analysis Data:\n"
        f"{analysis_data['analysis_text']}\n\n"
        
        "## Instruction:\n"
        "Evaluate the metadata alongside the analysis to determine how much manipulation, "
        "urgency, and deception AI content is present. The title, channel name, and description are critical "
        "signals — misleading titles, suspicious channel names, or sensationalist descriptions "
        "should increase the risk level.\n\n"
        "Respond with ONLY a valid JSON object (no markdown, no extra text) with these fields:\n"
        '- "title": the video title\n'
        '- "channel_name": the channel name\n'
        '- "unique_id": the video UUID\n'
        '- "summary": a concise risk summary covering manipulation, urgency, and deception findings within 15-20 words\n'
        '- "level": a score of risk involved between 1-10\n'
    )
