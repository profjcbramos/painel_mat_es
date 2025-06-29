import pandas as pd

# 1. Carregar as bases com o separador correto
ama2024 = pd.read_csv("../DadosBrutos/ama2024_2serie.csv", sep=";", encoding="utf-8-sig")
ama2025 = pd.read_csv("../DadosBrutos/ama2025_2serie.csv", sep=";", encoding="utf-8-sig")

# 2. Função para acrescentar sufixo nas colunas numéricas e de contagem
def acrescenta_sufixo(df, sufixo):
    colunas_sufixo = ['NU_ACERTO', 'NU_TOTAL', 'TX_ACERTO',
                      'ct_alto', 'ct_medio', 'ct_baixo', 'ct_muito_baixo']
    novas_colunas = {col: col + sufixo for col in colunas_sufixo if col in df.columns}
    return df.rename(columns=novas_colunas)

ama2024 = acrescenta_sufixo(ama2024, '_24')
ama2025 = acrescenta_sufixo(ama2025, '_25')

# 3. Definir colunas de merge
colunas_merge = ['CD_REGIONAL', 'NM_REGIONAL',
                 'CD_MUNICIPIO', 'NM_MUNICIPIO',
                 'CD_ESCOLA', 'NM_ESCOLA',
                 'CD_ETAPA_AVALIADA', 'DC_ETAPA_AVALIADA', 'NM_DISCIPLINA']

# 4. Fazer o merge
ama_merged = pd.merge(ama2024, ama2025, on=colunas_merge, how='inner')

# 5. Salvar em CSV
ama_merged.to_csv("../data/ama_2serie_2024_2025_merged.csv", index=False, encoding='utf-8-sig')

print("Merge concluído com sucesso! Arquivo salvo.")

print("Shape do resultado:", ama_merged.shape)
print("Colunas do resultado:", ama_merged.columns.tolist())
print(ama_merged.sample(5))
