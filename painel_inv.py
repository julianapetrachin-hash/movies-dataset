import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Magalog | BI Executive", page_icon="📊")

# --- CSS DEFINITIVO (FORÇANDO ESTILO NEON) ---
st.markdown("""
    <style>
    /* Fundo e Container */
    [data-testid="stAppViewContainer"] { background-color: #0d1117 !important; }
    .main { padding: 0rem !important; }
    
    /* Header Custom */
    .header-box {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%) !important;
        padding: 1.5rem; border-radius: 0 0 15px 15px; text-align: center;
        margin-bottom: 2rem; box-shadow: 0 4px 20px rgba(0, 210, 255, 0.3);
    }
    .header-title { color: white !important; font-size: 28px !important; font-weight: 800 !important; margin:0; }

    /* Estilo dos Cards KPI */
    div[data-testid="stMetric"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 12px !important;
        padding: 15px !important;
    }
    
    .card-neon {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 12px; padding: 20px; text-align: center;
        min-height: 140px; border-bottom: 3px solid #00d2ff;
    }
    .label-neon { color: #8b949e; font-size: 11px; font-weight: 600; text-transform: uppercase; }
    .value-neon { color: #f0f6fc; font-size: 24px; font-weight: 800; margin: 5px 0; }
    .sub-neon { color: #00d2ff; font-size: 12px; font-weight: 500; }

    /* Progress Bar */
    .p-bar-bg { background-color: #30363d; border-radius: 5px; height: 6px; width: 100%; margin-top: 10px; }
    .p-bar-fill { background: #00d2ff; height: 6px; border-radius: 5px; box-shadow: 0 0 8px #00d2ff; }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---
def limpar_valor(v):
    if pd.isna(v) or str(v).strip() in ["", "-", "nan"]: return 0.0
    val = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    val = re.sub(r'[^0-9\.\-]', '', val)
    try: return float(val)
    except: return 0.0

def mapear_divisional(cd):
    if pd.isna(cd) or str(cd).strip() in ["", "nan", "0"]: return "Indefinido"
    try:
        n_cd = int(re.sub(r'\D', '', str(cd).split('.')[0]))
    except: return "Indefinido"
    if n_cd in [590, 300, 50]: return 'Renato Nesello'
    elif n_cd in [2650, 994, 991, 1100, 1500, 1800, 1250]: return 'Antônio Paiva'
    elif n_cd in [350, 5200, 2900, 94, 490, 550, 2500, 1440]: return 'Christian'
    elif n_cd in [204, 2489, 97, 549, 2599, 1116, 1889, 389, 1879, 299, 1899, 2989, 5589, 1450, 49, 2999, 2099, 985, 93, 5289, 5299, 2649, 893, 5599, 1869, 1390]: return 'Mileide'
    return 'Outros'

@st.cache_data(ttl=300)
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/1iaHnigQGOH5w4xFlZXN0cXYSZlLqPuHE1Pdsgy0XSdI/export?format=csv&gid=1358149674"
    df = pd.read_csv(url).dropna(how='all')
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', str(c).strip().lower()) for c in df.columns]
    return df

try:
    df_raw = load_data().copy()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Filtros")
        if st.button("🔄 Atualizar"): st.cache_data.clear(); st.rerun()
        df_raw['tipo_clean'] = df_raw['tipo'].fillna('').astype(str).str.upper().str.strip()
        df_raw['divisional'] = df_raw['cd'].apply(mapear_divisional)
        t_sel = st.multiselect("Tipo", options=sorted(df_raw['tipo_clean'].unique()))
        d_sel = st.multiselect("Divisional", options=sorted([x for x in df_raw['divisional'].unique() if x != "Indefinido"]))

    # Dados
    c_1c = next((c for c in df_raw.columns if '1__ciclo' in c), None)
    c_fat = next((c for c in df_raw.columns if 'faturamento' in c), None)
    c_fal = next((c for c in df_raw.columns if 'falta_vol' in c), None)

    df_raw['v_1c'] = df_raw[c_1c].apply(limpar_valor)
    df_raw['v_fat'] = df_raw[c_fat].apply(limpar_valor)
    df_raw['v_fal'] = df_raw[c_fal].apply(limpar_valor)
    df_raw['is_fin'] = df_raw['v_1c'] != 0

    df_filt = df_raw.copy()
    if t_sel: df_filt = df_filt[df_filt['tipo_clean'].isin(t_sel)]
    if d_sel: df_filt = df_filt[df_filt['divisional'].isin(d_sel)]

    # --- UI ---
    st.markdown('<div class="header-box"><p class="header-title">BI FECHAMENTO MAGALOG 2026</p></div>', unsafe_allow_html=True)

    # Cards
    p1c = df_filt['v_1c'].sum(); vfal = df_filt['v_fal'].sum(); fat = df_filt['v_fat'].sum()
    p_glob = (abs(p1c + vfal)/fat*100) if fat > 0 else 0
    concl = (df_filt['is_fin'].sum()/len(df_filt)*100) if len(df_filt)>0 else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f'<div class="card-neon"><div class="label-neon">Perda Consolidada</div><div class="value-neon">R$ {p1c+vfal:,.0f}</div><div class="sub-neon">1C + Falta Vol</div></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="card-neon"><div class="label-neon">% Perda Global</div><div class="value-neon">{p_glob:.3f}%</div><div class="sub-neon">Sobre Faturamento</div></div>', unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="card-neon"><div class="label-neon">Volume Falta</div><div class="value-neon">{int(vfal):,}</div><div class="sub-neon">Itens Pendentes</div></div>', unsafe_allow_html=True)
    with k4: st.markdown(f'<div class="card-neon"><div class="label-neon">Evolução</div><div class="value-neon">{concl:.1f}%</div><div class="p-bar-bg"><div class="p-bar-fill" style="width:{concl}%"></div></div></div>', unsafe_allow_html=True)

   # --- SEÇÃO 1: GRÁFICO DE SAÚDE POR CD (LARGURA TOTAL) ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🏢 Visão Geral de Saúde por CD")
    
    df_tree = df_filt[df_filt['v_1c'] != 0].copy()
    df_tree['cd'] = df_tree['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
    
    fig_t = px.treemap(
        df_tree, 
        path=['divisional', 'cd'], 
        values=df_tree['v_1c'].abs(), 
        color='v_1c', 
        color_continuous_scale='Blues'
    )
    fig_t.update_layout(
        template="plotly_dark", 
        height=400, 
        margin=dict(t=30, b=10, l=0, r=0), 
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_t, use_container_width=True)

    # --- SEÇÃO 2: TABELA (ESQUERDA) + PIZZA (DIREITA) ---
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Criamos duas colunas: uma larga para a tabela (2.5) e uma estreita para a pizza (1)
    col_tab, col_graf = st.columns([2.5, 1])

    with col_tab:
        st.subheader("📋 Detalhamento Operacional")
        df_tab = df_filt.copy()
        df_tab['v_fat'] = pd.to_numeric(df_tab['v_fat'], errors='coerce').fillna(0)
        df_tab['%'] = (df_tab['v_1c'] / df_tab['v_fat'] * 100).fillna(0)
        df_tab['cd'] = df_tab['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        df_ex = df_tab[['semestre', 'tipo_clean', 'divisional', 'cd', 'local', 'v_1c', '%', 'v_fal', 'is_fin']]

        def styler(row):
            # Pintura total da linha: Vermelho para perda, Verde para ganho
            bg = 'background-color: #451a1a;' if row['v_1c'] < 0 else 'background-color: #1a4523;'
            return [bg] * len(row)

        st.dataframe(
            df_ex.style.apply(styler, axis=1), 
            column_config={
                "v_1c": st.column_config.NumberColumn("Resultado", format="R$ %.2f"),
                "%": st.column_config.NumberColumn("%", format="%.4f%%"),
                "v_fal": st.column_config.NumberColumn("Falta", format="%.0f"),
                "is_fin": "Fim?"
            }, 
            use_container_width=True, 
            hide_index=True,
            height=500 # Altura fixa para alinhar com o gráfico lateral
        )

    with col_graf:
        st.subheader("📍 Perda por Gerência")
        df_p = df_filt[df_filt['divisional'] != "Indefinido"]
        
        fig_p = px.pie(
            df_p, 
            values=df_p['v_1c'].abs(), 
            names='divisional', 
            hole=0.7, 
            color_discrete_sequence=["#00d2ff", "#008cff", "#0040ff", "#3a7bd5"]
        )
        fig_p.update_layout(
            template="plotly_dark", 
            height=500, # Mesma altura da tabela
            margin=dict(t=50, b=50, l=0, r=0), 
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_p, use_container_width=True)

except Exception as e:
    st.error(f"Erro: {e}")