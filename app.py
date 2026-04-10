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
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # URL direta para corrigir o erro 'Spreadsheet must be specified'
    url = "https://docs.google.com/spreadsheets/d/1SzYK2ocbSLisKk5oxEyqANNS8m3wZ4gcoLGSiFMNsQM/edit?usp=sharing"
    # ttl="0" garante que novos envios do Tally apareçam ao atualizar a página
    return conn.read(spreadsheet=url, ttl="0")

try:
    df_bruto = load_data()
except Exception as e:
    st.error(f"Erro ao conectar com a planilha: {e}")
    st.stop()

# 3. Tratamento e Mapeamento de Colunas
# Aqui limpamos os nomes das colunas que vêm do Tally para facilitar o uso
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

# --- SIDEBAR (Barra Lateral) ---
st.sidebar.title("🩺 Gestão de Pacientes")
# Garante que a lista de pacientes esteja limpa
lista_pacientes = sorted(df['nome'].dropna().unique())
paciente_selecionado = st.sidebar.selectbox("Selecione o Paciente", lista_pacientes)

# Filtrar dados do paciente específico
dados = df[df['nome'] == paciente_selecionado].iloc[0]

# --- CABEÇALHO ---
st.title(f"Prontuário Digital: {paciente_selecionado}")
st.caption(f"Dados sincronizados via Tally | Última Anamnese: {dados['data_envio']}")

# --- DIVISÃO EM ABAS ---
tab1, tab2, tab3 = st.tabs(["📋 Ficha de Anamnese", "📐 Mapa de Medidas", "📊 Evolução"])

with tab1:
    st.subheader("Informações Coletadas no Tally")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("🩺 Condições Clínicas")
        # Checagem flexível para valores 'True', '1' ou 'Sim'
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
    
    # Lógica de Troca de Imagem por Sexo
    is_masculino = str(dados.get('sexo_m')).lower() in ['true', '1.0', '1', 'sim']
    imagem_path = "homem.png" if is_masculino else "mulher.png"
    
    c_canvas, c_form = st.columns([1.5, 1])
    
    with c_canvas:
        try:
            bg_image = Image.open(imagem_path)
            st.caption(f"Silhueta exibida: {'Masculina' if is_masculino else 'Feminina'}")
            
            canvas_result = st_canvas(
                fill_color="rgba(255, 75, 75, 0.3)",
                stroke_width=2,
                stroke_color="#FF4B4B",
                background_image=bg_image,
                update_streamlit=True,
                height=700,
                width=450,
                drawing_mode="point",
                key="canvas_estetica",
            )
        except FileNotFoundError:
            st.error(f"⚠️ Erro: O arquivo '{imagem_path}' não foi encontrado no seu GitHub.")

    with c_form:
        st.markdown("### 📝 Nova Medida")
        if canvas_result.json_data and canvas_result.json_data["objects"]:
            # Captura a última marcação
            ponto = canvas_result.json_data["objects"][-1]
            x, y = int(ponto["left"]), int(ponto["top"])
            
            st.success(f"📍 Ponto selecionado: X={x}, Y={y}")
            
            regiao = st.text_input("Região do corpo", placeholder="Ex: Abdômen Inferior")
            medida_cm = st.number_input("Medida (cm)", min_value=0.0, step=0.1)
            prega_mm = st.number_input("Prega Cutânea (mm)", min_value=0.0, step=0.1)
            
            if st.button("Salvar Medida na Planilha"):
                # Estrutura para salvar na aba 'Medidas'
                nova_medida = pd.DataFrame([{
                    "Data": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"),
                    "Paciente": paciente_selecionado,
                    "Regiao": regiao,
                    "Medida_cm": medida_cm,
                    "Prega_mm": prega_mm,
                    "Coord_X": x,
                    "Coord_Y": y
                }])
                
                try:
                    # Tenta gravar na aba 'Medidas'
                    conn.create(worksheet="Medidas", data=nova_medida)
                    st.balloons()
                    st.success("Medida gravada com sucesso!")
                except:
                    st.error("Erro ao salvar. Verifique se a planilha permite edição e se existe uma aba chamada 'Medidas'.")
        else:
            st.info("Clique em uma região da silhueta ao lado para habilitar o formulário de medidas.")

with tab3:
    st.subheader("Acompanhamento de Resultados")
    st.write("Os dados salvos na aba 'Medidas' aparecerão aqui em formato de gráfico em breve.")
