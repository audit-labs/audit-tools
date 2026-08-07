"""
Creates a sample from a CSV or Excel file based on user-defined SAMPLE_SIZE.

NOTE: This is a minimal teaching snippet. For real fieldwork use the
`audit_sample.py` CLI (or the `sampling_tool` package), which records the
population hash, seed, method, and tool version in a manifest so the sample is
reproducible and defensible. This file fixes a SEED only so the example itself is
repeatable; it does not emit that provenance.
"""

# Import packages
import pandas as pd

# Define the sample size
SAMPLE_SIZE = 25

# A fixed seed makes the draw reproducible: same population + same seed => same
# rows. Record the seed alongside any sample you rely on.
SEED = 20260707

# Import the data to a pandas DataFrame
df = pd.read_csv("FILENAME_GOES_HERE.csv")

# ALTERNATIVE: If you use Excel, use this instead. Supports xls, xlsx, xlsm,
# xlsb, odf, ods and odt file extensions.
# df = pd.read_excel("FILENAME_GOES_HERE.xlsx")

# Print totals prior to sampling
print("Dataframe size (rows, columns): ", df.shape)

# Sample
sample = df.sample(SAMPLE_SIZE, random_state=SEED)
print("Sample size: ", SAMPLE_SIZE)
print("Sample:\n", sample)

# ALTERNATIVE: Replacement Samples
#
# If you want replacement samples (e.g., 10 samples & 3 replacements), you will
# need to increase sample size to the total you want (e.g., 13). If that is
# larger than the population, you will need to use the `replace=True` parameter.
#
# # Sample Size: 25 + 5 replacement samples
# SAMPLE_SIZE = 30
# sample = df.sample(SAMPLE_SIZE, replace=True, random_state=SEED)
