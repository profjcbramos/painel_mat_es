import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import st_folium

import geopandas as gpd

@st.cache_data
def carregar_geodados():
    gdf_municipios = gpd.read_file('data/shapefile_es/ES_Municipios_2024.shp')
    df_municipios_regionais = pd.read_csv('data/municipios_por_regional.csv', encoding='utf-8-sig')
    df_municipios_regionais.rename(columns={'NM_MUN': 'municipio'}, inplace=True)

    # Normalização
    gdf_municipios['municipio'] = gdf_municipios['NM_MUN'].str.upper().str.strip()
    df_municipios_regionais['municipio'] = df_municipios_regionais['municipio'].str.upper().str.strip()

    # Merge
    gdf_mapa = gdf_municipios.merge(df_municipios_regionais, on='municipio', how='left')

    # Simplificação
    gdf_mapa['geometry'] = gdf_mapa['geometry'].simplify(0.001, preserve_topology=True)

    return gdf_mapa

gdf_mapa = carregar_geodados()


# --- Configuração inicial ---
st.set_page_config (page_title='Painel Educacional - SEDU', layout='wide')


# --- Carregamento da base ---
@st.cache_data
def carregar_dados():
    df = pd.read_csv ('data/dados_escolas.csv', encoding='utf-8-sig')
    return df


df = carregar_dados ()

# --- Menu lateral ---
st.sidebar.title ('Menu de Navegação')
pagina = st.sidebar.radio (
    "Escolha a Visualização:",
    ["Visão Geral", "Regional", "Município"]
)

# --- Página: Visão Geral ---
if pagina == "Visão Geral":
    st.subheader ("Distribuição do Idebes por Regional")

    regionais = sorted (df ['regional'].dropna ().unique ())

    fig, axes = plt.subplots (4, 3, figsize=(15, 10))
    axes = axes.flatten ()

    for idx, reg in enumerate (regionais):
        df_reg = df [df ['regional'] == reg]
        sns.boxplot (y=df_reg ['idebes'], ax=axes [idx])
        axes [idx].set_title (f"Regional: {reg}")
        axes [idx].set_ylabel ('Idebes')
        axes [idx].set_xlabel ('')

    # Se sobrarem quadrantes (porque só temos 11 regionais):
    for i in range (len (regionais), len (axes)):
        fig.delaxes (axes [i])

    plt.tight_layout ()
    st.pyplot (fig)

    st.subheader ("Média Normalizada de AMA, Olimpíada e Idebes por Regional")

    # Normalizar AMA
    df_media = df.groupby ('regional') [['ama_tx_acerto', 'olimpiada', 'idebes']].mean ().reset_index ()
    df_media ['ama_tx_acerto'] = df_media ['ama_tx_acerto'] / 10  # Normalizando para 0 a 10

    # Reformatar para plotagem
    df_media_melted = df_media.melt (id_vars='regional', var_name='Indicador', value_name='Média')

    fig, ax = plt.subplots (figsize=(10, 6))
    sns.barplot (x='regional', y='Média', hue='Indicador', data=df_media_melted, ax=ax)
    ax.set_yticklabels ([])  # Remove os números do eixo Y

    # Ajuste de rótulos do eixo X
    plt.xticks (rotation=30, ha='right')
    ax.legend (title='Indicador', bbox_to_anchor=(1.05, 1), loc='upper left')

    # Remover rótulos de valor nas barras (por enquanto)
    st.pyplot (fig)

    st.subheader ("Mapa Coroplético - Regionalização")

    import geopandas as gpd
    import folium
    from streamlit_folium import st_folium
    import matplotlib.colors as mcolors

    # Ler shapefile e CSV de regionais
    gdf_municipios = gpd.read_file ('data/shapefile_es/ES_Municipios_2024.shp')
    df_municipios_regionais = pd.read_csv ('data/municipios_por_regional.csv', encoding='utf-8-sig')
    df_municipios_regionais.rename (columns={'NM_MUN': 'municipio'}, inplace=True)

    # Normalização
    gdf_municipios ['municipio'] = gdf_municipios ['NM_MUN'].str.upper ().str.strip ()
    df_municipios_regionais ['municipio'] = df_municipios_regionais ['municipio'].str.upper ().str.strip ()

    # Merge
    gdf_mapa = gdf_municipios.merge (df_municipios_regionais, on='municipio', how='left')

    # Simplificação para melhorar a performance no Streamlit
    gdf_mapa ['geometry'] = gdf_mapa ['geometry'].simplify (0.001, preserve_topology=True)

    # Criar mapa
    m = folium.Map (location=[-20, -40.3], zoom_start=8)

    # Cores distintas para cada regional
    regionais_unicas = gdf_mapa ['regional'].dropna ().unique ()
    color_list = list (mcolors.TABLEAU_COLORS.values ()) [:len (regionais_unicas)]
    color_dict = dict (zip (regionais_unicas, color_list))

    # Adicionar polígonos
    for _, row in gdf_mapa.iterrows ():
        if pd.notnull (row ['regional']):
            cor = color_dict.get (row ['regional'], 'gray')
            folium.GeoJson (
                row ['geometry'],
                style_function=lambda x, color=cor: {
                    'fillColor': color,
                    'color': 'black',
                    'weight': 0.5,
                    'fillOpacity': 0.6
                },
                tooltip=f"{row ['municipio']} - {row ['regional']}"
            ).add_to (m)

    st_folium (m, width=900, height=900)



