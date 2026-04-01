import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# 1. CONFIGURAÇÃO DA PÁGINA (ESTILO DASHBOARD PRO)
st.set_page_config(layout="wide", page_title="Magalog | BI Executive", page_icon="📊")

# --- ESTILIZAÇÃO CSS AVANÇADA (ESTILO NEON / FIGMA) ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0d1117; }
    .block-container { padding-top: 1rem !important; max-width: 95%; }
    
    /* TÍTULO COM GRADIENTE */
    .header-box {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        padding: 15px; border-radius: 12px; text-align: center;
        margin-bottom: 25px; box-shadow: 0 4px 20px rgba(0, 210, 255, 0.2);
    }
    .header-title { color: white; font-size: 28px; font-weight: 800; letter-spacing: 2px; margin:0; }

    /* CARDS ESTILO NEON */
    .card-kpi {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 15px; padding: 20px; text-align: center;
        transition: transform 0.3s;
    }
    .card-kpi:hover { transform: translateY(-5px); border-color: #00d2ff; }
    .label-kpi { color: #8b949e; font-size: 12px; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; }
    .value-kpi { color: #f0f6fc; font-size: 26px; font-weight: 800; }
    .sub-kpi { color: #00d2ff; font-size: 13px; margin-top: 5px; font-weight: 500; }
    
    /* BARRA DE PROGRESSO CUSTOM */
    .progress-bg { background-color: #30363d; border-radius: 10px; height: 8px; width: 100%; margin-top: 15px; }
    .progress-fill { 
        background: linear-gradient(90deg, #00d2ff 0%, #00f2ff 100%); 
        height: 8px; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 242, 255, 0.5); 
    }
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
    # Retorna "Indefinido" em vez de None para evitar erro de comparação float vs str
    if pd.isna(cd_bruto) or str(cd_bruto).strip() in ["", "nan", "None", "0", "0.0"]: 
        return "Indefinido"
    try:
        s_cd = str(cd_bruto).split('.')[0]
        cd = int(re.sub(r'\D', '', s_cd))
    except: return "Indefinido"
    
    if cd in [590, 300, 50]: return 'Renato Nesello'
    elif cd in [2650, 994, 991, 1100, 1500, 1800, 1250]: return 'Antônio Paiva'
    elif cd in [350, 5200, 2900, 94, 490, 550, 2500, 1440]: return 'Christian'
    elif cd in [204, 2489, 97, 549, 2599, 1116, 1889, 389, 1879, 299, 1899, 2989, 5589, 1450, 49, 2999, 2099, 985, 93, 5289, 5299, 2649, 893, 5599, 1869, 1390]: return 'Mileide'
    else: return 'Outros'

@st.cache_data(ttl=300)
def load_data():
    SHEET_ID = "1iaHnigQGOH5w4xFlZXN0cXYSZlLqPuHE1Pdsgy0XSdI"
    GID_MAIN = "1358149674"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_MAIN}"
    df = pd.read_csv(url).dropna(how='all')
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', str(c).strip().lower()) for c in df.columns]
    for col in ['tipo', 'semestre', 'cd', 'local']:
        if col in df.columns:
            df[col] = df[col].astype(str).replace('nan', '')
    return df

try:
    # 1. Carregamento e Base Fixa 2024
    df_raw = load_data().copy()
    
    df_2024 = pd.DataFrame([
        {"tipo_clean": "CD", "semestre": "1º semestre", "v_24": -9415271},
        {"tipo_clean": "CD", "semestre": "2º semestre", "v_24": -5379088},
        {"tipo_clean": "CROSS", "semestre": "1º semestre", "v_24": -2183},
        {"tipo_clean": "CROSS", "semestre": "2º semestre", "v_24": -1633},
        {"tipo_clean": "DQS", "semestre": "1º semestre", "v_24": -269835},
        {"tipo_clean": "DQS", "semestre": "2º semestre", "v_24": 268613},
        {"tipo_clean": "LV", "semestre": "1º semestre", "v_24": -619830},
        {"tipo_clean": "LV", "semestre": "2º semestre", "v_24": -2509390},
    ])

    # 2. Sidebar (Filtros)
    with st.sidebar:
        st.header("⚙️ Gerenciamento")
        if st.button("🔄 Atualizar Dados"):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        df_raw['tipo_clean'] = df_raw['tipo'].fillna('').astype(str).str.upper().str.strip()
        df_raw['divisional'] = df_raw['cd'].apply(mapear_divisional).astype(str)
        
        opcoes_tipo = sorted(df_raw['tipo_clean'].unique())
        tipos_sel = st.multiselect("Filtrar por Tipo", options=opcoes_tipo)
        
        opcoes_div = sorted([x for x in df_raw['divisional'].unique() if x != "Indefinido"])
        divs_sel = st.multiselect("Filtrar por Divisional", options=opcoes_div)

    # 3. Processamento de Colunas Dinâmicas
    def get_col(name_snippet):
        match = [c for c in df_raw.columns if name_snippet in c]
        return match[0] if match else None

    c_fat = get_col('faturamento')
    c_1c = get_col('1__ciclo')
    c_falta = get_col('falta_vol')

    df_raw['v_1c'] = df_raw[c_1c].apply(limpar_valor) if c_1c else 0.0
    df_raw['v_fat'] = df_raw[c_fat].apply(limpar_valor) if c_fat else 0.0
    df_raw['v_falta'] = df_raw[c_falta].apply(limpar_valor) if c_falta else 0.0
    df_raw['is_finalizado'] = df_raw['v_1c'] != 0

    df_filt = df_raw.copy()
    if tipos_sel: df_filt = df_filt[df_filt['tipo_clean'].isin(tipos_sel)]
    if divs_sel: df_filt = df_filt[df_filt['divisional'].isin(divs_sel)]

    # --- UI PRINCIPAL ---
    st.markdown('<div class="header-box"><p class="header-title">BI FECHAMENTO MAGALOG 2026</p></div>', unsafe_allow_html=True)

    # KPIs Superiores
    perda_1c = df_filt['v_1c'].sum()
    falta_vol = df_filt['v_falta'].sum()
    fat_total = df_filt['v_fat'].sum()
    perda_consolidada = perda_1c + falta_vol
    perc_global = (abs(perda_consolidada) / fat_total * 100) if fat_total > 0 else 0.0
    
    total_un = len(df_filt)
    finalizados = df_filt['is_finalizado'].sum()
    perc_conclusao = (finalizados / total_un * 100) if total_un > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="card-kpi"><div class="label-kpi">Perda Consolidada</div><div class="value-kpi">R$ {perda_consolidada:,.0f}</div><div class="sub-kpi">1C + Falta Vol</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="card-kpi"><div class="label-kpi">% Perda Global</div><div class="value-kpi">{perc_global:.3f}%</div><div class="sub-kpi">Sobre Faturamento</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="card-kpi"><div class="label-kpi">Volume de Falta</div><div class="value-kpi">{int(falta_vol):,}</div><div class="sub-kpi">Itens Pendentes</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'''<div class="card-kpi"><div class="label-kpi">Evolução</div><div class="value-kpi">{perc_conclusao:.1f}%</div>
        <div class="progress-bg"><div class="progress-fill" style="width: {perc_conclusao}%"></div></div></div>''', unsafe_allow_html=True)

    # --- SEÇÃO COMPARATIVO ---
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📊 Ver Comparativo YoY (2024 vs Atual)", expanded=False):
        resumo_atual = df_filt.groupby(['tipo_clean', 'semestre'])['v_1c'].sum().reset_index()
        df_comp = pd.merge(resumo_atual, df_2024, on=['tipo_clean', 'semestre'], how='left').fillna(0)
        df_comp['Diferença'] = df_comp['v_1c'] - df_comp['v_24']
        st.dataframe(df_comp, use_container_width=True, hide_index=True)

    # --- GRÁFICOS ---
    st.markdown("<br>", unsafe_allow_html=True)
    g1, g2 = st.columns([1, 1])
    
    with g1:
        st.subheader("📍 Perda por Gerência")
        df_pie = df_filt[~df_filt['divisional'].isin(['Indefinido', 'nan', ''])]
        # Cores manuais para evitar erro de atributo no Plotly
        fig_p = px.pie(df_pie, values=df_pie['v_1c'].abs(), names='divisional', hole=0.7, 
                       color_discrete_sequence=["#00d2ff", "#3a7bd5", "#7000ff", "#00f2ff"])
        fig_p.update_layout(template="plotly_dark", height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_p, use_container_width=True)

    with g2:
        st.subheader("🏢 Saúde por CD")
        df_tree = df_filt[df_filt['v_1c'] != 0].copy()
        df_tree['cd'] = df_tree['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        fig_t = px.treemap(df_tree, path=['divisional', 'cd'], values=df_tree['v_1c'].abs(), 
                           color='v_1c', color_continuous_scale='RdBu_r')
        fig_t.update_layout(template="plotly_dark", height=350, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_t, use_container_width=True)

    # --- TABELA DETALHADA ---
    st.subheader("📋 Detalhamento Operacional")
    df_tab = df_filt.copy()
    df_tab['v_fat'] = pd.to_numeric(df_tab['v_fat'].astype(str).str.replace('R$', '', regex=False).str.strip(), errors='coerce').fillna(0.0)
    df_tab['% Perda'] = df_tab.apply(lambda x: (x['v_1c'] / x['v_fat'] * 100) if x['v_fat'] != 0 else 0.0, axis=1).fillna(0.0)
    df_tab['cd'] = df_tab['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
    df_exibir = df_tab[['semestre', 'tipo_clean', 'divisional', 'cd', 'local', 'v_1c', '% Perda', 'v_falta', 'is_finalizado']]

    def style_performance(row):
        styles = [''] * len(row)
        v1c = row['v_1c']
        bg = 'background-color: #641e1e; color: #ff9999; font-weight: bold;' if v1c < 0 else 'background-color: #1e4620; color: #99ff99; font-weight: bold;'
        for col in ['v_1c', '% Perda', 'v_falta']:
            styles[row.index.get_loc(col)] = bg
        return styles

    st.dataframe(df_exibir.style.apply(style_performance, axis=1), column_config={
        "v_1c": st.column_config.NumberColumn("Resultado", format="R$ %.2f"),
        "% Perda": st.column_config.NumberColumn("%", format="%.3f%%"),
        "v_falta": st.column_config.NumberColumn("Falta Vol", format="%.0f"),
        "is_finalizado": st.column_config.CheckboxColumn("Fim")
    }, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"⚠️ Erro ao carregar dados: {e}")