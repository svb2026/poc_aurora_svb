import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

start_date = datetime(2025, 12, 1)
rows = []

for i in range(7):
    date = start_date + timedelta(days=i)
    hours = random.choice([0, 1.5, 2.0, 3.0])
    kp = random.uniform(1, 6)

    rows.append({
        "date": date,
        "hours_of_aurora": hours,
        "kp_mean": kp
    })

df = pd.DataFrame(rows)
df.to_parquet("levi_aurora_hours_per_night.parquet", index=False)

print("Dataset test généré.")

