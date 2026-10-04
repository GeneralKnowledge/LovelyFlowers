"""Optional procedural blips from morph params — mute-safe, not a music system."""

from __future__ import annotations

import math
from typing import Optional

from procgen.morph import MorphParams

_enabled = True
_initialized = False


def set_enabled(enabled: bool) -> None:
    global _enabled
    _enabled = enabled


def init_audio() -> bool:
    """Initialize pygame mixer if available. Returns False if audio unavailable."""
    global _initialized
    if _initialized:
        return True
    try:
        import pygame

        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        _initialized = True
        return True
    except Exception:
        return False


def _tone(frequency: float, ms: int = 90, volume: float = 0.18) -> Optional[object]:
    try:
        import array
        import pygame

        if not init_audio():
            return None
        sample_rate = 22050
        n = int(sample_rate * ms / 1000)
        buf = array.array("h")
        amp = int(32767 * max(0.0, min(1.0, volume)))
        for i in range(n):
            t = i / sample_rate
            # Soft attack/release envelope
            env = min(1.0, i / 200.0) * min(1.0, (n - i) / 400.0)
            val = int(amp * env * math.sin(2 * math.pi * frequency * t))
            buf.append(val)
        sound = pygame.mixer.Sound(buffer=buf)
        return sound
    except Exception:
        return None


def blip_from_morph(morph: MorphParams, kind: str = "mature") -> None:
    """Play a short tone derived from stem frequency/amplitude. No-op if muted/unavailable."""
    if not _enabled:
        return
    base = 180 + morph.stem_freq * 90 + morph.stem_amp * 120
    if kind == "breed":
        base *= 1.25
    elif kind == "discover":
        base *= 1.45
    sound = _tone(base, ms=70 if kind != "breed" else 110, volume=0.14)
    if sound is not None:
        try:
            sound.play()
        except Exception:
            pass
