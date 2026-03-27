import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
# Exibe o título estilizado
st.markdown('<div class="dashboard-title">INDICADOR DE RISCO LOGÍSTICA - DATA UNIT</div>', unsafe_allow_html=True)

st.markdown(
    """
    <style>
    /* 1. Esconde botões do GitHub, Fork e Menu padrão */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;} 

    /* 2. Garante que a barra lateral (filtros) funcione e tenha contraste */
    [data-testid="stSidebar"] {
        background-color: #111827;
    }

    /* 3. Ajuste de Espaçamento no Topo para o título não sumir */
    .block-container {
        padding-top: 2rem;
        margin-top: -30px;
    }

    /* 4. Estilização das métricas (Cards pretos) */
    .stMetric { 
        background-color: #111827; 
        border-radius: 10px; 
        padding: 15px; 
        border: 1px solid #374151; 
    }

    /* 5. Classe especial para o Título principal */
    .dashboard-title {
        background: linear-gradient(90deg, #1E3A8A 0%, #1e40af 100%);
        padding: 15px;
        border-radius: 8px;
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 22px;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# ==========================================
# 2. CARREGAMENTO DE DADOS
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
# 3. SIDEBAR E FILTROS (MELHORADO)
# ==========================================
with st.sidebar:
    st.header("⚙️ Painel de Controle")
    
    # Botão de atualização sempre visível
    if st.button('🔄 Atualizar Dados'):
        st.cache_data.clear()
        st.rerun()
        
    st.write(f"Última leitura: {datetime.now().strftime('%H:%M:%S')}")
    st.divider()

    # Verificamos se o DataFrame tem dados antes de mostrar os filtros
    if df_raw is not None and not df_raw.empty:
        st.subheader("Filtros de Pesquisa")
        
        # 1. Filtro de Data
        datas_todas = sorted(df_raw['DATA'].unique(), reverse=True)
        sel_date = st.selectbox("Selecione a Data", options=datas_todas, index=0)
        
        # 2. Filtro de Tipo (Unidade)
        col_tipo = 'TIPO'
        tipos_disp = sorted(df_raw[col_tipo].unique()) if col_tipo in df_raw.columns else []
        sel_tipos = st.multiselect("Tipo de Unidade", options=tipos_disp, default=tipos_disp)
        
        # 3. Filtro de CD (Filiais)
        col_cd = 'CD'
        # Filtra os CDs baseados nos tipos selecionados acima
        cds_filtrados = df_raw[df_raw[col_tipo].isin(sel_tipos)][col_cd].unique()
        cds_disp = sorted(cds_filtrados)
        sel_cds = st.multiselect("Filiais (CDs)", options=cds_disp, default=cds_disp)
    else:
        st.warning("⚠️ Conectando à base de dados... Se demorar, verifique a permissão da planilha.")
        st.stop() # Interrompe aqui se não houver dados

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

    # --- KPIs ---
    c1, c2, c3, c4 = st.columns([1.8, 1.2, 0.7, 1.2])

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
                    {'range': [0, 1], 'color': "green"}, 
                    {'range': [1, 2], 'color': "yellow"}, 
                    {'range': [2, 3], 'color': "red"}
                ]
            }
        ))
        # Margem "t" agora é 0 (mínimo permitido) para evitar o ValueError
        fig_gauge.update_layout(
            height=110, 
            margin=dict(l=10, r=10, t=0, b=0), 
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})

    with c2:
        dvg_hoje = df_at[col_dvg].sum()
        dvg_ontem = df_ps[col_dvg].sum()
        dif_valor = dvg_hoje - dvg_ontem
        st.metric(label="DIF vs Anterior", value=f"{dif_valor/1000:+.1f}k", delta=f"{dif_valor/1000:,.1f}k", delta_color="inverse")

    with c3:
        qtd_malha = int(df_at[col_malha].sum())
        st.metric(label="Qtd Malha", value=f"{qtd_malha:,}")

    with c4:
        dvg_total = df_at[col_dvg].sum()
        st.metric(label="DVG Atual", value=f"R$ {dvg_total/1000:,.1f}k")

    st.divider()

    # --- GRÁFICO PARETO ---
    st.subheader("Concentração de DVG por Unidade")
    df_p = df_at[df_at[col_dvg] > 0].sort_values(col_dvg, ascending=False).reset_index(drop=True)
    if not df_p.empty:
        df_p['cum_perc'] = 100 * df_p[col_dvg].cumsum() / df_p[col_dvg].sum()
        fig_p = go.Figure()
        fig_p.add_trace(go.Bar(x=df_p[col_cd].astype(str), y=df_p[col_dvg], name="DVG", marker_color='#3B82F6', text=[f"R$ {v/1000:.1f}k" for v in df_p[col_dvg]], textposition='outside'))
        fig_p.add_trace(go.Scatter(x=df_p[col_cd].astype(str), y=df_p['cum_perc'], name="%", yaxis="y2", line=dict(color="#F87171", width=3), mode='lines+markers'))
        fig_p.update_layout(height=380, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis2=dict(overlaying="y", side="right", range=[0, 110], showgrid=False), legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"))
        st.plotly_chart(fig_p, use_container_width=True)

    # --- TABELA DETALHADA ---
    st.subheader("📋 Detalhamento Operacional")
    df_table = df_at[[col_cd, 'CIDADE', col_rectec, col_malha, col_dvg, col_risco]].copy()

    def style_performance(styler):
        styler.format({col_dvg: 'R$ {:,.1f}k', col_risco: '{:.2f}', col_malha: '{:,.0f}', col_rectec: 'R$ {:,.0f}k'})
        styler.background_gradient(cmap='RdYlGn_r', subset=[col_dvg])
        styler.background_gradient(cmap='YlOrRd', subset=[col_risco], vmin=0, vmax=3)
        styler.set_properties(**{'text-align': 'center', 'border': '1px solid #262730'})
        return styler

    st.dataframe(style_performance(df_table.style), use_container_width=True, hide_index=True)

# ==========================================
# 5. INICIALIZAÇÃO
# ==========================================
render_dashboard(df_raw, sel_date, sel_cds)