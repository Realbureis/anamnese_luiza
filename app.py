import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import pandas as pd
import requests
from io import BytesIO

# 1. Configuração da Página
st.set_page_config(
    page_title="BioEstética - Dashboard Luiza",
    page_icon="🩺",
    layout="wide"
)

# --- FUNÇÃO PARA CARREGAR IMAGEM DA NUVEM ---
@st.cache_data
def load_image_from_google_drive(file_id):
    # Converte o ID do Drive em um link de download direto
    url = f'https://drive.google.com/uc?id={file_id}'
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        st.error(f"Erro ao baixar imagem do Drive: {e}")
        return None

# 2. Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    url = "https://docs.google.com/spreadsheets/d/1SzYK2ocbSLisKk5oxEyqANNS8m3wZ4gcoLGSiFMNsQM/edit?usp=sharing"
    return conn.read(spreadsheet=url, ttl="0")

try:
    df_bruto = load_data()
except Exception as e:
    st.error(f"Erro ao conectar com a planilha: {e}")
    st.stop()

# 3. Tratamento de Colunas
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
st.sidebar.title("🩺 Gestão de Pacientes")
lista_pacientes = sorted(df['nome'].dropna().unique())
paciente_selecionado = st.sidebar.selectbox("Selecione o Paciente", lista_pacientes)
dados = df[df['nome'] == paciente_selecionado].iloc[0]

# --- CABEÇALHO ---
st.title(f"Prontuário Digital: {paciente_selecionado}")
st.caption(f"Dados sincronizados via Tally | Última Anamnese: {dados['data_envio']}")

# --- ABAS ---
tab1, tab2, tab3 = st.tabs(["📋 Ficha de Anamnese", "📐 Mapa de Medidas", "📊 Evolução"])

with tab1:
    st.subheader("Informações da Anamnese")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("🩺 Condições Clínicas")
        if str(dados.get('doenca_sim')).lower() in ['true', '1.0', '1', 'sim']:
            st.error(f"**Doença:** {dados.get('doenca_detalhe', 'Relatada')}")
        else:
            st.success("Sem doenças relatadas.")
    with col2:
        st.info("⚠️ Alertas")
        if str(dados.get('gravida_sim')).lower() in ['true', '1.0', '1', 'sim']:
            st.warning("⚠️ Gestante/Lactante")
        if str(dados.get('alergia_sim')).lower() in ['true', '1.0', '1', 'sim']:
            st.error(f"**ALERGIA:** {dados.get('alergia_detalhe', 'Relatada')}")
    with col3:
        st.info("🎯 Queixa")
        st.write(dados.get('queixa', 'Não informado'))

with tab2:
    st.subheader("Marcação Corporal (Google Drive Cloud)")
    
    # IDs extraídos dos seus links
    id_homem = "1nQTT0v1B5Ik5OMhOtC2YMEDlZEkB-Phf"
    id_mulher = "1xppoQNIJKa0ZXJzNxDYEXiPPpKJ19eX7"
    
    is_masculino = str(dados.get('sexo_m')).lower() in ['true', '1.0', '1', 'sim']
    id_final = id_homem if is_masculino else id_mulher
    
    c_canvas, c_form = st.columns([1.5, 1])
    canvas_result = None

    with c_canvas:
        bg_image = load_image_from_google_drive(id_final)
        
        if bg_image:
            # Pegamos o tamanho da imagem que você redimensionou (400x733)
            largura, altura = bg_image.size
            
            canvas_result = st_canvas(
                fill_color="rgba(255, 75, 75, 0.3)",
                stroke_width=2,
                stroke_color="#FF4B4B",
                background_image=bg_image,
                update_streamlit=True,
                height=altura,
                width=largura,
                drawing_mode="point",
                key=f"canvas_drive_{paciente_selecionado}",
            )
        else:
            st.warning("Aguardando carregamento da silhueta do Google Drive...")

    with c_form:
        st.markdown("### 📝 Nova Medida")
        if canvas_result and canvas_result.json_data and canvas_result.json_data["objects"]:
            ponto = canvas_result.json_data["objects"][-1]
            x, y = int(ponto["left"]), int(ponto["top"])
            st.success(f"📍 Ponto: X={x}, Y={y}")
            
            regiao = st.text_input("Região", placeholder="Ex: Abdômen")
            medida = st.number_input("Medida (cm)", step=0.1)
            
            if st.button("Salvar Medida"):
                nova_medida = pd.DataFrame([{
                    "Data": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"),
                    "Paciente": paciente_selecionado,
                    "Regiao": regiao,
                    "Medida": medida,
                    "Coord_X": x, "Coord_Y": y
                }])
                try:
                    conn.create(worksheet="Medidas", data=nova_medida)
                    st.balloons()
                    st.success("Dados salvos na aba 'Medidas'!")
                except:
                    st.error("Erro ao salvar. Verifique se a aba 'Medidas' existe na planilha.")
        else:
            st.info("Clique na imagem para marcar um ponto.")

with tab3:
    st.subheader("Evolução")
    st.write("Em breve: Gráficos de evolução histórica.")
