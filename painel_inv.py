import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA (WIDE MODE)
st.set_page_config(layout="wide", page_title="Magalog | BI Executive", page_icon="📊")

# --- CSS SENIOR (TOPO ABSOLUTO E Z-INDEX) ---
st.markdown("""
    <style>
    [data-testid="stHeader"] { display: none; }
    .block-container { 
        padding-top: 0rem !important; 
        margin-top: -35px !important; 
    }
    [data-testid="stAppViewContainer"] { background-color: #0d1117 !important; }
    
    .header-box {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%) !important;
        padding: 0.8rem !important; border-radius: 0 0 15px 15px; text-align: center;
        margin-bottom: 1.5rem !important; box-shadow: 0 4px 15px rgba(0, 210, 255, 0.4);
    }
    .header-title { color: white !important; font-size: 24px !important; font-weight: 800 !important; margin:0; }

    .card-kpi {
        background: #161b22; border: 1px solid #30363d; border-radius: 12px;
        padding: 15px; text-align: center; min-height: 110px; border-bottom: 4px solid #00d2ff !important;
    }
    .value-kpi { color: #f0f6fc; font-size: 26px !important; font-weight: 900 !important; margin: 4px 0; }
    .label-kpi { color: #8b949e; font-size: 11px; font-weight: 600; text-transform: uppercase; }
    
    .plot-container {
        background-color: #161b22; padding: 15px; border-radius: 15px;
        border: 1px solid #30363d; box-shadow: 0 6px 12px rgba(0,0,0,0.4);
    }
    </style>
""", unsafe_allow_html=True)

# --- ENGINE DE DADOS ---
def limpar_valor(v):
    if pd.isna(v) or str(v).strip() in ["", "-", "nan"]: return 0.0
    val = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    val = re.sub(r'[^0-9\.\-]', '', val)
    try: return float(val)
    except: return 0.0

def mapear_divisional(cd):
    try:
        n_cd = int(re.sub(r'\D', '', str(cd).split('.')[0]))
        if n_cd in [590, 300, 50]: return 'Renato Nesello'
        elif n_cd in [2650, 994, 991, 1100, 1500, 1800, 1250]: return 'Antônio Paiva'
        elif n_cd in [350, 5200, 2900, 94, 490, 550, 2500, 1440]: return 'Christian'
        elif n_cd in [204, 2489, 97, 549, 2599, 1116, 1889, 389, 1879, 299, 1899, 2989, 5589, 1450, 49, 2999, 2099, 985, 93, 5289, 5299, 2649, 893, 5599, 1869, 1390]: return 'Mileide'
    except: pass
    return 'Outros'

@st.cache_data(ttl=60)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1iaHnigQGOH5w4xFlZXN0cXYSZlLqPuHE1Pdsgy0XSdI/export?format=csv&gid=1358149674"
    df = pd.read_csv(url).dropna(how='all')
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', str(c).strip().lower()) for c in df.columns]
    return df

