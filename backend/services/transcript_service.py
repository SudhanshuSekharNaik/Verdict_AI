from models.schemas import TranscriptEntry


def render_for_judge(transcript: list[TranscriptEntry]) -> str:
    """
    Turns the structured transcript into a plain-text court record for the judge
    agent to read, including classifier tags where present.
    """
    lines = []
    for entry in transcript:
        speaker_label = entry.speaker.value.upper()
        stage_label = entry.stage.replace("_", " ").title()
        tag = ""
        if entry.argument_type or entry.argument_strength:
            tag = f" [type: {entry.argument_type} | strength: {entry.argument_strength}]"
        lines.append(f"--- {stage_label} ({speaker_label}){tag} ---\n{entry.text}\n")
    return "\n".join(lines)
