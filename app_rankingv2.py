import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração inicial da página
st.set_page_config(page_title="Ranking desafio de I.A.", page_icon="💡", layout="wide")

# ==========================================
# CONFIGURAÇÃO DE SEGURANÇA
# ==========================================
# Defina a senha do administrador aqui
SENHA_ADMIN = "@@admin123"

# Inicializa as variáveis na memória (Session State)
if 'participantes' not in st.session_state:
    st.session_state.participantes = {}
if 'admin_logado' not in st.session_state:
    st.session_state.admin_logado = False

# Título principal (Visível para todos)
st.title("🏆 Ranking Desafio de I.A")
st.markdown("Acompanhe em tempo real quem está liderando e sabendo diferenciar melhor a imagem real de uma imagem gerada por IA!")

# ==========================================
# BARRA LATERAL (AUTENTICAÇÃO E CONTROLES)
# ==========================================
with st.sidebar:
    st.header("🔒 Área do Administrador")
    
    # Lógica de Login
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
        
        # Adicionar Participante
        with st.expander("👤 Adicionar/Remover Participante"):
            novo_nome = st.text_input("Nome do Participante:")
            col1, col2 = st.columns(2)
            if col1.button("Adicionar"):
                if novo_nome and novo_nome not in st.session_state.participantes:
                    st.session_state.participantes[novo_nome] = 0
                    st.success(f"{novo_nome} adicionado!")
                    st.rerun()
                elif novo_nome in st.session_state.participantes:
                    st.warning("Participante já existe.")
                    
            if col2.button("Remover"):
                if novo_nome in st.session_state.participantes:
                    del st.session_state.participantes[novo_nome]
                    st.success(f"{novo_nome} removido!")
                    st.rerun()

        # Adicionar/Remover Pontuação
        with st.expander("💡 Registrar Pontuação"):
            lista_nomes = list(st.session_state.participantes.keys())
            if lista_nomes:
                escolha = st.selectbox("Selecione o Participante:", lista_nomes)
                qtd_pontos = st.number_input("Quantidade", min_value=1, value=1, step=1)
                
                col3, col4 = st.columns(2)
                if col3.button("➕ Adicionar"):
                    st.session_state.participantes[escolha] += qtd_pontos
                    st.rerun()
                    
                if col4.button("➖ Remover"):
                    if st.session_state.participantes[escolha] >= qtd_pontos:
                        st.session_state.participantes[escolha] -= qtd_pontos
                    else:
                        st.session_state.participantes[escolha] = 0
                    st.rerun()
            else:
                st.info("Adicione um participante primeiro.")

# ==========================================
# ÁREA PRINCIPAL (VISUALIZAÇÃO DO RANKING)
# ==========================================
if not st.session_state.participantes:
    st.info("O ranking ainda está vazio. Aguardando o administrador adicionar os participantes!")
else:
    # Prepara os dados
    df = pd.DataFrame(
        list(st.session_state.participantes.items()), 
        columns=['Participante', 'Pontos']
    )
    
    # Ordena os dados (maior para o menor)
    df = df.sort_values(by='Pontos', ascending=False)

    # Gráfico de barras VERTICAIS
    fig = px.bar(
        df, 
        x='Participante', 
        y='Pontos',       
        text='Pontos',
        color='Pontos',
        color_continuous_scale=px.colors.sequential.Agsunset,
    )

    # Ajustes visuais do gráfico
    fig.update_traces(textposition='outside', textfont_size=16)
    fig.update_layout(
        xaxis_title="", 
        yaxis_title="Pontos",
        showlegend=False,
        height=500,
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    fig.update_yaxes(showticklabels=False, showgrid=False)

    # Exibe o gráfico

    st.plotly_chart(fig, use_container_width=True)
