# BEHIND THE BRAND
# Voice casting

Model: **eleven_v3** (stability 0.5, similarity 0.8). Timestamps: `/with-timestamps` works on v3 (tested). Same test line per candidate, all v3. wpm = words / total duration incl. dramatic pauses.

| Candidate | voice_id | Source | wpm | LUFS | True peak | Long silences | Notes |
|---|---|---|---|---|---|---|---|
| George | JBFqnCBsd6RMkjVDRZzb | account (British storyteller) | 152 | -20.7 | -3.1 | 1 | quiet; British |
| **Jon** | MFZUKuGQUsGJPQjTS4wC | library (added) | 151 | -16.8 | -1.7 | 0 | "warm & grounded storyteller"; 7.3B chars/yr, 856k clones; clean, no long gaps |
| Chris | iP95p4xoKVk53GoZ742B | account | 156 | -18.1 | -1.0 | 2 | casual, charming |
| Roger | CwhRBWXzGAHq8TQ4Fs17 | account | 126 | -19.1 | -0.9 | 1 | slow, laid-back |
| Brian | nPczCjzI2devNBz1zQrb | account | 136 | -18.8 | -0.5 | 0 | deep, comforting; less smiley |

**Winner: Jon.** Warm storyteller profile, ~151 wpm, strong usage, clean audio.

**Quote voice (opposite gender): Matilda (XrExE9yKIg1WjnnlVkGX), knowledgeable American.** Tested on a short quote line (peak -4 dB, clean).

Caveat: scores are objective only (no listening possible). Please listen to the WINNER mp3 and swap via config/voice.json if it is not right; other samples are in `samples/`.
