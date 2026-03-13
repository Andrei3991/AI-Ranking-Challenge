import streamlit as st
import pandas as pd
from supabase import create_client, Client
from streamlit_autorefresh import st_autorefresh

# ==========================================
# CONFIGURAÇÃO E CONEXÃO
# ==========================================
st.set_page_config(page_title="IA ou Real? - O Jogo", layout="wide")
st_autorefresh(interval=5000, key="game_loop") # Atualiza a cada 5s

SENHA_ADMIN = "@@admin123"

@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# ==========================================
# FUNÇÕES DE LÓGICA DO JOGO
# ==========================================

def registrar_participante(nome):
    # Verifica se já existe, se não, cria no ranking
    res = supabase.table('ranking').select("*").eq('participante', nome).execute()
    if not res.data:
        supabase.table('ranking').insert({'participante': nome, 'pontos': 0}).execute()
    st.session_state.usuario = nome

def buscar_rodada():
    res = supabase.table('rodada_atual').select("*").eq('id', 1).execute()
    return res.data[0] if res.data else None

def ja_votou(nome):
    res = supabase.table('votos').select("*").eq('participante', nome).execute()
    return True if res.data else False

# ==========================================
# INTERFACE DE LOGIN
# ==========================================
if 'usuario' not in st.session_state:
    st.title("🤖 IA ou Real? - O Desafio")
    nome_input = st.text_input("Digite seu nome para entrar no jogo:")
    if st.button("Começar!"):
        if nome_input:
            registrar_participante(nome_input.strip())
            st.rerun()
    st.stop()

# ================= : ÁREA DO JOGO : =================

# --- SIDEBAR (ADMIN) ---
with st.sidebar:
    if not st.session_state.get('admin_sessao', False):
        senha = st.text_input("Painel Admin", type="password")
        if st.button("Login Admin"):
            if senha == SENHA_ADMIN:
                st.session_state.admin_sessao = True
                st.rerun()
    else:
        st.subheader("⚙️ Controle da Rodada")
        img_a = st.text_input("URL Imagem A")
        img_b = st.text_input("URL Imagem B")
        correta = st.radio("Qual é a REAL?", ["A", "B"])
        
        if st.button("🚀 INICIAR NOVA RODADA"):
            # Limpa votos anteriores e atualiza a rodada
            supabase.table('votos').delete().neq('participante', '').execute()
            supabase.table('rodada_atual').update({
                'imagem_a': img_a,
                'imagem_b': img_b,
                'resposta_correta': correta,
                'status': 'votando'
            }).eq('id', 1).execute()
            st.success("Rodada iniciada!")
            st.rerun()
            
        if st.button("🛑 ENCERRAR E MOSTRAR RESULTADO"):
            supabase.table('rodada_atual').update({'status': 'resultado'}).eq('id', 1).execute()
            st.rerun()

# --- TELA PRINCIPAL DO JOGADOR ---
rodada = buscar_rodada()

st.title(f"Jogador: {st.session_state.usuario}")

if rodada['status'] == 'aguardando':
    st.info("Aguardando o organizador iniciar a próxima rodada...")

elif rodada['status'] == 'votando':
    if ja_votou(st.session_state.usuario):
        st.warning("Voto registrado! Aguarde o resultado...")
    else:
        st.subheader("Qual dessas imagens é REAL (não feita por IA)?")
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(rodada['imagem_a'], caption="Opção A")
            if st.button("Votar na A", use_container_width=True):
                # Lógica de Pontuação
                acertou = (rodada['resposta_correta'] == 'A')
                if acertou:
                    # Busca pontos atuais e soma
                    res = supabase.table('ranking').select("pontos").eq('participante', st.session_state.usuario).execute()
                    novos_pontos = res.data[0]['pontos'] + 1
                    supabase.table('ranking').update({'pontos': novos_pontos}).eq('participante', st.session_state.usuario).execute()
                
                # Registra que votou
                supabase.table('votos').insert({'participante': st.session_state.usuario, 'voto': 'A'}).execute()
                st.rerun()

        with col2:
            st.image(rodada['imagem_b'], caption="Opção B")
            if st.button("Votar na B", use_container_width=True):
                acertou = (rodada['resposta_correta'] == 'B')
                if acertou:
                    res = supabase.table('ranking').select("pontos").eq('participante', st.session_state.usuario).execute()
                    novos_pontos = res.data[0]['pontos'] + 1
                    supabase.table('ranking').update({'pontos': novos_pontos}).eq('participante', st.session_state.usuario).execute()
                
                supabase.table('votos').insert({'participante': st.session_state.usuario, 'voto': 'B'}).execute()
                st.rerun()

elif rodada['status'] == 'resultado':
    st.success(f"A resposta correta era a Opção {rodada['resposta_correta']}!")
    
    # Exibe o ranking atualizado
    st.divider()
    st.subheader("🏆 Ranking Atual")
    res_rank = supabase.table('ranking').select("*").order('pontos', desc=True).execute()
    df_rank = pd.DataFrame(res_rank.data)
    
    if not df_rank.empty:
        st.dataframe(df_rank[['participante', 'pontos']], use_container_width=True, hide_index=True)