import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime

# --- Configuração da Planilha Google ---
SHEET_ID = "1zc_0mrYa9Unw64cVXouMkdbRCswoItlqbtaG4Cw-dyA" 
URL_GOOGLE_SHEETS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

# -----------------------------------------------------------------------------
# Função de Análise e Limpeza (Cálculo da Diferença e Constância)
# -----------------------------------------------------------------------------
@st.cache_data
def analisar_e_limpar_dados(df_entrada):
    col_chave = 'CD_PRODUTO'
    col_wms = 'QT_PRODUTO_WMS'
    col_erp = 'QT_PRODUTO_ERP'
    col_data = 'DATA_REGISTRO' 

    df = df_entrada.copy()
    df.columns = df.columns.str.strip() 
        
    for col in ['CD_EMPRESA', col_chave, 'DS_PRODUTO', 'DS_AREA_ERP', 'NU_PROCESSO']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    
    for col in [col_wms, col_erp]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    if col_data in df.columns:
        df[col_data] = (
            df[col_data]
            .astype(str)
            .str.strip()
            .pipe(lambda s: pd.to_datetime(s, dayfirst=True, errors='coerce'))
            .dt.normalize() 
        )
        df.dropna(subset=[col_data], inplace=True)
    
    if col_wms in df.columns and col_erp in df.columns:
        df['DIFERENCA_ATUAL'] = df[col_wms] - df[col_erp]
    else:
        df['DIFERENCA_ATUAL'] = 0

    df_diferenca = df[df['DIFERENCA_ATUAL'] != 0].copy()

    def definir_status_sentido(diferenca):
        if diferenca > 0:
            return 'WMS_MAIOR_QUE_ERP (+)'
        elif diferenca < 0:
            return 'ERP_MAIOR_QUE_WMS (-)'
        else:
            return 'SEM_DIFERENCA'
            
    df_diferenca['STATUS_ANALISE'] = df_diferenca['DIFERENCA_ATUAL'].apply(definir_status_sentido)
    
    if col_data in df.columns:
        df_divergencia_por_dia = df[df['DIFERENCA_ATUAL'] != 0].copy()
        df_frequencia = df_divergencia_por_dia.groupby(col_chave)[col_data].nunique().reset_index(name='DIAS_COM_DIVERGENCIA')
        df_diferenca = pd.merge(df_diferenca, df_frequencia, on=col_chave, how='left')
        df_diferenca['DIAS_COM_DIVERGENCIA'] = df_diferenca['DIAS_COM_DIVERGENCIA'].fillna(0).astype(int)
        
        total_dias_analisados = df[col_data].nunique()
        
        def definir_constancia(dias):
            if total_dias_analisados <= 1:
                return 'N/A - Única Data'
            elif dias == total_dias_analisados:
                return 'CONSTANTE (Todas as Datas)'
            elif dias >= total_dias_analisados * 0.5:
                return 'RECORRENTE (>50% das Datas)'
            elif dias > 1:
                return f'ESPORÁDICO ({dias} Dias)'
            else:
                return 'APENAS NESTA DATA' 
                
        df_diferenca['STATUS_CONSTANCIA'] = df_diferenca['DIAS_COM_DIVERGENCIA'].apply(definir_constancia)
    else:
        df_diferenca['DIAS_COM_DIVERGENCIA'] = 1
        df_diferenca['STATUS_CONSTANCIA'] = 'N/A - Data Não Encontrada'

    cols_to_show = [
        'CD_EMPRESA', col_chave, 'DS_PRODUTO', col_wms, col_erp,
        'DIFERENCA_ATUAL', 'STATUS_ANALISE',
        'DIAS_COM_DIVERGENCIA', 'STATUS_CONSTANCIA', 
        'NU_PROCESSO', 'DS_AREA_ERP', col_data 
    ]
    cols_to_keep = [col for col in cols_to_show if col in df_diferenca.columns]
    
    return df.copy(), df_diferenca[cols_to_keep]

# -----------------------------------------------------------------------------
# Função para Carregar Dados do Google Sheets com "Agendamento"
# -----------------------------------------------------------------------------
@st.cache_data(ttl=86400) 
def carregar_dados_google(url, janela_atualizacao):
    return pd.read_excel(url, sheet_name=None, engine='openpyxl')

def determinar_janela_atualizacao():
    agora = datetime.datetime.now()
    if agora.hour < 10:
        return f"{agora.date() - datetime.timedelta(days=1)}_pos_15h"
    elif 10 <= agora.hour < 15:
        return f"{agora.date()}_janela_10h"
    else:
        return f"{agora.date()}_janela_15h"

# -----------------------------------------------------------------------------
# Configuração do Streamlit Dashboard
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Diferença Estoque - Google Sheets",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Análise de Divergência de Estoque (WMS vs ERP)")
st.caption(f"Conectado à nuvem: **Google Sheets (Atualizações às 10h e 15h)**")

