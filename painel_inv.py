import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Magalog | BI Executive", page_icon="📊")

# --- ESTILO CSS ---
st.markdown("""
    <style>
    [data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 1.5rem !important; margin-top: -30px !important; }
    [data-testid="stAppViewContainer"] { background-color: #0b0e14 !important; }
    .header-box {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 12px; border-radius: 5px; text-align: center;
        margin-bottom: 20px; border-bottom: 3px solid #00d2ff;
    }
    .header-title { color: white !important; font-size: 24px !important; font-weight: 800 !important; }
    .card-kpi {
        background: #1c222d; border: 1px solid #313d4f; border-radius: 10px;
        padding: 15px; text-align: center; border-top: 3px solid #00d2ff;
    }
    .value-kpi { color: white; font-size: 22px; font-weight: 900; margin: 0; }
    .label-kpi { color: #8b949e; font-size: 11px; text-transform: uppercase; }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÃO DE LIMPEZA ---
def limpar_universal(v):
    if pd.isna(v) or str(v).strip() in ["", "-", "nan", "#DIV/0!", "None"]: return 0.0
    s = str(v).replace('R$', '').replace('%', '').replace(' ', '')
    if ',' in s and '.' in s: s = s.replace('.', '').replace(',', '.')
    elif ',' in s: s = s.replace(',', '.')
    s = re.sub(r'[^0-9\.\-]', '', s)
    try: return float(s)
    except: return 0.0

@st.cache_data(ttl=60)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1iaHnigQGOH5w4xFlZXN0cXYSZlLqPuHE1Pdsgy0XSdI/export?format=csv&gid=1358149674"
    df = pd.read_csv(url).dropna(how='all')
    # Normaliza nomes de colunas: tudo minusculo, sem espaços, sem acentos
    df.columns = [re.sub(r'[^a-z0-9]', '_', str(c).strip().lower()) for c in df.columns]
    return df

try:
    df_raw = load_data().copy()
    
    # --- MAPEAMENTO DINÂMICO DE COLUNAS ---
    # Tenta encontrar as colunas mesmo que o nome mude levemente
    col_tipo = next((c for c in df_raw.columns if 'tipo' in c), None)
    col_cd = next((c for c in df_raw.columns if 'cd' in c and len(c) < 5), None)
    col_div = next((c for c in df_raw.columns if 'divisional' in c or 'gerente' in c or 'regional' in c), None)
    
    c_1c = next((c for c in df_raw.columns if '1' in c and 'ciclo' in c), None)
    c_falta = next((c for c in df_raw.columns if 'falta' in c and 'vol' in c), None)
    c_fat = next((c for c in df_raw.columns if 'faturamento' in c or 'fat' in c), None)

    # Conversão de Valores
    df_raw['v_1c'] = df_raw[c_1c].apply(limpar_universal).astype(float) if c_1c else 0.0
    df_raw['v_falta'] = df_raw[c_falta].apply(limpar_universal).astype(float) if c_falta else 0.0
    df_raw['v_fat'] = df_raw[c_fat].apply(limpar_universal).astype(float) if c_fat else 0.0
    
    # Tratamento de Strings para os Filtros
    df_raw['f_tipo'] = df_raw[col_tipo].fillna('OUTROS').astype(str).str.upper() if col_tipo else 'OUTROS'
    df_raw['f_cd'] = df_raw[col_cd].fillna('N/A').astype(str).str.replace(r'\.0$', '', regex=True) if col_cd else 'N/A'
    df_raw['f_gerente'] = df_raw[col_div].fillna('N/A').astype(str).str.upper() if col_div else 'N/A'

    # --- BARRA LATERAL (FILTROS) ---
    with st.sidebar:
        st.header("⚙️ Painel de Controle")
        
        if st.button("🔄 Sincronizar Google Sheets"):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        
        # Filtros Multiselect
        lista_tipos = sorted(df_raw['f_tipo'].unique())
        sel_tipos = st.multiselect("Filtrar por Tipo:", options=lista_tipos, default=[])
        
        lista_cds = sorted(df_raw['f_cd'].unique())
        sel_cds = st.multiselect("Filtrar por CD:", options=lista_cds, default=[])
        
        lista_gerentes = sorted(df_raw['f_gerente'].unique())
        sel_gerentes = st.multiselect("Filtrar por Gerente/Divisional:", options=lista_gerentes, default=[])

    # --- LÓGICA DE FILTRAGEM ---
    df_filt = df_raw.copy()
    if sel_tipos:
        df_filt = df_filt[df_filt['f_tipo'].isin(sel_tipos)]
    if sel_cds:
        df_filt = df_filt[df_filt['f_cd'].isin(sel_cds)]
    if sel_gerentes:
        df_filt = df_filt[df_filt['f_gerente'].isin(sel_gerentes)]

    # --- EXIBIÇÃO DASHBOARD ---
    st.markdown('<div class="header-box"><p class="header-title">📊 DASHBOARD EXECUTIVO MAGALOG 2026</p></div>', unsafe_allow_html=True)
    
    # KPIs
    v_perda_total = df_filt['v_1c'].sum() + df_filt['v_falta'].sum()
    fat_soma = df_filt['v_fat'].sum()
    perc_p = (abs(v_perda_total) / fat_soma * 100) if fat_soma > 0 else 0.0

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f'<div class="card-kpi"><p class="label-kpi">Perda Total</p><p class="value-kpi">R$ {v_perda_total:,.0f}</p></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="card-kpi"><p class="label-kpi">1º Ciclo</p><p class="value-kpi">R$ {df_filt["v_1c"].sum():,.0f}</p></div>', unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="card-kpi"><p class="label-kpi">Falta Vol</p><p class="value-kpi">R$ {df_filt["v_falta"].sum():,.0f}</p></div>', unsafe_allow_html=True)
    with k4: st.markdown(f'<div class="card-kpi"><p class="label-kpi">% Perda s/ Fat</p><p class="value-kpi">{perc_p:.3f}%</p></div>', unsafe_allow_html=True)

    st.write("") # Espaçador

    # Gráficos
    g1, g2 = st.columns([1, 1])
    with g1:
        df_g = df_filt.groupby('f_tipo')[['v_1c', 'v_falta']].sum().sum(axis=1).reset_index(name='total')
        fig = px.pie(df_g, names='f_tipo', values='total', hole=0.4, title="Distribuição por Tipo",
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(template="plotly_dark", showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    with g2:
        df_g2 = df_filt.groupby('f_cd')[['v_1c', 'v_falta']].sum().sum(axis=1).reset_index(name='total').sort_values('total', ascending=False).head(10)
        fig2 = px.bar(df_g2, x='f_cd', y='total', title="Top 10 CDs (Perda)", text_auto='.2s')
        fig2.update_layout(template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)

    # Tabela Detalhada
    st.markdown("### 📋 Detalhamento das Unidades")
    
    # Função para colorir valores negativos/positivos na tabela
    def colorir_valor(val):
        try:
            num = float(val)
            color = '#ff4b4b' if num < 0 else '#00ffcc' if num > 0 else 'white'
            return f'color: {color}'
        except: return ''

    df_final = df_filt[['f_tipo', 'f_cd', 'v_1c', 'v_falta', 'f_gerente']].copy()
    df_final.columns = ['Tipo', 'CD', '1º Ciclo', 'Falta Vol', 'Responsável']
    
    st.dataframe(
        df_final.style.map(colorir_valor, subset=['1º Ciclo', 'Falta Vol'])
        .format({'1º Ciclo': 'R$ {:,.2f}', 'Falta Vol': 'R$ {:,.2f}'}),
        use_container_width=True, hide_index=True
    )

except Exception as e:
    st.error(f"Aguardando dados ou erro na leitura: {e}")
    st.info("Dica: Verifique se as colunas da sua planilha contêm os termos 'tipo', 'cd' e '1 ciclo'.")