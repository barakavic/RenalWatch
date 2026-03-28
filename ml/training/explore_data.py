import scipy.io.arff as arff
import pandas as pd
from pathlib import Path

DATA_DIR = (
    Path(__file__).resolve().parents[2]
    / "assets"
    / "chronic+kidney+disease"
    / "Chronic_Kidney_Disease"
)

# Load both arff files
data1, meta1 = arff.loadarff(DATA_DIR / 'chronic_kidney_disease.arff')
data2, meta2 = arff.loadarff(DATA_DIR / 'chronic_kidney_disease_full.arff')

df1 = pd.DataFrame(data1)
df2 = pd.DataFrame(data2)

print(" FILE 1 ")
print("Shape:", df1.shape)
print("Columns:", df1.columns.tolist())

print("\n FILE 2 ")
print("Shape:", df2.shape)
print("Columns:", df2.columns.tolist())

# Read info file
with open(DATA_DIR / 'chronic_kidney_disease.info.txt', 'r', encoding='utf-8') as f:
    print("\nINFO ")
    print(f.read())
