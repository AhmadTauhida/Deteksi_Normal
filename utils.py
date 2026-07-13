import numpy as np
from collections import deque
from typing import Optional, Sequence, Tuple


def calculate_ankle_angle(knee: Sequence[float], ankle: Sequence[float], heel: Sequence[float]) -> Optional[float]:
    """Calculate the ankle angle (knee-ankle-heel) in degrees.

    Uses the vector dot product between knee->ankle and heel->ankle.
    Returns None when the calculation is invalid or landmarks are degenerate.
    """
    knee = np.asarray(knee, dtype=float)
    ankle = np.asarray(ankle, dtype=float)
    heel = np.asarray(heel, dtype=float)

    if knee.shape != ankle.shape or ankle.shape != heel.shape:
        return None

    v1 = knee - ankle
    v2 = heel - ankle

    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 < 1e-6 or norm_v2 < 1e-6:
        return None

    dot = np.dot(v1, v2)
    cos_angle = np.clip(dot / (norm_v1 * norm_v2), -1.0, 1.0)
    angle_radians = np.arccos(cos_angle)
    
    # ── UBAH DI SINI ────────────────────────────────────────────────────────
    # Kurangi dengan 90.0 agar posisi siku-siku/netral menjadi 0 derajat
    raw_angle = float(np.degrees(angle_radians))
    return raw_angle - 90.0


class MovingAverageSmoother:
    """Simple moving average smoother for noisy realtime measurements."""

    def __init__(self, window_size: int = 5):
        self.window_size = max(1, int(window_size))
        self.values = deque(maxlen=self.window_size)

    def smooth(self, value: Optional[float]) -> Optional[float]:
        if value is None:
            return None

        self.values.append(float(value))
        if not self.values:
            return None
        return float(sum(self.values) / len(self.values))


def apply_moving_average_filter(data: Sequence[float], window_size: int = 5) -> np.ndarray:
    """Apply a causal moving average filter to a 1D sequence."""
    if window_size <= 1:
        return np.asarray(data, dtype=float)

    values = np.asarray(data, dtype=float)
    kernel = np.ones(window_size, dtype=float) / window_size
    return np.convolve(values, kernel, mode="valid")
