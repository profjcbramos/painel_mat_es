import pandas as pd
import unicodedata
from unidecode import unidecode
import re

#carregar dados
ama2025 = pd.read_csv('../DadosBrutos/ama2025_1trim.csv', encoding = "ISO-8859-1", sep = ";")

print(ama2025.columns)

#definir colunas de interesse
ColunasDeInteresse = [ 'CD_REGIONAL', 'NM_REGIONAL', 'CD_MUNICIPIO',
       'NM_MUNICIPIO', 'CD_ESCOLA', 'NM_ESCOLA', 'CD_ETAPA_AVALIADA', 'DC_ETAPA_AVALIADA', 'NU_ACERTO', 'NU_TOTAL',
       'TX_ACERTO', 'DC_CATEGORIA_DESEMPENHO',
       'NM_DISCIPLINA']

ama2025_enxugada = ama2025[ColunasDeInteresse].copy()

# verificar tipos de dados e tratar se necessário

print(ama2025_enxugada.info())

colunas_num = ['NU_ACERTO', 'NU_TOTAL' ,'TX_ACERTO']
print(ama2025_enxugada[colunas_num].sample(10))

for col in colunas_num:
    ama2025_enxugada[col] = (
        ama2025_enxugada[col]
        .astype(str)
        .str.replace(',', '.', regex=False)
        .astype(float)
    )
print(ama2025_enxugada[colunas_num].info())

# filtrar e agregar

print(ama2025_enxugada['DC_ETAPA_AVALIADA'].unique())

ama2025_2serie = ama2025_enxugada.loc[ama2025_enxugada['DC_ETAPA_AVALIADA'] == 'ENSINO MEDIO - 2ª SERIE']

print(ama2025_2serie['DC_ETAPA_AVALIADA'].unique())

print(ama2025_2serie.columns.tolist())

cat_desemp = pd.get_dummies(ama2025_2serie['DC_CATEGORIA_DESEMPENHO'], prefix='ct')

cat_desemp = cat_desemp.astype(int)


cat_desemp.columns = [unidecode(col).lower().replace(' ', '_') for col in cat_desemp.columns]


ama2025_2serie = pd.concat([ama2025_2serie, cat_desemp], axis=1)


colunas_categoricas = ['CD_REGIONAL', 'NM_REGIONAL', 'CD_MUNICIPIO', 'NM_MUNICIPIO', 'CD_ESCOLA', 'NM_ESCOLA', 'CD_ETAPA_AVALIADA', 'DC_ETAPA_AVALIADA', 'NM_DISCIPLINA']

ama2025_2serie_porEscola = ama2025_2serie.groupby(colunas_categoricas).agg({'NU_ACERTO': 'sum',
    'NU_TOTAL': 'sum',
    'TX_ACERTO': 'mean',
    'ct_alto': 'sum',
    'ct_medio': 'sum',
    'ct_baixo': 'sum',
    'ct_muito_baixo': 'sum'}).reset_index()

# verificar e tratar valores ausentes em TX_ACERTO

ama2025_2serie_porEscola.dropna(subset=['TX_ACERTO'], inplace=True)
print(ama2025_2serie_porEscola.info())

# Gerar csv


ama2025_2serie_porEscola.to_csv('../DadosBrutos/ama2025_2serie.csv', encoding='utf-8',sep = ";" ,index=False)