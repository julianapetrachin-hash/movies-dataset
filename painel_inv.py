import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Magalog | BI Executive", page_icon="📊")

# --- CSS (Respiro Superior e Estilo Neon do Print) ---
st.markdown("""
    <style>
    [data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 2.5rem !important; margin-top: -10px !important; }
    [data-testid="stAppViewContainer"] { background-color: #0b0e14 !important; }
    .header-box {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 15px; border-radius: 5px; text-align: center;
        margin-bottom: 25px; border-bottom: 3px solid #00d2ff;
    }
    .header-title { color: white !important; font-size: 26px !important; font-weight: 800 !important; letter-spacing: 2px; }
    .card-kpi {
        background: #1c222d; border: 1px solid #313d4f; border-radius: 10px;
        padding: 15px; text-align: center; border-top: 3px solid #00d2ff; min-height: 110px;
    }
    .value-kpi { color: white; font-size: 24px; font-weight: 900; margin: 0; }
    .label-kpi { color: #8b949e; font-size: 11px; text-transform: uppercase; margin-bottom: 5px; }
    .sub-value { color: #00d2ff; font-size: 12px; font-weight: 700; margin-top: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- LIMPEZA DE DADOS SÊNIOR (TRATA #DIV/0, R$, % e TEXTOS) ---
def universal_clean(v):
    if pd.isna(v): return 0.0
    s = str(v).strip().upper()
    if any(err in s for err in ["#DIV/0", "NAN", "NONE", "#VALUE", "-"]): return 0.0
    
    # Remove símbolos financeiros e de unidade
    s = s.replace('R$', '').replace('%', '').replace(' ', '')
    
    # Ajuste de separadores: remove ponto de milhar e troca vírgula por ponto decimal
    if ',' in s and '.' in s: s = s.replace('.', '').replace(',', '.')
    elif ',' in s: s = s.replace(',', '.')
    
    # Mantém apenas números, ponto e o sinal de menos
    s = re.sub(r'[^0-9\.\-]', '', s)
    try:
        return float(s)
    except:
        return 0.0

@st.cache_data(ttl=60)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1iaHnigQGOH5w4xFlZXN0cXYSZlLqPuHE1Pdsgy0XSdI/export?format=csv&gid=1358149674"
    df = pd.read_csv(url).dropna(how='all')
    df.columns = [re.sub(r'[^a-z0-9]', '_', str(c).strip().lower()) for c in df.columns]
    return df

try:
    df_raw = load_data().copy()
    
    # Identificação Dinâmica de Colunas (Foco em 1º Ciclo, Falta e Faturamento)
    c_1c = next((c for c in df_raw.columns if '1' in c and 'ciclo' in c), None)
    c_fat = next((c for c in df_raw.columns if 'faturamento' in c or 'fat' in c), None)
    c_falta = next((c for c in df_raw.columns if 'falta' in c and 'vol' in c), None)
    
    # Limpeza e Conversão forçada para Float
    df_raw['v_1c'] = df_raw[c_1c].apply(universal_clean).astype(float) if c_1c else 0.0
    df_raw['v_fat'] = df_raw[c_fat].apply(universal_clean).astype(float) if c_fat else 0.0
    df_raw['v_falta'] = df_raw[c_falta].apply(universal_clean).astype(float) if c_falta else 0.0
    
    df_raw['tipo_clean'] = df_raw['tipo'].fillna('OUTROS').astype(str).str.upper()
    df_raw['cd_t'] = df_raw['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
    df_raw['is_fin'] = df_raw['v_1c'] != 0

    # --- FILTROS (RESTAURADOS) ---
    with st.sidebar:
        st.header("⚙️ Filtros Executivos")
        if st.button("🔄 Atualizar Dados"): st.cache_data.clear(); st.rerun()
        f_tipo = st.multiselect("Filtrar Tipo", options=sorted(df_raw['tipo_clean'].unique()))
        f_cd = st.multiselect("Filtrar CD", options=sorted(df_raw['cd_t'].unique()))
        f_ger = st.multiselect("Filtrar Gerente", options=sorted(df_raw['divisional'].unique()) if 'divisional' in df_raw.columns else [])

    df_filt = df_raw.copy()
    if f_tipo: df_filt = df_filt[df_filt['tipo_clean'].isin(f_tipo)]
    if f_cd: df_filt = df_filt[df_filt['cd_t'].isin(f_cd)]
    if f_ger: df_filt = df_filt[df_filt['divisional'].isin(f_ger)]

    # --- DASHBOARD ---
    st.markdown('<div class="header-box"><p class="header-title">PAINEL FECHAMENTO MAGALOG 2026</p></div>', unsafe_allow_html=True)
    
    # KPIs
    v_perda_total = df_filt['v_1c'].sum() + df_filt['v_falta'].sum()
    fat_soma = df_filt['v_fat'].sum()
    perc_p = (abs(v_perda_total) / fat_soma * 100) if fat_soma > 0 else 0.0

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: st.markdown(f'<div class="card-kpi"><p class="label-kpi">Perda Ano</p><p class="value-kpi">R$ {v_perda_total:,.0f}</p></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="card-kpi"><p class="label-kpi">1º Ciclo</p><p class="value-kpi">R$ {df_filt["v_1c"].sum():,.0f}</p></div>', unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="card-kpi"><p class="label-kpi">Falta Vol</p><p class="value-kpi">R$ {df_filt["v_falta"].sum():,.0f}</p></div>', unsafe_allow_html=True)
    with k4: st.markdown(f'<div class="card-kpi"><p class="label-kpi">% Perdas</p><p class="value-kpi">{perc_p:.3f}%</p></div>', unsafe_allow_html=True)
    with k5: 
        tu = len(df_filt); fu = df_filt['is_fin'].sum()
        st.markdown(f'''<div class="card-kpi"><p class="label-kpi">Status Unidades</p><p class="value-kpi">{tu}</p>
                    <p class="sub-value">Fin: {fu} | Pend: {tu-fu}</p></div>''', unsafe_allow_html=True)

    # GRÁFICOS
    g1, g2 = st.columns([1.2, 1])
    with g1:
        st.markdown("**Perdas por Tipo**")
        df_g = df_filt.groupby('tipo_clean')[['v_1c', 'v_falta']].sum().sum(axis=1).reset_index(name='t')
        fig = px.bar(df_g, x='tipo_clean', y=df_g['t'].abs(), color='tipo_clean', 
                     color_discrete_map={'CD':'#3a86ff','LV':'#8338ec','DQS':'#06d6a0'}, text_auto='.2s')
        fig.update_layout(template="plotly_dark", height=350, showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', yaxis_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with g2:
        st.markdown("**Status Treemap**")
        df_tree = df_filt[df_filt['v_1c'] != 0].copy()
        fig_t = px.treemap(df_tree, path=['tipo_clean', 'cd_t'], values=df_tree['v_1c'].abs(),
                           color='tipo_clean', color_discrete_map={'CD':'#0040ff','LV':'#aa00ff','DQS':'#00d2ff'})
        fig_t.update_layout(template="plotly_dark", height=350, margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig_t, use_container_width=True)

    # --- TABELA À PROVA DE ERROS (ESTILO PRÉ-CALCULADO) ---
    st.markdown("**Detalhamento Operacional**")
    df_tab = df_filt.copy()
    df_tab['%'] = (df_tab['v_1c'] / df_tab['v_fat'] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
    
    # GOLPE DE MISERICÓRDIA NO ERRO: Calculamos a cor antes de renderizar
    # O Styler apenas lê o texto da cor, ele não faz mais nenhuma comparação numérica
    df_tab['row_color'] = df_tab['v_1c'].apply(lambda x: '#451a1a' if x < 0 else '#1a4523')
    
    df_show = df_tab[['tipo_clean', 'cd_t', 'local', 'v_1c', '%', 'v_falta', 'row_color']].reset_index(drop=True)

    def apply_color_blinded(row):
        return [f"background-color: {row['row_color']}"] * len(row)

    st.dataframe(
        df_show.style.apply(apply_color_blinded, axis=1)
        .format({'v_1c': 'R$ {:,.2f}', 'v_falta': 'R$ {:,.2f}', '%': '{:.4f}%'}),
        column_config={"row_color": None}, # Esconde a coluna técnica de cores
        use_container_width=True, hide_index=True, height=450
    )

except Exception as e:
    st.error(f"Erro Crítico de Renderização: {e}")