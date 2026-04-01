import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Magalog | BI Executive", page_icon="📊")

# --- CSS REFINADO (Cards em linha única e Sidebar) ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0d1117 !important; }
    .main { padding: 0rem !important; }
    
    .header-box {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%) !important;
        padding: 1rem; border-radius: 0 0 15px 15px; text-align: center;
        margin-bottom: 1.5rem; box-shadow: 0 4px 20px rgba(0, 210, 255, 0.3);
    }
    .header-title { color: white !important; font-size: 24px !important; font-weight: 800 !important; margin:0; }

    /* Estilo Compacto para caber 6 na linha */
    .card-kpi {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 10px; padding: 10px; text-align: center;
        min-height: 110px; border-bottom: 3px solid #00d2ff;
    }
    .label-kpi { color: #8b949e; font-size: 10px; font-weight: 600; text-transform: uppercase; }
    .value-kpi { color: #f0f6fc; font-size: 18px; font-weight: 800; margin: 4px 0; }
    .sub-kpi { color: #00d2ff; font-size: 10px; font-weight: 500; }

    /* Barras de Target Compactas */
    .target-container {
        background: #21262d; border-radius: 3px; height: 20px; 
        position: relative; overflow: hidden; margin: 8px 0;
        display: flex; align-items: center; justify-content: center;
    }
    .target-fill { background: #00d2ff; height: 100%; position: absolute; left: 0; z-index: 1; }
    .target-text { color: white; font-weight: bold; z-index: 2; font-size: 11px; }
    .target-line { position: absolute; height: 100%; width: 2px; background: #00f2ff; z-index: 3; }
    .target-label { font-size: 8px; color: #8b949e; }
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
    try: n_cd = int(re.sub(r'\D', '', str(cd).split('.')[0]))
    except: return "Indefinido"
    if n_cd in [590, 300, 50]: return 'Renato Nesello'
    elif n_cd in [2650, 994, 991, 1100, 1500, 1800, 1250]: return 'Antônio Paiva'
    elif n_cd in [350, 5200, 2900, 94, 490, 550, 2500, 1440]: return 'Christian'
    elif n_cd in [204, 2489, 97, 549, 2599, 1116, 1889, 389, 1879, 299, 1899, 2989, 5589, 1450, 49, 2999, 2099, 985, 93, 5289, 5299, 2649, 893, 5599, 1869, 1390]: return 'Mileide'
    return 'Outros'

@st.cache_data(ttl=300)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1iaHnigQGOH5w4xFlZXN0cXYSZlLqPuHE1Pdsgy0XSdI/export?format=csv&gid=1358149674"
    df = pd.read_csv(url).dropna(how='all')
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', str(c).strip().lower()) for c in df.columns]
    return df

try:
    df_raw = load_data().copy()
    
    # TRATAMENTO INICIAL
    df_raw['tipo_clean'] = df_raw['tipo'].fillna('').astype(str).str.upper().str.strip()
    df_raw['divisional'] = df_raw['cd'].apply(mapear_divisional)
    
    c_1c = next((c for c in df_raw.columns if '1__ciclo' in c), None)
    c_fat = next((c for c in df_raw.columns if 'faturamento' in c), None)
    c_fal = next((c for c in df_raw.columns if 'falta_vol' in c), None)

    df_raw['v_1c'] = df_raw[c_1c].apply(limpar_valor) if c_1c else 0.0
    df_raw['v_fat'] = df_raw[c_fat].apply(limpar_valor) if c_fat else 0.0
    df_raw['v_falta'] = df_raw[c_fal].apply(limpar_valor) if c_fal else 0.0
    df_raw['is_fin'] = df_raw['v_1c'] != 0

    # SIDEBAR
    with st.sidebar:
        st.header("⚙️ Gerenciamento")
        if st.button("🔄 Atualizar Dados"): st.cache_data.clear(); st.rerun()
        t_sel = st.multiselect("Filtrar por Tipo", options=sorted(df_raw['tipo_clean'].unique()))
        d_sel = st.multiselect("Filtrar Gerente", options=sorted([x for x in df_raw['divisional'].unique() if x != "Indefinido"]))

    df_filt = df_raw.copy()
    if t_sel: df_filt = df_filt[df_filt['tipo_clean'].isin(t_sel)]
    if d_sel: df_filt = df_filt[df_filt['divisional'].isin(d_sel)]

    # --- UI PRINCIPAL ---
    st.markdown('<div class="header-box"><p class="header-title">BI FECHAMENTO MAGALOG 2026</p></div>', unsafe_allow_html=True)

    # CÁLCULOS
    p1c = df_filt['v_1c'].sum(); vfal = df_filt['v_falta'].sum()
    perda_total = p1c + vfal
    perc_falta = (vfal / perda_total * 100) if perda_total != 0 else 0
    total_uds = len(df_filt); fechadas = df_filt['is_fin'].sum(); pendentes = total_uds - fechadas
    target_pos = 70

    # LINHA ÚNICA COM 6 COLUNAS
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    
    with m1: st.markdown(f'<div class="card-kpi"><div class="label-kpi">Perda Consolidada</div><div class="value-kpi">R$ {perda_total:,.0f}</div><div class="sub-kpi">1C + Falta Vol</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="card-kpi"><div class="label-kpi">Volume Falta</div><div class="value-kpi">R$ {vfal:,.0f}</div><div class="sub-kpi">{abs(perc_falta):.1f}% do Total</div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="card-kpi"><div class="label-kpi">Média / Unidade</div><div class="value-kpi">R$ {perda_total/total_uds if total_uds>0 else 0:,.0f}</div><div class="sub-kpi">Base: {total_uds} Uds</div></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div class="card-kpi"><div class="label-kpi">Total Unidades</div><div class="value-kpi">{total_uds}</div><div class="sub-kpi">Base Operacional</div></div>', unsafe_allow_html=True)
    
    with m5:
        pf = (fechadas/total_uds*100) if total_uds > 0 else 0
        st.markdown(f'''<div class="card-kpi"><div class="label-kpi">Finalizadas</div><div class="target-container"><div class="target-fill" style="width:{pf}%;"></div><div class="target-line" style="left:{target_pos}%;"></div><div class="target-text">{fechadas}</div></div>
        <div style="display:flex;justify-content:space-between;"><span class="target-label">0</span><span class="target-label">target</span><span class="target-label">{total_uds}</span></div></div>''', unsafe_allow_html=True)
    
    with m6:
        pp = (pendentes/total_uds*100) if total_uds > 0 else 0
        st.markdown(f'''<div class="card-kpi"><div class="label-kpi">Pendentes</div><div class="target-container" style="background:#2a1b1b;"><div class="target-fill" style="width:{pp}%;background:#ff4b4b;"></div><div class="target-line" style="left:{target_pos}%;background:#ff4b4b;"></div><div class="target-text">{pendentes}</div></div>
        <div style="display:flex;justify-content:space-between;"><span class="target-label">0</span><span class="target-label">target</span><span class="target-label">{total_uds}</span></div></div>''', unsafe_allow_html=True)

    # --- GRÁFICOS E TABELA ---
    st.markdown("<br>", unsafe_allow_html=True)
    g1, g2 = st.columns([1, 1.1])
    with g1:
        st.subheader("📊 Resultado Consolidado")
        df_p = df_filt.groupby('tipo_clean')[['v_1c', 'v_falta']].sum().sum(axis=1).reset_index(name='res')
        fig_b = px.bar(df_p, x='tipo_clean', y=df_p['res'].abs(), text='res', color='tipo_clean', color_discrete_map={'CD':'#3a7bd5','LV':'#7000ff','DQS':'#00f2ff'})
        fig_b.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')
        fig_b.update_layout(template="plotly_dark", height=350, showlegend=False, yaxis_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_b, use_container_width=True)

    with g2:
        st.subheader("🏢 Status de Saúde")
        df_tree = df_filt.copy(); df_tree['res'] = df_tree['v_1c'] + df_tree['v_falta']
        df_tree = df_tree[df_tree['res'] != 0].copy()
        df_tree['cd_lbl'] = df_tree['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        fig_t = px.treemap(df_tree, path=['tipo_clean', 'cd_lbl'], values=df_tree['res'].abs(), color='tipo_clean', color_discrete_map={'CD':'#0040ff','LV':'#aa00ff','DQS':'#00d2ff'})
        fig_t.update_traces(textinfo="label+value", texttemplate="<b>%{label}</b><br>R$ %{value:,.0f}")
        fig_t.update_layout(template="plotly_dark", height=350, margin=dict(t=20, b=10, l=0, r=0))
        st.plotly_chart(fig_t, use_container_width=True)

    # TABELA E PIZZA
    b1, b2 = st.columns([3, 1.2])
    with b1:
        st.subheader("📋 Detalhamento")
        df_tab = df_filt.copy()
        df_tab['%'] = (df_tab['v_1c'] / df_tab['v_fat'] * 100).fillna(0)
        df_tab['cd'] = df_tab['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        df_ex = df_tab[['semestre', 'tipo_clean', 'divisional', 'cd', 'local', 'v_1c', '%', 'v_falta', 'is_fin']]
        st.dataframe(df_ex.style.apply(lambda r: ['background-color: #451a1a' if r['v_1c'] < 0 else 'background-color: #1a4523']*len(r), axis=1),
                     column_config={"v_1c": st.column_config.NumberColumn("Resultado", format="R$ %.2f"), "%": st.column_config.NumberColumn("%", format="%.3f%%"), "v_falta": st.column_config.NumberColumn("Falta", format="%.0f")},
                     use_container_width=True, hide_index=True, height=400)
    with b2:
        st.subheader("📍 Perda / Gerente")
        df_pi = df_filt[df_filt['divisional'] != "Indefinido"]
        fig_pi = px.pie(df_pi, values=df_pi['v_1c'].abs(), names='divisional', hole=0.7, color_discrete_sequence=["#00d2ff", "#008cff", "#0040ff", "#3a7bd5"])
        fig_pi.update_layout(template="plotly_dark", height=400, margin=dict(t=50, b=50, l=0, r=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
        st.plotly_chart(fig_pi, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ Erro ao processar BI: {e}")