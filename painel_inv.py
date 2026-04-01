import streamlit as st
import pandas as pd
import plotly.express as px
import re
import time

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Magalog | BI Executive", page_icon="📊")

# --- CSS (TOPO ABSOLUTO) ---
st.markdown("""
    <style>
    [data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 0rem !important; margin-top: -45px !important; }
    [data-testid="stAppViewContainer"] { background-color: #0d1117 !important; }
    .header-box {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%) !important;
        padding: 0.8rem !important; border-radius: 0 0 15px 15px; text-align: center;
        margin-bottom: 1.5rem !important; box-shadow: 0 4px 15px rgba(0, 210, 255, 0.4);
    }
    .header-title { color: white !important; font-size: 24px !important; font-weight: 800 !important; margin:0; }
    .card-kpi {
        background: #161b22; border: 1px solid #30363d; border-radius: 12px;
        padding: 15px; text-align: center; min-height: 110px; border-bottom: 4px solid #00d2ff !important;
    }
    .plot-container {
        background-color: #161b22; padding: 15px; border-radius: 15px;
        border: 1px solid #30363d; box-shadow: 0 6px 12px rgba(0,0,0,0.4);
    }
    </style>
""", unsafe_allow_html=True)

def limpar_valor(v):
    if pd.isna(v) or str(v).strip() in ["", "-", "nan"]: return 0.0
    val = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    val = re.sub(r'[^0-9\.\-]', '', val)
    try: return float(val)
    except: return 0.0

def mapear_divisional(cd):
    try:
        n_cd = int(re.sub(r'\D', '', str(cd).split('.')[0]))
        if n_cd in [590, 300, 50]: return 'Renato Nesello'
        elif n_cd in [2650, 994, 991, 1100, 1500, 1800, 1250]: return 'Antônio Paiva'
        elif n_cd in [350, 5200, 2900, 94, 490, 550, 2500, 1440]: return 'Christian'
        elif n_cd in [204, 2489, 97, 549, 2599, 1116, 1889, 389, 1879, 299, 1899, 2989, 5589, 1450, 49, 2999, 2099, 985, 93, 5289, 5299, 2649, 893, 5599, 1869, 1390]: return 'Mileide'
    except: pass
    return 'Outros'

@st.cache_data(ttl=60)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1iaHnigQGOH5w4xFlZXN0cXYSZlLqPuHE1Pdsgy0XSdI/export?format=csv&gid=1358149674"
    df = pd.read_csv(url).dropna(how='all')
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', str(c).strip().lower()) for c in df.columns]
    return df

