import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Magalog | BI Executive", page_icon="📊")

# --- CSS EXECUTIVO ---
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
        padding: 15px; text-align: center; border-top: 3px solid #00d2ff; min-height: 100px;
    }
    .value-kpi { color: white; font-size: 20px; font-weight: 900; margin: 0; }
    .label-kpi { color: #8b949e; font-size: 11px; text-transform: uppercase; }
    </style>
""", unsafe_allow_html=True)

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
    # Mantemos os nomes originais para os gráficos, mas criamos uma versão limpa para busca técnica
    return df

try:
    df_raw = load_data().copy()
    
    # Identificação Dinâmica de Colunas Financeiras
    c_1c = next((c for c in df_raw.columns if '1' in c and 'Ciclo' in c), df_raw.columns[0])
    c_falta = next((c for c in df_raw.columns if 'Falta' in c and 'Vol' in c), df_raw.columns[0])
    c_fat = next((c for c in df_raw.columns if 'Faturamento' in c or 'Fat' in c), df_raw.columns[0])
    col_tipo = next((c for c in df_raw.columns if 'Tipo' in c), 'Tipo')
    col_cd = next((c for c in df_raw.columns if 'CD' in c and len(c) < 5), 'CD')
    col_div = next((c for c in df_raw.columns if 'Divisional' in c or 'Gerente' in c), 'Divisional')

    # Conversão de Dados
    df_raw['v_1c'] = df_raw[c_1c].apply(limpar_universal)
    df_raw['v_falta'] = df_raw[c_falta].apply(limpar_universal)
    df_raw['v_fat'] = df_raw[c_fat].apply(limpar_universal)
    df_raw['total_perda'] = df_raw['v_1c'] + df_raw['v_falta']
    
    # --- SIDEBAR COM FILTROS ---
    with st.sidebar:
        st.title("⚙️ Configurações")
        if st.button("🔄 Atualizar e Sincronizar"):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        f_tipo = st.multiselect("Filtrar Tipo:", options=sorted(df_raw[col_tipo].dropna().unique()))
        f_cd = st.multiselect("Filtrar CD:", options=sorted(df_raw[col_cd].astype(str).unique()))
        f_ger = st.multiselect("Filtrar Gerente:", options=sorted(df_raw[col_div].dropna().unique()) if col_div in df_raw.columns else [])

    # Aplicação dos Filtros
    df_filt = df_raw.copy()
    if f_tipo: df_filt = df_filt[df_filt[col_tipo].isin(f_tipo)]
    if f_cd: df_filt = df_filt[df_filt[col_cd].astype(str).isin(f_cd)]
    if f_ger: df_filt = df_filt[df_filt[col_div].isin(f_ger)]

    # --- CABEÇALHO ---
    st.markdown('<div class="header-box"><p class="header-title">📊 DASHBOARD ESTRATÉGICO MAGALOG 2026</p></div>', unsafe_allow_html=True)
    
    # --- CARDS KPI (RESTAURADOS) ---
    k1, k2, k3, k4, k5 = st.columns(5)
    fat_total = df_filt['v_fat'].sum()
    perda_total = df_filt['total_perda'].sum()
    
    with k1: st.markdown(f'<div class="card-kpi"><p class="label-kpi">Perda Total</p><p class="value-kpi">R$ {perda_total:,.0f}</p></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="card-kpi"><p class="label-kpi">1º Ciclo</p><p class="value-kpi">R$ {df_filt["v_1c"].sum():,.0f}</p></div>', unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="card-kpi"><p class="label-kpi">Falta Vol</p><p class="value-kpi">R$ {df_filt["v_falta"].sum():,.0f}</p></div>', unsafe_allow_html=True)
    with k4: st.markdown(f'<div class="card-kpi"><p class="label-kpi">% Perda / Fat</p><p class="value-kpi">{(abs(perda_total)/fat_total*100 if fat_total>0 else 0):.3f}%</p></div>', unsafe_allow_html=True)
    with k5: 
        saude = "Saudável" if (abs(perda_total)/fat_total if fat_total>0 else 0) < 0.01 else "Atenção"
        st.markdown(f'<div class="card-kpi"><p class="label-kpi">Status Saúde</p><p class="value-kpi">{saude}</p></div>', unsafe_allow_html=True)

    # --- GRÁFICOS (CD, DQS, LV E ACUMULADO) ---
    st.write("### 📈 Análise de Processos e Acumulados")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        # Gráfico por Tipo (Processo)
        df_proc = df_filt.groupby(col_tipo)['total_perda'].sum().reset_index()
        fig_proc = px.bar(df_proc, x=col_tipo, y='total_perda', title="Perdas por Processo (CD, LV, DQS)", 
                          color=col_tipo, color_discrete_map={'CD':'#1e3c72', 'LV':'#00d2ff', 'DQS':'#ff4b4b'})
        st.plotly_chart(fig_proc, use_container_width=True)

    with c2:
        # Perdas por Gerente (Divisional)
        df_gerente = df_filt.groupby(col_div)['total_perda'].sum().reset_index().sort_values('total_perda', ascending=True)
        fig_ger = px.bar(df_gerente, y=col_div, x='total_perda', orientation='h', title="Perdas por Gerente", color_discrete_sequence=['#00d2ff'])
        st.plotly_chart(fig_ger, use_container_width=True)

    with c3:
        # Top CDs com maior impacto
        df_top_cd = df_filt.groupby(col_cd)['total_perda'].sum().reset_index().sort_values('total_perda', ascending=True).head(10)
        fig_cd = px.bar(df_top_cd, x=col_cd, y='total_perda', title="Top 10 CDs Críticos", color_discrete_sequence=['#ff4b4b'])
        st.plotly_chart(fig_cd, use_container_width=True)

    # --- TABELA DE DETALHAMENTO ---
    st.markdown("### 📋 Detalhamento das Unidades")
    
    def style_negative(val):
        try:
            return 'color: #ff4b4b' if float(val) < 0 else 'color: #00ffcc'
        except: return ''

    df_display = df_filt[[col_tipo, col_cd, c_1c, c_falta, col_div]].copy()
    
    st.dataframe(
        df_display.style.map(style_negative, subset=[c_1c, c_falta]),
        use_container_width=True, hide_index=True
    )

except Exception as e:
    st.error(f"Erro na execução do dashboard: {e}")
    st.info("Certifique-se de que a planilha do Google não teve colunas renomeadas.")