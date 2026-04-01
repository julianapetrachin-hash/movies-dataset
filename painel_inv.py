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
    if pd.isna(cd_bruto) or str(cd_bruto).strip() in ["", "nan", "None", "0", "0.0"]:
        return None
    try:
        s_cd = str(cd_bruto).split('.')[0]
        cd = int(re.sub(r'\D', '', s_cd))
    except:
        return None
    
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
    # 1. Carrega os dados atuais
    df_raw = load_data().copy()

    # --- 2. INSERE OS DADOS FIXOS DE 2024 AQUI ---
    # Usamos os nomes de colunas padronizados para o merge funcionar depois
    dados_2024 = [
        {"tipo_clean": "CD", "semestre": "1º semestre", "v_24": -9415271},
        {"tipo_clean": "CD", "semestre": "2º semestre", "v_24": -5379088},
        {"tipo_clean": "CROSS", "semestre": "1º semestre", "v_24": -2183},
        {"tipo_clean": "CROSS", "semestre": "2º semestre", "v_24": -1633},
        {"tipo_clean": "DQS", "semestre": "1º semestre", "v_24": -269835},
        {"tipo_clean": "DQS", "semestre": "2º semestre", "v_24": 268613},
        {"tipo_clean": "LV", "semestre": "1º semestre", "v_24": -619830},
        {"tipo_clean": "LV", "semestre": "2º semestre", "v_24": -2509390},
    ]
    df_2024 = pd.DataFrame(dados_2024)

    # 3. Configuração da Sidebar (Filtros)
    with st.sidebar:
        st.header("⚙️ Gerenciamento")
        if st.button("🔄 Atualizar Dados"):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        
        # Criação das colunas de apoio
        df_raw['tipo_clean'] = df_raw['tipo'].fillna('').astype(str).str.upper().str.strip()
        df_raw['divisional'] = df_raw['cd'].apply(mapear_divisional).astype(str)
        
        # Filtros dinâmicos
        opcoes_tipo = sorted([str(x) for x in df_raw['tipo_clean'].unique() if x != ''])
        tipos_sel = st.multiselect("Filtrar por Tipo", options=opcoes_tipo)
        
        opcoes_div = sorted([str(x) for x in df_raw['divisional'].unique() if x not in ['None', 'nan']])
        divs_sel = st.multiselect("Filtrar por Divisional", options=opcoes_div)

    # O RESTANTE DO SEU CÓDIGO (Cálculos, Filtros de df_filt, etc) SEGUE ABAIXO...

    with st.sidebar:
        st.header("⚙️ Gerenciamento")
        if st.button("🔄 Atualizar Dados"):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        df_raw['tipo_clean'] = df_raw['tipo'].fillna('').astype(str).str.upper().str.strip()
        df_raw['divisional'] = df_raw['cd'].apply(mapear_divisional).astype(str)
        opcoes_tipo = sorted([str(x) for x in df_raw['tipo_clean'].unique() if x != ''])
        tipos_sel = st.multiselect("Filtrar por Tipo", options=opcoes_tipo)
        opcoes_div = sorted([str(x) for x in df_raw['divisional'].unique() if x not in ['None', 'nan']])
        divs_sel = st.multiselect("Filtrar por Divisional", options=opcoes_div)

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

    st.markdown('<div class="header-container"><div class="main-title">BI FECHAMENTO MAGALOG 2026</div></div>', unsafe_allow_html=True)

    perda_1c = df_filt['v_1c'].sum()
    falta_vol = df_filt['v_falta'].sum()
    fat_total = df_filt['v_fat'].sum()
    perda_consolidada = perda_1c + falta_vol
    perc_global = (abs(perda_consolidada) / fat_total * 100) if fat_total > 0 else 0.0

    total_un = len(df_filt)
    finalizados = df_filt['is_finalizado'].sum()
    total_pendentes = total_un - finalizados
    perc_conclusao = (finalizados / total_un * 100) if total_un > 0 else 0
    
    df_pend = df_filt[~df_filt['is_finalizado']]
    pend_1s = len(df_pend[df_pend['semestre'].astype(str).str.contains('1', na=False)])

    col_c1, col_c2, col_c3 = st.columns([1.2, 1, 1.2])
    with col_c1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Perda Consolidada</div><div class="metric-value">R$ {perda_consolidada:,.2f}</div><div style="color:#8b949e; font-size:12px;">1º Ciclo: R$ {perda_1c:,.2f}<br>Falta Vol: {falta_vol:,.0f}</div></div>', unsafe_allow_html=True)
    with col_c2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">% Perda Global</div><div class="metric-value">{perc_global:.3f}%</div><div style="color:#8b949e; font-size:12px;">Sobre faturamento total</div></div>', unsafe_allow_html=True)
    with col_c3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Evolução</div><div class="metric-value">{int(finalizados)}/{total_un} <span style="font-size:13px; color:#58a6ff;">({perc_conclusao:.1f}%)</span></div><div style="color:#8b949e; font-size:12px;">Pendentes 1S: {pend_1s}<br>Total Pendentes: {total_pendentes}</div><div class="progress-container"><div class="progress-bar" style="width: {perc_conclusao}%"></div></div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    g1, g2 = st.columns([1, 1.2])
    with g1:
        st.subheader("Perda por Divisional")
        df_pie = df_filt[df_filt['divisional'].notna() & (~df_filt['divisional'].astype(str).str.lower().isin(['none', 'null', 'nan', '']))].copy()
        fig = px.pie(df_pie, values=df_pie['v_1c'].abs(), names='divisional', hole=0.6)
        fig.update_layout(template="plotly_dark", height=300, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    with g2:
        st.subheader("Visão Geral por CD")
        if not df_filt.empty:
            df_tree = df_filt[df_filt['v_1c'] != 0].copy()
            df_tree['cd'] = df_tree['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
            fig_t = px.treemap(df_tree, path=['divisional', 'cd'], values=df_tree['v_1c'].abs(), color='v_1c', color_continuous_scale='RdBu_r')
            fig_t.update_layout(template="plotly_dark", height=300, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)')
            fig_t.update_traces(textinfo="label+value")
            st.plotly_chart(fig_t, use_container_width=True)

   # --- TABELA FINAL ---
    st.subheader("📋 Detalhamento por Unidade")
    df_tab = df_filt.copy()
    
    # 1. TRATAMENTO PESADO DE NULOS NO FATURAMENTO
    # Converte para string, limpa espaços, remove R$, converte para número e o que sobrar de vazio vira 0
    df_tab['v_fat'] = pd.to_numeric(
        df_tab['v_fat'].astype(str).str.replace('R$', '', regex=False).str.strip(), 
        errors='coerce'
    ).fillna(0.0)
    
    # 2. CÁLCULO DO % (Agora com garantia de que v_fat nunca é 'vazio' técnico)
    # Se faturamento for 0, o resultado será 0 em vez de vazio
    df_tab['% Perda'] = df_tab.apply(
        lambda x: (x['v_1c'] / x['v_fat'] * 100) if x['v_fat'] != 0 else 0.0, 
        axis=1
    ).fillna(0.0)
    
    # 3. Limpeza do CD e Seleção de colunas
    df_tab['cd'] = df_tab['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
    colunas_show = ['semestre', 'tipo_clean', 'divisional', 'cd', 'local', 'v_1c', '% Perda', 'v_falta', 'is_finalizado']
    df_exibir = df_tab[colunas_show]

    # 4. FUNÇÃO DE ESTILIZAÇÃO
    def style_performance(row):
        styles = [''] * len(row)
        v1c = row['v_1c']
        
        # Cores para Dark Mode (Vermelho/Verde)
        if v1c < 0:
            bg = 'background-color: #641e1e; color: #ff9999; font-weight: bold;'
        else:
            bg = 'background-color: #1e4620; color: #99ff99; font-weight: bold;'

        # Pintar colunas financeiras e Falta Vol
        for col_name in ['v_1c', '% Perda', 'v_falta']:
            if col_name in row.index:
                styles[row.index.get_loc(col_name)] = bg
        return styles

    # 5. EXIBIÇÃO
    st.dataframe(
        df_exibir.style.apply(style_performance, axis=1),
        column_config={
            "v_1c": st.column_config.NumberColumn("Resultado 1C", format="R$ %.2f"),
            "% Perda": st.column_config.NumberColumn("% Perda", format="%.4f%%"),
            "v_falta": st.column_config.NumberColumn("Falta Vol", format="%.0f"),
            "is_finalizado": st.column_config.CheckboxColumn("Fim?"),
            "tipo_clean": "Tipo", "cd": "CD", "local": "Unidade"
        },
        use_container_width=True,
        hide_index=True
    )

except Exception as e:
    st.error(f"⚠️ Erro ao carregar dados: {e}")