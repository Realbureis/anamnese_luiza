import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="BioEstética - Dashboard", layout="wide")

# 2. Conexão com Google Sheets
# No Streamlit Cloud, as credenciais devem estar nos 'Secrets'
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read()

df_bruto = load_data()

# 3. Limpeza de Colunas (Tratando os nomes gigantes do Tally)
# Criamos um mapeamento para não ter que usar frases inteiras no código
df = df_bruto.rename(columns={
    'Nome completo': 'nome',
    '1.Você possui alguma doença? (crônica, hormonal, autoimune) (Sim)': 'doenca_sim',
    'Se sim, qual?': 'doenca_detalhe',
    '6.Está grávida ou amamentando? (Sim)': 'gravida_sim',
    '4. Possui alergia a medicamentos ou\n\xa0cosméticos? (Sim)': 'alergia_sim',
    'Se sim, quais?': 'alergia_detalhe',
    '27. Qual sua principal queixa? E seu objetivo com o tratamento?': 'queixa',
    'Submitted at': 'data_envio'
})

# Sidebar - Seleção de Paciente
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3448/3448520.png", width=100)
st.sidebar.title("Painel da Biomédica")
lista_pacientes = df['nome'].unique()
paciente_selecionado = st.sidebar.selectbox("Escolha o Paciente", lista_pacientes)

# Filtrar dados do paciente
dados = df[df['nome'] == paciente_selecionado].iloc[0]

# --- Interface Principal ---
st.title(f"Paciente: {paciente_selecionado}")
st.write(f"**Última atualização da anamnese:** {dados['data_envio']}")

tab1, tab2, tab3 = st.tabs(["📋 Ficha de Anamnese", "📐 Silhueta e Medidas", "📈 Evolução"])

with tab1:
    st.subheader("Informações de Saúde")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("🩺 Condições Clínicas")
        status_doenca = "⚠️ Sim" if dados['doenca_sim'] else "✅ Não"
        st.write(f"**Doenças:** {status_doenca}")
        if dados['doenca_sim']:
            st.warning(dados['doenca_detalhe'])

    with col2:
        st.info("🚫 Alergias e Riscos")
        status_alergia = "⚠️ Sim" if dados['alergia_sim'] else "✅ Não"
        st.write(f"**Alergias:** {status_alergia}")
        
        status_gravida = "🛑 SIM" if dados['gravida_sim'] else "✅ Não"
        st.write(f"**Gestante/Lactante:** {status_gravida}")

    with col3:
        st.info("🎯 Objetivo")
        st.write(f"**Queixa Principal:** {dados['queixa']}")

    st.divider()
    st.write("**Resumo da Rotina:**")
    st.caption(dados.get('28. Conte um pouco da sua rotina (trabalho, cuidados com a pele, alimentação...)', 'Não informado'))

with tab2:
    st.subheader("Mapeamento Corporal")
    
    c1, c2 = st.columns([1.5, 1])
    
    with c1:
        st.markdown("Clique na região desejada para registrar a medida:")
        
        # Tenta carregar a imagem da silhueta
        try:
            bg_image = Image.open("corpo.png")
            
            canvas_result = st_canvas(
                fill_color="rgba(255, 75, 75, 0.3)",  # Cor do círculo de marcação
                stroke_width=2,
                stroke_color="#FF4B4B",
                background_image=bg_image,
                update_streamlit=True,
                height=650,
                width=450,
                drawing_mode="point",
                key="canvas_corpo",
            )
        except FileNotFoundError:
            st.error("Erro: Arquivo 'corpo.png' não encontrado no repositório.")

    with c2:
        st.write("### Nova Medida")
        if canvas_result.json_data and canvas_result.json_data["objects"]:
            # Captura o último ponto clicado
            last_point = canvas_result.json_data["objects"][-1]
            x, y = last_point["left"], last_point["top"]
            
            st.success(f"Ponto capturado! (X: {int(x)}, Y: {int(y)})")
            
            regiao = st.text_input("Região (ex: Abdômen, Braço Dir.)", key="reg")
            valor = st.number_input("Medida em cm", min_value=0.0, step=0.1)
            prega = st.number_input("Prega Cutânea (mm)", min_value=0.0, step=0.1)
            
            if st.button("Salvar na Planilha"):
                # Aqui você adicionaria a lógica para salvar em uma nova aba 'Medidas'
                st.balloons()
                st.write(f"Salvando: {regiao} - {valor}cm no banco de dados...")
        else:
            st.info("Clique na imagem ao lado para habilitar a edição.")

with tab3:
    st.subheader("Histórico de Resultados")
    st.write("Aqui aparecerão os gráficos de evolução assim que as medidas forem salvas na aba de Medidas.")
    # Exemplo de gráfico futuro:
    # st.line_chart(df_medidas_filtrado)
