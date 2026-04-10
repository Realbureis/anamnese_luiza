import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import pandas as pd

# 1. Configuração da Página
st.set_page_config(
    page_title="BioEstética - Dashboard Luiza",
    page_icon="🩺",
    layout="wide"
)

# 2. Conexão com Google Sheets
# O link da planilha será pego automaticamente dos Secrets configurados
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # ttl="0" força o Streamlit a buscar dados novos da planilha a cada refresh
    return conn.read(ttl="0")

try:
    df_bruto = load_data()
except Exception as e:
    st.error(f"Erro ao conectar com a planilha: {e}")
    st.stop()

# 3. Tratamento de Dados (Mapeamento exato das colunas do seu Tally)
# Usei os nomes que você me passou na lista anterior
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
lista_pacientes = df['nome'].unique()
paciente_selecionado = st.sidebar.selectbox("Selecione o Paciente", lista_pacientes)

# Filtrar dados do paciente específico
dados = df[df['nome'] == paciente_selecionado].iloc[0]

# --- CABEÇALHO ---
st.title(f"Prontuário: {paciente_selecionado}")
st.caption(f"Último envio da Anamnese: {dados['data_envio']}")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📋 Ficha Técnica", "📐 Medidas Corporais", "📊 Evolução"])

with tab1:
    st.subheader("Resumo Clínico (Tally)")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.info("🩺 Histórico")
        if str(dados['doenca_sim']).lower() in ['true', '1.0', '1', 'sim']:
            st.error(f"**Doença:** {dados.get('Se sim, qual?', 'Sim (ver planilha)')}")
        else:
            st.success("Sem doenças relatadas")
            
    with c2:
        st.info("⚠️ Riscos")
        if str(dados['gravida_sim']).lower() in ['true', '1.0', '1', 'sim']:
            st.warning("⚠️ Gestante/Lactante")
        if str(dados['alergia_sim']).lower() in ['true', '1.0', '1', 'sim']:
            st.error(f"**ALERGIA:** {dados.get('alergia_detalhe', 'Sim')}")
        else:
            st.success("Sem alergias relatadas")

    with c3:
        st.info("🎯 Queixa Principal")
        st.write(dados['queixa'])

with tab2:
    st.subheader("Mapeamento na Silhueta")
    
    # Lógica de Silhueta Dinâmica
    # Verifica se a coluna Masculino é verdadeira
    is_masc = str(dados['sexo_m']).lower() in ['true', '1.0', '1', 'sim']
    img_path = "homem.png" if is_masc else "mulher.png"
    
    col_canvas, col_form = st.columns([1.5, 1])
    
    with col_canvas:
        try:
            bg_image = Image.open(img_path)
            canvas_result = st_canvas(
                fill_color="rgba(255, 75, 75, 0.4)",
                stroke_width=2,
                stroke_color="#FF4B4B",
                background_image=bg_image,
                update_streamlit=True,
                height=700,
                width=450,
                drawing_mode="point",
                key="canvas_medidas",
            )
        except FileNotFoundError:
            st.error(f"Arquivo {img_path} não encontrado no GitHub.")

    with col_form:
        st.markdown("### Registrar Medida")
        if canvas_result.json_data and canvas_result.json_data["objects"]:
            last_point = canvas_result.json_data["objects"][-1]
            x, y = int(last_point["left"]), int(last_point["top"])
            
            st.markdown(f"📍 **Ponto:** X:{x}, Y:{y}")
            regiao = st.text_input("Região", placeholder="Ex: Abdômen")
            valor = st.number_input("Medida (cm)", step=0.1)
            prega = st.number_input("Prega (mm)", step=0.1)
            
            if st.button("Salvar Medida"):
                # Para salvar, você precisa criar uma aba chamada 'Medidas' na planilha
                nova_linha = pd.DataFrame([{
                    "Data": pd.Timestamp.now().strftime("%d/%m/%Y"),
                    "Paciente": paciente_selecionado,
                    "Regiao": regiao,
                    "Medida": valor,
                    "Prega": prega,
                    "X": x, "Y": y
                }])
                try:
                    conn.create(worksheet="Medidas", data=nova_linha)
                    st.success("Salvo com sucesso!")
                    st.balloons()
                except:
                    st.error("Erro ao salvar. Verifique se a planilha está como 'Editor' e se existe a aba 'Medidas'.")
        else:
            st.info("Clique na imagem para marcar.")

with tab3:
    st.subheader("Histórico")
    st.write("Dados da aba 'Medidas' aparecerão aqui em breve.")
