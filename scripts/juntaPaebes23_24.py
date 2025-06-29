import pandas as pd

# carregar dados de 2023 e de 2024

paebesMun23 = pd.read_csv("D:\PÓS MDE\Seminario_VD\DadosBrutos\paebesMun2023.csv")
paebesMun24 = pd.read_csv("D:\PÓS MDE\Seminario_VD\DadosBrutos\paebesMun2024.csv")

# revisar colunas para fazer o merge
print('paebesMun23:')
for column in paebesMun23.columns:
     print(f'{column}')

print('\n')

print('paebesMun24:')
for column in paebesMun24.columns:
     print(f'{column}')
# verificar nomes dos municípios e normalizar se necessário

set_23 = set(paebesMun23["municipio"])
set_24 = set(paebesMun24["municipio"])

interseção = set_23 & set_24  # municípios em comum
print(f"Municípios em comum: {len(interseção)}")

so_em_23 = set_23 - set_24
so_em_24 = set_24 - set_23

print("Somente em 2023:", sorted(so_em_23))
print("Somente em 2024:", sorted(so_em_24))

# Acrescentar coluna de edição (2024 e 2024)
# tratar a questão das regionais em uma base e código na outra
    # Não é necessário, pois já se resolve no merge
# fazer o merge
    # acrescentar sufixos

paebesMun23 = paebesMun23.rename(columns={
    col: f"{col}_23" for col in paebesMun23.columns if col not in ["municipio", "codigo_da_regional"]
})

paebesMun24 = paebesMun24.rename(columns={
    col: f"{col}_24" for col in paebesMun24.columns if col not in ["municipio", "regional"]
})

paebesMun_23e24 = pd.merge(paebesMun23, paebesMun24, on="municipio", how="inner")

# verificar

print(paebesMun_23e24.info())
# Remove e guarda a coluna
regional = paebesMun_23e24.pop("regional")

# Insere na posição desejada (ex: no início, índice 0)
paebesMun_23e24.insert(1, "regional", regional)  # 1 para vir logo após 'municipio'

print(paebesMun_23e24.info())

# Acrescentar coluna de evolução

paebesMun_23e24["evolucao_proficiencia"] = (
    paebesMun_23e24["proficiencia_media_24"] - paebesMun_23e24["proficiencia_media_23"]
)

# salvar em csv

paebesMun_23e24.to_csv("D:\PÓS MDE\Seminario_VD\data\paebesMun_23e24.csv", index=False)
