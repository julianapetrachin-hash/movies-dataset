import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    layout="wide", 
    page_title="Dashboard Risco Logística", 
    page_icon="🚛",
    initial_sidebar_state="expanded"
)

# --- CSS PROFISSIONAL E RECUPERAÇÃO DO BOTÃO ---
st.markdown(
    """
    <style>
    /* Esconde lixo visual mas deixa a Sidebar funcional */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;} 

    /* FORÇA O BOTÃO DE ABRIR SIDEBAR A APARECER SEMPRE */
    button[data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
        position: fixed !important;
        top: 15px !important;
        left: 10px !important;
        z-index: 99999;
        background-color: #1e3a8a !important;
        color: white !important;
        border-radius: 50% !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.5);
    }

    /* Ajuste do Container Principal */
    .block-container {
        padding-top: 2rem;
        margin-top: -30px;
    }

    /* TÍTULO ESTILIZADO */
    .dashboard-title {
        background: linear-gradient(90deg, #1E3A8A 0%, #1e40af 100%);
        padding: 12px;
        border-radius: 10px;
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 24px;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }

    /* CARDS PROFISSIONAIS (Efeito Glassmorphism) */
    [data-testid="stMetric"] {
        background: rgba(17, 24, 39, 0.8) !important;
        border: 1px solid rgba(55, 65, 81, 1) !important;
        border-radius: 15px !important;
        padding: 20px !important;
        transition: transform 0.3s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border-color: #3B82F6 !important;
    }
    </style>
    <div class="dashboard-title">INDICADOR DE RISCO LOGÍSTICA - DATA UNIT</div>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. CARREGAMENTO DE DADOS (Original)
# ==========================================
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1dSYbGC3dFW2TP01ICfWY55P9OiurB0ngLsmrqM5kSYg/export?format=csv&gid=629990986"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(URL_PLANILHA)
        df.columns = df.columns.str.strip().str.replace('\n', ' ').str.replace('  ', ' ')
        cols_num = ['DVG EM em Milhares', 'REC. TEC. em Milhares', 'GRAU DE RISCO GERAL', 'MALHA EM QNT']
        for col in cols_num:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df['DATA'] = pd.to_datetime(df['DATA'], dayfirst=True).dt.date
        return df
    except Exception as e:
        return pd.DataFrame()

df_raw = load_data()

# ==========================================
# 3. SIDEBAR E FILTROS
# ==========================================
with st.sidebar:
    st.header("⚙️ Painel de Controle")
    if st.button('🔄 Atualizar Dados'):
        st.cache_data.clear()
        st.rerun()
    st.divider()

    if df_raw is not None and not df_raw.empty:
        datas_todas = sorted(df_raw['DATA'].unique(), reverse=True)
        sel_date = st.selectbox("📅 Data", options=datas_todas, index=0)
        
        col_tipo, col_cd = 'TIPO', 'CD'
        tipos_disp = sorted(df_raw[col_tipo].unique()) if col_tipo in df_raw.columns else []
        sel_tipos = st.multiselect("Tipo", options=tipos_disp, default=tipos_disp)
        
        cds_filtrados = df_raw[df_raw[col_tipo].isin(sel_tipos)][col_cd].unique()
        sel_cds = st.multiselect("CDs", options=sorted(cds_filtrados), default=sorted(cds_filtrados))
    else:
        st.stop()

# ==========================================
# 4. CONTEÚDO VISUAL
# ==========================================
@st.fragment(run_every=600)
def render_dashboard(df_all, date_val, cds_val):
    datas_todas = sorted(df_all['DATA'].unique(), reverse=True)
    idx = datas_todas.index(date_val)
    date_ant = datas_todas[idx + 1] if idx + 1 < len(datas_todas) else date_val

    col_dvg, col_risco, col_malha = 'DVG EM em Milhares', 'GRAU DE RISCO GERAL', 'MALHA EM QNT'
    col_rectec, col_cd = 'REC. TEC. em Milhares', 'CD'
    
    df_at = df_all[(df_all['DATA'] == date_val) & (df_all[col_cd].isin(cds_val))].copy()
    df_ps = df_all[(df_all['DATA'] == date_ant) & (df_all[col_cd].isin(cds_val))].copy()

    # --- KPIs (Layout Simétrico) ---
    c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])

    with c1:
        risco_med_val = df_at[col_risco].mean()
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", 
            value = risco_med_val,
            number = {'font': {'color': 'white', 'size': 26}, 'valueformat': '.2f'},
            title = {'text': "Risco Médio", 'font': {'color': '#94A3B8', 'size': 12}},
            gauge = {
                'axis': {'range': [0, 3]}, 
                'bar': {'color': "#3B82F6"},
                'steps': [
                    {'range': [0, 1], 'color': "#22c55e"}, 
                    {'range': [1, 2], 'color': "#eab308"}, 
                    {'range': [2, 3], 'color': "#ef4444"}
                ]
            }
        ))
        fig_gauge.update_layout(height=120, margin=dict(l=10, r=10, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})

    with c2:
        dif = df_at[col_dvg].sum() - df_ps[col_dvg].sum()
        st.metric(label="DIF vs Anterior", value=f"{dif/1000:+.1f}k", delta=f"{dif/1000:.1f}k", delta_color="inverse")

    with c3:
        st.metric(label="Qtd Malha", value=f"{int(df_at[col_malha].sum()):,}")

    with c4:
        st.metric(label="DVG Atual", value=f"R$ {df_at[col_dvg].sum()/1000:,.1f}k")

    # --- GRÁFICO PARETO E TABELA (Originais) ---
    st.markdown("---")
    # ... (Seu código de Pareto e Tabela aqui embaixo)
    st.subheader("Concentração de DVG por Unidade")
    df_p = df_at[df_at[col_dvg] > 0].sort_values(col_dvg, ascending=False).reset_index(drop=True)
    if not df_p.empty:
        df_p['cum_perc'] = 100 * df_p[col_dvg].cumsum() / df_p[col_dvg].sum()
        fig_p = go.Figure()
        fig_p.add_trace(go.Bar(x=df_p[col_cd].astype(str), y=df_p[col_dvg], name="DVG", marker_color='#3B82F6'))
        fig_p.add_trace(go.Scatter(x=df_p[col_cd].astype(str), y=df_p['cum_perc'], name="%", yaxis="y2", line=dict(color="#ef4444", width=3)))
        fig_p.update_layout(height=380, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis2=dict(overlaying="y", side="right", range=[0, 110]))
        st.plotly_chart(fig_p, use_container_width=True)

# Chamada final
render_dashboard(df_raw, sel_date, sel_cds)