try:
    with st.spinner("Conectando ao Google Sheets e baixando dados..."):
        chave_cache = determinar_janela_atualizacao()
        data_dict = carregar_dados_google(URL_GOOGLE_SHEETS, chave_cache)
    
    sheet_names = list(data_dict.keys())
    aba_selecionada_display = ", ".join(sheet_names)
    
    with st.sidebar:
        st.header("⚙️ Configuração da Planilha")
        abas_selecionadas = st.multiselect(
            "Selecione as Abas (Sheets) para Análise:", 
            sheet_names,
            default=sheet_names 
        )
        st.markdown("---")
        st.caption(f"Última verificação de janela de cache: {chave_cache}")
        
    if not abas_selecionadas:
        st.warning("Por favor, selecione pelo menos uma aba (sheet) na barra lateral para iniciar a análise.")
        st.stop()
        
    list_dfs = [data_dict[sheet_name] for sheet_name in abas_selecionadas]
    df_bruto = pd.concat(list_dfs, ignore_index=True)
    aba_selecionada_display = ", ".join(abas_selecionadas)
    
    df_completo, df_diferenca = analisar_e_limpar_dados(df_bruto)
    
    total_registros = len(df_completo)
    total_diferencas = len(df_diferenca)
    col_data_final = 'DATA_REGISTRO' 
    total_dias_analisados = df_completo[col_data_final].nunique() if col_data_final in df_completo.columns else 1

    with st.sidebar:
        if col_data_final in df_completo.columns:
            datas_unicas_lidas = df_completo[col_data_final].dropna().unique()
            datas_formatadas = [pd.to_datetime(d).strftime('%d/%m/%Y') for d in datas_unicas_lidas]
            
            st.subheader("🔎 Debug de Datas (Constância)")
            st.info(
                f"Abas Lidas: **{aba_selecionada_display}**\n\n"
                f"Dias Únicos Encontrados: **{total_dias_analisados}**\n\n"
                f"Datas Lidas: **{', '.join(datas_formatadas)}**"
            )
            st.markdown("---") 

    with st.sidebar:
        st.header("Filtros Globais")
        empresas_unicas = ['Todas'] + sorted(list(df_diferenca['CD_EMPRESA'].unique()))
        empresa_selecionada = st.selectbox("Filtrar por Empresa", empresas_unicas)
        
        sentidos_divergencia = ['Ambos'] + list(df_diferenca['STATUS_ANALISE'].unique())
        sentido_selecionado = st.selectbox("Filtrar Sentido da Divergência", sentidos_divergencia)
        
        df_filtrado_base = df_diferenca.copy()
        
        if 'STATUS_CONSTANCIA' in df_diferenca.columns and total_dias_analisados > 1:
            st.subheader("Filtro de Constância")
            status_constancia_unicos = ['Todos'] + list(df_diferenca['STATUS_CONSTANCIA'].unique())
            if 'N/A - Única Data' in status_constancia_unicos:
                status_constancia_unicos.remove('N/A - Única Data')
                
            constancia_selecionada = st.multiselect("Filtrar por Status de Constância", status_constancia_unicos, default='Todos', key='multiselect_constancia')
            
            if 'Todos' not in constancia_selecionada:
                df_filtrado_base = df_filtrado_base[df_filtrado_base['STATUS_CONSTANCIA'].isin(constancia_selecionada)]
                
        st.markdown("---")
        
        df_filtrado = df_filtrado_base.copy()
        if empresa_selecionada != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['CD_EMPRESA'] == empresa_selecionada]
        if sentido_selecionado != 'Ambos':
            df_filtrado = df_filtrado[df_filtrado['STATUS_ANALISE'] == sentido_selecionado]
            
    tab_dashboard, tab_detalhe_completo = st.tabs(["📊 Dashboard de Divergências", "📑 Detalhamento Consolidado"])

    with tab_dashboard:
        st.header("1. Visão Geral da Análise")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de Registros Analisados", f"{total_registros:,.0f}".replace(",", "."))
        col2.metric("Total de Itens com Divergência", f"{total_diferencas:,.0f}".replace(",", "."))
        col3.metric("Dias Únicos Analisados", f"{total_dias_analisados:,.0f}".replace(",", "."))
        percentual_diferenca = (total_diferencas / total_registros) * 100 if total_registros > 0 else 0
        col4.metric("Percentual de Divergência", f"{percentual_diferenca:.2f}%")
        st.markdown("---")

        st.header("2. Divergência por Empresa/Área")
        df_empresa_sum = df_diferenca.groupby('CD_EMPRESA')['DIFERENCA_ATUAL'].agg(['count', 'sum']).reset_index()
        df_empresa_sum.rename(columns={'count': 'Total de Itens com Diferença', 'sum': 'Diferença Total (Soma)'}, inplace=True)
        
        col_grafico, col_tabela_top = st.columns([2, 1])
        with col_grafico:
            st.subheader("Top 10 Empresas por Número de Divergências")
            df_top_10 = df_empresa_sum.nlargest(10, 'Total de Itens com Diferença')
            fig_bar = px.bar(df_top_10, x='CD_EMPRESA', y='Total de Itens com Diferença', title='Itens Divergentes (Top 10)', color='Total de Itens com Diferença', template='seaborn')
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_tabela_top:
            st.subheader("Distribuição por Área ERP (Filtros Aplicados)")
            df_area_sum = df_filtrado.groupby('DS_AREA_ERP')['DIFERENCA_ATUAL'].agg('count').reset_index()
            df_area_sum.rename(columns={'DIFERENCA_ATUAL': 'Total de Divergências'}, inplace=True)
            fig_pie = px.pie(df_area_sum, values='Total de Divergências', names='DS_AREA_ERP', title='Distribuição por Área ERP')
            st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("---")
        
        st.header("3. Análise de Constância dos Itens Divergentes")
        if 'STATUS_CONSTANCIA' in df_diferenca.columns and total_dias_analisados > 1:
            col_const_graf, col_const_tabela = st.columns([1, 1])
            with col_const_graf:
                df_constancia_count = df_diferenca.drop_duplicates(subset=['CD_PRODUTO']).groupby('STATUS_CONSTANCIA')['CD_PRODUTO'].count().reset_index(name='Total de Produtos')
                fig_constancia = px.pie(df_constancia_count, values='Total de Produtos', names='STATUS_CONSTANCIA', title='Distribuição dos Itens Divergentes por Constância')
                st.plotly_chart(fig_constancia, use_container_width=True)

            with col_const_tabela:
                st.subheader("Top 10 Itens Mais Recorrentes (Todas as Empresas)")
                df_top_recorrentes = df_diferenca.sort_values(by=['DIAS_COM_DIVERGENCIA', 'DIFERENCA_ATUAL'], ascending=[False, False]).drop_duplicates(subset=['CD_PRODUTO']).nlargest(10, 'DIAS_COM_DIVERGENCIA')
                st.dataframe(df_top_recorrentes[['CD_PRODUTO', 'DS_PRODUTO', 'DIAS_COM_DIVERGENCIA', 'STATUS_CONSTANCIA', 'DIFERENCA_ATUAL', 'CD_EMPRESA']], use_container_width=True)
        else:
            st.info(f"Análise de Constância não aplicável. Foi encontrada apenas **{total_dias_analisados}** data única.")
        st.markdown("---")
        
        st.header(f"4. Detalhamento dos Itens (Exibidos: {len(df_filtrado):,.0f})")
        max_diff = df_filtrado['DIFERENCA_ATUAL'].abs().max() if not df_filtrado.empty else 0
        min_diff_abs = st.slider("Filtrar Diferença Mínima (Valor Absoluto)", min_value=0, max_value=int(max_diff) if max_diff > 0 else 1, value=0, step=1, key='slider_min_diff')

        df_final = df_filtrado[df_filtrado['DIFERENCA_ATUAL'].abs() >= min_diff_abs]
        st.info(f"Exibindo **{len(df_final):,.0f}** de **{len(df_filtrado):,.0f}** itens filtrados na tabela abaixo, com Diferença Absoluta >= **{min_diff_abs}**.")
        
        st.dataframe(
            df_final, 
            use_container_width=True,
            column_config={
                'DIFERENCA_ATUAL': st.column_config.NumberColumn("Diferença (WMS - ERP)", format="%d"),
                'QT_PRODUTO_WMS': st.column_config.NumberColumn("QT WMS", format="%d"),
                'QT_PRODUTO_ERP': st.column_config.NumberColumn("QT ERP", format="%d"),
                'DIAS_COM_DIVERGENCIA': st.column_config.NumberColumn("Dias Divergindo", format="%d"),
            },
            height=300
        )

    with tab_detalhe_completo:
        st.header("📑 Detalhamento do Arquivo Consolidado (Todos os Registros)")
        st.info(f"Esta aba exibe os **{total_registros:,.0f}** registros originais da nuvem.")
        
        st.dataframe(
            df_completo, 
            use_container_width=True,
            column_config={
                'DIFERENCA_ATUAL': st.column_config.NumberColumn("Diferença (WMS - ERP)", format="%d"),
                'QT_PRODUTO_WMS': st.column_config.NumberColumn("QT WMS", format="%d"),
                'QT_PRODUTO_ERP': st.column_config.NumberColumn("QT ERP", format="%d"),
            },
            height=600
        )

except ValueError as e:
    st.error(f"Erro ao processar a planilha. Verifique se o ID está correto ou se a planilha está publicada na Web.")
    st.info(f"Detalhes: {e}")
    st.stop()
except ImportError:
    st.error("⚠️ ATENÇÃO: A biblioteca 'openpyxl' não está instalada no servidor do Streamlit.")
    st.info("Para corrigir isso, garanta que o arquivo 'requirements.txt' no GitHub contenha a linha: openpyxl==3.1.2")
    st.stop()
except Exception as e:
    st.error(f"Ocorreu um erro geral ao acessar o Google Sheets. Detalhes: {e}")