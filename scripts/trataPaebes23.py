import pandas as pd
import unicodedata
import re

#Carregar dados Paebes 2023
paebes_2023 = pd.read_csv("D:\PÓS MDE\Seminario_VD\DadosBrutos\paebesMun2023.csv", encoding="iso8859-1", sep = ";")

print(paebes_2023.head())
print(paebes_2023.columns)
print(paebes_2023.info())

# Verificar valores de recorte nas colunas

colunasRecorte =  ['Rede', 'Etapa', 'Componente Curricular']

for coluna in colunasRecorte:
    print(paebes_2023[coluna].unique())

# Selecionar as colunas de interesse

colunas_p2023 = ['Código da Regional',
       'Município', 'Previstos', 'Avaliados','Proficiência Média', 'Abaixo do básico',
        'Básico', 'Proficiente', 'Avançado']

paebes_2023_enxugado =  paebes_2023[colunas_p2023].copy()

# Verificar valores inválidos e tipos de dados

print(paebes_2023_enxugado.isna().sum())
print(paebes_2023_enxugado.dtypes)

# tratar colunas com valores inválidos para manipulação

# Lista das colunas com porcentagem
colunas_percentuais = ['Abaixo do básico', 'Básico', 'Proficiente', 'Avançado']

# Remover símbolo de porcentagem e converter para float
for col in colunas_percentuais:
    paebes_2023_enxugado[col] = (
        paebes_2023_enxugado[col]
        .str.replace('%', '', regex=False)
        .str.replace(',', '.', regex=False)  # caso esteja no formato europeu
        .astype(float)
    )
    paebes_2023_enxugado [col] /= 100

# Padronizar os nomes das colunas

def padronizar_colunas(df):
    colunas_novas = []
    for col in df.columns:
        # Normaliza e remove acentos
        col_sem_acentos = ''.join(
            c for c in unicodedata.normalize('NFKD', col)
            if not unicodedata.combining(c)
        )
        # Substitui espaços por _
        col_sem_espaco = col_sem_acentos.replace(' ', '_')
        # Remove caracteres especiais (mantém letras, números e _)
        col_limpa = re.sub(r'[^a-zA-Z0-9_]', '', col_sem_espaco)
        # Converte para minúsculas
        col_final = col_limpa.lower()
        colunas_novas.append(col_final)
    df.columns = colunas_novas
    return df

paebes_2023_enxugado = padronizar_colunas(paebes_2023_enxugado)

#Verificar novamente

print(paebes_2023_enxugado.isna().sum())
print(paebes_2023_enxugado.dtypes)
print(paebes_2023_enxugado.sample(10))
print(paebes_2023_enxugado.columns)

paebes_2023_enxugado.to_csv('D:\PÓS MDE\Seminario_VD\DadosBrutos\paebesMun2023.csv', index = False)



