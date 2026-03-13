import streamlit as st
import pandas as pd
import plotly.express as px
import time
from supabase import create_client, Client
from streamlit_autorefresh import st_autorefresh

# ==========================================
# CONFIGURAÇÃO, CONEXÃO E REFRESH
# ==========================================
st.set_page_config(page_title="IA ou Real? - O Jogo", layout="wide")

# Atualiza a cada 2 segundos para o cronómetro e ranking serem fluidos
st_autorefresh(interval=2000, key="game_loop")

SENHA_ADMIN = "@@admin123"

@st.cache_resource
def init_connection() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Erro nas credenciais do Supabase nos Secrets.")
        st.stop()

supabase = init_connection()

# ==========================================
# FUNÇÕES DE LÓGICA DO BANCO DE DADOS
# ==========================================

def buscar_rodada():
    try:
        res = supabase.table('rodada_atual').select("*").eq('id', 1).execute()
        if res.data:
            return res.data[0]
        return {"status": "aguardando", "imagem_a": "", "imagem_b": "", "resposta_correta": "A", "tempo_fim": 0}
    except:
        return {"status": "aguardando"}

def buscar_voto_usuario(nome):
    res = supabase.table('votos').select("*").eq('participante', nome).execute()
    return res.data[0] if res.data else None

def carregar_ranking():
    res = supabase.table('ranking').select("*").order('pontos', desc=True).execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=['participante', 'pontos'])

# ================= : TELA DE ENTRADA : =================
if 'perfil' not in st.session_state:
    st.title("🤖 IA ou Real? - O Desafio")
    aba1, aba2 = st.tabs(["👤 Entrar como Jogador", "🔐 Acesso Admin"])
    
    with aba1:
        nome_input = st.text_input("Seu nome:")
        if st.button("Entrar no Jogo"):
            if nome_input:
                nome_limpo = nome_input.strip()
                res = supabase.table('ranking').select("*").eq('participante', nome_limpo).execute()
                if not res.data:
                    supabase.table('ranking').insert({'participante': nome_limpo, 'pontos': 0}).execute()
                st.session_state.usuario = nome_limpo
                st.session_state.perfil = "jogador"
                st.rerun()

    with aba2:
        senha = st.text_input("Senha de acesso:", type="password")
