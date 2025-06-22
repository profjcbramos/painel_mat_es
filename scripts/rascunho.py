import pandas as pd

# Carregar os dados
df_ama = pd.read_csv("../ama3_2024.csv", encoding="ISO-8859-1", sep=";")
print(df_ama['NU_ACERTO'].dtype)