import pandas as pd
import unicodedata
from unidecode import unidecode
import re

#carregar dados
ama2024 = pd.read_csv('../DadosBrutos/ama2024_1trim.csv', encoding = "ISO-8859-1", sep = ";")

print(ama2024.columns)

#definir colunas de interesse
ColunasDeInteresse = [ 'CD_REGIONAL', 'NM_REGIONAL', 'CD_MUNICIPIO',
       'NM_MUNICIPIO', 'CD_ESCOLA', 'NM_ESCOLA', 'CD_ETAPA_AVALIADA', 'DC_ETAPA_AVALIADA', 'NU_ACERTO', 'NU_TOTAL',
       'TX_ACERTO', 'DC_CATEGORIA_DESEMPENHO',
       'NM_DISCIPLINA']

ama2024_enxugada = ama2024[ColunasDeInteresse].copy()

# verificar tipos de dados e tratar se necessário

print(ama2024_enxugada.info())

colunas_num = ['NU_ACERTO', 'NU_TOTAL' ,'TX_ACERTO']
print(ama2024_enxugada[colunas_num].sample(10))

for col in colunas_num:
    ama2024_enxugada[col] = (
        ama2024_enxugada[col]
        .astype(str)
        .str.replace(',', '.', regex=False)
        .astype(float)
    )
print(ama2024_enxugada[colunas_num].info())

# filtrar e agregar

print(ama2024_enxugada['DC_ETAPA_AVALIADA'].unique())

ama2024_2serie = ama2024_enxugada.loc[ama2024_enxugada['DC_ETAPA_AVALIADA'] == 'ENSINO MEDIO - 2ª SERIE']

print(ama2024_2serie['DC_ETAPA_AVALIADA'].unique())

print(ama2024_2serie.columns.tolist())

cat_desemp = pd.get_dummies(ama2024_2serie['DC_CATEGORIA_DESEMPENHO'], prefix='ct')

cat_desemp = cat_desemp.astype(int)


cat_desemp.columns = [unidecode(col).lower().replace(' ', '_') for col in cat_desemp.columns]


ama2024_2serie = pd.concat([ama2024_2serie, cat_desemp], axis=1)


colunas_categoricas = ['CD_REGIONAL', 'NM_REGIONAL', 'CD_MUNICIPIO', 'NM_MUNICIPIO', 'CD_ESCOLA', 'NM_ESCOLA', 'CD_ETAPA_AVALIADA', 'DC_ETAPA_AVALIADA', 'NM_DISCIPLINA']

ama2024_2serie_porEscola = ama2024_2serie.groupby(colunas_categoricas).agg({'NU_ACERTO': 'sum',
    'NU_TOTAL': 'sum',
    'TX_ACERTO': 'mean',
    'ct_alto': 'sum',
    'ct_medio': 'sum',
    'ct_baixo': 'sum',
    'ct_muito_baixo': 'sum'}).reset_index()

# verificar e tratar valores ausentes em TX_ACERTO

ama2024_2serie_porEscola.dropna(subset=['TX_ACERTO'], inplace=True)
print(ama2024_2serie_porEscola.info())

# Gerar csv


ama2024_2serie_porEscola.to_csv('../DadosBrutos/ama2024_2serie.csv', encoding='utf-8',sep = ";" ,index=False)