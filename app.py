import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_drawable_canvas import st_canvas
import pandas as pd

# 1. Configuração da Página
st.set_page_config(
    page_title="BioEstética - Dashboard Luiza",
    page_icon="🩺",
    layout="wide"
)

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
    '27. Qual sua principal queixa? E seu objetivo com o tratamento?': 'queixa',
    'Submitted at': 'data_envio'
})

# --- SIDEBAR ---
st.sidebar.title("🩺 Pacientes")
lista_pacientes = sorted(df['nome'].dropna().unique())
paciente_selecionado = st.sidebar.selectbox("Selecione o Paciente", lista_pacientes)
dados = df[df['nome'] == paciente_selecionado].iloc[0]

# --- CABEÇALHO ---
st.title(f"Prontuário Digital: {paciente_selecionado}")

# --- ABAS ---
tab1, tab2, tab3 = st.tabs(["📋 Ficha de Anamnese", "📐 Mapa de Medidas", "📊 Evolução"])

with tab1:
    st.subheader("Resumo da Anamnese")
    st.info(f"**Queixa Principal:** {dados.get('queixa', 'Não informada')}")
    st.write(f"**Data da Anamnese:** {dados.get('data_envio')}")

with tab2:
    st.subheader("Marcação na Silhueta")
    
    # LÓGICA DE URL DIRETA (Evita o erro AttributeError)
    is_masculino = str(dados.get('sexo_m')).lower() in ['true', '1.0', '1', 'sim']
    
    # Links RAW do seu repositório GitHub
    url_base = "https://raw.githubusercontent.com/Realbureis/anamnese_luiza/main/"
    url_imagem = f"{url_base}{'homem.png' if is_masculino else 'mulher.png'}"
    
    c_canvas, c_form = st.columns([1.5, 1])

    with c_canvas:
        st.caption(f"Carregando silhueta de: {url_imagem}")
        
        # PASSANDO A URL DIRETAMENTE (Isso resolve o problema)
        canvas_result = st_canvas(
            fill_color="rgba(255, 75, 75, 0.3)",
            stroke_width=2,
            stroke_color="#FF4B4B",
            background_image=url_imagem, # Passamos a String da URL, não o objeto Image
            update_streamlit=True,
            height=733, # Tamanho que você definiu na proporção
            width=400,
            drawing_mode="point",
            key=f"canvas_final_{paciente_selecionado}",
        )

    with c_form:
        st.markdown("### 📝 Nova Medida")
        if canvas_result and canvas_result.json_data and canvas_result.json_data["objects"]:
            ponto = canvas_result.json_data["objects"][-1]
            x, y = int(ponto["left"]), int(ponto["top"])
            st.success(f"📍 Ponto: X={x}, Y={y}")
            
            regiao = st.text_input("Região")
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
                    st.error("Erro ao salvar. Verifique se existe a aba 'Medidas' na planilha.")
        else:
            st.info("Clique na imagem para marcar.")

with tab3:
    st.write("Evolução histórica aparecerá aqui.")
