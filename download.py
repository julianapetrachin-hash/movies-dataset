import streamlit as st
import pandas as pd
import io
import plotly.express as px

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E DESIGN (FUTURISTA)
# ==========================================
st.set_page_config(page_title="Centro de Comando | Estoque", page_icon="🛸", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        /* Tema Escuro / Cyberpunk */
        .main-header { font-size: 2.5rem; color: #00FFC4; font-weight: 800; text-align: center; margin-bottom: 0; text-transform: uppercase; letter-spacing: 2px;}
        .sub-header { font-size: 1.1rem; color: #8892B0; text-align: center; margin-bottom: 30px; }
        
        /* Cards Neon Futuristas */
        .kpi-card { background: linear-gradient(145deg, #0B132B, #1C2541); padding: 20px; border-radius: 12px; border-left: 5px solid #00FFC4; box-shadow: 0 4px 15px rgba(0, 255, 196, 0.15); color: white; transition: 0.3s;}
        .kpi-card:hover { transform: translateY(-5px); box-shadow: 0 6px 20px rgba(0, 255, 196, 0.3); border-left: 5px solid #00B4D8;}
        .kpi-title { margin:0; font-size: 14px; color: #8892B0; font-weight: 600; text-transform: uppercase;}
        .kpi-value { margin:0; font-size: 32px; color: #00FFC4; font-weight: bold; font-family: 'Courier New', monospace;}
        
        /* Botão de Download Moderno */
        .stDownloadButton>button { background: linear-gradient(90deg, #00FFC4 0%, #00B4D8 100%); color: #0B132B; border: none; padding: 15px 32px; font-size: 18px; border-radius: 8px; width: 100%; font-weight: 800; transition: 0.4s; text-transform: uppercase;}
        .stDownloadButton>button:hover { opacity: 0.8; transform: scale(1.02); color: #0B132B;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNÇÕES DE CARREGAMENTO E TRATAMENTO
# ==========================================
SHEET_ID = "11-IwzWjgFVKynzDTkqpr4_Fbs4GclKhS7W0KTKms0q4" 

@st.cache_data(ttl=600)
def carregar_dados():
    # Adicionamos o parâmetro decimal para o Pandas entender a vírgula do Sheets
    url_resultados = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=BigQuery+Results"
    url_historico = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Historico"
    
    try:
        # Lemos o CSV tratando vírgula como decimal (padrão Brasil do seu Sheets)
        df_res = pd.read_csv(url_resultados, decimal=',')
        df_hist = pd.read_csv(url_historico)
        
        # Tratamento de segurança para garantir que tudo seja FLOAT
        cols_financeiras = ['VALOR_TOTAL_ESTOQUE_ATUALIZADO', 'QT_ESTOQUE', 'CUSTO_MEDIO', 'CUSTO_PGTO']
        
        for col in cols_financeiras:
            if col in df_res.columns:
                # Se ainda houver sujeira de string, limpamos antes de converter
                if df_res[col].dtype == 'object':
                    df_res[col] = df_res[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df_res[col] = pd.to_numeric(df_res[col], errors='coerce').fillna(0)
            
        return df_res, df_hist
    except Exception as e:
        st.error(f"Erro na matriz de dados: {e}")
        return None, None

def limpar_dados_para_excel(df):
    df_clean = df.copy()
    palavras_chave = ['ID', 'CD_', 'EAN', 'SKU', 'ITEM', 'PEDIDO', 'LOTE', 'BLOCO', 'APTO', 'SALA', 'EMPRESA', 'DIGIT']
    for col in df_clean.columns:
        if any(palavra in col.upper() for palavra in palavras_chave):
            df_clean[col] = df_clean[col].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
    return df_clean

def converter_para_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Base Consolidada')
    return output.getvalue()

# ==========================================
# 3. INTERFACE DA APLICAÇÃO (UI)
# ==========================================
st.markdown('<p class="main-header">🛸 COMMAND CENTER | ESTOQUE</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Monitoramento de Divergências e Estoque Não Vendável</p>', unsafe_allow_html=True)

with st.spinner('Sincronizando com o BigQuery via Satélite...'):
    df_resultados, df_historico = carregar_dados()

if df_resultados is not None and not df_resultados.empty:
    
    # Organização em Abas
    tab1, tab2 = st.tabs(["📊 DASHBOARD VISÃO GLOBAL", "📥 EXTRAÇÃO DE DADOS"])
    
    with tab1:
        # ---- CÁLCULO DOS KPIs ----
        total_valor = df_resultados['VALOR_TOTAL_ESTOQUE_ATUALIZADO'].sum()
        total_pecas = df_resultados['QT_ESTOQUE'].sum()
        qtd_cds = df_resultados['CD_EMPRESA'].nunique() if 'CD_EMPRESA' in df_resultados.columns else 0
        qtd_areas = df_resultados['DS_AREA_ARMAZ'].nunique() if 'DS_AREA_ARMAZ' in df_resultados.columns else 0
        
        # Formatando valores
        valor_formatado = f"R$ {total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        pecas_formatado = f"{int(total_pecas):,}".replace(",", ".")
        
        # ---- LINHA 1: CARDS FUTURISTAS ----
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'<div class="kpi-card"><p class="kpi-title">Capital Imobilizado</p><p class="kpi-value">{valor_formatado}</p></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="kpi-card"><p class="kpi-title">Volume (Peças)</p><p class="kpi-value">{pecas_formatado}</p></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="kpi-card"><p class="kpi-title">Centros de Distribuição</p><p class="kpi-value">{qtd_cds} CDs</p></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="kpi-card"><p class="kpi-title">Áreas Críticas</p><p class="kpi-value">{qtd_areas} Setores</p></div>', unsafe_allow_html=True)
            
        st.write("---")
        
        # ---- LINHA 2: GRÁFICOS (PLOTLY DARK THEME) ----
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("⚠️ Concentração por Área de Armazém")
            if 'DS_AREA_ARMAZ' in df_resultados.columns:
                df_area = df_resultados.groupby('DS_AREA_ARMAZ')['QT_ESTOQUE'].sum().reset_index().sort_values(by='QT_ESTOQUE', ascending=False).head(7)
                fig_area = px.pie(df_area, values='QT_ESTOQUE', names='DS_AREA_ARMAZ', hole=0.6, 
                                  color_discrete_sequence=px.colors.sequential.Teal)
                fig_area.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#8892B0", showlegend=False)
                fig_area.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_area, use_container_width=True)
                
        with c2:
            st.subheader("🏢 Top 5 Filiais por Valor Retido (R$)")
            if 'CD_EMPRESA' in df_resultados.columns:
                df_cd = df_resultados.groupby('CD_EMPRESA')['VALOR_TOTAL_ESTOQUE_ATUALIZADO'].sum().reset_index().sort_values(by='VALOR_TOTAL_ESTOQUE_ATUALIZADO', ascending=True).tail(5)
                # Garantir que CD é texto para não virar gráfico contínuo
                df_cd['CD_EMPRESA'] = "Filial " + df_cd['CD_EMPRESA'].astype(str).str.replace(r'\.0$', '', regex=True)
                fig_cd = px.bar(df_cd, x='VALOR_TOTAL_ESTOQUE_ATUALIZADO', y='CD_EMPRESA', orientation='h',
                                text_auto='.2s', color='VALOR_TOTAL_ESTOQUE_ATUALIZADO', color_continuous_scale="Tealgrn")
                fig_cd.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#8892B0", coloraxis_showscale=False)
                fig_cd.update_xaxes(title="", showgrid=False)
                fig_cd.update_yaxes(title="")
                st.plotly_chart(fig_cd, use_container_width=True)

    with tab2:
        # ---- ÁREA DE DOWNLOAD (Design Original) ----
        st.markdown('### 📡 Status da Transmissão')
        ultimo_registro = df_historico.iloc[-1]
        
        st.info(f"**Última Atualização:** {ultimo_registro['DATA_HORA_ATUALIZACAO']} | **Status:** {ultimo_registro['STATUS']} | **Linhas:** {ultimo_registro['QTD_LINHAS']}")
        
        with st.expander("👀 Visualizar matriz bruta dos dados"):
            st.dataframe(df_resultados.head(10), use_container_width=True)
            
        st.write("---")
        
        df_tratado = limpar_dados_para_excel(df_resultados)
        arquivo_excel = converter_para_excel(df_tratado)
        
        st.download_button(
            label="📥 INICIAR DOWNLOAD DA BASE TRATADA (.XLSX)",
            data=arquivo_excel,
            file_name="estoque_comando_tratado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )