import pandas as pd

# Carregar os dados
df_ama = pd.read_csv("../ama3_2024.csv", encoding="ISO-8859-1", sep=";")

# Corrigir o separador decimal
for coluna in ['NU_ACERTO', 'TX_ACERTO', 'NU_TOTAL']:
    df_ama[coluna] = df_ama[coluna].astype(str).str.replace(',', '.').str.strip().astype(float)

# Filtrar apenas as colunas relevantes
colunas = ['CD_REGIONAL', 'NM_REGIONAL', 'CD_MUNICIPIO', 'NM_MUNICIPIO', 'CD_ESCOLA', 'NM_ESCOLA', 'CD_ALUNO_INEP', 'NM_DISCIPLINA', 'NU_ACERTO', 'NU_TOTAL', 'TX_ACERTO']
df_ama = df_ama[colunas]

# ✅ Filtro pela disciplina Matemática
df_ama = df_ama[df_ama['NM_DISCIPLINA'].str.upper().str.strip() == 'MATEMÁTICA']

# Agrupar por escola: somar acertos e total, fazer média da taxa de acerto
df_ama_escola = df_ama.groupby(
    ['CD_ESCOLA', 'NM_ESCOLA', 'CD_MUNICIPIO', 'NM_MUNICIPIO', 'CD_REGIONAL', 'NM_REGIONAL']
).agg({
    'NU_ACERTO': 'sum',
    'NU_TOTAL': 'sum',
    'TX_ACERTO': 'mean'
}).reset_index()

# Exportar para CSV
df_ama_escola.to_csv('ama_escola.csv', index=False, encoding='utf-8-sig', sep=',')

# Exibir amostra
print(df_ama_escola.head(10))
