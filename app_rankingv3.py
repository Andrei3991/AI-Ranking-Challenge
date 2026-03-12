import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from streamlit_autorefresh import st_autorefresh

# ==========================================
# CONFIGURAÇÃO INICIAL E SEGURANÇA
# ==========================================
st.set_page_config(page_title="Ranking de Desafio de IA", page_icon="💡", layout="wide")

#Atualiza a página a cada 10 segundos para refletir as mudanças em tempo real
st_autorefresh(interval=10000, key="datarefresh")

# Senha para habilitar os controles de edição na barra lateral
SENHA_ADMIN = "@@admin123" 

if 'admin_logado' not in st.session_state:
    st.session_state.admin_logado = False

# ==========================================
# CONEXÃO COM O SUPABASE
# ==========================================
@st.cache_resource
def init_connection() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"].strip().rstrip("/")
        key = st.secrets["SUPABASE_KEY"]. strip()
        return create_client(url, key)
    except Exception as e:
        st.error("Erro ao ler segredos (Secrets). Verifique se configurou SUPABASE_URL e SUPABASE_KEY.")
        st.stop()

supabase = init_connection()

# Função para carregar os dados com tratamento de erro detalhado
def carregar_dados():
    try:
        # Tenta buscar os dados da tabela 'ranking'
        resposta = supabase.table('ranking').select("*").execute()
        
        # Converte para DataFrame
        df_temp = pd.DataFrame(resposta.data)
        
        if df_temp.empty:
            return pd.DataFrame(columns=['id', 'participante', 'pontos'])
            
        # Garante que a coluna 'pontos' seja tratada como número
        df_temp['pontos'] = pd.to_numeric(df_temp['pontos'], errors='coerce').fillna(0).astype(int)
        return df_temp
        
    except Exception as e:
        # Exibe o erro real para facilitar o diagnóstico (ex: tabela não encontrada ou RLS ativo)
        st.error(f"⚠️ Erro de API no Supabase: {e}")
        return pd.DataFrame(columns=['id', 'participante', 'pontos'])

# Carregamento inicial dos dados
df = carregar_dados()

# ==========================================
# TÍTULO PRINCIPAL
# ==========================================
st.title("🏆 Ranking Dinâmico de Desafio de IA")
st.write(f"Atualizando automaticamente a cada 10 segundos para refletir as mudanças em tempo real!")

# ==========================================
# BARRA LATERAL (AUTENTICAÇÃO E CONTROLES)
# ==========================================
with st.sidebar:
    st.header("🔐 Cantinho do Admin")
    
    if not st.session_state.admin_logado:
        senha = st.text_input("Senha Admin:", type="password")
        if st.button("Acessar"):
            if senha == SENHA_ADMIN:
                st.session_state.admin_logado = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
    else:
        st.success("Modo Edição Ativo")
        if st.button("Encerrar Sessão"):
            st.session_state.admin_logado = False
            st.rerun()
            
        st.divider()
        
        # Gestão de Participantes
        with st.expander("👥 Participantes"):
            nome = st.text_input("Nome:")
            c1, c2 = st.columns(2)
            if c1.button("Adicionar"):
                if nome:
                    supabase.table('ranking').insert({'participante': nome, 'pontos': 0}).execute()
                    st.rerun()
            if c2.button("Remover"):
                supabase.table('ranking').delete().eq('participante', nome).execute()
                st.rerun()
        
    st.divider()
        
        # Gestão de Participantes
    with st.expander("👥 Participantes"):
            nome = st.text_input("Nome:")
            c1, c2 = st.columns(2)
            if c1.button("Adicionar"):
                if nome:
                    supabase.table('ranking').insert({'participante': nome, 'pontos': 0}).execute()
                    st.rerun()
            if c2.button("Remover"):
                supabase.table('ranking').delete().eq('participante', nome).execute()
                st.rerun()

    # Registro de Pontos
            if not df.empty:
             st.divider()
             st.subheader("💡 Pontuar")
            selecionado = st.selectbox("Quem?", df['participante'].tolist())
            pontos = st.number_input("Qtd pontos", min_value=1, value=1)
            
            if st.button("Confirmar Pontuação"):
                atual = int(df.loc[df['participante'] == selecionado, 'pontos'].values[0])
                nova_qtd = atual + pontos
                supabase.table('ranking').update({'pontos': nova_qtd}).eq('participante', selecionado).execute()
                st.rerun()

# ==========================================
# ÁREA PRINCIPAL (VISUALIZAÇÃO DO RANKING)
# ==========================================
if df.empty:
    st.warning("Aguardando o início da competição...")
else:
    # Ordenar para o pódio
    df_rank = df.sort_values(by='pontos', ascending=False)

    # Gráfico Plotly
    fig = px.bar(
        df_rank, 
        x='participante', 
        y='pontos',
        text='pontos',
        color='pontos',
        color_continuous_scale='Viridis'
    )

    fig.update_traces(textposition='outside', textfont_size=20, marker_line_color='rgb(8,48,107)', marker_line_width=1.5)
    fig.update_layout(
        yaxis_visible=False, 
        xaxis_title="", 
        height=600,
        margin=dict(t=50)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Mostrar Tabela Simples abaixo (opcional)
    with st.expander("Ver lista detalhada"):
        st.table(df_rank[['participante', 'pontos']].reset_index(drop=True))
