import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Magalog | BI Executive", page_icon="📊")

# --- CSS PERSONALIZADO (CORES DO PRINT) ---
st.markdown("""
    <style>
    [data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 0rem !important; margin-top: -45px !important; }
    [data-testid="stAppViewContainer"] { background-color: #0b0e14 !important; }
    
    /* Título Principal Estilo Print */
    .header-box {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 10px; border-radius: 5px; text-align: center;
        margin-bottom: 20px; border-bottom: 3px solid #00d2ff;
    }
    .header-title { color: white !important; font-size: 24px !important; font-weight: 800 !important; letter-spacing: 2px; }

    /* Cards Estilizados */
    .card-kpi {
        background: #1c222d; border: 1px solid #313d4f; border-radius: 10px;
        padding: 15px; text-align: center;
        border-top: 3px solid #00d2ff;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .value-kpi { color: white; font-size: 24px; font-weight: 900; }
    .label-kpi { color: #8b949e; font-size: 12px; text-transform: uppercase; }
    
    /* Container de Gráfico */
    .plot-container {
        background: #1c222d; padding: 15px; border-radius: 10px;
        border: 1px solid #313d4f;
    }
    </style>
""", unsafe_allow_html=True)

# --- ENGINE DE DADOS ---
@st.cache_data(ttl=60)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1iaHnigQGOH5w4xFlZXN0cXYSZlLqPuHE1Pdsgy0XSdI/export?format=csv&gid=1358149674"
    df = pd.read_csv(url).dropna(how='all')
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', str(c).strip().lower()) for c in df.columns]
    return df

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

try:
    df_raw = load_data().copy()
    df_raw['divisional'] = df_raw['cd'].apply(mapear_divisional)
    df_raw['tipo_clean'] = df_raw['tipo'].fillna('').astype(str).str.upper()

    # Mapeamento de valores
    df_raw['v_1c'] = df_raw['1__ciclo'].apply(limpar_valor) if '1__ciclo' in df_raw.columns else 0.0
    df_raw['v_falta'] = df_raw['falta_vol'].apply(limpar_valor) if 'falta_vol' in df_raw.columns else 0.0
    df_raw['v_fat'] = df_raw['faturamento'].apply(limpar_valor) if 'faturamento' in df_raw.columns else 0.0
    df_raw['is_fin'] = df_raw['v_1c'] != 0

    # --- FILTROS (BARRA LATERAL RESTAURADA) ---
    with st.sidebar:
        st.markdown("### 📊 Gerenciamento")
        if st.button("🔄 Atualizar Dados"):
            st.cache_data.clear()
            st.rerun()
        
        t_sel = st.multiselect("Tipo", options=sorted(df_raw['tipo_clean'].unique()))
        d_sel = st.multiselect("Gerente", options=sorted(df_raw['divisional'].unique()))

    df_filt = df_raw.copy()
    if t_sel: df_filt = df_filt[df_filt['tipo_clean'].isin(t_sel)]
    if d_sel: df_filt = df_filt[df_filt['divisional'].isin(d_sel)]

    # --- TÍTULO PRINCIPAL ---
    st.markdown('<div class="header-box"><p class="header-title">PAINEL FECHAMENTO MAGALOG 2026</p></div>', unsafe_allow_html=True)

    # --- KPIS ---
    v_1c = df_filt['v_1c'].sum()
    v_falta = df_filt['v_falta'].sum()
    total_un = len(df_filt)
    fechadas = df_filt['is_fin'].sum()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.markdown(f'<div class="card-kpi"><p class="label-kpi">1º Ciclo</p><p class="value-kpi">R$ {v_1c:,.0f}</p></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="card-kpi"><p class="label-kpi">Falta Vol</p><p class="value-kpi">R$ {v_falta:,.0f}</p></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="card-kpi"><p class="label-kpi">Perda Ano</p><p class="value-kpi">R$ {v_1c + v_falta:,.0f}</p></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="card-kpi"><p class="label-kpi">Health %</p><p class="value-kpi">{(abs(v_1c+v_falta)/df_filt["v_fat"].sum()*100):.3f}%</p></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="card-kpi"><p class="label-kpi">Finalizadas</p><p class="value-kpi">{fechadas}</p></div>', unsafe_allow_html=True)
    c6.markdown(f'<div class="card-kpi"><p class="label-kpi">Pendentes</p><p class="value-kpi" style="color:#ff4b4b">{total_un - fechadas}</p></div>', unsafe_allow_html=True)

    st.write("")

    # --- GRÁFICOS CENTRAIS ---
    g1, g2 = st.columns([1.2, 1])
    
    with g1:
        st.markdown("**Perdas vs. Estornos**")
        df_g = df_filt.groupby('tipo_clean')[['v_1c', 'v_falta']].sum().reset_index()
        df_g['total'] = df_g['v_1c'] + df_g['v_falta']
        
        fig = px.bar(df_g, x='tipo_clean', y='total', color='tipo_clean', 
                     color_discrete_map={'CD':'#3a86ff','LV':'#8338ec','DQS':'#06d6a0'},
                     text_auto='.2s')
        fig.update_layout(template="plotly_dark", height=380, showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    with g2:
        st.markdown("**Status de Saúde Treemap**")
        df_tree = df_filt[df_filt['v_1c'] != 0].copy()
        df_tree['cd_lbl'] = df_tree['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        
        fig_t = px.treemap(df_tree, path=['tipo_clean', 'cd_lbl'], values=df_tree['v_1c'].abs(),
                           color='tipo_clean', color_discrete_map={'CD':'#0040ff','LV':'#aa00ff','DQS':'#00d2ff'})
        fig_t.update_layout(template="plotly_dark", height=380, margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig_t, use_container_width=True)

    # --- TABELA E PIZZA ---
    b1, b2 = st.columns([2, 1])
    
    with b1:
        st.markdown("**Detalhamento Operacional**")
        df_tab = df_filt.copy()
        df_tab['cd_t'] = df_tab['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        df_tab['%'] = (df_tab['v_1c'] / df_tab['v_fat'] * 100).fillna(0)
        
        df_show = df_tab[['divisional', 'cd_t', 'local', 'v_1c', '%', 'v_falta', 'is_fin']].reset_index(drop=True)
        
        # Estilização segura para evitar erro de length
        def style_rows(row):
            color = '#451a1a' if row['v_1c'] < 0 else '#1a4523'
            return [f'background-color: {color}'] * len(row)

        st.dataframe(df_show.style.apply(style_rows, axis=1), use_container_width=True, hide_index=True, height=400)

    with b2:
        st.markdown("**Total Geral por Gerente**")
        df_pi = df_filt.groupby('divisional')['v_1c'].sum().abs().reset_index()
        fig_p = px.pie(df_pi, values='v_1c', names='divisional', hole=0.6,
                       color_discrete_sequence=px.colors.sequential.Blues_r)
        fig_p.update_layout(template="plotly_dark", height=400, showlegend=True, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_p, use_container_width=True)

except Exception as e:
    st.error(f"Erro detectado: {e}")