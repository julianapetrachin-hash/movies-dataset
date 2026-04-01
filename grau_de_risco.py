import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
# st.set_page_config DEVE ser a primeira linha de comando Streamlit
st.set_page_config(
    layout="wide", 
    page_title="Dashboard Risco Logística", 
    page_icon="🚛",
    initial_sidebar_state="collapsed"
)

if "sidebar_state" not in st.session_state:
    st.session_state.sidebar_state = 'collapsed'

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>🔐 Acesso Restrito - Data Unit</h2>", unsafe_allow_html=True)
        password = st.text_input("Digite a senha", type="password")
        if st.button("Entrar"):
            if password == "LOG2026":
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
        return False
    return True

if check_password():
    # CSS Customizado
    st.markdown("""
        <style>
        [data-testid="stStatusWidget"], .stAppDeployButton {display:none !important;}
        #MainMenu, footer {visibility: hidden;}
        .dashboard-title {
            background: linear-gradient(90deg, #1E3A8A 0%, #1e40af 100%);
            padding: 12px; border-radius: 8px; color: white;
            text-align: center; font-weight: bold; font-size: 22px;
            margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        [data-testid="stMetric"] {
            background-color: #111827 !important;
            border: 1px solid #374151 !important;
            border-radius: 10px !important;
            padding: 10px !important;
        }
        </style>
        <div class="dashboard-title">INDICADOR DE RISCO LOGÍSTICA - DATA UNIT</div>
    """, unsafe_allow_html=True)

    # ==========================================
    # 2. CARREGAMENTO DE DADOS (COM CORREÇÃO DE TIPOS)
    # ==========================================
    URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1dSYbGC3dFW2TP01ICfWY55P9OiurB0ngLsmrqM5kSYg/export?format=csv&gid=629990986"

    @st.cache_data(ttl=60)
    def load_data():
        try:
            df = pd.read_csv(URL_PLANILHA)
            df.columns = df.columns.str.strip().str.replace('\n', ' ').str.replace('  ', ' ')
            
            # Garante que colunas de identificação sejam STRING para evitar erro de float vs str
            for c in ['CD', 'TIPO', 'CIDADE']:
                if c in df.columns:
                    df[c] = df[c].astype(str).replace('nan', 'Não Informado')

            cols_num = ['DVG EM em Milhares', 'REC. TEC. em Milhares', 'GRAU DE RISCO GERAL', 'MALHA EM QNT']
            for col in cols_num:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            df['DATA'] = pd.to_datetime(df['DATA'], dayfirst=True).dt.date
            return df
        except Exception as e:
            st.error(f"Erro ao carregar: {e}")
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
        
        if not df_raw.empty:
            datas_todas = sorted(df_raw['DATA'].unique(), reverse=True)
            sel_date = st.selectbox("📅 Selecione a Data", options=datas_todas)
            
            tipos_disp = sorted(df_raw['TIPO'].unique())
            sel_tipos = st.multiselect("Tipo de Unidade", options=tipos_disp, default=tipos_disp)
            
            cds_filtrados = df_raw[df_raw['TIPO'].isin(sel_tipos)]['CD'].unique()
            sel_cds = st.multiselect("Filiais (CDs)", options=sorted(cds_filtrados), default=sorted(cds_filtrados))
        else:
            st.warning("Base de dados vazia.")
            st.stop()

    # ==========================================
    # 4. DASHBOARD (Lógica de Renderização)
    # ==========================================
    def render_dashboard(df_all, date_val, cds_val):
        datas_todas = sorted(df_all['DATA'].unique(), reverse=True)
        idx = datas_todas.index(date_val)
        date_ant = datas_todas[idx + 1] if idx + 1 < len(datas_todas) else date_val

        col_dvg, col_risco, col_malha = 'DVG EM em Milhares', 'GRAU DE RISCO GERAL', 'MALHA EM QNT'
        col_rectec, col_cd = 'REC. TEC. em Milhares', 'CD'
        
        df_at = df_all[(df_all['DATA'] == date_val) & (df_all[col_cd].isin(cds_val))].copy()
        df_ps = df_all[(df_all['DATA'] == date_ant) & (df_all[col_cd].isin(cds_val))].copy()

        # KPIs
        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
        with c1:
            val = df_at[col_risco].mean()
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=val,
                number={'font': {'color': 'white', 'size': 26}, 'valueformat': '.2f'},
                gauge={'axis': {'range': [0, 3]}, 'bar': {'color': "#3B82F6"},
                       'steps': [{'range': [0, 1], 'color': "#22c55e"},
                                 {'range': [1, 2], 'color': "#eab308"},
                                 {'range': [2, 3], 'color': "#ef4444"}]}))
            fig.update_layout(height=150, margin=dict(l=10, r=10, t=20, b=0), paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            dif = df_at[col_dvg].sum() - df_ps[col_dvg].sum()
            st.metric("DIF vs Anterior", f"{dif/1000:+.1f}k", delta=f"{dif/1000:.1f}k", delta_color="inverse")
        with c3:
            st.metric("Qtd Malha", f"{int(df_at[col_malha].sum()):,}")
        with c4:
            st.metric("DVG Atual", f"R$ {df_at[col_dvg].sum()/1000:,.1f}k")

        # Gráfico Pareto
        st.subheader("Concentração de DVG por Unidade")
        df_p = df_at[df_at[col_dvg] > 0].sort_values(col_dvg, ascending=False)
        if not df_p.empty:
            fig_p = go.Figure()
            fig_p.add_trace(go.Bar(x=df_p[col_cd], y=df_p[col_dvg], name="DVG"))
            fig_p.update_layout(height=350, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_p, use_container_width=True)

        # Tabela
        st.subheader("📋 Detalhamento")
        st.dataframe(df_at[[col_cd, 'CIDADE', col_rectec, col_malha, col_dvg, col_risco]], use_container_width=True, hide_index=True)

    render_dashboard(df_raw, sel_date, sel_cds)