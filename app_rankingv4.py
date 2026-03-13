import streamlit as st
import pandas as pd
import plotly.express as px
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
# FUNÇÕES DE BANCO DE DADOS
# ==========================================

def buscar_rodada():
    try:
        res = supabase.table('rodada_atual').select("*").eq('id', 1).execute()
        return res.data[0] if res.data else {"status": "aguardando"}
    except:
        return {"status": "aguardando"}

def buscar_voto_usuario(nome):
    res = supabase.table('votos').select("*").eq('participante', nome).execute()
    return res.data[0] if res.data else None

def carregar_ranking():
    res = supabase.table('ranking').select("*").order('pontos', desc=True).execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=['participante', 'pontos'])

# ==========================================
# TELA DE ENTRADA
# ==========================================
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
        if st.button("Acessar Painel"):
            if senha == SENHA_ADMIN:
                st.session_state.perfil = "admin"
                st.rerun()
    st.stop()

# ================= : PAINEL ADMIN : =================
if st.session_state.perfil == "admin":
    st.title("⚙️ Admin")
    if st.button("⬅️ Sair"):
        del st.session_state.perfil
        st.rerun()

    col_cfg, col_gestao = st.columns([1, 1])

    with col_cfg:
        st.subheader("🚀 Próxima Rodada")
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
        st.subheader("👥 Gestão")
        df_rank = carregar_ranking()
        if not df_rank.empty:
            alvo = st.selectbox("Participante:", df_rank['participante'].tolist())
            b1, b2 = st.columns(2)
            if b1.button("🗑️ Excluir"):
                supabase.table('ranking').delete().eq('participante', alvo).execute()
                st.rerun()
            if b2.button("🔄 Zerar Tudo"):
                supabase.table('ranking').update({'pontos': 0}).neq('participante', '').execute()
                st.rerun()

# ================= : TELA JOGADOR : =================
else:
    rodada = buscar_rodada()
    st.title(f"Jogador: {st.session_state.usuario}")
    
    if rodada['status'] == 'aguardando':
        st.info("Aguardando o início da rodada...")
        
    elif rodada['status'] == 'votando':
        voto_feito = buscar_voto_usuario(st.session_state.usuario)
        
        if voto_feito:
            # FEEDBACK DE ACERTO/ERRO EM TEMPO REAL
            if voto_feito['voto'] == rodada['resposta_correta']:
                st.success("✨ Você acertou! Aguarde o resultado oficial.")
            else:
                st.error("❌ Ops! Você escolheu a imagem de IA. Mais sorte na próxima!")
        else:
            st.subheader("Qual das imagens NÃO foi feita por uma IA ?")
            col1, col2 = st.columns(2)
            for col, letra, url in zip([col1, col2], ["A", "B"], [rodada['imagem_a'], rodada['imagem_b']]):
                with col:
                    if url: st.image(url, caption=f"Opção {letra}")
                    if st.button(f"Votar na {letra}", use_container_width=True):
                        if rodada['resposta_correta'] == letra:
                            res = supabase.table('ranking').select("pontos").eq('participante', st.session_state.usuario).execute()
                            supabase.table('ranking').update({'pontos': res.data[0]['pontos'] + 1}).eq('participante', st.session_state.usuario).execute()
                        supabase.table('votos').insert({'participante': st.session_state.usuario, 'voto': letra}).execute()
                        st.rerun()

    elif rodada['status'] == 'resultado':
        st.success(f"🏆 A resposta correta era a Opção {rodada['resposta_correta']}!")
        
        # --- EXIBIÇÃO EM GRÁFICO ---
        df_rank = carregar_ranking()
        if not df_rank.empty:
            st.subheader("📊 Ranking Geral")
            fig = px.bar(
                df_rank, x='participante', y='pontos', 
                color='pontos', text='pontos',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(yaxis_visible=False)
            st.plotly_chart(fig, use_container_width=True)
