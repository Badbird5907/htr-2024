import numpy as np
from datasets import load_from_disk, Dataset, concatenate_datasets, Features, Array2D, Value
from collections import Counter

# Step 1: Load the Dataset
OUTPUT_PATH = "HTR-2024-brachy/"
dataset = load_from_disk("HTR-2024-brachy")

# Step 2: Analyze Class Distribution
def count_labels(ds):
    return Counter(ds['label'])

label_counts = count_labels(dataset)
print(f"Original Class Distribution: {label_counts}")

minority_count = label_counts.get(1, 0)
majority_count = label_counts.get(0, 0)
print(f"Minority Class (1) Count: {minority_count}")
print(f"Majority Class (0) Count: {majority_count}")

# Step 3: Define Augmentation Techniques
def add_noise(signal, noise_level=0.01):
    noise = np.random.normal(0, noise_level, signal.shape)
    return signal + noise

def time_shift(signal, shift_max=0.2):
    shift = np.random.randint(int(shift_max * signal.shape[1]))
    return np.roll(signal, shift, axis=1)

def scaling(signal, scale_min=0.9, scale_max=1.1):
    scale = np.random.uniform(scale_min, scale_max, size=(signal.shape[0], 1))
    return signal * scale

def permutation(signal, n_segments=4):
    orig_steps = np.linspace(0, signal.shape[1], n_segments + 1, dtype=int)
    for i in range(n_segments):
        start = orig_steps[i]
        end = orig_steps[i + 1]
        np.random.shuffle(signal[:, start:end])
    return signal

# Step 4: Apply Augmentation to the Minority Class
desired_count = majority_count  # To make minority count equal to majority count
current_minority = minority_count
samples_needed = desired_count - current_minority
print(f"Samples needed to balance: {samples_needed}")

minority_dataset = dataset.filter(lambda x: x['label'] == 1)
print(f"Number of minority samples: {len(minority_dataset)}")

def augment_sample(sample):
    augmented_sample = sample.copy()
    signal = np.array(sample['input'])  # Shape: (2, 3750)

    # Randomly choose augmentation techniques
    augmentations = [add_noise, time_shift, scaling, permutation]
    np.random.shuffle(augmentations)

    # Apply a random number of augmentations (e.g., 1 to 4)
    num_augmentations = np.random.randint(1, len(augmentations) + 1)
    for aug in augmentations[:num_augmentations]:
        signal = aug(signal)

    # Ensure signal is float32
    signal = signal.astype(np.float32)

    # Update the input
    augmented_sample['input'] = signal.tolist()

    # Cast 'infant_id' and 'segment_id' to int32
    augmented_sample['infant_id'] = np.int32(sample['infant_id'])
    augmented_sample['segment_id'] = np.int32(sample['segment_id'])

    return augmented_sample

# Calculate how many times to iterate over the minority dataset
augmentations_needed = samples_needed
augmented_samples = []
times_to_repeat = int(np.ceil(augmentations_needed / len(minority_dataset)))

for _ in range(times_to_repeat):
    for sample in minority_dataset:
        if len(augmented_samples) >= augmentations_needed:
            break
        augmented_sample = augment_sample(sample)
        augmented_samples.append(augmented_sample)

        if len(augmented_samples) >= augmentations_needed:
            break

print(f"Generated {len(augmented_samples)} augmented minority samples.")

# Create a new Dataset from augmented samples with the same features as the original
augmented_dataset = Dataset.from_list(augmented_samples, features=dataset.features)

# Concatenate the original dataset with the augmented minority dataset
balanced_dataset = concatenate_datasets([dataset, augmented_dataset])

print(f"New dataset size: {len(balanced_dataset)}")

# Step 5: Verify the New Class Distribution
new_label_counts = count_labels(balanced_dataset)
print(f"New Class Distribution: {new_label_counts}")

# Step 6: Shuffle the Dataset
balanced_dataset = balanced_dataset.shuffle(seed=42)

# Step 7: Save the Balanced Dataset
balanced_output_path = "/HTR-2024-brachy-balanced"
balanced_dataset.save_to_disk(balanced_output_path)
print(f"Balanced dataset saved to {balanced_output_path}")
