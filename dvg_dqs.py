import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime

# --- Configuração das Planilhas ---
SHEET_ID_DIVERGENCIA = "1zc_0mrYa9Unw64cVXouMkdbRCswoItlqbtaG4Cw-dyA" 
URL_DIVERGENCIA = f"https://docs.google.com/spreadsheets/d/{SHEET_ID_DIVERGENCIA}/export?format=xlsx"

SHEET_ID_RESUMO = "1GjfNcXngLsT0FKIEBrp4VPRZDmfN_DmuwMzpVa-5D6c"
URL_RESUMO = f"https://docs.google.com/spreadsheets/d/{SHEET_ID_RESUMO}/export?format=xlsx"

# -----------------------------------------------------------------------------
# Funções de Carregamento e Limpeza
# -----------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def carregar_dados_resumo(url):
    try:
        # Lê especificamente a aba RESUMO
        df = pd.read_excel(url, sheet_name='RESUMO', engine='openpyxl')
        
        # Normaliza nomes das colunas: remove espaços e coloca em MAIÚSCULO
        df.columns = df.columns.str.strip().str.upper()
        
        # Mapeia possíveis variações de nomes
        mapeamento = {'DATA': 'DATA', 'CD': 'CD', 'ACURACIDADE': 'ACURACIDADE', 'ACURICIDADE': 'ACURACIDADE'}
        df = df.rename(columns=mapeamento)

        # Validação de colunas
        cols_necessarias = ['DATA', 'CD', 'ACURACIDADE']
        if not all(c in df.columns for c in cols_necessarias):
            st.error(f"Colunas não encontradas em 'RESUMO'. Encontradas: {list(df.columns)}")
            return pd.DataFrame()

        # Tratamento de tipos
        df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce').dt.normalize()
        df['CD'] = df['CD'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        
        # Converte Acuracidade para numérico (trata string "95%" ou "95,5")
        if df['ACURACIDADE'].dtype == 'object':
            df['ACURACIDADE'] = df['ACURACIDADE'].astype(str).str.replace('%', '').str.replace(',', '.')
        
        df['ACURACIDADE'] = pd.to_numeric(df['ACURACIDADE'], errors='coerce')
        
        return df.dropna(subset=['DATA', 'ACURACIDADE']).sort_values('DATA')
    except Exception as e:
        st.error(f"Erro ao acessar aba RESUMO: {e}. Verifique se a planilha está como 'Qualquer pessoa com o link'.")
        return pd.DataFrame()

@st.cache_data
def analisar_e_limpar_dados(df_entrada):
    # (Mantendo sua lógica original de limpeza de divergências)
    col_chave, col_wms, col_erp, col_data = 'CD_PRODUTO', 'QT_PRODUTO_WMS', 'QT_PRODUTO_ERP', 'DATA_REGISTRO'
    df = df_entrada.copy()
    df.columns = df.columns.str.strip() 
    for col in ['CD_EMPRESA', col_chave, 'DS_PRODUTO', 'DS_AREA_ERP', 'NU_PROCESSO']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '').str.strip()
    for col in [col_wms, col_erp]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    if col_data in df.columns:
        df[col_data] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce').dt.normalize()
        df.dropna(subset=[col_data], inplace=True)
    df['DIFERENCA_ATUAL'] = df[col_wms] - df[col_erp] if col_wms in df.columns else 0
    df_diferenca = df[df['DIFERENCA_ATUAL'] != 0].copy()
    df_diferenca['STATUS_ANALISE'] = df_diferenca['DIFERENCA_ATUAL'].apply(lambda x: 'WMS_MAIOR_QUE_ERP (+)' if x > 0 else 'ERP_MAIOR_QUE_WMS (-)')
    return df, df_diferenca

@st.cache_data(ttl=3600)
def carregar_dados_google(url, janela):
    return pd.read_excel(url, sheet_name=None, engine='openpyxl')

# -----------------------------------------------------------------------------
# UI e Layout
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Dashboard Estoque", layout="wide")

st.markdown("""
    <style>
        .kpi-card { background-color: #1E2130; padding: 20px; border-radius: 12px; border-left: 5px solid #00FFC4; }
        .kpi-value { font-size: 32px; font-weight: 800; color: #00FFC4; }
    </style>
""", unsafe_allow_html=True)

try:
    with st.spinner("Carregando dados..."):
        # Dados de Divergência
        janela = datetime.datetime.now().strftime("%H")
        data_dict = carregar_dados_google(URL_DIVERGENCIA, janela)
        df_bruto = pd.concat(data_dict.values(), ignore_index=True)
        df_completo, df_diferenca = analisar_e_limpar_dados(df_bruto)
        
        # Dados de Acuracidade (ABA RESUMO)
        df_resumo = carregar_dados_resumo(URL_RESUMO)

    # Tabs
    tab_dash, tab_dados = st.tabs(["🚀 DASHBOARD", "📑 DADOS"])

    with tab_dash:
        # KPIs (Simplificado)
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="kpi-card">Registros<br><span class="kpi-value">{len(df_completo)}</span></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="kpi-card" style="border-left-color: #FF5252;">Divergentes<br><span class="kpi-value" style="color: #FF5252;">{len(df_diferenca)}</span></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="kpi-card" style="border-left-color: #FFD700;">Acuracidade Média<br><span class="kpi-value" style="color: #FFD700;">{df_resumo["ACURACIDADE"].mean():.1f}%</span></div>', unsafe_allow_html=True)

        st.write("")

        col_esq, col_dir = st.columns([1.5, 1])

        with col_esq:
            # Grafico Top 10
            df_top = df_diferenca.groupby('CD_EMPRESA').size().reset_index(name='Total').nlargest(10, 'Total')
            fig_bar = px.bar(df_top, x='Total', y='CD_EMPRESA', orientation='h', title='🔥 Top 10 CDs com Divergência', color='Total', color_continuous_scale='Reds')
            st.plotly_chart(fig_bar, use_container_width=True)

            # --- O NOVO GRÁFICO DE LINHA ---
            st.markdown("### 📈 Histórico de Acuracidade")
            if not df_resumo.empty:
                fig_line = px.line(df_resumo, x='DATA', y='ACURACIDADE', color='CD', markers=True,
                                   title='Evolução da Acuracidade por CD (Aba RESUMO)')
                fig_line.update_yaxes(ticksuffix="%")
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("Aguardando dados da aba RESUMO...")

        with col_dir:
            # Gráfico de Pizza
            df_area = df_diferenca.groupby('DS_AREA_ERP').size().reset_index(name='Total')
            fig_pie = px.pie(df_area, values='Total', names='DS_AREA_ERP', title='🎯 Distribuição por Área', hole=0.5)
            st.plotly_chart(fig_pie, use_container_width=True)

        # Tabela de Itens
        st.markdown("### 🔎 Detalhes")
        st.dataframe(df_diferenca.head(100), use_container_width=True)

except Exception as e:
    st.error(f"Erro geral: {e}")
    