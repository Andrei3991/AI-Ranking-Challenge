import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# ==========================================
# CONFIGURAÇÃO INICIAL E SEGURANÇA
# ==========================================
st.set_page_config(page_title="Ranking desafio de IA", page_icon="💡", layout="wide")

SENHA_ADMIN = "@@admin123" # Altere para a senha desejada

if 'admin_logado' not in st.session_state:
    st.session_state.admin_logado = False

# ==========================================
# CONEXÃO COM O SUPABASE
# ==========================================
@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# Função para carregar os dados do banco
def carregar_dados():
    resposta = supabase.table('ranking').select("*").execute()
    df_temp = pd.DataFrame(resposta.data)
    if df_temp.empty:
        return pd.DataFrame(columns=['id', 'participante', 'pontos'])
    return df_temp

df = carregar_dados()

# ==========================================
# TÍTULO PRINCIPAL
# ==========================================
st.title("🏆 Ranking Dinâmico")
st.markdown("Acompanhe em tempo real quem está liderando o desafio de IA!")

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
                    # Insere no Supabase
                    supabase.table('ranking').insert({'participante': novo_nome, 'ideias': 0}).execute()
                    st.success(f"{novo_nome} adicionado!")
                    st.rerun()
                elif novo_nome in df['participante'].values:
                    st.warning("Participante já existe.")
                    
            if col2.button("Remover"):
                if novo_nome in df['participante'].values:
                    # Deleta do Supabase
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
                    # Descobre quantos pontos a pessoa tem hoje e soma
                    pontos_atuais = int(df.loc[df['participante'] == escolha, 'pontos'].values[0])
                    nova_qtd = pontos_atuais + qtd_pontos
                    
                    # Atualiza no Supabase
                    supabase.table('ranking').update({'pontos': nova_qtd}).eq('participante', escolha).execute()
                    st.rerun()
                    
                if col4.button("➖ Remover"):
                    pontos_atuais = int(df.loc[df['participante'] == escolha, 'pontos'].values[0])
                    nova_qtd = pontos_atuais - qtd_pontos
                    
                    # Garante que não fique negativo
                    if nova_qtd < 0:
                        nova_qtd = 0
                        
                    # Atualiza no Supabase
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
    # Ordena os dados do maior para o menor
    df_grafico = df.sort_values(by='pontos', ascending=False)

    # Gráfico
    fig = px.bar(
        df_grafico, 
        x='participante', 
        y='pontos',       
        text='pontos',
        color='pontos',
        color_continuous_scale=px.colors.sequential.Agsunset,
    )

    fig.update_traces(textposition='outside', textfont_size=16)
    fig.update_layout(
        xaxis_title="", 
        yaxis_title="Número de Pontos",
        showlegend=False,
        height=500,
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    fig.update_yaxes(showticklabels=False, showgrid=False)

    st.plotly_chart(fig, use_container_width=True)