# --- Página: Regional ---
elif pagina == "Regional":

    st.title ("📍 Análise por Regional")
       # --- Seletor de Regional ---
    regionais = sorted (df ['regional'].dropna ().unique ())
    selecao_regional = st.sidebar.selectbox ("Selecione a Regional:", regionais)

    # --- Filtrar a base para a regional escolhida ---
    df_regional = df[df['regional'] == selecao_regional]

    # --- HISTOGRAMA POR MUNICÍPIO: IDEBES, AMA, OLIMPÍADA ---
    st.markdown ("### Comparativo entre Municípios da Regional")

    # Normalizar indicadores (AMA de 0-100 para 0-10)
    df_regional ['idebes_norm'] = df_regional ['idebes']
    df_regional ['ama_norm'] = df_regional ['ama_tx_acerto'] / 10
    df_regional ['olimpiada_norm'] = df_regional ['olimpiada']

    # Calcular média por município
    df_municipios = df_regional.groupby ('municipio') [
        ['idebes_norm', 'ama_norm', 'olimpiada_norm']].mean ().reset_index ()

    # Plot
    fig, ax = plt.subplots (figsize=(10, 6))
    largura = 0.25
    x = range (len (df_municipios))

    ax.bar ([p - largura for p in x], df_municipios ['idebes_norm'], width=largura, label='Idebes')
    ax.bar (x, df_municipios ['ama_norm'], width=largura, label='AMA')
    ax.bar ([p + largura for p in x], df_municipios ['olimpiada_norm'], width=largura, label='Olimpíada')

    ax.set_xticks (x)
    ax.set_xticklabels (df_municipios ['municipio'], rotation=45, ha='right')
    ax.get_yaxis ().set_visible (False)  # Oculta o eixo Y
    ax.legend (title='Indicador')

    st.pyplot (fig)

    import folium
    from folium.plugins import HeatMap
    from streamlit_folium import st_folium
    import branca.colormap as cm

    st.markdown ("### Mapa de Desempenho - Idebes por Escola")

    # --- Definir centroide e zoom dinâmico com base na área da regional ---
    municipios_regional = df_regional ['municipio'].unique ().tolist ()
    gdf_regional_geom = gdf_mapa [gdf_mapa ['municipio'].isin (municipios_regional)]

    regional_union = gdf_regional_geom.unary_union
    regional_center = regional_union.centroid
    center_lat = regional_center.y
    center_lon = regional_center.x

    area_km2 = regional_union.area

    # Definir zoom dinâmico
    if area_km2 < 300:
        zoom_level = 10
    elif area_km2 < 700:
        zoom_level = 9
    elif area_km2 < 1500:
        zoom_level = 8
    elif area_km2 < 3000:
        zoom_level = 7
    else:
        zoom_level = 6

    # --- Criar mapa ---
    m = folium.Map (location=[center_lat, center_lon], zoom_start=zoom_level, tiles='cartodbpositron')

    # --- Polígonos dos municípios ---
    for idx, row in gdf_mapa.iterrows ():
        mun = row ['municipio']
        na_regional = mun in municipios_regional

        cor_preenchimento = '#3186cc' if na_regional else '#d3d3d3'
        opacidade_preenchimento = 0.5 if na_regional else 0.2
        espessura_borda = 1.5 if na_regional else 0.5

        if na_regional:
            media_idebes = df_regional [df_regional ['municipio'] == mun] ['idebes'].mean ()
            media_ama = df_regional [df_regional ['municipio'] == mun] ['ama_tx_acerto'].mean ()
            media_olimp = df_regional [df_regional ['municipio'] == mun] ['olimpiada'].mean ()

            popup_text = (
                f"<b>{mun}</b><br>"
                f"Idebes: {media_idebes:.2f}<br>"
                f"AMA: {media_ama:.2f}<br>"
                f"Olimpíada: {media_olimp:.2f}"
            )
        else:
            popup_text = f"<b>{mun}</b> (Fora da regional selecionada)"

        folium.GeoJson (
            row ['geometry'],
            style_function=lambda x, fill_color=cor_preenchimento, border_weight=espessura_borda,
                                  fill_opacity=opacidade_preenchimento: {
                'fillColor': fill_color,
                'color': 'black',
                'weight': border_weight,
                'fillOpacity': fill_opacity
            },
            tooltip=folium.Tooltip (popup_text, sticky=True)
        ).add_to (m)

    # --- Marcadores das escolas com cor proporcional ao Idebes ---
    colormap = cm.linear.YlOrRd_09.scale (0, 10)  # Escala de 0 a 10 (amarelo → vermelho)

    for idx, row in df_regional.iterrows ():
        nome_escola = row ['nome_escola']  # Ajuste para o nome real da sua coluna
        idebes = row ['idebes']
        ama = row ['ama_tx_acerto']
        olimp = row ['olimpiada']

        # Garantir que o valor do Idebes está dentro da escala
        cor = colormap (min (max (idebes, 0), 10))  # Limita entre 0 e 10

        popup_text = (
            f"<b>{nome_escola}</b><br>"
            f"Idebes: {idebes:.2f}<br>"
            f"AMA: {ama:.2f}<br>"
            f"Olimpíada: {olimp:.2f}"
        )

        folium.CircleMarker (
            location=[row ['latitude'], row ['longitude']],
            radius=6,
            color=cor,
            fill=True,
            fill_color=cor,
            fill_opacity=0.8,
            popup=popup_text
        ).add_to (m)

    # --- Adicionar legenda de cores ---
    colormap.caption = 'Idebes por Escola'
    colormap.add_to (m)

    # --- Exibir mapa ---
    st_folium (m, width=900, height=900)

    # --- TABELA RESUMO ---
    st.markdown ("### Resumo dos Dados por Município")

    tabela_resumo = df_regional.groupby ('municipio').agg ({
        'idebes': 'mean',
        'ama_tx_acerto': 'mean',
        'olimpiada': 'mean'
    }).reset_index ()

    tabela_resumo.columns = ['Município', 'Média Idebes', 'Média AMA', 'Média Olimpíada']

    st.dataframe (tabela_resumo.style.format ({
        'Média Idebes': '{:.2f}',
        'Média AMA': '{:.2f}',
        'Média Olimpíada': '{:.2f}'
    }))

    st.markdown ("### Resumo dos Dados por Escola")

    # --- Preparar tabela base ---
    tabela_resumo_escolas = df_regional [['nome_escola', 'municipio', 'idebes', 'ama_tx_acerto', 'olimpiada']].copy ()
    tabela_resumo_escolas.columns = ['Escola', 'Município', 'Idebes', 'AMA', 'Olimpíada']

    # --- Filtro por município ---
    municipios_disponiveis = sorted (tabela_resumo_escolas ['Município'].unique ())
    municipio_selecionado = st.selectbox ("Filtrar por Município:", ["Todos"] + municipios_disponiveis)

    if municipio_selecionado != "Todos":
        tabela_resumo_escolas = tabela_resumo_escolas [tabela_resumo_escolas ['Município'] == municipio_selecionado]

    # --- Campo de busca por escola ---
    busca_escola = st.text_input ("Buscar por nome da escola (ou parte do nome):")

    if busca_escola:
        tabela_resumo_escolas = tabela_resumo_escolas [
            tabela_resumo_escolas ['Escola'].str.contains (busca_escola, case=False, na=False)
        ]

    # --- Opção de ordenação ---
    opcao_ordenacao = st.selectbox (
        "Ordenar por:",
        ["Sem ordenação", "Idebes", "Olimpíada", "AMA"]
    )

    # Aplicar ordenação
    if opcao_ordenacao == "Idebes":
        tabela_resumo_escolas = tabela_resumo_escolas.sort_values (by='Idebes', ascending=False)
    elif opcao_ordenacao == "Olimpíada":
        tabela_resumo_escolas = tabela_resumo_escolas.sort_values (by='Olimpíada', ascending=False)
    elif opcao_ordenacao == "AMA":
        tabela_resumo_escolas = tabela_resumo_escolas.sort_values (by='AMA', ascending=False)

    # --- Exibir tabela formatada ---
    st.dataframe (
        tabela_resumo_escolas.style.format ({
            'Idebes': '{:.2f}',
            'AMA': '{:.2f}',
            'Olimpíada': '{:.2f}'
        })
    )



# --- Página: Município ---
elif pagina == "Município":
    st.title ("🏫 Análise por Município")

    municipios = df ['municipio'].dropna ().unique ()
    municipio_selecionado = st.sidebar.selectbox ('Selecione o Município:', options=sorted (municipios))

    df_filtrado = df [df ['municipio'] == municipio_selecionado]

    st.write (f"Total de escolas no Município {municipio_selecionado}: {df_filtrado.shape [0]}")

    # Exemplo: Mapa das escolas no município
    m = folium.Map (location=[-20.3, -40.3], zoom_start=8)

    for index, row in df_filtrado.iterrows ():
        folium.Marker (
            location=[row ['latitude'], row ['longitude']],
            popup=f"{row ['nome_escola']} - IDEBES: {row ['idebes']}"
        ).add_to (m)

    st_folium (m, width=900, height=600)