try:
    df_raw = load_data().copy()
    df_raw['tipo_clean'] = df_raw['tipo'].fillna('').astype(str).str.upper().str.strip()
    df_raw['divisional'] = df_raw['cd'].apply(mapear_divisional)
    
    # Identificação Dinâmica de Colunas
    c_1c = next((c for c in df_raw.columns if '1__ciclo' in c), None)
    c_fat = next((c for c in df_raw.columns if 'faturamento' in c), None)
    c_fal = next((c for c in df_raw.columns if 'falta_vol' in c), None)

    df_raw['v_1c'] = df_raw[c_1c].apply(limpar_valor) if c_1c else 0.0
    df_raw['v_fat'] = df_raw[c_fat].apply(limpar_valor) if c_fat else 0.0
    df_raw['v_falta'] = df_raw[c_fal].apply(limpar_valor) if c_fal else 0.0
    df_raw['is_fin'] = df_raw['v_1c'] != 0

    # --- SIDEBAR (CONTROLES) ---
    with st.sidebar:
        st.header("⚙️ Filtros Executivos")
        if st.button("🔄 Forçar Refresh"): st.cache_data.clear(); st.rerun()
        t_sel = st.multiselect("Tipo de Unidade", options=sorted(df_raw['tipo_clean'].unique()))
        d_sel = st.multiselect("Gerente Responsável", options=sorted(df_raw['divisional'].unique()))

    df_filt = df_raw.copy()
    if t_sel: df_filt = df_filt[df_filt['tipo_clean'].isin(t_sel)]
    if d_sel: df_filt = df_filt[df_filt['divisional'].isin(d_sel)]

    # --- HEADER ---
    st.markdown('<div class="header-box"><p class="header-title">BI FECHAMENTO MAGALOG 2026</p></div>', unsafe_allow_html=True)

    # --- INDICADORES ---
    p1c = df_filt['v_1c'].sum(); vfal = df_filt['v_falta'].sum()
    perda_total = p1c + vfal
    total_un = len(df_filt); fechadas = df_filt['is_fin'].sum(); pendentes = total_un - fechadas

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1: st.markdown(f'<div class="card-kpi"><div class="label-kpi">Perda Consolidada</div><div class="value-kpi">R$ {perda_total:,.0f}</div></div>', unsafe_allow_html=True)
    with kpi2: st.markdown(f'<div class="card-kpi"><div class="label-kpi">Falta Volume</div><div class="value-kpi">R$ {vfal:,.0f}</div></div>', unsafe_allow_html=True)
    with kpi3: st.markdown(f'<div class="card-kpi"><div class="label-kpi">Unidades Totais</div><div class="value-kpi">{total_un}</div></div>', unsafe_allow_html=True)
    with kpi4: st.markdown(f'<div class="card-kpi"><div class="label-kpi">Finalizadas</div><div class="value-kpi" style="color:#00d2ff">{fechadas}</div></div>', unsafe_allow_html=True)
    with kpi5: st.markdown(f'<div class="card-kpi"><div class="label-kpi">Pendentes</div><div class="value-kpi" style="color:#ff4b4b">{pendentes}</div></div>', unsafe_allow_html=True)

    # --- BODY DASHBOARD ---
    col_g1, col_g2 = st.columns([1, 1.2])
    
    with col_g1:
        st.subheader("📊 Performance por Tipo")
        st.markdown('<div class="plot-container">', unsafe_allow_html=True)
        df_p = df_filt.groupby('tipo_clean')[['v_1c', 'v_falta']].sum().sum(axis=1).reset_index(name='val')
        fig_b = px.bar(df_p[df_p['val']!=0], x='tipo_clean', y=df_p['val'].abs(), text='val', color='tipo_clean',
                       color_discrete_map={'CD':'#3a7bd5','LV':'#7000ff','DQS':'#00f2ff'})
        fig_b.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')
        fig_b.update_layout(template="plotly_dark", height=380, showlegend=False, yaxis_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=40))
        st.plotly_chart(fig_b, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_g2:
        st.subheader("🏢 Status de Saúde (Hierarquia CD)")
        st.markdown('<div class="plot-container">', unsafe_allow_html=True)
        df_tree = df_filt[df_filt['v_1c'] != 0].copy()
        df_tree['cd_id'] = df_tree['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        
        # AQUI RESOLVEMOS A SEPARAÇÃO: Path hierárquico
        fig_t = px.treemap(df_tree, path=[px.Constant("Rede"), 'tipo_clean', 'cd_id'], 
                           values=df_tree['v_1c'].abs(), color='tipo_clean',
                           color_discrete_map={'CD':'#0040ff','LV':'#aa00ff','DQS':'#00d2ff'})
        fig_t.update_traces(textinfo="label+value", texttemplate="<b>%{label}</b><br>R$ %{value:,.0f}")
        fig_t.update_layout(template="plotly_dark", height=380, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_t, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- BASE (TABELA + PIZZA) ---
    col_b1, col_b2 = st.columns([2.5, 1.2])
    
    with col_b1:
        st.subheader("📋 Detalhamento")
        df_tab = df_filt.copy()
        df_tab['%_unid'] = (df_tab['v_1c'] / df_tab['v_fat'] * 100).fillna(0)
        df_tab['cd_str'] = df_tab['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        
        # Seleção estrita e Reset de Index para evitar erro de length
        df_ex = df_tab[['semestre', 'tipo_clean', 'divisional', 'cd_str', 'local', 'v_1c', '%_unid', 'v_falta', 'is_fin']].reset_index(drop=True)

        # MÉTODO SENIOR: Estilização via função que ignora o índice e foca no subset
        def color_negative_red(val):
            color = '#451a1a' if val < 0 else '#1a4523'
            return f'background-color: {color}'

        st.dataframe(
            df_ex.style.map(color_negative_red, subset=['v_1c']), 
            column_config={
                "v_1c": st.column_config.NumberColumn("Resultado", format="R$ %.2f"),
                "%_unid": st.column_config.NumberColumn("% Unid", format="%.4f%%"),
                "v_falta": st.column_config.NumberColumn("Falta", format="R$ %.0f")
            },
            use_container_width=True, hide_index=True, height=450
        )
    
    with col_b2:
        st.subheader("📍 Perda / Gerente")
        df_pi = df_filt[df_filt['divisional'] != "Outros"].copy()
        if not df_pi.empty:
            fig_pi = px.pie(df_pi, values=df_pi['v_1c'].abs(), names='divisional', hole=0.6,
                            color_discrete_sequence=px.colors.sequential.Blues_r)
            fig_pi.update_layout(template="plotly_dark", height=450, showlegend=True, 
                                paper_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", y=-0.1))
            st.plotly_chart(fig_pi, use_container_width=True)
        else:
            st.info("Sem dados para o gráfico de pizza.")

except Exception as e:
    st.error(f"Erro Crítico: {e}")