INSERT INTO utterances (
    audio_properties_id,
    speaker,
    start_time,
    end_time,
    text,
    confidence,
    sequence,
    sentiment,
    profane,
    created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'));
