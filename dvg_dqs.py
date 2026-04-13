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
        df = pd.read_excel(url, sheet_name='RESUMO', engine='openpyxl')
        df.columns = df.columns.str.strip().str.upper()
        
        # Mapeamento para a nova coluna solicitada: TOTAL DIF. PÇ
        # Adicionei variações caso haja erro de digitação na planilha
        mapeamento = {
            'DATA': 'DATA', 
            'CD': 'CD', 
            'TOTAL DIF. PÇ': 'DIF_PECAS',
            'TOTA DIF. PÇ': 'DIF_PECAS',
            'TOTAL DIF PÇ': 'DIF_PECAS'
        }
        df = df.rename(columns=mapeamento)

        if not all(c in df.columns for c in ['DATA', 'CD', 'DIF_PECAS']):
            st.error(f"Colunas necessárias não encontradas. Colunas na aba: {list(df.columns)}")
            return pd.DataFrame()

        df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce').dt.normalize()
        df['CD'] = df['CD'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        
        # Converte Diferença de Peças para numérico
        df['DIF_PECAS'] = pd.to_numeric(df['DIF_PECAS'], errors='coerce').fillna(0)
        
        return df.dropna(subset=['DATA']).sort_values('DATA')
    except Exception as e:
        st.error(f"Erro ao acessar aba RESUMO: {e}")
        return pd.DataFrame()

@st.cache_data
def analisar_e_limpar_dados(df_entrada):
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
    
    df['DIFERENCA_ATUAL'] = df[col_wms] - df[col_erp] if col_wms in df.columns else 0
    df_diferenca = df[df['DIFERENCA_ATUAL'] != 0].copy()
    return df, df_diferenca

@st.cache_data(ttl=3600)
def carregar_dados_google(url, janela):
    return pd.read_excel(url, sheet_name=None, engine='openpyxl')

# -----------------------------------------------------------------------------
# Interface Principal (UI)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Dashboard Diferença Peças", layout="wide")

st.markdown("""
    <style>
        .kpi-card { background-color: #1E2130; padding: 20px; border-radius: 12px; border-left: 5px solid #00FFC4; margin-bottom: 20px; }
        .kpi-title { color: #8892B0; font-size: 14px; font-weight: bold; }
        .kpi-value { font-size: 30px; font-weight: 800; color: #00FFC4; }
    </style>
""", unsafe_allow_html=True)

try:
    with st.spinner("Sincronizando dados..."):
        janela = datetime.datetime.now().strftime("%H")
        data_dict = carregar_dados_google(URL_DIVERGENCIA, janela)
        df_bruto = pd.concat(data_dict.values(), ignore_index=True)
        df_completo, df_diferenca = analisar_e_limpar_dados(df_bruto)
        df_resumo = carregar_dados_resumo(URL_RESUMO)

    st.markdown("### 📊 Monitoramento de Diferença de Peças por CD")

    # --- LINHA 1: KPIs ---
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="kpi-card"><p class="kpi-title">TOTAL REGISTROS</p><p class="kpi-value">{len(df_completo)}</p></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card" style="border-left-color: #FF5252;"><p class="kpi-title">ITENS COM DIVERGÊNCIA</p><p class="kpi-value" style="color: #FF5252;">{len(df_diferenca)}</p></div>', unsafe_allow_html=True)
    
    # Soma da Diferença Total de Peças da Aba Resumo
    total_dif_pcs = df_resumo['DIF_PECAS'].sum() if not df_resumo.empty else 0
    c3.markdown(f'<div class="kpi-card" style="border-left-color: #FFD700;"><p class="kpi-title">TOTAL DIF. PEÇAS (Geral)</p><p class="kpi-value" style="color: #FFD700;">{total_dif_pcs:,.0f}</p></div>'.replace(",", "."), unsafe_allow_html=True)

    # --- LINHA 2: GRÁFICOS LADO A LADO ---
    col_bar, col_pie = st.columns([1.5, 1])

    with col_bar:
        df_top = df_diferenca.groupby('CD_EMPRESA').size().reset_index(name='Total').nlargest(10, 'Total')
        df_top['CD_EMPRESA'] = "CD " + df_top['CD_EMPRESA'].astype(str)
        fig_bar = px.bar(df_top, x='Total', y='CD_EMPRESA', orientation='h', 
                         title='🔥 Top 10 CDs com Mais Ocorrências', 
                         color='Total', color_continuous_scale='Reds')
        fig_bar.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#8892B0")
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_pie:
        df_area = df_diferenca.groupby('DS_AREA_ERP').size().reset_index(name='Total')
        fig_pie = px.pie(df_area, values='Total', names='DS_AREA_ERP', 
                         title='🎯 Ocorrências por Área', hole=0.5,
                         color_discrete_sequence=px.colors.sequential.Teal)
        fig_pie.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#8892B0")
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- LINHA 3: GRÁFICO DE LINHA (LARGURA TOTAL) ---
    st.markdown("### 📈 Evolução de Diferença de Peças (Total Dif. Pç)")
    if not df_resumo.empty:
        fig_line = px.line(df_resumo, x='DATA', y='DIF_PECAS', color='CD', markers=True,
                           title='Evolução Histórica da Diferença de Peças por Unidade')
        fig_line.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", 
            paper_bgcolor="rgba(0,0,0,0)", 
            font_color="#8892B0",
            xaxis_title="Data",
            yaxis_title="Qtd. Peças Diferença",
            legend_title="CD",
            hovermode="x unified"
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Aguardando dados da aba RESUMO para exibir o gráfico de evolução.")

except Exception as e:
    st.error(f"Ocorreu um erro no Dashboard: {e}")