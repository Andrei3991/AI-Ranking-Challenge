import streamlit as st
import pandas as pd
from supabase import create_client, Client
from streamlit_autorefresh import st_autorefresh

# ==========================================
# CONFIGURAÇÃO E CONEXÃO
# ==========================================
st.set_page_config(page_title="IA ou Real? - O Jogo", layout="wide")
st_autorefresh(interval=5000, key="game_loop")

SENHA_ADMIN = "@@admin123"

@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# ==========================================
# FUNÇÕES DE BANCO DE DADOS (COM TRATAMENTO DE ERRO)
# ==========================================

def buscar_rodada():
    try:
        res = supabase.table('rodada_atual').select("*").eq('id', 1).execute()
        if res.data: return res.data[0]
        return {"status": "aguardando", "imagem_a": "", "imagem_b": "", "resposta_correta": "A"}
    except:
        return {"status": "aguardando"}

def ja_votou(nome):
    if not nome: return False
    res = supabase.table('votos').select("*").eq('participante', nome).execute()
    return len(res.data) > 0

def carregar_ranking():
    res = supabase.table('ranking').select("*").order('pontos', desc=True).execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=['participante', 'pontos'])

# ==========================================
# TELA DE ENTRADA (JOGADOR OU ADMIN)
# ==========================================
if 'perfil' not in st.session_state:
    st.title("🤖 IA ou Real? - O Desafio")
    
    aba1, aba2 = st.tabs(["👤 Entrar como Jogador", "🔐 Acesso Admin"])
    
    with aba1:
        nome_input = st.text_input("Seu nome:")
        if st.button("Entrar no Jogo"):
            if nome_input:
                nome_limpo = nome_input.strip()
                # Cria participante se não existir
                res = supabase.table('ranking').select("*").eq('participante', nome_limpo).execute()
                if not res.data:
                    supabase.table('ranking').insert({'participante': nome_limpo, 'pontos': 0}).execute()
                st.session_state.usuario = nome_limpo
                st.session_state.perfil = "jogador"
                st.rerun()

    with aba2:
        senha = st.text_input("Senha de acesso:", type="password")
        if st.button("Acessar Painel"):
            if senha == SENHA_ADMIN:
                st.session_state.perfil = "admin"
                st.rerun()
            else:
                st.error("Senha incorreta!")
    st.stop()

# ==========================================
# PAINEL DO ADMINISTRADOR
# ==========================================
if st.session_state.perfil == "admin":
    st.title("⚙️ Painel de Controle - Admin")
    if st.button("⬅️ Sair do Painel"):
        del st.session_state.perfil
        st.rerun()

    col_cfg, col_gestao = st.columns([1, 1])

    with col_cfg:
        st.subheader("🚀 Configurar Rodada")
        img_a = st.text_input("URL Imagem A")
        img_b = st.text_input("URL Imagem B")
        correta = st.radio("Qual é a REAL?", ["A", "B"])
        
        c1, c2 = st.columns(2)
        if c1.button("🔥 INICIAR", use_container_width=True):
            supabase.table('votos').delete().neq('participante', '').execute()
            supabase.table('rodada_atual').update({
                'imagem_a': img_a, 'imagem_b': img_b, 
                'resposta_correta': correta, 'status': 'votando'
            }).eq('id', 1).execute()
            st.success("Rodada iniciada!")

        if c2.button("🛑 ENCERRAR", use_container_width=True):
            supabase.table('rodada_atual').update({'status': 'resultado'}).eq('id', 1).execute()
            st.rerun()

    with col_gestao:
        st.subheader("👥 Gestão de Pontos")
        df_rank = carregar_ranking()
        if not df_rank.empty:
            alvo = st.selectbox("Participante:", df_rank['participante'].tolist())
            pts_ajuste = st.number_input("Quantidade:", min_value=1, value=1)
            
            b1, b2, b3 = st.columns(3)
            if b1.button("➕ Pontuar"):
                atual = int(df_rank.loc[df_rank['participante'] == alvo, 'pontos'].values[0])
                supabase.table('ranking').update({'pontos': atual + pts_ajuste}).eq('participante', alvo).execute()
                st.rerun()
            if b2.button("➖ Remover"):
                atual = int(df_rank.loc[df_rank['participante'] == alvo, 'pontos'].values[0])
                supabase.table('ranking').update({'pontos': max(0, atual - pts_ajuste)}).eq('participante', alvo).execute()
                st.rerun()
            if b3.button("🗑️ Excluir"):
                supabase.table('ranking').delete().eq('participante', alvo).execute()
                st.rerun()

# ==========================================
# TELA DO JOGADOR
# ==========================================
else:
    rodada = buscar_rodada()
    st.title(f"Jogador: {st.session_state.get('usuario', 'Visitante')}")
    
    if st.button("Sair do Jogo"):
        del st.session_state.perfil
        del st.session_state.usuario
        st.rerun()

    if rodada['status'] == 'aguardando':
        st.info("Aguardando o organizador iniciar a rodada...")
        
    elif rodada['status'] == 'votando':
        if ja_votou(st.session_state.usuario):
            st.warning("Voto registrado! Aguarde o resultado...")
        else:
            st.subheader("Qual é a imagem REAL?")
            col1, col2 = st.columns(2)
            
            for col, letra, img_url in zip([col1, col2], ["A", "B"], [rodada['imagem_a'], rodada['imagem_b']]):
                with col:
                    if img_url: st.image(img_url, caption=f"Opção {letra}")
                    else: st.error(f"URL da Imagem {letra} inválida.")
                    
                    if st.button(f"Votar na {letra}", use_container_width=True):
                        if rodada['resposta_correta'] == letra:
                            # Soma ponto
                            res = supabase.table('ranking').select("pontos").eq('participante', st.session_state.usuario).execute()
                            if res.data:
                                novos = res.data[0]['pontos'] + 1
                                supabase.table('ranking').update({'pontos': novos}).eq('participante', st.session_state.usuario).execute()
                        
                        supabase.table('votos').insert({'participante': st.session_state.usuario, 'voto': letra}).execute()
                        st.rerun()

    elif rodada['status'] == 'resultado':
        st.success(f"A resposta correta era a Opção {rodada['resposta_correta']}!")
        df_rank = carregar_ranking()
        st.subheader("🏆 Ranking Atual")
        st.dataframe(df_rank[['participante', 'pontos']], use_container_width=True, hide_index=True)
