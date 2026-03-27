import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA (Sempre a primeira)
# ==========================================
st.set_page_config(layout="wide", page_title="Dashboard Risco Logística", page_icon="🚛")

# ==========================================
# 2. FUNÇÃO DE CARREGAMENTO DE DADOS (COM CACHE)
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
# 3. SIDEBAR (CONTROLES E FILTROS TOTAIS)
# ==========================================
with st.sidebar:
    st.header("⚙️ Painel de Controle")
    if st.button('🔄 Forçar Atualização de Dados'):
        st.cache_data.clear()
        st.rerun()
    st.write(f"Última leitura: {datetime.now().strftime('%H:%M:%S')}")
    st.divider()

    if not df_raw.empty:
        st.subheader("Filtros")
        datas_todas = sorted(df_raw['DATA'].unique(), reverse=True)
        sel_date = st.selectbox("Selecione a Data", options=datas_todas)
        
        col_tipo, col_cd = 'TIPO', 'CD'
        tipos_disp = sorted(df_raw[col_tipo].unique()) if col_tipo in df_raw.columns else []
        sel_tipos = st.multiselect("Tipo de Unidade", options=tipos_disp, default=tipos_disp)
        
        cds_disp = sorted(df_raw[df_raw[col_tipo].isin(sel_tipos)][col_cd].unique())
        sel_cds = st.multiselect("Filiais (CDs)", options=cds_disp, default=cds_disp)
    else:
        st.error("Aguardando dados da planilha...")
        st.stop()

# ==========================================
# 4. CONTEÚDO VISUAL (DENTRO DO FRAGMENTO)
# ==========================================
@st.fragment(run_every=600) # Auto-refresh a cada 10 minutos
def render_dashboard(df_all, date_val, cds_val):
    # Lógica de comparação de datas
    datas_todas = sorted(df_all['DATA'].unique(), reverse=True)
    idx = datas_todas.index(date_val)
    date_ant = datas_todas[idx + 1] if idx + 1 < len(datas_todas) else date_val

    # Filtragem Final
    col_dvg, col_risco, col_malha = 'DVG EM em Milhares', 'GRAU DE RISCO GERAL', 'MALHA EM QNT'
    col_rectec, col_cd = 'REC. TEC. em Milhares', 'CD'
    
    df_at = df_all[(df_all['DATA'] == date_val) & (df_all[col_cd].isin(cds_val))].copy()
    df_ps = df_all[(df_all['DATA'] == date_ant) & (df_all[col_cd].isin(cds_val))].copy()

    # --- CSS Original ---
    st.markdown("""
        <style>
        .stMetric { background-color: #111827; border-radius: 10px; padding: 15px; border: 1px solid #374151; }
        .header-bar { background: linear-gradient(90deg, #1E3A8A 0%, #1e40af 100%); padding: 15px; border-radius: 8px; color: white; margin-bottom: 25px; text-align: center; font-weight: bold; font-size: 22px; }
        .gauge-card { background-color: #111827; border: 1px solid #374151; border-radius: 10px; padding: 10px; height: 100%; }
        </style>
        <div class="header-bar">INDICADOR DE RISCO LOGÍSTICA - DATA UNIT</div>
    """, unsafe_allow_html=True)

    # --- LINHA 1: Restauração dos KPIs Originais com Gauge ---
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1.2])

    with c1:
        st.metric("DVG Atual", f"R$ {df_at[col_dvg].sum()/1000:,.1f}k")
    
    with c2:
        dvg_hoje = df_at[col_dvg].sum()
        dvg_ontem = df_ps[col_dvg].sum()
        dif_valor = dvg_hoje - dvg_ontem
        st.metric("DIF vs Anterior", f"{dif_valor/1000:+.1f}k", delta=f"{dif_valor/1000:,.1f}k", delta_color="inverse")

    with c3:
        st.metric("Qtd Malha", f"{int(df_at[col_malha].sum()):,}")

    with c4:
        # RESTAURAÇÃO DO GAUGE (VELOCÍMETRO)
        st.markdown('<div class="gauge-card">', unsafe_allow_html=True)
        risco_med = df_at[col_risco].mean()
        
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = risco_med,
            number = {'font': {'color': 'white', 'size': 30}, 'valueformat': '.2f'},
            title = {'text': "Risco Médio", 'font': {'color': '#94A3B8', 'size': 12}},
            gauge = {'axis': {'range': [0, 3]}, 'bar': {'color': "#3B82F6"},
                     'steps': [{'range': [0, 1], 'color': "green"}, {'range': [1, 2], 'color': "yellow"}, {'range': [2, 3], 'color': "red"}]}
        ))
        fig_gauge.update_layout(height=130, margin=dict(l=15, r=15, t=30, b=5), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # --- LINHA 2: Gráfico de Pareto (DVG por CD) ---
    st.subheader("Concentração de DVG por Unidade")
    df_p = df_at[df_at[col_dvg] > 0].sort_values(col_dvg, ascending=False).reset_index(drop=True)
    if not df_p.empty:
        df_p['cum_perc'] = 100 * df_p[col_dvg].cumsum() / df_p[col_dvg].sum()
        fig_p = go.Figure()
        # Barras de DVG
        fig_p.add_trace(go.Bar(x=df_p[col_cd].astype(str), y=df_p[col_dvg], name="DVG", marker_color='#3B82F6', text=[f"R$ {v/1000:.1f}k" for v in df_p[col_dvg]], textposition='outside'))
        # Linha de % Acumulada
        fig_p.add_trace(go.Scatter(x=df_p[col_cd].astype(str), y=df_p['cum_perc'], name="%", yaxis="y2", line=dict(color="#F87171", width=3), mode='lines+markers'))
        
        fig_p.update_layout(height=380, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis=dict(title="DVG (Milhões)"), yaxis2=dict(overlaying="y", side="right", range=[0, 110], showgrid=False), legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"), margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_p, use_container_width=True)

    # --- LINHA 3: Tabela Estilizada Original ---
    st.subheader("📋 Detalhamento Operacional")
    df_table = df_at[[col_cd, 'CIDADE', col_rectec, col_malha, col_dvg, col_risco]].copy()

    def style_performance(styler):
        # Formatação Numérica
        styler.format({col_dvg: 'R$ {:,.1f}k', col_risco: '{:.2f}', col_malha: '{:,}'})
        # Gradiente para DVG (Inverso: Vermelho alto, Verde baixo)
        styler.background_gradient(cmap='RdYlGn_r', subset=[col_dvg])
        # Gradiente para Risco (Amarelo/Vermelho)
        styler.background_gradient(cmap='YlOrRd', subset=[col_risco], vmin=0, vmax=3)
        
        # Correção de contraste do texto no Risco
        def color_contrast(val):
            if isinstance(val, (int, float)) and val < 1.5: return 'color: black; font-weight: bold;'
            return 'color: white; font-weight: bold;'
        
        styler.map(color_contrast, subset=[col_risco])
        styler.set_properties(**{'text-align': 'center', 'border': '1px solid #262730'})
        return styler

    st.dataframe(style_performance(df_table.style), use_container_width=True, hide_index=True)

# ==========================================
# 5. INICIALIZAÇÃO
# ==========================================
render_dashboard(df_raw, sel_date, sel_cds)