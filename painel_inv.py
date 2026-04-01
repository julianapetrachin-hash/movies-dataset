import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Magalog | BI", page_icon="📊")

# --- ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0b0e14; }
    .block-container { padding-top: 2rem !important; }
    .header-container { width: 100%; padding: 10px 0; margin-bottom: 20px; border-bottom: 1px solid #30363d; text-align: center; }
    .main-title { color: #f0f6fc; font-size: 26px; font-weight: 700; }
    .metric-card { background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 15px; min-height: 140px; }
    .metric-label { color: #8b949e; font-size: 11px; font-weight: 600; text-transform: uppercase; }
    .metric-value { color: #f0f6fc; font-size: 22px; font-weight: 700; }
    .highlight-blue { color: #58a6ff; font-weight: 700; }
    .progress-container { background-color: #30363d; border-radius: 10px; height: 6px; width: 100%; margin-top: 10px; }
    .progress-bar { background: linear-gradient(90deg, #58a6ff 0%, #00f2ff 100%); height: 6px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE TRATAMENTO ---
def limpar_valor(valor):
    if pd.isna(valor) or str(valor).strip() in ["", "-", "nan", "DIV/0"]: return 0.0
    v = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    v = re.sub(r'[^0-9\.\-]', '', v)
    try: return float(v)
    except: return 0.0

def mapear_divisional(cd_bruto):
    try:
        # Força a conversão para string, tira o .0 se existir, e vira int
        s_cd = str(cd_bruto).split('.')[0]
        cd = int(re.sub(r'\D', '', s_cd))
    except: return 'Outros'
    
    if cd in [590, 300, 50]: return 'Renato Nesello'
    elif cd in [2650, 994, 991, 1100, 1500, 1800, 1250]: return 'Antônio Paiva'
    elif cd in [350, 5200, 2900, 94, 490, 550, 2500]: return 'Christian'
    elif cd in [204, 2489, 97, 549, 2599, 1116, 1889, 389, 1879, 299, 1899, 2989, 5589, 1450, 49, 2999, 2099, 985, 93, 5289, 5299, 2649, 893, 5599, 1869, 1390]: return 'Mileide'
    else: return 'Outros'

@st.cache_data(ttl=300)
def load_data():
    SHEET_ID = "1iaHnigQGOH5w4xFlZXN0cXYSZlLqPuHE1Pdsgy0XSdI"
    GID_MAIN = "1358149674"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_MAIN}"
    df = pd.read_csv(url).dropna(how='all')
    # Normaliza nomes de colunas
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', str(c).strip().lower()) for c in df.columns]
    
    # --- CURA DOS DADOS (Evita o erro de float vs str) ---
    for col in df.columns:
        if col in ['tipo', 'semestre', 'cd', 'local']:
            df[col] = df[col].astype(str).replace('nan', '')
            
    return df

try:
    df_raw = load_data().copy()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Gerenciamento")
        if st.button("🔄 Atualizar Dados"):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        
        df_raw['tipo_clean'] = df_raw['tipo'].str.upper().str.strip()
        df_raw['divisional'] = df_raw['cd'].apply(mapear_divisional)
        
        tipos_sel = st.multiselect("Tipo", options=sorted(df_raw['tipo_clean'].unique()))
        divs_sel = st.multiselect("Divisional", options=sorted(df_raw['divisional'].unique()))

    # Localização Dinâmica de Colunas
    def get_col(name_snippet):
        match = [c for c in df_raw.columns if name_snippet in c]
        return match[0] if match else None

    c_fat = get_col('faturamento')
    c_1c = get_col('1__ciclo')
    c_falta = get_col('falta_vol')

    # Conversão Numérica Segura
    df_raw['v_1c'] = df_raw[c_1c].apply(limpar_valor) if c_1c else 0.0
    df_raw['v_fat'] = df_raw[c_fat].apply(limpar_valor) if c_fat else 0.0
    df_raw['v_falta'] = df_raw[c_falta].apply(limpar_valor) if c_falta else 0.0
    df_raw['is_finalizado'] = df_raw['v_1c'] != 0

    # Aplicação de Filtros
    df_filt = df_raw.copy()
    if tipos_sel: df_filt = df_filt[df_filt['tipo_clean'].isin(tipos_sel)]
    if divs_sel: df_filt = df_filt[df_filt['divisional'].isin(divs_sel)]

    # Cabeçalho
    st.markdown('<div class="header-container"><div class="main-title">BI FECHAMENTO MAGALOG 2026</div></div>', unsafe_allow_html=True)

    # Cálculos KPIs
    perda_1c = df_filt['v_1c'].sum()
    falta_vol = df_filt['v_falta'].sum()
    fat_total = df_filt['v_fat'].sum()
    perda_consolidada = perda_1c + falta_vol
    perc_global = (abs(perda_consolidada) / fat_total * 100) if fat_total > 0 else 0.0

    total_un = len(df_filt)
    finalizados = df_filt['is_finalizado'].sum()
    total_pendentes = total_un - finalizados
    perc_conclusao = (finalizados / total_un * 100) if total_un > 0 else 0
    
    # Pendentes (Tratamento de String para evitar erro)
    df_pend = df_filt[~df_filt['is_finalizado']]
    pend_1s = len(df_pend[df_pend['semestre'].astype(str).str.contains('1', na=False)])

    # Exibição dos Cards
    col_c1, col_c2, col_c3 = st.columns([1.2, 1, 1.2])

    with col_c1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Perda Consolidada</div><div class="metric-value">R$ {perda_consolidada:,.2f}</div><div style="color:#8b949e; font-size:12px;">1º Ciclo: R$ {perda_1c:,.2f}<br>Falta Vol: {falta_vol:,.0f}</div></div>', unsafe_allow_html=True)

    with col_c2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">% Perda Global</div><div class="metric-value">{perc_global:.3f}%</div><div style="color:#8b949e; font-size:12px;">Sobre faturamento total</div></div>', unsafe_allow_html=True)

    with col_c3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Evolução</div><div class="metric-value">{int(finalizados)}/{total_un} <span style="font-size:13px; color:#58a6ff;">({perc_conclusao:.1f}%)</span></div><div style="color:#8b949e; font-size:12px;">Pendentes 1S: {pend_1s}<br>Total Pendentes: {total_pendentes}</div><div class="progress-container"><div class="progress-bar" style="width: {perc_conclusao}%"></div></div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráficos
    g1, g2 = st.columns([1, 1.2])
    with g1:
        st.subheader("Perda por Divisional")
        fig = px.pie(df_filt, values=df_filt['v_1c'].abs(), names='divisional', hole=0.6)
        fig.update_layout(template="plotly_dark", height=300, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    with g2:
        st.subheader("Visão Geral por CD")
        if not df_filt.empty:
            fig_t = px.treemap(df_filt[df_filt['v_1c'] != 0], path=['divisional', 'cd'], values=df_filt[df_filt['v_1c'] != 0]['v_1c'].abs(), color='v_1c', color_continuous_scale='RdBu_r')
            fig_t.update_layout(template="plotly_dark", height=300, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_t, use_container_width=True)

    # Tabela Final
    st.dataframe(
        df_filt[['semestre', 'tipo_clean', 'divisional', 'cd', 'local', 'v_1c', 'v_falta', 'is_finalizado']],
        column_config={
            "v_1c": st.column_config.NumberColumn("Resultado 1C", format="R$ %.2f"),
            "v_falta": st.column_config.NumberColumn("Falta Vol", format="%.0f"),
            "is_finalizado": st.column_config.CheckboxColumn("Finalizado?")
        },
        use_container_width=True, hide_index=True
    )

except Exception as e:
    st.error(f"⚠️ Erro ao carregar dados: {e}")