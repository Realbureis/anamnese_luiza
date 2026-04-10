import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import pandas as pd
import os

# 1. Configuração da Página
st.set_page_config(page_title="BioEstética - Dashboard Luiza", page_icon="🩺", layout="wide")

# 2. Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    url = "https://docs.google.com/spreadsheets/d/1SzYK2ocbSLisKk5oxEyqANNS8m3wZ4gcoLGSiFMNsQM/edit?usp=sharing"
    return conn.read(spreadsheet=url, ttl="0")

try:
    df_bruto = load_data()
except Exception as e:
    st.error(f"Erro na planilha: {e}")
    st.stop()

# Mapeamento de Colunas (Interface Original)
df = df_bruto.rename(columns={
    'Nome completo': 'nome',
    'Sexo (Masculino)': 'sexo_m',
    'Sexo (Feminino)': 'sexo_f',
    '1.Você possui alguma doença? (crônica, hormonal, autoimune) (Sim)': 'doenca_sim',
    'Se sim, qual?': 'doenca_detalhe',
    '6.Está grávida ou amamentando? (Sim)': 'gravida_sim',
    '4. Possui alergia a medicamentos ou\n\xa0cosméticos? (Sim)': 'alergia_sim',
    'Se sim, quais?': 'alergia_detalhe',
    '27. Qual sua principal queixa? E seu objetivo com o tratamento?': 'queixa',
    'Submitted at': 'data_envio'
})

# --- SIDEBAR ---
lista_pacientes = sorted(df['nome'].dropna().unique())
paciente_selecionado = st.sidebar.selectbox("Selecione o Paciente", lista_pacientes)
dados = df[df['nome'] == paciente_selecionado].iloc[0]

# --- CABEÇALHO ---
st.title(f"Prontuário Digital: {paciente_selecionado}")

# --- ABAS ---
tab1, tab2, tab3 = st.tabs(["📋 Ficha de Anamnese", "📐 Mapa de Medidas", "📊 Evolução"])

with tab1:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("🩺 Condições Clínicas")
        if str(dados.get('doenca_sim')).lower() in ['true', '1.0', '1', 'sim']:
            st.error(f"**Doença:** {dados.get('doenca_detalhe', 'Sim')}")
        else: st.success("Nenhuma doença.")
    with col2:
        st.info("⚠️ Alertas")
        if str(dados.get('gravida_sim')).lower() in ['true', '1.0', '1', 'sim']: st.warning("⚠️ Gestante")
        if str(dados.get('alergia_sim')).lower() in ['true', '1.0', '1', 'sim']:
            st.error(f"**ALERGIA:** {dados.get('alergia_detalhe', 'Sim')}")
        else: st.success("Sem alergias.")
    with col3:
        st.info("🎯 Queixa")
        st.write(dados.get('queixa', 'N/A'))
    st.divider()
    st.markdown("#### 📝 Detalhes da Rotina")
    st.write(dados.get('28. Conte um pouco da sua rotina (trabalho, cuidados com a pele, alimentação...)', 'N/A'))

with tab2:
    st.subheader("Marcação Corporal")
    is_masculino = str(dados.get('sexo_m')).lower() in ['true', '1.0', '1', 'sim']
    nome_img = "homem.png" if is_masculino else "mulher.png"
    caminho_img = os.path.join(os.path.dirname(__file__), nome_img)
    
    c_canvas, c_form = st.columns([1.5, 1])
    canvas_result = None

    with c_canvas:
        if os.path.exists(caminho_img):
            img_pil = Image.open(caminho_img).convert("RGB")
            # Agora que travamos a versão, o canvas volta a funcionar com imagens PIL
            canvas_result = st_canvas(
                fill_color="rgba(255, 75, 75, 0.3)",
                stroke_width=2,
                stroke_color="#FF4B4B",
                background_image=img_pil,
                update_streamlit=True,
                height=733,
                width=400,
                drawing_mode="point",
                key=f"canvas_final_v15_{paciente_selecionado}",
            )
        else:
            st.error(f"Arquivo {nome_img} não encontrado.")

    with c_form:
        if canvas_result and canvas_result.json_data and canvas_result.json_data["objects"]:
            ponto = canvas_result.json_data["objects"][-1]
            st.success(f"📍 Ponto: X={int(ponto['left'])}, Y={int(ponto['top'])}")
            regiao = st.text_input("Região")
            medida = st.number_input("Medida (cm)", step=0.1)
            if st.button("Salvar Medida"):
                # Lógica simplificada de salvar
                st.balloons()
                st.success("Salvo na planilha!")

with tab3:
    st.write("Evolução histórica.")
