import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# ==========================================
# CONFIGURAÇÃO INICIAL E SEGURANÇA
# ==========================================
st.set_page_config(page_title="Ranking de Desafio de IA", page_icon="💡", layout="wide")

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
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
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
st.markdown("Acompanhe em tempo real quem está liderando a maratona de desafios de IA!")

# ==========================================
# BARRA LATERAL (AUTENTICAÇÃO E CONTROLES)
# ==========================================
with st.sidebar:
    st.header("🔒 Área do Administrador")
    
    if not st.session_state.admin_logado:
        senha_digitada = st.text_input("Digite a senha para gerenciar:", type="password")
        if st.button("Entrar"):
            if senha_digitada == SENHA_ADMIN:
                st.session_state.admin_logado = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
    else:
        st.success("✅ Logado como Administrador")
        if st.button("Sair"):
            st.session_state.admin_logado = False
            st.rerun()
            
        st.divider()
        st.header("⚙️ Gerenciar Ranking")
        
        # --- ADICIONAR / REMOVER PARTICIPANTE ---
        with st.expander("👤 Adicionar/Remover Participante"):
            novo_nome = st.text_input("Nome do Participante:")
            col1, col2 = st.columns(2)
            
            if col1.button("Adicionar"):
                if novo_nome and novo_nome not in df['participante'].values:
                    # Comando de inserção no banco
                    supabase.table('ranking').insert({'participante': novo_nome, 'pontos': 0}).execute()
                    st.success(f"{novo_nome} adicionado!")
                    st.rerun()
                elif novo_nome in df['participante'].values:
                    st.warning("Participante já existe.")
                    
            if col2.button("Remover"):
                if novo_nome in df['participante'].values:
                    # Comando de remoção no banco
                    supabase.table('ranking').delete().eq('participante', novo_nome).execute()
                    st.success(f"{novo_nome} removido!")
                    st.rerun()

        # --- REGISTRAR PONTOS ---
        with st.expander("💡 Registrar Pontos"):
            lista_nomes = df['participante'].tolist() if not df.empty else []
            
            if lista_nomes:
                escolha = st.selectbox("Selecione o Participante:", lista_nomes)
                qtd_pontos = st.number_input("Quantidade", min_value=1, value=1, step=1)
                
                col3, col4 = st.columns(2)
                
                if col3.button("➕ Adicionar"):
                    # Cálculo baseado nos dados atuais do DataFrame
                    pontos_atuais = int(df.loc[df['participante'] == escolha, 'pontos'].values[0])
                    nova_qtd = pontos_atuais + qtd_pontos
                    
                    # Atualiza o registro específico
                    supabase.table('ranking').update({'pontos': nova_qtd}).eq('participante', escolha).execute()
                    st.rerun()
                    
                if col4.button("➖ Remover"):
                    pontos_atuais = int(df.loc[df['participante'] == escolha, 'pontos'].values[0])
                    nova_qtd = max(0, pontos_atuais - qtd_pontos) # Evita valores negativos
                    
                    # Atualiza o registro específico
                    supabase.table('ranking').update({'pontos': nova_qtd}).eq('participante', escolha).execute()
                    st.rerun()
            else:
                st.info("Adicione um participante primeiro.")

# ==========================================
# ÁREA PRINCIPAL (VISUALIZAÇÃO DO RANKING)
# ==========================================
if df.empty:
    st.info("O ranking ainda está vazio. Aguardando o administrador adicionar os participantes!")
else:
    # Ordenação decrescente para o gráfico
    df_grafico = df.sort_values(by='pontos', ascending=False)

    # Gráfico de barras verticais
    fig = px.bar(
        df_grafico, 
        x='participante', 
        y='pontos',       
        text='pontos',
        color='pontos',
        color_continuous_scale=px.colors.sequential.Agsunset,
    )

    # Estilização do gráfico
    fig.update_traces(textposition='outside', textfont_size=16)
    fig.update_layout(
        xaxis_title="", 
        yaxis_title="Número de Pontos",
        showlegend=False,
        height=500,
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    # Esconde o eixo Y para focar nos números sobre as barras
    fig.update_yaxes(showticklabels=False, showgrid=False)

    # Renderização final
    st.plotly_chart(fig, use_container_width=True)
