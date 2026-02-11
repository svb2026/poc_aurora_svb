# Script minimal pour générer un CSV test pour le POC Aurores
import pandas as pd
from datetime import datetime, timedelta

# Générer des dates de test
dates = [datetime(2025, 12, i+1) for i in range(7)]  # 7 jours de test
# Générer des heures d'aurores aléatoires
hours = [2.5, 3.0, 0, 1.5, 2.0, 0, 3.5]

df = pd.DataFrame({
    "date": dates,
    "hours_of_aurora": hours
})

# Sauvegarder le CSV
df.to_csv("levi_aurora_hours_per_night.csv", index=False)
print("CSV de test généré : levi_aurora_hours_per_night.csv")
