import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Magalog | Business Intelligence", page_icon="📊")

# --- ESTILIZAÇÃO CSS (AJUSTADO PARA SUBIR INDICADORES) ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0b0e14; }
    
    /* Reduzindo o espaço no topo da página */
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    
    .header-container { 
        padding: 0.5rem 0; 
        margin-bottom: 1rem; /* Diminuído para subir os cards */
        border-bottom: 1px solid #30363d; 
        text-align: center; 
    }
    .main-title { color: #f0f6fc; font-size: 22px; font-weight: 700; }

    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 12px 15px; /* Reduzido */
        min-height: 130px; /* Reduzido */
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .metric-label { color: #8b949e; font-size: 10px; font-weight: 600; text-transform: uppercase; margin-bottom: 2px; }
    .metric-value { color: #f0f6fc; font-size: 20px; font-weight: 700; margin-bottom: 2px; }
    .metric-subtext { color: #8b949e; font-size: 11px; line-height: 1.2; }
    .highlight-blue { color: #58a6ff; font-weight: 700; }
    
    .progress-container { background-color: #30363d; border-radius: 10px; height: 5px; width: 100%; margin-top: 8px; }
    .progress-bar { background: linear-gradient(90deg, #58a6ff 0%, #00f2ff 100%); height: 5px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES ---
def limpar_valor(valor):
    if pd.isna(valor) or str(valor).strip() in ["", "-", "nan", "DIV/0"]: return 0.0
    v = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    v = re.sub(r'[^0-9\.\-]', '', v)
    try: return float(v)
    except: return 0.0

def mapear_divisional(cd_bruto):
    try: cd = int(float(str(cd_bruto).replace(',', '.')))
    except: return 'Outros'
    if cd in [590, 300, 50]: return 'Renato Nesello'
    elif cd in [2650, 994, 991, 1100, 1500, 1800, 1250]: return 'Antônio Paiva'
    elif cd in [350, 5200, 2900, 94, 490, 550, 2500]: return 'Christian'
    elif cd in [204, 2489, 97, 549, 2599, 1116, 1889, 389, 1879, 299, 1899, 2989, 5589, 1450, 49, 2999, 2099, 985, 93, 5289, 5299, 2649, 893, 5599, 1869, 1390]: return 'Mileide'
    else: return 'Outros'

@st.cache_data
def load_data():
    SHEET_ID = "1iaHnigQGOH5w4xFlZXN0cXYSZlLqPuHE1Pdsgy0XSdI"
    GID_MAIN = "1358149674"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_MAIN}"
    df = pd.read_csv(url).dropna(how='all')
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', str(c).strip().lower()) for c in df.columns]
    return df

try:
    df_raw = load_data()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Gerenciamento")
        if st.button("🔄 Atualizar Dados"):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        
        df_raw['tipo_clean'] = df_raw['tipo'].astype(str).str.upper().str.strip()
        df_raw['divisional'] = df_raw['cd'].apply(mapear_divisional)
        df_raw['semestre'] = df_raw['semestre'].astype(str).str.strip()

        tipos_sel = st.multiselect("Tipo", options=sorted(df_raw['tipo_clean'].unique()))
        divs_sel = st.multiselect("Divisional", options=sorted(df_raw['divisional'].unique()))
        semestre_sel = st.multiselect("Semestre", options=sorted(df_raw['semestre'].unique()))

    # Tratamento Numérico
    col_fat = [c for c in df_raw.columns if 'faturamento' in c][0]
    col_1c = [c for c in df_raw.columns if '1__ciclo' in c][0]
    col_falta = [c for c in df_raw.columns if 'falta_vol' in c][0]

    df_raw['v_1c'] = df_raw[col_1c].apply(limpar_valor)
    df_raw['v_fat'] = df_raw[col_fat].apply(limpar_valor)
    df_raw['v_falta'] = df_raw[col_falta].apply(limpar_valor)
    
    # Lógica de Finalização (Se ciclo 1 for diferente de zero, está fechado)
    df_raw['is_finalizado'] = df_raw['v_1c'] != 0

    # Aplicação de Filtros
    df_filt = df_raw.copy()
    if tipos_sel: df_filt = df_filt[df_filt['tipo_clean'].isin(tipos_sel)]
    if divs_sel: df_filt = df_filt[df_filt['divisional'].isin(divs_sel)]
    if semestre_sel: df_filt = df_filt[df_filt['semestre'].isin(semestre_sel)]

    # --- UI CABEÇALHO ---
    st.markdown('<div class="header-container"><span class="main-title">BI FECHAMENTO MAGALOG 2026</span></div>', unsafe_allow_html=True)

    # Cálculos das Métricas
    perda_1c = df_filt['v_1c'].sum()
    falta_vol = df_filt['v_falta'].sum()
    fat_total = df_filt['v_fat'].sum()
    
    perda_consolidada = perda_1c + falta_vol
    perc_global = (abs(perda_consolidada) / fat_total * 100) if fat_total > 0 else 0.0

    # Lógica de Status (Correção da soma matemática)
    total_un = len(df_filt)
    finalizados = df_filt['is_finalizado'].sum()
    total_pendentes = total_un - finalizados # Garante que a soma sempre bata
    perc_conclusao = (finalizados / total_un * 100) if total_un > 0 else 0
    
    # Distribuição de pendentes (Melhorado para ser à prova de falhas)
    df_pend = df_filt[~df_filt['is_finalizado']]
    pend_1s = len(df_pend[df_pend['semestre'].str.contains('1', na=False)])
    # O 2º semestre pega o que sobrou para fechar a conta exata do total de pendentes
    pend_2s = total_pendentes - pend_1s 

    # Layout de Cards
    c1, c2, c3 = st.columns([1.2, 1, 1.2])

    with c1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Perda Consolidada (1C + Falta)</div>
                <div class="metric-value">R$ {perda_consolidada:,.2f}</div>
                <div class="metric-subtext">
                    1º Ciclo: R$ {perda_1c:,.2f}<br>
                    Falta Vol: {falta_vol:,.0f} itens
                </div>
            </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">% Perda Global</div>
                <div class="metric-value">{perc_global:.3f}%</div>
                <div class="metric-subtext">Resultado consolidado<br>sobre faturamento.</div>
            </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Status de Evolução</div>
                <div class="metric-value">{int(finalizados)} / {total_un} <span style="font-size:13px; color:#58a6ff;">({perc_conclusao:.1f}%)</span></div>
                <div class="metric-subtext">
                    Pendentes 1º Sem: <span class="highlight-blue">{pend_1s}</span><br>
                    Pendentes 2º Sem: <span class="highlight-blue">{pend_2s}</span>
                </div>
                <div class="progress-container"><div class="progress-bar" style="width: {perc_conclusao}%"></div></div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráficos (Ajustados para Layout Compacto)
    col_g1, col_g2 = st.columns([1, 1.2])
    with col_g1:
        st.subheader("Perda por Divisional")
        fig = px.pie(df_filt, values=df_filt['v_1c'].abs(), names='divisional', hole=0.7)
        fig.update_layout(template="plotly_dark", height=300, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    with col_g2:
        st.subheader("Treemap de Saúde")
        df_tree = df_filt[df_filt['v_1c'] != 0].copy()
        if not df_tree.empty:
            df_tree['abs_val'] = df_tree['v_1c'].abs()
            fig_t = px.treemap(df_tree, path=['divisional', 'cd'], values='abs_val', color='v_1c', color_continuous_scale='RdBu_r')
            fig_t.update_layout(template="plotly_dark", height=300, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_t, use_container_width=True)

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