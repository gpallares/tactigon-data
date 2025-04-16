import pandas as pd
import numpy as np

# Configuration parameters
TOTAL_DURATION = 10.0  # seconds
SINE_DURATION = 3.0    # seconds
CONSTANT_DURATION = 3.0  # seconds
LINEAR_DURATION = 4.0    # seconds (10 - 3 - 3 = 4)

SINE_AMPLITUDE = 2.0    # m/s²
SINE_FREQUENCY = 1.0    # Hz
CONSTANT_VALUE = 1.5     # m/s²
LINEAR_START = 1.5       # m/s²
LINEAR_END = 4.0         # m/s²

def generate_synthetic_acceleration(num_samples):
    """Generate a synthetic acceleration signal with three phases"""
    t = np.linspace(0, TOTAL_DURATION, num_samples)
    acc = np.zeros(num_samples)
    
    # Phase 1: Sine wave (0-3 seconds)
    phase1_mask = t <= SINE_DURATION
    acc[phase1_mask] = SINE_AMPLITUDE * np.sin(2 * np.pi * SINE_FREQUENCY * t[phase1_mask])
    
    # Phase 2: Constant acceleration (3-6 seconds)
    phase2_mask = (t > SINE_DURATION) & (t <= SINE_DURATION + CONSTANT_DURATION)
    acc[phase2_mask] = CONSTANT_VALUE
    
    # Phase 3: Linear acceleration (6-10 seconds)
    phase3_mask = t > SINE_DURATION + CONSTANT_DURATION
    phase3_t = t[phase3_mask] - (SINE_DURATION + CONSTANT_DURATION)
    acc[phase3_mask] = LINEAR_START + (LINEAR_END - LINEAR_START) * phase3_t / LINEAR_DURATION
    
    return acc

# Load original data
df = pd.read_csv('tskin_log_20250402_162343.csv', on_bad_lines='skip', engine='python')

# Generate synthetic acceleration signal with the same number of samples
synthetic_acc_x = generate_synthetic_acceleration(len(df))

# Replace acc_x column while preserving other data
df['acc_x'] = synthetic_acc_x

# Save modified data
df.to_csv('modified_data.csv', index=False)

print("Synthetic acceleration generated and saved to modified_data.csv")