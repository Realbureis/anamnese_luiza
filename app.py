import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import pandas as pd
import os

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

# 3. Tratamento de Colunas (Interface Original)
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
    st.subheader("Informações Coletadas no Tally")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("🩺 Condições Clínicas")
        if str(dados.get('doenca_sim')).lower() in ['true', '1.0', '1', 'sim']:
            st.error(f"**Doença Relatada:** {dados.get('doenca_detalhe', 'Ver na planilha')}")
        else:
            st.success("Nenhuma doença relatada.")
    with col2:
        st.info("⚠️ Alertas de Risco")
        if str(dados.get('gravida_sim')).lower() in ['true', '1.0', '1', 'sim']:
            st.warning("⚠️ Paciente Gestante ou Lactante")
        if str(dados.get('alergia_sim')).lower() in ['true', '1.0', '1', 'sim']:
            st.error(f"**ALERGIA:** {dados.get('alergia_detalhe', 'Ver na planilha')}")
        else:
            st.success("Sem alergias conhecidas.")
    with col3:
        st.info("🎯 Queixa Principal")
        st.write(dados.get('queixa', 'Não informado'))
    st.divider()
    st.markdown("#### 📝 Detalhes da Rotina")
    st.write(dados.get('28. Conte um pouco da sua rotina (trabalho, cuidados com a pele, alimentação...)', 'Informação não disponível.'))

with tab2:
    st.subheader("Marcação Corporal e Facial")
    
    is_masculino = str(dados.get('sexo_m')).lower() in ['true', '1.0', '1', 'sim']
    nome_img = "homem.png" if is_masculino else "mulher.png"
    
    # FORÇA A BUSCA DO ARQUIVO LOCAL
    caminho_base = os.path.dirname(__file__)
    caminho_completo = os.path.join(caminho_base, nome_img)
    
    c_canvas, c_form = st.columns([1.5, 1])
    canvas_result = None

    with c_canvas:
        if os.path.exists(caminho_completo):
            img_aberta = Image.open(caminho_completo)
            # Redimensiona para o tamanho ideal que conversamos
            img_aberta = img_aberta.convert("RGBA").resize((400, 733))
            
            canvas_result = st_canvas(
                fill_color="rgba(255, 75, 75, 0.3)",
                stroke_width=2,
                stroke_color="#FF4B4B",
                background_image=img_aberta,
                update_streamlit=True,
                height=733,
                width=400,
                drawing_mode="point",
                key=f"canv_local_{paciente_selecionado}_{nome_img}",
            )
        else:
            st.error(f"Arquivo não encontrado no GitHub: {nome_img}")

    with c_form:
        st.markdown("### 📝 Nova Medida")
        if canvas_result is not None and canvas_result.json_data and canvas_result.json_data["objects"]:
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
                    st.success("Salvo!")
                except:
                    st.error("Erro ao salvar. Verifique a aba 'Medidas'.")
        else:
            st.info("Clique na silhueta para marcar.")

with tab3:
    st.subheader("Acompanhamento de Resultados")
    st.write("Dados históricos aparecerão aqui.")
