import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Magalog | BI Executive", page_icon="📊")

# --- CSS DEFINITIVO (Ajuste de Topo e Filtros) ---
st.markdown("""
    <style>
    [data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 0.5rem !important; margin-top: -20px !important; }
    [data-testid="stAppViewContainer"] { background-color: #0d1117 !important; }

    .header-box {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%) !important;
        padding: 0.8rem !important; border-radius: 10px; text-align: center;
        margin-bottom: 1.5rem !important; box-shadow: 0 4px 15px rgba(0, 210, 255, 0.3);
    }
    .header-title { color: white !important; font-size: 22px !important; font-weight: 800 !important; margin:0; }

    .card-kpi {
        background: #161b22; border: 1px solid #30363d; border-radius: 12px;
        padding: 15px; text-align: center; min-height: 120px; border-bottom: 4px solid #00d2ff !important;
    }
    .value-kpi { color: #f0f6fc; font-size: 28px !important; font-weight: 900 !important; margin: 4px 0; }
    .label-kpi { color: #8b949e; font-size: 10px; font-weight: 600; text-transform: uppercase; }
    .sub-kpi { color: #00d2ff; font-size: 11px; }

    .plot-container {
        background-color: #161b22; padding: 15px; border-radius: 15px;
        border: 1px solid #30363d; box-shadow: 0 6px 12px rgba(0,0,0,0.4);
    }
    </style>
""", unsafe_allow_html=True)

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
    df_raw['tipo_clean'] = df_raw['tipo'].fillna('').astype(str).str.upper().str.strip()
    df_raw['divisional'] = df_raw['cd'].apply(mapear_divisional)
    
    c_1c = next((c for c in df_raw.columns if '1__ciclo' in c), None)
    c_fat = next((c for c in df_raw.columns if 'faturamento' in c), None)
    c_fal = next((c for c in df_raw.columns if 'falta_vol' in c), None)

    df_raw['v_1c'] = df_raw[c_1c].apply(limpar_valor) if c_1c else 0.0
    df_raw['v_fat'] = df_raw[c_fat].apply(limpar_valor) if c_fat else 0.0
    df_raw['v_falta'] = df_raw[c_fal].apply(limpar_valor) if c_fal else 0.0
    df_raw['is_fin'] = df_raw['v_1c'] != 0

    with st.sidebar:
        st.header("⚙️ Gerenciamento")
        if st.button("🔄 Atualizar"): st.cache_data.clear(); st.rerun()
        t_sel = st.multiselect("Filtrar por Tipo", options=sorted(df_raw['tipo_clean'].unique()))
        d_sel = st.multiselect("Filtrar Gerente", options=sorted([x for x in df_raw['divisional'].unique() if x != "Indefinido"]))

    df_filt = df_raw.copy()
    if t_sel: df_filt = df_filt[df_filt['tipo_clean'].isin(t_sel)]
    if d_sel: df_filt = df_filt[df_filt['divisional'].isin(d_sel)]

    st.markdown('<div class="header-box"><p class="header-title">BI FECHAMENTO MAGALOG 2026</p></div>', unsafe_allow_html=True)

    # KPIS
    p1c = df_filt['v_1c'].sum(); vfal = df_filt['v_falta'].sum()
    perda_total = p1c + vfal
    total_un = len(df_filt); fechadas = df_filt['is_fin'].sum(); pendentes = total_un - fechadas

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: st.markdown(f'<div class="card-kpi"><div class="label-kpi">Perda Consolidada</div><div class="value-kpi">R$ {perda_total:,.0f}</div><div class="sub-kpi">1C + Falta</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="card-kpi"><div class="label-kpi">Falta Volume</div><div class="value-kpi">R$ {vfal:,.0f}</div><div class="sub-kpi">Itens de Estoque</div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="card-kpi"><div class="label-kpi">Total Unidades</div><div class="value-kpi">{total_un}</div><div class="sub-kpi">Base Operacional</div></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div class="card-kpi"><div class="label-kpi">Finalizadas</div><div class="value-kpi" style="color:#00d2ff">{fechadas}</div><div class="sub-kpi">Status Concluído</div></div>', unsafe_allow_html=True)
    with m5: st.markdown(f'<div class="card-kpi"><div class="label-kpi">Pendentes</div><div class="value-kpi" style="color:#ff4b4b">{pendentes}</div><div class="sub-kpi">Em Aberto</div></div>', unsafe_allow_html=True)

    g1, g2 = st.columns([1, 1.1])
    with g1:
        st.subheader("📊 Resultado Consolidado")
        st.markdown('<div class="plot-container">', unsafe_allow_html=True)
        df_p = df_filt.groupby('tipo_clean')[['v_1c', 'v_falta']].sum().sum(axis=1).reset_index(name='res')
        fig_b = px.bar(df_p[df_p['res']!=0], x='tipo_clean', y=df_p['res'].abs(), text='res', color='tipo_clean',
                       color_discrete_map={'CD':'#3a7bd5','LV':'#7000ff','DQS':'#00f2ff'})
        fig_b.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')
        fig_b.update_layout(template="plotly_dark", height=350, showlegend=False, yaxis_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_b, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with g2:
        st.subheader("🏢 Status de Saúde (Divisória por CD)")
        st.markdown('<div class="plot-container">', unsafe_allow_html=True)
        df_tree = df_filt[df_filt['v_1c'] != 0].copy()
        df_tree['cd_label'] = df_tree['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        # PATH com dois níveis cria a divisória visual
        fig_t = px.treemap(df_tree, path=['tipo_clean', 'cd_label'], values=df_tree['v_1c'].abs(), 
                           color='tipo_clean', color_discrete_map={'CD':'#0040ff','LV':'#aa00ff','DQS':'#00d2ff'})
        fig_t.update_traces(textinfo="label+value", texttemplate="<b>%{label}</b><br>R$ %{value:,.0f}")
        fig_t.update_layout(template="plotly_dark", height=350, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_t, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("📋 Detalhamento Operacional")
    df_tab = df_filt.copy()
    df_tab['%'] = (df_tab['v_1c'] / df_tab['v_fat'] * 100).fillna(0)
    df_tab['cd_t'] = df_tab['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
    df_ex = df_tab[['semestre', 'tipo_clean', 'divisional', 'cd_t', 'local', 'v_1c', '%', 'v_falta', 'is_fin']]

    def styler(row):
        color = 'background-color: #451a1a' if row['v_1c'] < 0 else 'background-color: #1a4523'
        return [color] * len(row)

    st.dataframe(df_ex.style.apply(styler, axis=1), 
                 column_config={
                     "v_1c": st.column_config.NumberColumn("Resultado", format="R$ %.2f"),
                     "%": st.column_config.NumberColumn("% Unid", format="%.4f%%"),
                     "v_falta": st.column_config.NumberColumn("Falta", format="R$ %.0f")
                 },
                 use_container_width=True, hide_index=True, height=400)

except Exception as e:
    st.error(f"Erro: {e}")