try:
    # 1. CARGA LIMPA
    df_raw = load_data().copy()
    df_raw['tipo_clean'] = df_raw['tipo'].fillna('').astype(str).str.upper().str.strip()
    df_raw['divisional'] = df_raw['cd'].apply(mapear_divisional)
    
    # Identificar colunas dinamicamente
    c_1c = next((c for c in df_raw.columns if '1__ciclo' in c), None)
    c_fat = next((c for c in df_raw.columns if 'faturamento' in c), None)
    c_fal = next((c for c in df_raw.columns if 'falta_vol' in c), None)

    df_raw['v_1c'] = df_raw[c_1c].apply(limpar_valor) if c_1c else 0.0
    df_raw['v_fat'] = df_raw[c_fat].apply(limpar_valor) if c_fat else 0.0
    df_raw['v_falta'] = df_raw[c_fal].apply(limpar_valor) if c_fal else 0.0
    df_raw['is_fin'] = df_raw['v_1c'] != 0

    # SIDEBAR
    with st.sidebar:
        st.header("⚙️ Gerenciamento")
        if st.button("🔄 Atualizar Dados"): 
            st.cache_data.clear()
            st.rerun()
        t_sel = st.multiselect("Filtrar por Tipo", options=sorted(df_raw['tipo_clean'].unique()))
        d_sel = st.multiselect("Filtrar Gerente", options=sorted(df_raw['divisional'].unique()))

    # FILTRAGEM
    df_filt = df_raw.copy()
    if t_sel: df_filt = df_filt[df_filt['tipo_clean'].isin(t_sel)]
    if d_sel: df_filt = df_filt[df_filt['divisional'].isin(d_sel)]

    # HEADER
    st.markdown('<div class="header-box"><p class="header-title">BI FECHAMENTO MAGALOG 2026</p></div>', unsafe_allow_html=True)

    # KPIS
    v_1c_sum = df_filt['v_1c'].sum()
    v_falta_sum = df_filt['v_falta'].sum()
    total_uds = len(df_filt)
    finalizadas = df_filt['is_fin'].sum()

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: st.markdown(f'<div class="card-kpi">PERDA TOTAL<br><b>R$ {v_1c_sum + v_falta_sum:,.0f}</b></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="card-kpi">FALTA VOL.<br><b>R$ {v_falta_sum:,.0f}</b></div>', unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="card-kpi">UNIDADES<br><b>{total_uds}</b></div>', unsafe_allow_html=True)
    with k4: st.markdown(f'<div class="card-kpi">FINALIZADAS<br><b style="color:#00d2ff">{finalizadas}</b></div>', unsafe_allow_html=True)
    with k5: st.markdown(f'<div class="card-kpi">PENDENTES<br><b style="color:#ff4b4b">{total_uds - finalizadas}</b></div>', unsafe_allow_html=True)

    # GRÁFICOS LADO A LADO
    g1, g2 = st.columns([1, 1.2])
    with g1:
        st.subheader("📊 Resultado por Tipo")
        st.markdown('<div class="plot-container">', unsafe_allow_html=True)
        df_p = df_filt.groupby('tipo_clean')[['v_1c', 'v_falta']].sum().sum(axis=1).reset_index(name='val')
        st.plotly_chart(px.bar(df_p[df_p['val']!=0], x='tipo_clean', y='val', color='tipo_clean', template="plotly_dark", height=350), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with g2:
        st.subheader("🏢 Saúde (Por CD)")
        st.markdown('<div class="plot-container">', unsafe_allow_html=True)
        df_tree = df_filt[df_filt['v_1c'] != 0].copy()
        df_tree['cd_lbl'] = df_tree['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        # HIERARQUIA PARA SEPARAR OS CDs
        fig_t = px.treemap(df_tree, path=[px.Constant("Rede"), 'tipo_clean', 'cd_lbl'], values=df_tree['v_1c'].abs(), color='tipo_clean', template="plotly_dark", height=350)
        fig_t.update_traces(textinfo="label+value", texttemplate="<b>%{label}</b><br>R$ %{value:,.0f}")
        st.plotly_chart(fig_t, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # TABELA E PIZZA
    b1, b2 = st.columns([2.5, 1.2])
    with b1:
        st.subheader("📋 Detalhamento")
        # FORÇAR OBJETO NOVO PARA A TABELA (Reset Index + Copy)
        df_final_tab = df_filt.copy()
        df_final_tab['%_unid'] = (df_final_tab['v_1c'] / df_final_tab['v_fat'] * 100).fillna(0)
        df_final_tab['cd_t'] = df_final_tab['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        
        # Seleção estrita das colunas
        df_display = df_final_tab[['semestre', 'tipo_clean', 'divisional', 'cd_t', 'local', 'v_1c', '%_unid', 'v_falta', 'is_fin']].reset_index(drop=True)
        
        # AQUI REATIVAMOS O ESTILO USANDO UMA FUNÇÃO QUE NÃO QUEBRA
        def color_v1c(val):
            return f'background-color: {"#451a1a" if val < 0 else "#1a4523"}'

        # Renderizamos com uma KEY única baseada no tempo para forçar o Streamlit a destruir o cache antigo
        st.dataframe(
            df_display.style.map(color_v1c, subset=['v_1c']), 
            column_config={"v_1c": st.column_config.NumberColumn("Resultado", format="R$ %.2f"), "%_unid": st.column_config.NumberColumn("% Unid", format="%.4f%%")},
            use_container_width=True, hide_index=True, height=450,
            key=f"df_table_{int(time.time())}"
        )
    
    with b2:
        st.subheader("📍 Perda / Gerente")
        df_pi = df_filt[df_filt['divisional'] != "Outros"].copy()
        if not df_pi.empty:
            st.plotly_chart(px.pie(df_pi, values=df_pi['v_1c'].abs(), names='divisional', hole=0.6, template="plotly_dark", height=450), use_container_width=True)

except Exception as e:
    st.error(f"Erro Crítico: {e}")