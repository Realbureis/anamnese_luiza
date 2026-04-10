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

# --- FUNÇÃO PARA CARREGAR IMAGEM DO GITHUB (LINK RAW) ---
@st.cache_data
def load_image_from_github(sexo):
    # Usando o link RAW do seu próprio GitHub para evitar bloqueios do Google Drive
    base_url = "https://raw.githubusercontent.com/Realbureis/anamnese_luiza/main/"
    filename = "homem.png" if sexo == "M" else "mulher.png"
    url = base_url + filename
    
    try:
        response = requests.get(url)
        # Verifica se o download foi bem sucedido
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        else:
            st.error(f"Erro {response.status_code} ao buscar {filename}")
            return None
    except Exception as e:
        st.error(f"Erro ao carregar imagem do GitHub: {e}")
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
st.caption(f"Dados atualizados via Tally")

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
        else:
            st.success("Sem alergias.")
    with col3:
        st.info("🎯 Queixa Principal")
        st.write(dados.get('queixa', 'Não informado'))

with tab2:
    st.subheader("Mapa de Medidas Corporal")
    
    # Identifica o sexo
    is_masculino = str(dados.get('sexo_m')).lower() in ['true', '1.0', '1', 'sim']
    sexo_key = "M" if is_masculino else "F"
    
    c_canvas, c_form = st.columns([1.5, 1])
    canvas_result = None

    with c_canvas:
        # Carrega imagem do GitHub
        bg_image = load_image_from_github(sexo_key)
        
        if bg_image:
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
                key=f"canvas_gh_{paciente_selecionado}_{sexo_key}",
            )
        else:
            st.warning("Tentando carregar silhueta do servidor...")

    with c_form:
        st.markdown("### 📝 Registrar Medida")
        if canvas_result and canvas_result.json_data and canvas_result.json_data["objects"]:
            ponto = canvas_result.json_data["objects"][-1]
            x, y = int(ponto["left"]), int(ponto["top"])
            st.success(f"📍 Ponto: X={x}, Y={y}")
            
            regiao = st.text_input("Região do corpo")
            medida = st.number_input("Medida (cm)", step=0.1)
            
            if st.button("Salvar Medida"):
                nova_medida = pd.DataFrame([{
                    "Data": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"),
                    "Paciente": paciente_selecionado,
                    "Regiao": regiao,
                    "Medida": medida,
                    "X": x, "Y": y
                }])
                try:
                    conn.create(worksheet="Medidas", data=nova_medida)
                    st.balloons()
                    st.success("Salvo com sucesso!")
                except:
                    st.error("Erro ao salvar. Verifique a aba 'Medidas' na planilha.")
        else:
            st.info("Clique na silhueta para marcar um ponto.")

with tab3:
    st.subheader("Histórico")
    st.write("Em breve: Gráfico de evolução.")
