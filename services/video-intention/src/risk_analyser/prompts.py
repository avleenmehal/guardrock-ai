def build_risk_summary_prompt(analysis_data: dict) -> str:
    metadata = analysis_data['metadata']
    return (
        f"""# You are a risk analyst specializing in detecting AI generated content, manipulation, urgency tactics, "
        "and deception in video content to prevent users from taking sensitive action. You are provided with metadata that has some scores based on AI generated content, manipulation, urgency tactics.\n\n"

    ## Video Metadata
    - Title: {metadata['title']}
    - Channel: {metadata['channel']}
    - Description: {metadata['description']}
    - Timestamp: {metadata['timestamp']}
    "## Analysis Data:\n"
        f"{analysis_data['analysis_text']}\n\n"

    ## Task
    Analyze this video for the following risk indicators:

    1. **AI-Generated Content:**
       - Synthetic voices (unnatural cadence, robotic tone)
       - Deepfake or AI-generated visuals
       - Generic stock footage with AI voiceover
       - Automated text-to-speech narration
       - **If AI content is detected, minimum risk level is 5**

    2. **Manipulation Tactics:**
       - Emotional appeals (fear, anger, shock, outrage)
       - Loaded or inflammatory language
       - One-sided arguments without counterpoints
       - Authority misuse ("experts say" without sources)
       - "Us vs. them" divisive rhetoric
       - Exaggerated claims or hyperbole
       - Cherry-picking facts or context removal

    3. **Urgency Indicators:**
       - Time pressure ("act now", "limited time", "before it's too late")
       - Consequence threats ("if you don't act")
       - Breaking news framing without verification
       - Immediacy language ("urgent", "critical", "must watch")

    4. **Deception Signals:**
       - Unverified claims as facts
       - Missing or vague sources
       - Conspiracy theory language
       - "They don't want you to know" rhetoric
       - Misleading titles or thumbnails
       - Suspicious channel names

    ## Output Format
    Respond with ONLY a valid JSON object (no markdown, no extra text):

    {
        "ai_content_detected": boolean,
      "manipulation_score": 0-10,
      "urgency_score": 0-10,
      "deception_score": 0-10,
      "overall_risk_level": 1-10,
      "key_findings": ["finding1", "finding2", "finding3"],
      "red_flags": ["flag1", "flag2"],
      "summary": "Concise 15-20 word risk assessment"
    }

    **Critical Rules:**
    - If AI content detected, overall_risk_level must be ≥5
    - Consider title, channel, description as credibility signals
    - Quote specific phrases from video as evidence
    - Be specific and direct"""
    )
