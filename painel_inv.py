import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Magalog | BI Executive", page_icon="📊")

# --- CSS (Espaçamento Superior e Estilo Magalog) ---
st.markdown("""
    <style>
    [data-testid="stHeader"] { display: none; }
    .block-container { 
        padding-top: 1.5rem !important; 
        margin-top: -15px !important; 
    }
    [data-testid="stAppViewContainer"] { background-color: #0b0e14 !important; }
    
    .header-box {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 15px; border-radius: 5px; text-align: center;
        margin-bottom: 25px; border-bottom: 3px solid #00d2ff;
    }
    .header-title { color: white !important; font-size: 26px !important; font-weight: 800 !important; letter-spacing: 2px; }

    .card-kpi {
        background: #1c222d; border: 1px solid #313d4f; border-radius: 10px;
        padding: 15px; text-align: center; border-top: 3px solid #00d2ff;
        min-height: 110px;
    }
    .value-kpi { color: white; font-size: 24px; font-weight: 900; margin: 0; }
    .label-kpi { color: #8b949e; font-size: 11px; text-transform: uppercase; margin-bottom: 5px; }
    .sub-value { color: #00d2ff; font-size: 12px; font-weight: 700; margin-top: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE LIMPEZA PESADA ---
@st.cache_data(ttl=60)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1iaHnigQGOH5w4xFlZXN0cXYSZlLqPuHE1Pdsgy0XSdI/export?format=csv&gid=1358149674"
    df = pd.read_csv(url).dropna(how='all')
    df.columns = [re.sub(r'[^a-z0-9]', '_', str(c).strip().lower()) for c in df.columns]
    return df

def force_numeric(v):
    if pd.isna(v): return 0.0
    # Remove R$, espaços e ajusta separadores
    s = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    s = re.sub(r'[^0-9\.\-]', '', s)
    try:
        return float(s)
    except:
        return 0.0

try:
    df_raw = load_data().copy()
    
    # Identificação de Colunas
    c_1c = next((c for c in df_raw.columns if '1' in c and 'ciclo' in c), None)
    c_falta = next((c for c in df_raw.columns if 'falta' in c and 'vol' in c), None)
    c_fat = next((c for c in df_raw.columns if 'faturamento' in c or 'fat' in c), None)
    c_div = next((c for c in df_raw.columns if 'divisional' in c or 'gerente' in c), None)

    # 1ª CAMADA DE PROTEÇÃO (VETORIZADA)
    # Convertemos para String, limpamos e forçamos o tipo Float64 do Pandas
    for col_ref, col_name in [(c_1c, 'v_1c'), (c_falta, 'v_falta'), (c_fat, 'v_fat')]:
        if col_ref:
            df_raw[col_name] = df_raw[col_ref].apply(force_numeric).astype(float)
        else:
            df_raw[col_name] = 0.0
    
    df_raw['tipo_clean'] = df_raw['tipo'].fillna('OUTROS').astype(str).str.upper().str.strip()
    df_raw['cd_t'] = df_raw['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
    df_raw['div_clean'] = df_raw[c_div].fillna('OUTROS').astype(str).str.upper() if c_div else 'OUTROS'
    df_raw['is_fin'] = df_raw['v_1c'] != 0

    # --- SIDEBAR (FILTROS REATIVADOS) ---
    with st.sidebar:
        st.header("⚙️ Controle")
        if st.button("🔄 Atualizar Dados"):
            st.cache_data.clear()
            st.rerun()
        f_tipo = st.multiselect("Tipo", options=sorted(df_raw['tipo_clean'].unique()))
        f_ger = st.multiselect("Gerente", options=sorted(df_raw['div_clean'].unique()))
        f_cd = st.multiselect("CD", options=sorted(df_raw['cd_t'].unique()))

    df_filt = df_raw.copy()
    if f_tipo: df_filt = df_filt[df_filt['tipo_clean'].isin(f_tipo)]
    if f_ger: df_filt = df_filt[df_filt['div_clean'].isin(f_ger)]
    if f_cd: df_filt = df_filt[df_filt['cd_t'].isin(f_cd)]

    # --- HEADER ---
    st.markdown('<div class="header-box"><p class="header-title">PAINEL FECHAMENTO MAGALOG 2026</p></div>', unsafe_allow_html=True)

    # --- KPIs (Ordem do Print) ---
    v_1c_sum = df_filt['v_1c'].sum()
    v_falta_sum = df_filt['v_falta'].sum()
    v_perda_total = v_1c_sum + v_falta_sum
    faturamento = df_filt['v_fat'].sum()
    perc_perda = (abs(v_perda_total) / faturamento * 100) if faturamento > 0 else 0.0
    
    total_un = len(df_filt)
    finalizadas = df_filt['is_fin'].sum()

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: st.markdown(f'<div class="card-kpi"><p class="label-kpi">Perda Ano</p><p class="value-kpi">R$ {v_perda_total:,.0f}</p></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="card-kpi"><p class="label-kpi">1º Ciclo</p><p class="value-kpi">R$ {v_1c_sum:,.0f}</p></div>', unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="card-kpi"><p class="label-kpi">Falta Vol</p><p class="value-kpi">R$ {v_falta_sum:,.0f}</p></div>', unsafe_allow_html=True)
    with k4: st.markdown(f'<div class="card-kpi"><p class="label-kpi">% Perdas</p><p class="value-kpi">{perc_perda:.3f}%</p></div>', unsafe_allow_html=True)
    with k5: st.markdown(f'''<div class="card-kpi"><p class="label-kpi">Status Unidades</p><p class="value-kpi">{total_un}</p>
                <p class="sub-value"><span style="color:#00d2ff">Fin: {finalizadas}</span> | <span style="color:#ff4b4b">Pend: {total_un-finalizadas}</span></p></div>''', unsafe_allow_html=True)

    # --- GRÁFICOS ---
    g1, g2 = st.columns([1.2, 1])
    with g1:
        st.markdown("**Perdas vs. Estornos (Visão por Tipo)**")
        df_g = df_filt.groupby('tipo_clean')[['v_1c', 'v_falta']].sum().sum(axis=1).reset_index(name='total')
        fig = px.bar(df_g, x='tipo_clean', y=df_g['total'].abs(), color='tipo_clean', 
                     color_discrete_map={'CD':'#3a86ff','LV':'#8338ec','DQS':'#06d6a0'},
                     text=df_g['total'].apply(lambda x: f"R$ {x:,.0f}"))
        fig.update_layout(template="plotly_dark", height=380, showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    with g2:
        st.markdown("**Status de Saúde Treemap**")
        df_tree = df_filt[df_filt['v_1c'] != 0].copy()
        fig_t = px.treemap(df_tree, path=['tipo_clean', 'cd_t'], values=df_tree['v_1c'].abs(),
                           color='tipo_clean', color_discrete_map={'CD':'#0040ff','LV':'#aa00ff','DQS':'#00d2ff'})
        fig_t.update_layout(template="plotly_dark", height=380, margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig_t, use_container_width=True)

    # --- TABELA (Sanitização Final Sênior) ---
    st.markdown("**Detalhamento Operacional**")
    df_tab = df_filt.copy()
    df_tab['perc_unid'] = (df_tab['v_1c'] / df_tab['v_fat'] * 100).replace([float('inf'), float('-inf')], 0).fillna(0)
    
    # Seleção de colunas para exibição
    df_show = df_tab[['tipo_clean', 'cd_t', 'div_clean', 'v_1c', 'perc_unid', 'v_falta', 'is_fin']].reset_index(drop=True)
    
    # 2ª CAMADA DE PROTEÇÃO: Função de estilo com cast local forçado
    def style_final(row):
        try:
            # Forçamos a leitura como float para a comparação lógica
            val = float(row['v_1c'])
        except:
            val = 0.0
        
        color = '#451a1a' if val < 0 else '#1a4523'
        return [f'background-color: {color}'] * len(row)

    # Renderização final com formatação de MOEDA R$
    st.dataframe(
        df_show.style.apply(style_final, axis=1)
        .format({
            'v_1c': 'R$ {:,.2f}', 
            'v_falta': 'R$ {:,.2f}', 
            'perc_unid': '{:.4f}%'
        }), 
        use_container_width=True, hide_index=True, height=450
    )

except Exception as e:
    st.error(f"Erro Crítico de Renderização: {e}")