import os
import numpy as np
import pandas as pd
from scipy.signal import resample
from datasets import Dataset
import wfdb  # For reading WFDB records

# Constants
BASE_PATH = "path/to/PICS/database"
OUTPUT_PATH = "path/to/output/parquet/dataset"
TARGET_SAMPLING_RATE = 250  # Target sampling rate for all signals (Hz)
RESP_SAMPLING_RATE = 50
ECG_SAMPLING_RATES = {1: 250, 5: 250}  # ECG sampling rates for infants 1 and 5
DEFAULT_ECG_SAMPLING_RATE = 500

# Helper Function: Resample signals to target sampling rate
def resample_signal(signal, original_rate, target_rate):
    if original_rate != target_rate:
        num_samples = int(len(signal) * target_rate / original_rate)
        return resample(signal, num_samples)
    return signal

# Helper Function: Load WFDB signal and annotations
def load_signals_and_annotations(infant_id):
    # Load ECG
    ecg_record = wfdb.rdrecord(f"{BASE_PATH}/infant{infant_id}_ecg")
    ecg_sampling_rate = ECG_SAMPLING_RATES.get(infant_id, DEFAULT_ECG_SAMPLING_RATE)
    ecg_signal = resample_signal(ecg_record.p_signal[:, 0], ecg_sampling_rate, TARGET_SAMPLING_RATE)
    
    # Load Respiration
    resp_record = wfdb.rdrecord(f"{BASE_PATH}/infant{infant_id}_resp")
    resp_signal = resample_signal(resp_record.p_signal[:, 0], RESP_SAMPLING_RATE, TARGET_SAMPLING_RATE)
    
    # Load Bradycardia Annotations
    brady_ann = wfdb.rdann(f"{BASE_PATH}/infant{infant_id}_ecg", 'atr')
    brady_times = np.array(brady_ann.sample) / ecg_sampling_rate  # Convert to seconds
    
    return ecg_signal, resp_signal, brady_times

# Process Dataset
data = []
infants = range(1, 11)  # Infants 1 to 10

for infant_id in infants:
    try:
        ecg_signal, resp_signal, brady_times = load_signals_and_annotations(infant_id)
        
        # Synchronize signals
        min_length = min(len(ecg_signal), len(resp_signal))
        ecg_signal = ecg_signal[:min_length]
        resp_signal = resp_signal[:min_length]
        
        # Extract Features: ECG and Respiration as combined signal
        combined_signal = np.stack([ecg_signal, resp_signal], axis=0)  # Shape: (2, time)
        
        # Create Labels: Binary bradycardia onset within the signal window
        signal_length_seconds = min_length / TARGET_SAMPLING_RATE
        brady_labels = np.zeros((min_length,), dtype=int)
        for brady_time in brady_times:
            brady_idx = int(brady_time * TARGET_SAMPLING_RATE)
            if brady_idx < len(brady_labels):
                brady_labels[brady_idx] = 1  # Mark bradycardia onset
        
        # Split into 15-second segments
        segment_length = TARGET_SAMPLING_RATE * 15
        for start in range(0, len(ecg_signal) - segment_length + 1, segment_length):
            segment = combined_signal[:, start:start+segment_length]
            label = 1 if np.any(brady_labels[start:start+segment_length]) else 0
            data.append({"input": segment.tolist(), "label": label})
    except Exception as e:
        print(f"Error processing infant {infant_id}: {e}")

# Convert to Hugging Face Dataset
df = pd.DataFrame(data)
hf_dataset = Dataset.from_pandas(df)

# Save Dataset to Parquet
hf_dataset.cast_column("input", "list<float>")
hf_dataset.save_to_disk(OUTPUT_PATH)

print(f"Dataset saved to {OUTPUT_PATH}")
