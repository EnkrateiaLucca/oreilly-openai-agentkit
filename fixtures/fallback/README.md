# Offline fallback recording

`recording.json` was captured from the deterministic offline runtime. It contains two turns, actual local PDF/CSV tool results, and the resulting briefs. **No model inference occurred.** It demonstrates the application workflow when Wi-Fi, model access, or a managed sandbox is unavailable; it does not establish model capability.

Replay with `python -m course replay`. Run `python -m course demo --runtime responses --follow-up --output outputs/live-recording` to capture an actual live alternative when authorized. Review it before replacing this fallback and retain its `kind`, timestamp, and runtime labels.
