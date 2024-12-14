import os
import numpy as np
import pandas as pd
from scipy.signal import resample
from datasets import Dataset
import wfdb  # For reading WFDB records

# Constants
BASE_PATH = "model_def/physionet.org/files/picsdb/1.0.0/"
OUTPUT_PATH = "HTR-2024-brachy"
TARGET_SAMPLING_RATE = 250  # Target sampling rate for all signals (Hz)
RESP_SAMPLING_RATE = 250  # Assuming all respiration signals will be resampled to 250Hz

# ECG Sampling Rates for specific infants
ECG_SAMPLING_RATES = {1: 250, 5: 250}  # ECG sampling rates for infants 1 and 5
DEFAULT_ECG_SAMPLING_RATE = 500  # Default ECG sampling rate

# Helper Function: Resample signals to target sampling rate
def resample_signal(signal, original_rate, target_rate):
    if original_rate != target_rate:
        num_samples = int(len(signal) * target_rate / original_rate)
        return resample(signal, num_samples)
    return signal

# Helper Function: Load WFDB signal and annotations
def load_signals_and_annotations(infant_id):
    try:
        # ECG
        ecg_record_name = f"infant{infant_id}_ecg"
        ecg_record = wfdb.rdrecord(os.path.join(BASE_PATH, ecg_record_name))
        ecg_sampling_rate = ECG_SAMPLING_RATES.get(infant_id, DEFAULT_ECG_SAMPLING_RATE)
        ecg_signal = ecg_record.p_signal[:, 0]  # Assuming single channel ECG
        ecg_signal = resample_signal(ecg_signal, ecg_sampling_rate, TARGET_SAMPLING_RATE)
        
        # Respiration
        resp_record_name = f"infant{infant_id}_resp"
        resp_record = wfdb.rdrecord(os.path.join(BASE_PATH, resp_record_name))
        resp_sampling_rate = resp_record.fs  # Original respiration sampling rate
        resp_signal = resp_record.p_signal[:, 0]  # Assuming single channel Respiration
        resp_signal = resample_signal(resp_signal, resp_sampling_rate, RESP_SAMPLING_RATE)
        
        # Load Bradycardia Annotations
        brady_ann = wfdb.rdann(os.path.join(BASE_PATH, ecg_record_name), 'atr')
        brady_times = np.array(brady_ann.sample) / ecg_sampling_rate  # Convert to seconds
        
        return ecg_signal, resp_signal, brady_times
    except Exception as e:
        print(f"Error loading data for infant {infant_id}: {e}")
        return None, None, None

# Process Dataset
data = []
infants = range(1, 11)  # Infants 1 to 10

for infant_id in infants:
    print(f"Processing Infant {infant_id}...")
    ecg_signal, resp_signal, brady_times = load_signals_and_annotations(infant_id)
    
    if ecg_signal is None or resp_signal is None:
        print(f"Skipping Infant {infant_id} due to loading error.")
        continue
    
    # Synchronize signals
    min_length = min(len(ecg_signal), len(resp_signal))
    ecg_signal = ecg_signal[:min_length]
    resp_signal = resp_signal[:min_length]
    
    # Combine ECG and Respiration into a 2-channel signal
    combined_signal = np.stack([ecg_signal, resp_signal], axis=0)  # Shape: (2, time)
    
    # Create Bradycardia Labels
    brady_labels = np.zeros(min_length, dtype=int)
    for brady_time in brady_times:
        brady_idx = int(brady_time * TARGET_SAMPLING_RATE)
        if brady_idx < len(brady_labels):
            brady_labels[brady_idx] = 1  # Mark bradycardia onset
    
    # Aggregate Bradycardia within 15s segments
    segment_length = TARGET_SAMPLING_RATE * 15  # 15 seconds
    total_segments = len(ecg_signal) // segment_length
    
    for seg in range(total_segments):
        start = seg * segment_length
        end = start + segment_length
        segment = combined_signal[:, start:end]
        label = 1 if np.any(brady_labels[start:end]) else 0
        data.append({
            "infant_id": infant_id,
            "segment_id": seg,
            "input": segment.T.tolist(),  # Shape: (3750, 2) -> transpose for channels last
            "label": label
        })
    
    print(f"Infant {infant_id}: {total_segments} segments processed.")

# Convert to Pandas DataFrame
df = pd.DataFrame(data)

# Verify DataFrame
print(f"Total segments: {len(df)}")
print(df.head())

# Convert to Hugging Face Dataset
hf_dataset = Dataset.from_pandas(df)

# Cast the 'input' column to list of floats (flattened)
# Since 'input' is a list of [ [ecg, resp], ... ], we need to flatten or handle appropriately
# Alternatively, keep it as list of lists
hf_dataset = hf_dataset.cast_column("input", "float32")

# Save Dataset to Disk in Parquet Format
hf_dataset.save_to_disk(OUTPUT_PATH)

print(f"Dataset successfully saved to {OUTPUT_PATH}")
