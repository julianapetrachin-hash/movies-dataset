import streamlit as st
import pandas as pd
import io

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E DESIGN (CSS)
# ==========================================
st.set_page_config(page_title="Portal de Estoque", page_icon="📦", layout="centered")

st.markdown("""
    <style>
        .main-header { font-size: 2.5rem; color: #1E3A8A; font-weight: 700; text-align: center; margin-bottom: 0; }
        .sub-header { font-size: 1.1rem; color: #6B7280; text-align: center; margin-bottom: 30px; }
        .status-box { background-color: #F3F4F6; padding: 20px; border-radius: 10px; border-left: 6px solid #10B981; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .stDownloadButton>button { background-color: #10B981; color: white; border: none; padding: 15px 32px; text-align: center; font-size: 18px; border-radius: 8px; width: 100%; font-weight: bold; transition: 0.3s; }
        .stDownloadButton>button:hover { background-color: #059669; color: white; transform: scale(1.02); }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNÇÕES DE CARREGAMENTO E TRATAMENTO
# ==========================================
# Substitua o ID_AQUI pelo ID da sua planilha copiado no passo 1
SHEET_ID = "https://docs.google.com/spreadsheets/d/11-IwzWjgFVKynzDTkqpr4_Fbs4GclKhS7W0KTKms0q4/edit?gid=1243680312#gid=1243680312" 

@st.cache_data(ttl=600) # Faz cache dos dados por 10 minutos para não sobrecarregar
def carregar_dados():
    url_resultados = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=BigQuery+Results"
    url_historico = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Historico"
    
    try:
        df_res = pd.read_csv(url_resultados)
        df_hist = pd.read_csv(url_historico)
        return df_res, df_hist
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None, None

def limpar_dados_para_excel(df):
    """Garante que IDs, códigos e lotes não fiquem com ponto decimal (.0) no Excel"""
    df_clean = df.copy()
    
    # Lista de palavras-chave que indicam colunas que NÃO devem ter casas decimais
    palavras_chave = ['ID', 'CD_', 'EAN', 'SKU', 'ITEM', 'PEDIDO', 'LOTE', 'BLOCO', 'APTO', 'SALA', 'EMPRESA', 'DIGIT']
    
    for col in df_clean.columns:
        if any(palavra in col.upper() for palavra in palavras_chave):
            # Converte para string e remove o ".0" do final (gerado pelo pandas em colunas com vazios)
            df_clean[col] = df_clean[col].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
            
    return df_clean

def converter_para_excel(df):
    """Gera o arquivo XLSX em memória"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Estoque Não Vendável')
    return output.getvalue()

# ==========================================
# 3. INTERFACE DO USUÁRIO (UI)
# ==========================================
st.markdown('<p class="main-header">📦 Portal de Extração de Estoque</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Baixe a base atualizada do BigQuery de forma rápida e tratada.</p>', unsafe_allow_html=True)

with st.spinner('Conectando ao banco de dados...'):
    df_resultados, df_historico = carregar_dados()

if df_resultados is not None and df_historico is not None:
    # Pegar o último registro do histórico
    ultimo_registro = df_historico.iloc[-1]
    data_hora = ultimo_registro['DATA_HORA_ATUALIZACAO']
    status = ultimo_registro['STATUS']
    qtd_linhas = ultimo_registro['QTD_LINHAS']
    
    # Exibir caixa de status
    cor_status = "🟢" if status == "SUCESSO" else "🔴"
    st.markdown(f"""
        <div class="status-box">
            <h4>{cor_status} Status da Última Atualização</h4>
            <p><b>Data/Hora:</b> {data_hora}<br>
            <b>Status do Sistema:</b> {status}<br>
            <b>Volume Processado:</b> {qtd_linhas} produtos identificados</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Preview dos dados
    with st.expander("👀 Visualizar uma amostra dos dados"):
        st.dataframe(df_resultados.head(5), use_container_width=True)
    
    st.write("---")
    
    # Processar e gerar botão de download
    df_tratado = limpar_dados_para_excel(df_resultados)
    arquivo_excel = converter_para_excel(df_tratado)
    
    st.download_button(
        label="📥 BAIXAR BASE COMPLETA (.XLSX)",
        data=arquivo_excel,
        file_name="estoque_nao_vendavel_tratado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.caption("O arquivo gerado já possui os códigos e IDs formatados corretamente como texto, prontos para uso em tabelas dinâmicas ou PROCV.")