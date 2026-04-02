import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Prevenção | BI Executive", page_icon="📊")

# --- ESTILIZAÇÃO CSS (Big Numbers + 6 Cards) ---
# --- ESTILIZAÇÃO CSS (Big Numbers + Cards) ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0d1117 !important; }
    .main { padding: 0rem !important; }
    
    .header-box {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%) !important;
        padding: 1rem; border-radius: 0 0 15px 15px; text-align: center;
        margin-bottom: 0px !important; 
        box-shadow: 0 4px 20px rgba(0, 210, 255, 0.3);
        position: relative;
        z-index: 99;
    }
    .header-title { color: white !important; font-size: 26px !important; font-weight: 800 !important; margin:0; }

    .card-kpi {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 12px; padding: 15px; text-align: center;
        border-bottom: 4px solid #00d2ff;
        margin-top: -55px; /* <-- AUMENTEI AQUI: Puxa os cards mais pra cima para colar no título! */
    }
    .label-kpi { color: #8b949e; font-size: 11px; font-weight: 600; text-transform: uppercase; margin-bottom: 5px; }
    .value-kpi { color: #f0f6fc; font-size: 26px !important; font-weight: 900 !important; margin: 5px 0; letter-spacing: -1px; }
    .sub-kpi { color: #00d2ff; font-size: 12px; font-weight: 500; }
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
        if st.button("🔄 Atualizar Dados"): st.cache_data.clear(); st.rerun()
        
        # Filtros adicionados: Semestre, Tipo e Gerente
        s_sel = st.multiselect("Filtrar Semestre", options=sorted(df_raw['semestre'].dropna().unique())) if 'semestre' in df_raw.columns else []
        t_sel = st.multiselect("Filtrar por Tipo", options=sorted(df_raw['tipo_clean'].unique()))
        d_sel = st.multiselect("Filtrar Gerente", options=sorted([x for x in df_raw['divisional'].unique() if x != "Indefinido"]))

    df_filt = df_raw.copy()
    if s_sel: df_filt = df_filt[df_filt['semestre'].isin(s_sel)]
    if t_sel: df_filt = df_filt[df_filt['tipo_clean'].isin(t_sel)]
    if d_sel: df_filt = df_filt[df_filt['divisional'].isin(d_sel)]

    # --- UI PRINCIPAL ---
    st.markdown('<div class="header-box"><p class="header-title">BI FECHAMENTO INV PREVENÇAO DE PERDAS 2026</p></div>', unsafe_allow_html=True)

    # CÁLCULOS
    p1c = df_filt['v_1c'].sum()
    vfal = df_filt['v_falta'].sum()
    vfat_total = df_filt['v_fat'].sum()
    perda_total = p1c + vfal
    
    perc_falta = (vfal / perda_total * 100) if perda_total != 0 else 0
    perc_geral_perdas = (perda_total / vfat_total * 100) if vfat_total != 0 else 0
    perc_geral_str = f"{perc_geral_perdas:.3f}".replace('.', ',') + "%"
    
    total_uds = len(df_filt)
    fechadas = df_filt['is_fin'].sum()
    pendentes = total_uds - fechadas
    target_pos = 70

    # --- CÁLCULO DINÂMICO DE COMPARAÇÃO COM 2025 ---
    dados_2025 = pd.DataFrame([
        {'tipo': 'CD', 'semestre': '1º semestre', 'valor': 9415271},
        {'tipo': 'CD', 'semestre': '2º semestre', 'valor': 5379088},
        {'tipo': 'CROSS', 'semestre': '1º semestre', 'valor': 2183},
        {'tipo': 'CROSS', 'semestre': '2º semestre', 'valor': 1633},
        {'tipo': 'DQS', 'semestre': '1º semestre', 'valor': 269835},
        {'tipo': 'DQS', 'semestre': '2º semestre', 'valor': -268613},
        {'tipo': 'LV', 'semestre': '1º semestre', 'valor': 619830},
        {'tipo': 'LV', 'semestre': '2º semestre', 'valor': 2509390}
    ])

    tipos_presentes = df_filt['tipo_clean'].unique()
    
    if 'semestre' in df_filt.columns:
        semestres_presentes = df_filt['semestre'].astype(str).str.lower().str.strip().unique()
        dados_2025['semestre_clean'] = dados_2025['semestre'].str.lower().str.strip()
        df_2025_filt = dados_2025[(dados_2025['tipo'].isin(tipos_presentes)) & (dados_2025['semestre_clean'].isin(semestres_presentes))]
    else:
        df_2025_filt = dados_2025[dados_2025['tipo'].isin(tipos_presentes)]

    perda_2025_abs = df_2025_filt['valor'].sum()
    perda_total_abs = abs(perda_total)
    
    if perda_2025_abs != 0:
        var_perc = ((perda_total_abs - perda_2025_abs) / abs(perda_2025_abs)) * 100
    else:
        var_perc = 0

    if var_perc < 0:
        texto_var = f'<span style="color:#3fb950; font-weight:bold;">▼ {abs(var_perc):.1f}% (Redução)</span> vs 2025'
    elif var_perc > 0:
        texto_var = f'<span style="color:#ff4b4b; font-weight:bold;">▲ {var_perc:.1f}% (Aumento)</span> vs 2025'
    else:
        texto_var = "Igual a 2025"


    # 6 CARDS KPI 
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
   # 4 CARDS KPI (ajustado para 4 colunas iguais, dando mais largura para a tabela)
    c1, c2, c3, c4 = st.columns(4)
    
   # 4 CARDS KPI 
    c1, c2, c3, c4 = st.columns(4)
    
    # Estilo unificado: altura fixa de 250px e centralização vertical do conteúdo
    estilo_card = "height: 250px; display: flex; flex-direction: column; justify-content: center; align-items: center;"
# 4 CARDS KPI 
    c1, c2, c3, c4 = st.columns(4)
    
    # Estilo unificado: altura fixa de 250px e centralização vertical do conteúdo
    estilo_card = "height: 250px; display: flex; flex-direction: column; justify-content: center; align-items: center;"

    # 4 CARDS KPI 
    c1, c2, c3, c4 = st.columns(4)
    
    # Reduzimos a altura para 200px para ficar mais compacto e tiramos os espaços excessivos
    estilo_card = "height: 200px; display: flex; flex-direction: column; justify-content: center; align-items: center;"

    # 4 CARDS KPI 
    c1, c2, c3, c4 = st.columns(4)
    
    # Altura "sob medida" (160px) e padding reduzido (10px) para eliminar a "testa" grande
    estilo_card = "height: 160px; padding: 10px; display: flex; flex-direction: column; justify-content: center; align-items: center; box-sizing: border-box;"

   # 4 CARDS KPI 
    c1, c2, c3, c4 = st.columns(4)
    
    # Trocamos "justify-content: center" por "flex-start" para alinhar os títulos no topo!
    estilo_card = "height: 175px; padding: 15px 10px; display: flex; flex-direction: column; justify-content: flex-start; align-items: center; box-sizing: border-box;"

    # 4 CARDS KPI 
    c1, c2, c3, c4 = st.columns(4)
    
    # Altura corrigida para 195px para caber a tabela inteira dentro da borda
    estilo_card = "height: 195px; padding: 15px 10px; display: flex; flex-direction: column; justify-content: flex-start; align-items: center; box-sizing: border-box;"

   # 5 CARDS KPI (Separando a tabela em um card próprio)
    c1, c2, c3, c4, c5 = st.columns(5)
    
    # Altura elegante de 150px e conteúdo perfeitamente centralizado no meio!
    estilo_card = "height: 150px; padding: 10px; display: flex; flex-direction: column; justify-content: center; align-items: center; box-sizing: border-box;"

   # --- 5 CARDS KPI ---
    c1, c2, c3, c4, c5 = st.columns(5)
    
    # Altura elegante de 150px e conteúdo perfeitamente centralizado no meio!
    estilo_card = "height: 150px; padding: 10px; display: flex; flex-direction: column; justify-content: center; align-items: center; box-sizing: border-box;"

    with c1: 
        st.markdown(f'''
        <div class="card-kpi" style="{estilo_card}">
            <div style="width: 100%;">
                <div class="label-kpi">Perda Consolidada</div>
                <div class="value-kpi">R$ {perda_total:,.0f}</div>
                <div class="sub-kpi">{texto_var}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
    with c2: 
        st.markdown(f'''
        <div class="card-kpi" style="{estilo_card}">
            <div style="width: 100%;">
                <div class="label-kpi">Falta Volume</div>
                <div class="value-kpi">R$ {vfal:,.0f}</div>
                <div class="sub-kpi">{abs(perc_falta):.1f}% da Perda</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
    with c3: 
        st.markdown(f'''
        <div class="card-kpi" style="{estilo_card}">
            <div style="width: 100%;">
                <div class="label-kpi">% Geral de Perdas</div>
                <div class="value-kpi">{perc_geral_str}</div>
                <div class="sub-kpi">Sobre Faturamento</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
    with c4: 
        perc_finalizadas = (fechadas / total_uds * 100) if total_uds > 0 else 0
        st.markdown(f'''
        <div class="card-kpi" style="{estilo_card}">
            <div style="width: 100%;">
                <div class="label-kpi">Total Unidades</div>
                <div class="value-kpi">{total_uds}</div>
                <div class="sub-kpi">{perc_finalizadas:.1f}% Finalizadas</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

    with c5: 
        df_validos = df_filt[df_filt['tipo_clean'].str.strip() != '']
        resumo_tipos = df_validos.groupby('tipo_clean').agg(
            Total=('tipo_clean', 'count'),
            Fim=('is_fin', 'sum')
        ).reset_index()
        resumo_tipos['Pen'] = resumo_tipos['Total'] - resumo_tipos['Fim']

        linhas_html = ""
        for _, row in resumo_tipos.iterrows():
            # Adicionado white-space: nowrap; na primeira coluna para evitar quebra
            linhas_html += f"<tr><td style='text-align:left; color:#8b949e; padding:2px; white-space: nowrap;'>{row['tipo_clean']}</td><td style='color:#f0f6fc; text-align:center; padding:2px;'>{row['Total']}</td><td style='color:#3fb950; text-align:center; padding:2px;'>{row['Fim']}</td><td style='color:#ff4b4b; text-align:center; padding:2px;'>{row['Pen']}</td></tr>"

        # Adicionado white-space: nowrap; em todos os cabeçalhos (Tot, Fim, Pen)
        tabela_html = f"<table style='width:100%; table-layout: fixed; font-size:10.5px; margin-top:0px; border-top:1px solid #30363d; padding-top:4px; border-collapse: collapse;'><thead><tr style='color:#8b949e; text-transform:uppercase; border-bottom:1px solid #30363d;'><th style='text-align:left; padding-bottom:4px; padding-left:2px;'>Tipo</th><th style='text-align:center; padding-bottom:4px; white-space: nowrap;'>Tot</th><th style='text-align:center; padding-bottom:4px; white-space: nowrap;'>Fim</th><th style='text-align:center; padding-bottom:4px; padding-right:2px; white-space: nowrap;'>Pen</th></tr></thead><tbody>{linhas_html}</tbody></table>"
        
        html_final = f"""<div class="card-kpi" style="{estilo_card}">
            <div style="width: 100%;">
                <div class="label-kpi" style="margin-bottom:8px;">Status por Tipo</div>
                {tabela_html}
            </div>
        </div>"""

        st.markdown(html_final, unsafe_allow_html=True)
    ##  with c6:
       ##   pp = (pendentes/total_uds*100) if total_uds > 0 else 0
        ##  st.markdown(f'''<div class="card-kpi" style="min-height: 180px;"><div class="label-kpi">Pendentes</div><div class="target-container" style="background:#2a1b1b;"><div class="target-fill" style="width:{pp}%;background:#ff4b4b;"></div><div class="target-line" style="left:{target_pos}%;background:#ff4b4b;"></div><div class="target-text">{pendentes}</div></div>
        ##  <div style="display:flex;justify-content:space-between;"><span class="target-label">0</span><span class="target-label">target</span><span class="target-label">{total_uds}</span></div></div>''', unsafe_allow_html=True)

    # --- GRÁFICOS DO MEIO ---
    st.markdown("<br>", unsafe_allow_html=True)
    g1, g2 = st.columns([1, 1.1])
    
    with g1:
        st.subheader("📊 Resultado Consolidado (1C + Falta Vol)")
        df_proc = df_filt.copy()
        df_proc['res_total'] = df_proc['v_1c'] + df_proc['v_falta']
        df_plot = df_proc.groupby('tipo_clean')['res_total'].sum().reset_index()
        fig_b = px.bar(df_plot, x='tipo_clean', y=df_plot['res_total'].abs(), text='res_total', color='tipo_clean', 
                       color_discrete_map={'CD':'#3a7bd5','LV':'#7000ff','DQS':'#00f2ff'})
        fig_b.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')
        fig_b.update_layout(template="plotly_dark", height=380, showlegend=False, yaxis_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_b, use_container_width=True)

    with g2:
        st.subheader("🏢 Status de Saúde (Apenas 1º Ciclo)")
        df_tree = df_filt[df_filt['v_1c'] != 0].copy()
        df_tree['cd_lbl'] = df_tree['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        fig_t = px.treemap(df_tree, path=['tipo_clean', 'cd_lbl'], values=df_tree['v_1c'].abs(), color='tipo_clean', 
                           color_discrete_map={'CD':'#0040ff','LV':'#aa00ff','DQS':'#00d2ff'})
        fig_t.update_traces(textinfo="label+value", texttemplate="<b>%{label}</b><br>R$ %{value:,.0f}")
        fig_t.update_layout(template="plotly_dark", height=380, margin=dict(t=20, b=10, l=0, r=0))
        st.plotly_chart(fig_t, use_container_width=True)

    # --- BASE (TABELA + PIZZA) ---
    st.markdown("<br>", unsafe_allow_html=True)
    b1, b2 = st.columns([3, 1.2])
    with b1:
        st.subheader("📋 Detalhamento")
        df_tab = df_filt.copy()
        df_tab['%'] = (df_tab['v_1c'] / df_tab['v_fat'] * 100).fillna(0)
        df_tab['cd_t'] = df_tab['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        
        # Mantemos os nomes originais para não quebrar a lógica de cores
        df_ex = df_tab[['semestre', 'tipo_clean', 'divisional', 'cd_t', 'local', 'v_1c', '%', 'v_falta', 'is_fin']]
        
        # Aplicamos a cor baseada na coluna original 'v_1c' e usamos o column_config para traduzir os títulos
        st.dataframe(
            df_ex.style.apply(lambda r: ['background-color: #451a1a' if r['v_1c'] < 0 else 'background-color: #1a4523']*len(r), axis=1),
            column_config={
                "semestre": "SEMESTRE",
                "tipo_clean": "TIPO",
                "divisional": "GERENTE",
                "cd_t": "UNIDADES",
                "local": "LOCAL",
                "v_1c": st.column_config.NumberColumn("$RESULTADO", format="R$ %.2f"), 
                "%": st.column_config.NumberColumn("%PERDAS", format="%.3f%%"), 
                "v_falta": st.column_config.NumberColumn("FALTA VOL.", format="%.0f"),
                "is_fin": "FINALIZADA"
            },
            use_container_width=True, 
            hide_index=True, 
            height="content"
        )
    with b2:
        st.subheader("📍 Perda / Gerente")
        df_pi = df_filt[df_filt['divisional'] != "Indefinido"]
        fig_pi = px.pie(df_pi, values=df_pi['v_1c'].abs(), names='divisional', hole=0.7, color_discrete_sequence=["#00d2ff", "#008cff", "#0040ff", "#3a7bd5"])
        fig_pi.update_layout(template="plotly_dark", height=450, margin=dict(t=50, b=50, l=0, r=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
        st.plotly_chart(fig_pi, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ Erro crítico: {e}")