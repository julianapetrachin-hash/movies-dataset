import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime

# --- Configuração da Planilha Google ---
SHEET_ID = "1zc_0mrYa9Unw64cVXouMkdbRCswoItlqbtaG4Cw-dyA" 
URL_GOOGLE_SHEETS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

# -----------------------------------------------------------------------------
# Função de Análise e Limpeza 
# -----------------------------------------------------------------------------
@st.cache_data
def analisar_e_limpar_dados(df_entrada):
    col_chave = 'CD_PRODUTO'
    col_wms = 'QT_PRODUTO_WMS'
    col_erp = 'QT_PRODUTO_ERP'
    col_data = 'DATA_REGISTRO' 

    df = df_entrada.copy()
    df.columns = df.columns.str.strip() 
        
    for col in ['CD_EMPRESA', col_chave, 'DS_PRODUTO', 'DS_AREA_ERP', 'NU_PROCESSO']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    
    for col in [col_wms, col_erp]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    if col_data in df.columns:
        df[col_data] = (
            df[col_data]
            .astype(str)
            .str.strip()
            .pipe(lambda s: pd.to_datetime(s, dayfirst=True, errors='coerce'))
            .dt.normalize() 
        )
        df.dropna(subset=[col_data], inplace=True)
    
    if col_wms in df.columns and col_erp in df.columns:
        df['DIFERENCA_ATUAL'] = df[col_wms] - df[col_erp]
    else:
        df['DIFERENCA_ATUAL'] = 0

    df_diferenca = df[df['DIFERENCA_ATUAL'] != 0].copy()

    def definir_status_sentido(diferenca):
        if diferenca > 0:
            return 'WMS_MAIOR_QUE_ERP (+)'
        elif diferenca < 0:
            return 'ERP_MAIOR_QUE_WMS (-)'
        else:
            return 'SEM_DIFERENCA'
            
    df_diferenca['STATUS_ANALISE'] = df_diferenca['DIFERENCA_ATUAL'].apply(definir_status_sentido)
    
    if col_data in df.columns:
        df_divergencia_por_dia = df[df['DIFERENCA_ATUAL'] != 0].copy()
        df_frequencia = df_divergencia_por_dia.groupby(col_chave)[col_data].nunique().reset_index(name='DIAS_COM_DIVERGENCIA')
        df_diferenca = pd.merge(df_diferenca, df_frequencia, on=col_chave, how='left')
        df_diferenca['DIAS_COM_DIVERGENCIA'] = df_diferenca['DIAS_COM_DIVERGENCIA'].fillna(0).astype(int)
        
        total_dias_analisados = df[col_data].nunique()
        
        def definir_constancia(dias):
            if total_dias_analisados <= 1:
                return 'N/A - Única Data'
            elif dias == total_dias_analisados:
                return 'CONSTANTE (Todas as Datas)'
            elif dias >= total_dias_analisados * 0.5:
                return 'RECORRENTE (>50% das Datas)'
            elif dias > 1:
                return f'ESPORÁDICO ({dias} Dias)'
            else:
                return 'APENAS NESTA DATA' 
                
        df_diferenca['STATUS_CONSTANCIA'] = df_diferenca['DIAS_COM_DIVERGENCIA'].apply(definir_constancia)
    else:
        df_diferenca['DIAS_COM_DIVERGENCIA'] = 1
        df_diferenca['STATUS_CONSTANCIA'] = 'N/A - Data Não Encontrada'

    cols_to_show = [
        'CD_EMPRESA', col_chave, 'DS_PRODUTO', col_wms, col_erp,
        'DIFERENCA_ATUAL', 'STATUS_ANALISE',
        'DIAS_COM_DIVERGENCIA', 'STATUS_CONSTANCIA', 
        'NU_PROCESSO', 'DS_AREA_ERP', col_data 
    ]
    cols_to_keep = [col for col in cols_to_show if col in df_diferenca.columns]
    
    return df.copy(), df_diferenca[cols_to_keep]

