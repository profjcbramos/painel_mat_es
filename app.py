import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import plotly.express as px



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
    ["Visão Geral", "Regional", "Análise de Impacto"]
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



# --- Página: Análise de Impacto ---################################################################

elif pagina == "Análise de Impacto":
    st.title("📊 Análise de Impacto das Rotinas Pedagógicas")

    # --- Carregamento das bases específicas ---

    @st.cache_data
    def carregar_bases_impacto():
        df_paebes = pd.read_csv('data/paebesMun_23e24.csv', encoding='utf-8-sig')
        df_paebes_lp = pd.read_csv ("data/paebes_LP_23e24.csv", encoding="utf-8-sig")
        df_ama = pd.read_csv('data/ama_2serie_2024_2025_merged.csv', encoding='utf-8-sig')
        df_escolas = pd.read_csv('data/dados_escolas.csv', encoding='utf-8-sig')
        return df_paebes, df_paebes_lp, df_ama, df_escolas

    df_paebes, df_paebes_lp, df_ama, df_escolas  = carregar_bases_impacto()

    # --- Filtros laterais compartilhados ---
    st.sidebar.markdown("### 🎯 Filtros de Recorte")
    regioes_disponiveis = sorted(df_paebes['regional'].dropna().unique())
    selecao_regional = st.sidebar.selectbox("Selecione a Regional:", options=["Todas"] + regioes_disponiveis)

    selecao_municipio = "Todos"
    if selecao_regional != "Todas":
        df_paebes = df_paebes[df_paebes['regional'] == selecao_regional]
        df_ama = df_ama[df_ama['NM_REGIONAL'] == selecao_regional]
        df_escolas = df_escolas[df_escolas['regional'] == selecao_regional]

        municipios_disponiveis = sorted(df_paebes['municipio'].dropna().unique())
        selecao_municipio = st.sidebar.selectbox("Filtrar por Município:", ["Todos"] + municipios_disponiveis)
        if selecao_municipio != "Todos":
            df_paebes = df_paebes[df_paebes['municipio'] == selecao_municipio]
            df_ama = df_ama[df_ama['NM_MUNICIPIO'] == selecao_municipio]
            df_escolas = df_escolas[df_escolas['municipio'] == selecao_municipio]

    # ================= VELOCÍMETROS =================

    st.markdown("## 🎯 Evolução Geral - AMA (Escolas) e Paebes (Municípios)")

    # --- Cálculo da média LP/MAT para AMA ---
    df_ama['TX_ACERTO_24'] = pd.to_numeric(df_ama['TX_ACERTO_24'], errors='coerce')
    df_ama['TX_ACERTO_25'] = pd.to_numeric(df_ama['TX_ACERTO_25'], errors='coerce')
    df_ama_valid = df_ama.dropna(subset=['TX_ACERTO_24', 'TX_ACERTO_25'])
    total_escolas = df_ama_valid.shape[0]
    escolas_evoluiram = df_ama_valid[df_ama_valid['TX_ACERTO_25'] > df_ama_valid['TX_ACERTO_24']].shape[0]

    # --- Paebes ---

    # --- Paebes Matemática ---
    df_paebes ['proficiencia_media_23'] = pd.to_numeric (df_paebes ['proficiencia_media_23'], errors='coerce')
    df_paebes ['proficiencia_media_24'] = pd.to_numeric (df_paebes ['proficiencia_media_24'], errors='coerce')
    df_paebes_valid = df_paebes.dropna (subset=['proficiencia_media_23', 'proficiencia_media_24'])

    # --- Paebes Língua Portuguesa ---
    df_paebes_lp ['proficiencia_media_23'] = pd.to_numeric (df_paebes_lp ['proficiencia_media_23'], errors='coerce')
    df_paebes_lp ['proficiencia_media_24'] = pd.to_numeric (df_paebes_lp ['proficiencia_media_24'], errors='coerce')
    df_paebes_lp_valid = df_paebes_lp.dropna (subset=['proficiencia_media_23', 'proficiencia_media_24'])

    # --- Combinar as médias (por município) ---
    df_merged = pd.merge (
        df_paebes_valid [['municipio', 'proficiencia_media_23', 'proficiencia_media_24']],
        df_paebes_lp_valid [['municipio', 'proficiencia_media_23', 'proficiencia_media_24']],
        on='municipio',
        suffixes=('_mat', '_lp')
    )

    df_merged ['media_23'] = (df_merged ['proficiencia_media_23_mat'] + df_merged ['proficiencia_media_23_lp']) / 2
    df_merged ['media_24'] = (df_merged ['proficiencia_media_24_mat'] + df_merged ['proficiencia_media_24_lp']) / 2

    total_municipios = df_merged.shape [0]


    # --- Porcentagens ---

    perc_escolas = (escolas_evoluiram / total_escolas) * 100 if total_escolas > 0 else 0
    municipios_evoluiram = df_merged [df_merged ['media_24'] > df_merged ['media_23']].shape [0]
    perc_municipios = (municipios_evoluiram / total_municipios) * 100 if total_municipios > 0 else 0

    # --- Velocímetros com Plotly ---
    col1, col2 = st.columns(2)

    with col1:
        fig_escolas = go.Figure(go.Indicator(
            mode="gauge+number",
            value=perc_escolas,
            title={'text': "Escolas com Evolução (AMA)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': 'lightcoral'},
                    {'range': [50, 75], 'color': 'khaki'},
                    {'range': [75, 100], 'color': 'lightgreen'}
                ],
            }
        ))
        st.plotly_chart(fig_escolas, use_container_width=True)

    with col2:
        fig_mun = go.Figure(go.Indicator(
            mode="gauge+number",
            value=perc_municipios,
            title={'text': "Municípios com Evolução (Paebes)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkgreen"},
                'steps': [
                    {'range': [0, 50], 'color': 'lightcoral'},
                    {'range': [50, 75], 'color': 'khaki'},
                    {'range': [75, 100], 'color': 'lightgreen'}
                ],
            }
        ))
        st.plotly_chart(fig_mun, use_container_width=True)

    # A PARTIR DAQUI CONTINUAM OS BOXPLOTS (já usando os dados filtrados acima)


    #============================== boxplot AMA ===========================================================


    st.markdown("### Distribuição da Taxa de Acerto - AMA 2024 x 2025")

    fig = go.Figure()

    # --- Língua Portuguesa ---
    fig.add_trace(go.Box(
        y=df_ama[df_ama['NM_DISCIPLINA'] == 'Língua Portuguesa']['TX_ACERTO_24'],
        name='LP - 2024',
        marker_color='blue',
        width = 0.5
    ))

    fig.add_trace(go.Box(
        y=df_ama[df_ama['NM_DISCIPLINA'] == 'Língua Portuguesa']['TX_ACERTO_25'],
        name='LP - 2025',
        marker_color='lightblue',
        width = 0.5
    ))

    # --- Matemática ---
    fig.add_trace(go.Box(
        y=df_ama[df_ama['NM_DISCIPLINA'] == 'Matemática']['TX_ACERTO_24'],
        name='MAT - 2024',
        marker_color='green',
        width = 0.5
    ))

    fig.add_trace(go.Box(
        y=df_ama[df_ama['NM_DISCIPLINA'] == 'Matemática']['TX_ACERTO_25'],
        name='MAT - 2025',
        marker_color='lightgreen',
        width = 0.5

    ))

    fig.update_layout(
        boxmode='group',         # Agrupa lado a lado
        boxgap=0.1,              # Espaço entre boxplots (menor valor = mais largas)
        boxgroupgap=0.1,         # Espaço entre grupos
        showlegend=False,
        width=800,
        height=400,
        margin=dict(l=40, r=40, t=40, b=40)
    )

    st.plotly_chart(fig, use_container_width=False)

    #================================ Boxplot Paebes ===============================================================

    import plotly.graph_objects as go

    st.markdown ("### 📊 Evolução da Proficiência Média no Paebes (Língua Portuguesa e Matemática)")

    df_plot = df_paebes.copy()
    df_plot = df_plot.dropna(subset=['proficiencia_media_23', 'proficiencia_media_24'])

    # Filtro por regional ou município, se existir
    if selecao_regional != "Todas":
        df_plot = df_plot[df_plot['regional'] == selecao_regional]
        df_paebes_lp = df_paebes_lp [df_paebes_lp['regional'] == selecao_regional]
    if selecao_municipio != "Todos":
        df_plot = df_plot[df_plot['municipio'] == selecao_municipio]
        df_paebes_lp = df_paebes_lp [df_paebes_lp ['municipio'] == selecao_municipio]

    # Criar figura
    fig = go.Figure()

    # --- Matemática ---
    fig.add_trace (go.Box (
        y=df_paebes ['proficiencia_media_23'],
        name="MAT - 2023",
        marker_color='green',
        width=0.5

    ))
    fig.add_trace (go.Box (
        y=df_paebes ['proficiencia_media_24'],
        name="MAT - 2024",
        marker_color='lightgreen',
        width=0.5
    ))

    # --- Língua Portuguesa ---
    fig.add_trace (go.Box (
        y=df_paebes_lp ['proficiencia_media_23'],
        name="LP - 2023",
        marker_color='blue',
        width=0.5
    ))
    fig.add_trace (go.Box (
        y=df_paebes_lp ['proficiencia_media_24'],
        name="LP - 2024",
        marker_color='lightblue',
        width=0.5
    ))

    # Layout
    fig.update_layout(
        showlegend=False,
        yaxis_title="Proficiência Média",
        xaxis_title="",
        template="plotly_dark",
        boxmode='group',         # Agrupa lado a lado
        boxgap=0.1,              # Espaço entre boxplots (menor valor = mais largas)
        boxgroupgap=0.1,         # Espaço entre grupos
        width=800,
        height=400,
        margin=dict(l=40, r=40, t=40, b=40)
    )

    st.plotly_chart(fig, use_container_width=False)

    #============================= Histogramas =============================================
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import numpy as np

    # --- Mapeamento dos níveis e cores ---
    niveis = ['ct_muito_baixo', 'ct_baixo', 'ct_medio', 'ct_alto']
    cores_niveis = ['#ff9999', '#ffcc99', '#99ccff', '#66b266']
    labels_niveis = ['Muito Baixo', 'Baixo', 'Médio', 'Alto']

    # --- Escolher agrupamento: por regional ou por município ---
    if selecao_regional == "Todas":
        df_agrupado = df_ama.copy()
        df_agrupado['agrupador'] = df_agrupado['NM_REGIONAL']
        titulo_geral = 'Espírito Santo'
    else:
        df_agrupado = df_ama[df_ama['NM_REGIONAL'] == selecao_regional].copy()
        df_agrupado['agrupador'] = df_agrupado['NM_MUNICIPIO']
        titulo_geral = selecao_regional

    # --- Adicionar o total agregado como primeiro agrupamento ---
    colunas_niveis = [nivel + sufixo for nivel in niveis for sufixo in ['_24', '_25']]
    df_total = df_agrupado[colunas_niveis].sum().to_frame().T
    df_total['agrupador'] = titulo_geral
    df_total = df_total[[*colunas_niveis, 'agrupador']]


    df_agrupado = pd.concat([df_total, df_agrupado], ignore_index=True)

    # --- Agrupar e somar ---
    df_ama_grouped = df_agrupado.groupby('agrupador').agg({nivel + suf: 'sum' for nivel in niveis for suf in ['_24', '_25']}).reset_index()

    # --- Preparar grid de subplots ---
    num_graficos = df_ama_grouped.shape[0]
    num_colunas = 4
    num_linhas = int(np.ceil(num_graficos / num_colunas))
    altura_total = num_linhas * 350

    fig_grid = make_subplots(rows=num_linhas, cols=num_colunas, subplot_titles=df_ama_grouped['agrupador'].tolist())

    # --- Construir dicionário de dados para cada gráfico ---
    dados_por_grupo = {}
    for _, row in df_ama_grouped.iterrows():
        nome = row['agrupador']
        df_temp = pd.DataFrame([row])
        dados_por_grupo[nome] = df_temp

    # --- Adicionar cada gráfico individual ---
    for idx, (nome, df_sub) in enumerate(dados_por_grupo.items()):
        linha = idx // num_colunas + 1
        coluna = idx % num_colunas + 1

        for ano, sufixo, cor_borda in zip(['2024', '2025'], ['_24', '_25'], ['gray', 'black']):
            valores = df_sub[[f'{nivel}{sufixo}' for nivel in niveis]].iloc[0]
            total = valores.sum()
            if total == 0:
                continue
            porcentagens = (valores / total * 100).round(1)

            for nivel, cor, label in zip(niveis, cores_niveis, labels_niveis):
                fig_grid.add_trace(go.Bar(
                    name=label,
                    x=[ano],
                    y=[porcentagens.get(f'{nivel}{sufixo}', 0)],
                    marker=dict(color=cor, line=dict(width=1.5, color=cor_borda)),
                    showlegend=(idx == 0 and ano == '2025')
                ), row=linha, col=coluna)


    # --- Layout final ---
    fig_grid.update_layout(
        height=altura_total,
        width=1000  ,
        title_text=titulo_geral,
        showlegend=True,
        barmode='stack',
        legend=dict (
            orientation="h",  # horizontal
            yanchor="bottom",  # ancora na parte de baixo da legenda
            y=1.05,  # posição vertical (acima da figura = >1)
            xanchor="center",  # ancora no centro horizontal
            x=0.5  # posição horizontal (0=esquerda, 0.5=centro, 1=direita)
        ),
        margin=dict(t=50, b=100)
    )

    st.markdown("### Distribuição dos Níveis de Desempenho - AMA (2024 x 2025)")
    st.plotly_chart(fig_grid, use_container_width=False)

    #################################################

    # --- Unir as bases de LP e Matemática ---
    df_paebes['disciplina'] = 'Matemática'
    df_paebes_lp['disciplina'] = 'Língua Portuguesa'

    df_paebes_completo = pd.concat([df_paebes, df_paebes_lp], ignore_index=True)

    # --- Conversão de colunas percentuais para numéricas ---
    col_pct_23 = ['abaixo_do_basico_23', 'basico_23', 'proficiente_23', 'avancado_23']
    col_pct_24 = ['abaixo_do_basico_24', 'basico_24', 'proficiente_24', 'avancado_24']

    for col in col_pct_23 + col_pct_24:
        df_paebes_completo[col] = pd.to_numeric(df_paebes_completo[col], errors='coerce')

    # --- Agrupamento por Município ---
    agrupado_mun = df_paebes_completo.groupby(['municipio'], as_index=False).apply(
        lambda grupo: pd.Series({
            'abaixo_do_basico_23': round((grupo['abaixo_do_basico_23'] * grupo['avaliados_(pct)_23']).sum() / grupo['avaliados_(pct)_23'].sum(), 1),
            'basico_23': round((grupo['basico_23'] * grupo['avaliados_(pct)_23']).sum() / grupo['avaliados_(pct)_23'].sum(), 1),
            'proficiente_23': round((grupo['proficiente_23'] * grupo['avaliados_(pct)_23']).sum() / grupo['avaliados_(pct)_23'].sum(), 1),
            'avancado_23': round((grupo['avancado_23'] * grupo['avaliados_(pct)_23']).sum() / grupo['avaliados_(pct)_23'].sum(), 1),
            'abaixo_do_basico_24': round((grupo['abaixo_do_basico_24'] * grupo['avaliados_(pct)_24']).sum() / grupo['avaliados_(pct)_24'].sum(), 1),
            'basico_24': round((grupo['basico_24'] * grupo['avaliados_(pct)_24']).sum() / grupo['avaliados_(pct)_24'].sum(), 1),
            'proficiente_24': round((grupo['proficiente_24'] * grupo['avaliados_(pct)_24']).sum() / grupo['avaliados_(pct)_24'].sum(), 1),
            'avancado_24': round((grupo['avancado_24'] * grupo['avaliados_(pct)_24']).sum() / grupo['avaliados_(pct)_24'].sum(), 1),
            'regional': grupo['regional'].iloc[0]  # manter informação da regional para filtro posterior
        })
    ).reset_index(drop=True)

    # --- Agrupamento por Regional (para gráfico geral) ---
    agrupado_regional = df_paebes_completo.groupby(['regional'], as_index=False).apply(
        lambda grupo: pd.Series({
            'abaixo_do_basico_23': round((grupo['abaixo_do_basico_23'] * grupo['avaliados_(pct)_23']).sum() / grupo['avaliados_(pct)_23'].sum(), 1),
            'basico_23': round((grupo['basico_23'] * grupo['avaliados_(pct)_23']).sum() / grupo['avaliados_(pct)_23'].sum(), 1),
            'proficiente_23': round((grupo['proficiente_23'] * grupo['avaliados_(pct)_23']).sum() / grupo['avaliados_(pct)_23'].sum(), 1),
            'avancado_23': round((grupo['avancado_23'] * grupo['avaliados_(pct)_23']).sum() / grupo['avaliados_(pct)_23'].sum(), 1),
            'abaixo_do_basico_24': round((grupo['abaixo_do_basico_24'] * grupo['avaliados_(pct)_24']).sum() / grupo['avaliados_(pct)_24'].sum(), 1),
            'basico_24': round((grupo['basico_24'] * grupo['avaliados_(pct)_24']).sum() / grupo['avaliados_(pct)_24'].sum(), 1),
            'proficiente_24': round((grupo['proficiente_24'] * grupo['avaliados_(pct)_24']).sum() / grupo['avaliados_(pct)_24'].sum(), 1),
            'avancado_24': round((grupo['avancado_24'] * grupo['avaliados_(pct)_24']).sum() / grupo['avaliados_(pct)_24'].sum(), 1)
        })
    ).reset_index(drop=True)
    agrupado_regional['municipio'] = agrupado_regional['regional']
    agrupado_regional['tipo'] = 'regional'

    # --- Unir bases de município e regional ---
    agrupado_mun['tipo'] = 'municipio'
    df_paebes_niveis = pd.concat([agrupado_regional, agrupado_mun], ignore_index=True)

    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import numpy as np

    # --- Mapeamento de níveis e cores ---
    niveis = ['abaixo_do_basico', 'basico', 'proficiente', 'avancado']
    cores_niveis = ['#ff9999', '#ffcc99', '#99ccff', '#66b266']
    labels_niveis = ['Abaixo do Básico', 'Básico', 'Proficiente', 'Avançado']

    # --- Selecionar agrupamento de acordo com o filtro ---
    if selecao_regional == "Todas":
        df_agrupado = df_paebes_niveis[df_paebes_niveis['tipo'] == 'municipio'].copy()
        df_agrupado['agrupador'] = df_agrupado['municipio']
        titulo_geral = 'Espírito Santo'
        filtro_superior = df_paebes_niveis[df_paebes_niveis['tipo'] == 'regional'].copy()
        filtro_superior = filtro_superior.rename(columns={'municipio': 'agrupador'})
        filtro_superior = filtro_superior[filtro_superior['agrupador'] == titulo_geral]
    else:
        df_agrupado = df_paebes_niveis[(df_paebes_niveis['regional'] == selecao_regional) & (df_paebes_niveis['tipo'] == 'municipio')].copy()
        df_agrupado['agrupador'] = df_agrupado['municipio']
        titulo_geral = selecao_regional
        filtro_superior = df_paebes_niveis[(df_paebes_niveis['municipio'] == selecao_regional) & (df_paebes_niveis['tipo'] == 'regional')].copy()
        filtro_superior['agrupador'] = filtro_superior['municipio']

    # --- Adicionar gráfico total no topo ---
    colunas_niveis = [nivel + suf for nivel in niveis for suf in ['_23', '_24']]
    df_total = filtro_superior[colunas_niveis + ['agrupador']]
    df_agrupado = pd.concat([df_total, df_agrupado], ignore_index=True)

    # --- Agrupamento final ---
    df_paebes_grouped = df_agrupado.groupby('agrupador').agg({col: 'sum' for col in colunas_niveis}).reset_index()

    # --- Subplots grid ---
    num_graficos = df_paebes_grouped.shape[0]
    num_colunas = 4
    num_linhas = int(np.ceil(num_graficos / num_colunas))
    altura_total = num_linhas * 350

    fig_grid = make_subplots(
        rows=num_linhas, cols=num_colunas,
        subplot_titles=df_paebes_grouped['agrupador'].tolist()
    )

    # --- Dicionário por agrupador ---
    dados_por_grupo = {row['agrupador']: row for _, row in df_paebes_grouped.iterrows()}

    # --- Adicionar cada gráfico ---
    for idx, (nome, row) in enumerate(dados_por_grupo.items()):
        linha = idx // num_colunas + 1
        coluna = idx % num_colunas + 1

        for ano, sufixo, cor_borda in zip(['2023', '2024'], ['_23', '_24'], ['gray', 'black']):
            valores = [row[f'{nivel}{sufixo}'] for nivel in niveis]
            total = sum(valores)
            if total == 0:
                continue
            porcentagens = [round(val / total * 100, 1) for val in valores]

            for nivel, cor, label, y_val in zip(niveis, cores_niveis, labels_niveis, porcentagens):
                fig_grid.add_trace(go.Bar(
                    name=label,
                    x=[ano],
                    y=[y_val],
                    marker=dict(color=cor, line=dict(width=1.5, color=cor_borda)),
                    showlegend=(idx == 0 and ano == '2024')
                ), row=linha, col=coluna)

    # --- Layout ---
    fig_grid.update_layout(
        height=altura_total,
        width=1000,
        title_text=titulo_geral,
        showlegend=True,
        barmode='stack',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=50, b=100)
    )

    # --- Renderização ---
    st.markdown("### Distribuição dos Níveis de Desempenho - Paebes (2023 x 2024)")
    st.plotly_chart(fig_grid, use_container_width=False)






