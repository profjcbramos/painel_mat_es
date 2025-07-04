import pandas as pd

# === 1. Carregar os dados ===
df_ama = pd.read_csv('../data/ama_2serie_2024_2025_merged.csv')
df_coord = pd.read_csv('../data/dados_escolas.csv')

# === 2. Converter para numérico e limpar ===
for col in ['TX_ACERTO_24', 'TX_ACERTO_25']:
    df_ama[col] = pd.to_numeric(df_ama[col], errors='coerce')

# Remover registros com valores inválidos
df_ama_limpo = df_ama.dropna(subset=['TX_ACERTO_24', 'TX_ACERTO_25'])
df_ama_limpo = df_ama_limpo[(df_ama_limpo['TX_ACERTO_24'] > 0) & (df_ama_limpo['TX_ACERTO_25'] > 0)]

# === 3. Calcular média de acerto por escola ===
df_medias = df_ama_limpo.groupby('CD_ESCOLA').agg({
    'NM_ESCOLA': 'first',
    'NM_MUNICIPIO': 'first',
    'NM_REGIONAL': 'first',
    'TX_ACERTO_24': 'mean',
    'TX_ACERTO_25': 'mean'
}).reset_index()

# === 4. Calcular evolução percentual ===
df_medias['evolucao_pct'] = round((df_medias['TX_ACERTO_25'] - df_medias['TX_ACERTO_24']), 2)

# === 5. Mesclar com coordenadas ===
df_coord_filtrado = df_coord[['cod_inep', 'latitude', 'longitude']].dropna()
df_coord_filtrado['cod_inep'] = df_coord_filtrado['cod_inep'].astype(str)
df_medias['CD_ESCOLA'] = df_medias['CD_ESCOLA'].astype(str)

df_final = pd.merge(df_medias, df_coord_filtrado, left_on='CD_ESCOLA', right_on='cod_inep', how='left')

# === 6. Exportar resultado ===
df_final.to_csv('../data/escolas_com_evolucao.csv', index=False)
