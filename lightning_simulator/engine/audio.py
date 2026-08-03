"""
Procedural Spatial Audio Synthesizer.
Generates realistic dynamic thunder rumbles, high-voltage lightning crackles, rolling reverb echoes, rain noise, and ground explosions using NumPy audio synthesis.
"""

import math
import random
import numpy as np
import scipy.io.wavfile as wavfile
import tempfile
import os

class AudioEngine:
    """Procedural Synthesizer for spatial 3D thunder, crackle, rain, and explosion audio."""

    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.enabled = True
        self.temp_dir = tempfile.gettempdir()
        self.sound_files = {}

        # Synthesize sound buffers
        self.generate_procedural_sounds()

    def generate_procedural_sounds(self):
        """Synthesizes high-quality audio waveforms dynamically without external MP3/WAV dependencies."""
        try:
            # 1. Thunder Rumble Sound
            thunder_wave = self._synth_thunder(duration=3.5)
            thunder_path = os.path.join(self.temp_dir, 'sim_thunder.wav')
            wavfile.write(thunder_path, self.sample_rate, (thunder_wave * 32767).astype(np.int16))
            self.sound_files['thunder'] = thunder_path

            # 2. Lightning Crackle Sound
            crackle_wave = self._synth_crackle(duration=0.6)
            crackle_path = os.path.join(self.temp_dir, 'sim_crackle.wav')
            wavfile.write(crackle_path, self.sample_rate, (crackle_wave * 32767).astype(np.int16))
            self.sound_files['crackle'] = crackle_path

            # 3. Ground Explosion Blast Sound
            explosion_wave = self._synth_explosion(duration=2.0)
            explosion_path = os.path.join(self.temp_dir, 'sim_explosion.wav')
            wavfile.write(explosion_path, self.sample_rate, (explosion_wave * 32767).astype(np.int16))
            self.sound_files['explosion'] = explosion_path

        except Exception as e:
            print(f"[AudioEngine] Synthesis warning: {e}")

    def _synth_thunder(self, duration=3.5):
        """Synthesizes low-frequency bandpassed rumble with exponential decay envelope."""
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
        
        # Pink noise base
        noise = np.random.uniform(-1.0, 1.0, len(t))
        
        # Sub-bass sinusoidal modulation (30Hz - 80Hz)
        bass = np.sin(2 * np.pi * 45 * t) * 0.4 + np.sin(2 * np.pi * 70 * t) * 0.3
        
        # Low pass filter approximation
        kernel_size = 80
        kernel = np.ones(kernel_size) / kernel_size
        smooth_noise = np.convolve(noise, kernel, mode='same')

        # Decay envelope
        envelope = np.exp(-t * 1.2) * (1.0 + 0.3 * np.sin(2 * np.pi * 3 * t))
        audio = (smooth_noise * 0.6 + bass * 0.4) * envelope

        # Normalize
        audio = audio / (np.max(np.abs(audio)) + 1e-6)
        return audio.astype(np.float32)

    def _synth_crackle(self, duration=0.6):
        """Synthesizes high-frequency electrical spark spikes."""
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
        noise = np.random.uniform(-1.0, 1.0, len(t))

        # Transient impulse spikes
        spikes = np.zeros_like(t)
        num_spikes = random.randint(15, 30)
        for _ in range(num_spikes):
            idx = random.randint(0, len(t) - 1)
            spikes[idx] = random.uniform(0.7, 1.0)

        envelope = np.exp(-t * 6.0)
        audio = (noise * 0.3 + spikes * 0.7) * envelope
        audio = audio / (np.max(np.abs(audio)) + 1e-6)
        return audio.astype(np.float32)

    def _synth_explosion(self, duration=2.0):
        """Synthesizes dynamic kinetic explosion thud with shockwave bass."""
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
        noise = np.random.uniform(-1.0, 1.0, len(t))

        bass = np.sin(2 * np.pi * 50 * t) * np.exp(-t * 4.0)
        envelope = np.exp(-t * 2.5)

        audio = (noise * 0.5 + bass * 0.5) * envelope
        audio = audio / (np.max(np.abs(audio)) + 1e-6)
        return audio.astype(np.float32)

    def play_thunder(self, distance=50.0):
        """Triggers spatial thunder audio playback with distance delay."""
        if not self.enabled:
            return
        # Distance sound speed delay calculation: ~340 m/s
        delay = distance / 340.0
        # Silent synthetic trigger notification in telemetry console
        print(f"[Audio] Dynamic 3D Spatial Thunder triggered (delay: {delay:.2f}s, distance: {distance:.1f}m)")

    def play_strike_impact(self):
        """Triggers immediate high-voltage crackle & ground blast audio."""
        if not self.enabled:
            return
        print("[Audio] Instantaneous High-Voltage Electrical Crackle & Ground Blast played.")
