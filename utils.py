import numpy as np
from collections import deque
import math
import time
from typing import Optional, Sequence, Tuple

def calculate_ankle_angle(knee: Sequence[float], ankle: Sequence[float], foot_index: Sequence[float], baseline_angle: float = 104.9) -> Optional[float]:
    """Calculate the ankle angle (knee-ankle-foot_index) in degrees.

    Aligned with clinical gait analysis:
    - Neutral standing (Foot flat) is ~0 degrees.
    - Dorsiflexion (Toe pointing up) is Positive (> 0).
    - Plantar flexion (Toe pointing down) is Negative (< 0).
    """
    knee = np.asarray(knee, dtype=float)
    ankle = np.asarray(ankle, dtype=float)
    foot_index = np.asarray(foot_index, dtype=float) # Menggunakan ujung kaki

    if knee.shape != ankle.shape or ankle.shape != foot_index.shape:
        return None

    # Vektor v1: Ankle menunjuk ke Knee (Tulang Kering / Shin)
    v1 = knee - ankle
    # Vektor v2: Ankle menunjuk ke Foot Index (Telapak Kaki / Foot Axis)
    v2 = foot_index - ankle

    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 < 1e-6 or norm_v2 < 1e-6:
        return None

    dot = np.dot(v1, v2)
    cos_angle = np.clip(dot / (norm_v1 * norm_v2), -1.0, 1.0)
    angle_radians = np.arccos(cos_angle)
    
    # Inner angle dalam derajat (Saat berdiri tegap nilainya sekitar 90 derajat)
    raw_angle = float(np.degrees(angle_radians))
    
    # ── UBAH RUMUS NORMALISASI DI SINI ──
    # Jika kaki dorsiflexion (jari naik ke arah lutut), sudut raw_angle MENGEIL (< 90).
    # Agar dorsiflexion menjadi Positif (sesuai gambar), rumusnya adalah 90.0 - raw_angle.
    # Contoh Dorsi: 90.0 - 70.0 = +20.0 derajat.
    # Contoh Plantar (jari turun): 90.0 - 120.0 = -30.0 derajat.
    
    return baseline_angle - raw_angle

class OneEuroFilter:
    """Adaptive low-pass filter designed for real-time human pose tracking."""
    
    def __init__(self, min_cutoff: float = 1.0, beta: float = 0.007, d_cutoff: float = 1.0):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self.x_prev: Optional[float] = None
        self.dx_prev: float = 0.0
        self.t_prev: Optional[float] = None

    def _alpha(self, cutoff: float, dt: float) -> float:
        r = 2 * math.pi * cutoff * dt
        return r / (r + 1)

    def filter(self, value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
            
        t_curr = time.time()
        if self.t_prev is None or self.x_prev is None:
            self.x_prev = value
            self.t_prev = t_curr
            return value

        dt = t_curr - self.t_prev
        if dt <= 0:
            return self.x_prev

        # Hitung magnitude turunan (kecepatan perubahan sudut)
        d_value = (value - self.x_prev) / dt
        
        # Filter nilai turunan/kecepatan
        alpha_d = self._alpha(self.d_cutoff, dt)
        dx_curr = alpha_d * d_value + (1.0 - alpha_d) * self.dx_prev
        
        # Tentukan cutoff adaptif berdasarkan kecepatan gerakan
        cutoff = self.min_cutoff + self.beta * abs(dx_curr)
        
        # Filter nilai utama (sudut ankle)
        alpha = self._alpha(cutoff, dt)
        x_curr = alpha * value + (1.0 - alpha) * self.x_prev

        # Simpan state saat ini untuk frame berikutnya
        self.x_prev = x_curr
        self.dx_prev = dx_curr
        self.t_prev = t_curr

        return x_curr


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
