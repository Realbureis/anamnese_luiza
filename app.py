import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import pandas as pd
import os

# 1. Configuração
st.set_page_config(page_title="BioEstética - Luiza", layout="wide")

# 2. Conexão
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1SzYK2ocbSLisKk5oxEyqANNS8m3wZ4gcoLGSiFMNsQM/edit?usp=sharing"
    return conn.read(spreadsheet=url)

try:
    df_bruto = load_data()
    # Mapeamento original que você aprovou
    df = df_bruto.rename(columns={
        'Nome completo': 'nome',
        'Sexo (Masculino)': 'sexo_m',
        '27. Qual sua principal queixa? E seu objetivo com o tratamento?': 'queixa'
    })
except:
    st.error("Erro ao carregar os dados da planilha.")
    st.stop()

# --- SIDEBAR ---
lista_pacientes = sorted(df['nome'].dropna().unique())
paciente_selecionado = st.sidebar.selectbox("Selecione o Paciente", lista_pacientes)
dados = df[df['nome'] == paciente_selecionado].iloc[0]

# --- CABEÇALHO ---
st.title(f"Prontuário: {paciente_selecionado}")

# --- ABAS ---
tab1, tab2, tab3 = st.tabs(["📋 Ficha", "📐 Medidas", "📊 Evolução"])

with tab1:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("🩺 Condições")
        st.write("Verificar anamnese completa.")
    with col2:
        st.info("⚠️ Alertas")
        st.warning("Alergias e restrições.")
    with col3:
        st.info("🎯 Queixa")
        st.write(dados.get('queixa', 'N/A'))

with tab2:
    st.subheader("Mapa Corporal")
    is_m = str(dados.get('sexo_m')).lower() in ['true', '1.0', '1', 'sim']
    img_name = "homem.png" if is_m else "mulher.png"
    img_path = os.path.join(os.path.dirname(__file__), img_name)

    c1, c2 = st.columns([2, 1])

    if os.path.exists(img_path):
        with c1:
            # Abrimos a imagem e garantimos que ela seja compatível
            bg = Image.open(img_path).convert("RGB")
            
            canvas_result = st_canvas(
                fill_color="rgba(255, 75, 75, 0.3)",
                stroke_width=2,
                stroke_color="#FF4B4B",
                background_image=bg,
                update_streamlit=True,
                height=733,
                width=400,
                drawing_mode="point",
                key=f"c_{paciente_selecionado}",
            )
        
        with c2:
            if canvas_result.json_data and canvas_result.json_data["objects"]:
                p = canvas_result.json_data["objects"][-1]
                st.success(f"📍 X: {int(p['left'])}, Y: {int(p['top'])}")
                regiao = st.text_input("Região")
                if st.button("Salvar Medida"):
                    st.balloons()
    else:
        st.error(f"Arquivo {img_name} não encontrado.")