# -----------------------------------------------------------------------------
# Carregamento do Google Sheets
# -----------------------------------------------------------------------------
@st.cache_data(ttl=86400) 
def carregar_dados_google(url, janela_atualizacao):
    return pd.read_excel(url, sheet_name=None, engine='openpyxl')

def determinar_janela_atualizacao():
    agora = datetime.datetime.now()
    if agora.hour < 10:
        return f"{agora.date() - datetime.timedelta(days=1)}_pos_15h"
    elif 10 <= agora.hour < 15:
        return f"{agora.date()}_janela_10h"
    else:
        return f"{agora.date()}_janela_15h"

# -----------------------------------------------------------------------------
# Configuração Visual e UI do Dashboard
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Dashboard Diferença Estoque", layout="wide", initial_sidebar_state="collapsed")

# Estilo Customizado (CSS) para os Cards
st.markdown("""
    <style>
        .kpi-card { background-color: #1E2130; padding: 20px; border-radius: 12px; border-left: 5px solid #00FFC4; box-shadow: 2px 2px 10px rgba(0,0,0,0.2); }
        .kpi-title { font-size: 14px; color: #8892B0; margin-bottom: 5px; text-transform: uppercase; font-weight: bold;}
        .kpi-value { font-size: 32px; font-weight: 800; color: #00FFC4; margin: 0;}
        .block-container { padding-top: 2rem; padding-bottom: 0rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown("### 📊 Centro de Comando: Divergência de Estoque (WMS vs ERP)")

try:
    with st.spinner("Sincronizando com o Google Sheets..."):
        chave_cache = determinar_janela_atualizacao()
        data_dict = carregar_dados_google(URL_GOOGLE_SHEETS, chave_cache)
    
    sheet_names = list(data_dict.keys())
    aba_selecionada_display = ", ".join(sheet_names)
    
    with st.sidebar:
        st.header("⚙️ Configurações")
        abas_selecionadas = st.multiselect("Abas (Sheets):", sheet_names, default=sheet_names )
        st.caption(f"Última verificação de janela de cache: {chave_cache}")
        
    if not abas_selecionadas:
        st.warning("Selecione pelo menos uma aba na barra lateral.")
        st.stop()
        
    list_dfs = [data_dict[sheet_name] for sheet_name in abas_selecionadas]
    df_bruto = pd.concat(list_dfs, ignore_index=True)
    df_completo, df_diferenca = analisar_e_limpar_dados(df_bruto)
    
    total_registros = len(df_completo)
    total_diferencas = len(df_diferenca)
    col_data_final = 'DATA_REGISTRO' 
    total_dias_analisados = df_completo[col_data_final].nunique() if col_data_final in df_completo.columns else 1

    with st.sidebar:
        st.markdown("---")
        st.header("Filtros Globais")
        empresas_unicas = ['Todas'] + sorted(list(df_diferenca['CD_EMPRESA'].unique()))
        empresa_selecionada = st.selectbox("Filtrar por Empresa", empresas_unicas)
        
        sentidos_divergencia = ['Ambos'] + list(df_diferenca['STATUS_ANALISE'].unique())
        sentido_selecionado = st.selectbox("Filtrar Sentido da Divergência", sentidos_divergencia)
        
        df_filtrado_base = df_diferenca.copy()
        
        if 'STATUS_CONSTANCIA' in df_diferenca.columns and total_dias_analisados > 1:
            status_constancia_unicos = ['Todos'] + list(df_diferenca['STATUS_CONSTANCIA'].unique())
            if 'N/A - Única Data' in status_constancia_unicos:
                status_constancia_unicos.remove('N/A - Única Data')
            constancia_selecionada = st.multiselect("Status de Constância", status_constancia_unicos, default='Todos')
            
            if 'Todos' not in constancia_selecionada:
                df_filtrado_base = df_filtrado_base[df_filtrado_base['STATUS_CONSTANCIA'].isin(constancia_selecionada)]
                
        df_filtrado = df_filtrado_base.copy()
        if empresa_selecionada != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['CD_EMPRESA'] == empresa_selecionada]
        if sentido_selecionado != 'Ambos':
            df_filtrado = df_filtrado[df_filtrado['STATUS_ANALISE'] == sentido_selecionado]
            
    tab_dashboard, tab_detalhe_completo = st.tabs(["🚀 DASHBOARD", "📑 DADOS CONSOLIDADOS"])

    with tab_dashboard:
        # --- LINHA 1: KPIs ---
        col1, col2, col3, col4 = st.columns(4)
        percentual_diferenca = (total_diferencas / total_registros) * 100 if total_registros > 0 else 0
        
        with col1:
            st.markdown(f'<div class="kpi-card"><p class="kpi-title">Registros Analisados</p><p class="kpi-value">{total_registros:,.0f}</p></div>'.replace(",", "."), unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="kpi-card" style="border-left-color: #FF5252;"><p class="kpi-title">Itens Divergentes</p><p class="kpi-value" style="color: #FF5252;">{total_diferencas:,.0f}</p></div>'.replace(",", "."), unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="kpi-card" style="border-left-color: #FFD700;"><p class="kpi-title">% Divergência</p><p class="kpi-value" style="color: #FFD700;">{percentual_diferenca:.1f}%</p></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="kpi-card" style="border-left-color: #A6ACCD;"><p class="kpi-title">Dias Analisados</p><p class="kpi-value" style="color: #A6ACCD;">{total_dias_analisados:,.0f}</p></div>'.replace(",", "."), unsafe_allow_html=True)
            
        st.write("") # Espaço

        # --- LINHA 2: GRÁFICOS PRINCIPAIS ---
        col_graf_bar, col_graf_pie = st.columns([1.5, 1])
        
        with col_graf_bar:
            df_empresa_sum = df_filtrado.groupby('CD_EMPRESA')['DIFERENCA_ATUAL'].agg('count').reset_index(name='Total_Divergencias')
            df_top_10 = df_empresa_sum.nlargest(10, 'Total_Divergencias').sort_values(by='Total_Divergencias', ascending=True) # Ordena para o Plotly
            df_top_10['CD_EMPRESA'] = "Filial " + df_top_10['CD_EMPRESA'].astype(str) # Força ser texto
            
            fig_bar = px.bar(
                df_top_10, x='Total_Divergencias', y='CD_EMPRESA', orientation='h',
                title='🔥 Top 10 Filiais Críticas (Qtd. de Diferenças)', text='Total_Divergencias',
                color='Total_Divergencias', color_continuous_scale='Reds'
            )
            fig_bar.update_traces(textposition='outside')
            fig_bar.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#8892B0", coloraxis_showscale=False, xaxis_title="", yaxis_title="")
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_graf_pie:
            df_area_sum = df_filtrado.groupby('DS_AREA_ERP')['DIFERENCA_ATUAL'].agg('count').reset_index(name='Total_Divergencias')
            fig_pie = px.pie(
                df_area_sum, values='Total_Divergencias', names='DS_AREA_ERP', 
                title='🎯 Distribuição por Área ERP', hole=0.5, color_discrete_sequence=px.colors.sequential.Teal
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#8892B0", showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)

        # --- LINHA 3: DETALHES ---
        st.markdown("### 🔎 Detalhamento dos Itens")
        df_final = df_filtrado.sort_values(by='DIFERENCA_ATUAL', ascending=False)
        st.dataframe(
            df_final, use_container_width=True, height=350,
            column_config={
                'DIFERENCA_ATUAL': st.column_config.NumberColumn("Diferença", format="%d"),
                'QT_PRODUTO_WMS': st.column_config.NumberColumn("QT WMS", format="%d"),
                'QT_PRODUTO_ERP': st.column_config.NumberColumn("QT ERP", format="%d"),
            }
        )

    with tab_detalhe_completo:
        st.info("Visualização da base bruta importada do Google Sheets.")
        st.dataframe(df_completo, use_container_width=True, height=600)

except Exception as e:
    st.error(f"Erro na conexão com os dados. Detalhes: {e}")