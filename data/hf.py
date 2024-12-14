from datasets import load_dataset

ds = load_dataset("alonso130r/HTR-2024-brachy")
# take the first 5 rows
ds = ds.select(range(5))

# save to csv
ds.to_csv("data/htr-2024-brachy.csv")

