import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime

# --- IDs das Planilhas ---
SHEET_ID_DIVERGENCIA = "1zc_0mrYa9Unw64cVXouMkdbRCswoItlqbtaG4Cw-dyA"
SHEET_ID_RESUMO = "1GjfNcXngLsT0FKIEBrp4VPRZDmfN_DmuwMzpVa-5D6c"

URL_DIVERGENCIA = f"https://docs.google.com/spreadsheets/d/{SHEET_ID_DIVERGENCIA}/export?format=xlsx"
URL_RESUMO = f"https://docs.google.com/spreadsheets/d/{SHEET_ID_RESUMO}/export?format=xlsx"

@st.cache_data(ttl=600) # Atualiza a cada 10 min
def carregar_resumo(url):
    try:
        df = pd.read_excel(url, sheet_name='RESUMO', engine='openpyxl')
        df.columns = df.columns.str.strip()
        
        # Mapeamento robusto para a coluna de diferença de peças
        # Procura por nomes parecidos caso haja erro de digitação
        cols_map = {
            'DATA': 'DATA',
            'CD': 'CD',
            'TOTAL DIF. PÇ': 'DIF_PECAS',
            'TOTA DIF. PÇ': 'DIF_PECAS',
            'TOTAL DIF PÇ': 'DIF_PECAS'
        }
        df.rename(columns=cols_map, inplace=True)
        
        df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
        df['DIF_PECAS'] = pd.to_numeric(df['DIF_PECAS'], errors='coerce').fillna(0)
        df['CD'] = df['CD'].astype(str).str.replace(r'\.0$', '', regex=True)
        
        return df.dropna(subset=['DATA']).sort_values('DATA')
    except Exception as e:
        st.error(f"Erro na aba RESUMO: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def carregar_divergencias(url):
    try:
        data_dict = pd.read_excel(url, sheet_name=None, engine='openpyxl')
        df = pd.concat(data_dict.values(), ignore_index=True)
        df.columns = df.columns.str.strip()
        
        # Limpeza básica
        for col in ['CD_EMPRESA', 'DS_AREA_ERP']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True)
        
        df_div = df[(df['QT_PRODUTO_WMS'] - df['QT_PRODUTO_ERP']) != 0].copy()
        return df, df_div
    except Exception as e:
        st.error(f"Erro nos dados de divergência: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- Layout ---
st.set_page_config(page_title="Dashboard Peças", layout="wide")
st.markdown("### 📊 Monitoramento de Diferenças (WMS vs ERP)")

df_completo, df_diferenca = carregar_divergencias(URL_DIVERGENCIA)
df_resumo = carregar_resumo(URL_RESUMO)

if not df_diferenca.empty:
    # KPIs
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Total Analisado", f"{len(df_completo)}")
    with c2: st.metric("Itens Divergentes", f"{len(df_diferenca)}", delta_color="inverse")
    with c3: 
        soma_pecas = df_resumo['DIF_PECAS'].sum() if not df_resumo.empty else 0
        st.metric("Total Peças (Dif)", f"{int(soma_pecas)}")

    # Gráficos Superiores
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        top_10 = df_diferenca['CD_EMPRESA'].value_counts().nlargest(10).reset_index()
        fig_bar = px.bar(top_10, x='count', y='CD_EMPRESA', orientation='h', title="Top 10 CDs Críticos", color='count', color_continuous_scale='Reds')
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col2:
        area_dist = df_diferenca['DS_AREA_ERP'].value_counts().reset_index()
        fig_pie = px.pie(area_dist, values='count', names='DS_AREA_ERP', title="Áreas com Divergência", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Gráfico de Linha Inferior (TOTAL DIF. PÇ)
    st.markdown("---")
    st.markdown("#### 📈 Evolução do Total de Peças Divergentes por CD")
    if not df_resumo.empty:
        fig_line = px.line(df_resumo, x='DATA', y='DIF_PECAS', color='CD', markers=True)
        fig_line.update_layout(xaxis_title="Data", yaxis_title="Soma de Diferença (Peças)")
        st.plotly_chart(fig_line, use_container_width=True)
else:
    st.warning("Verifique se a planilha está pública (Qualquer pessoa com o link).")
    

