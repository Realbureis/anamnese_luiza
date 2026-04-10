)

# 2. Conexão com Google Sheets
# O link da planilha será pego automaticamente dos Secrets configurados
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # ttl="0" força o Streamlit a buscar dados novos da planilha a cada refresh
    return conn.read(ttl="0")
    # URL direta para corrigir o erro 'Spreadsheet must be specified'
    url = "https://docs.google.com/spreadsheets/d/1SzYK2ocbSLisKk5oxEyqANNS8m3wZ4gcoLGSiFMNsQM/edit?usp=sharing"
    # ttl="0" garante que novos envios do Tally apareçam ao atualizar a página
    return conn.read(spreadsheet=url, ttl="0")

try:
df_bruto = load_data()
except Exception as e:
st.error(f"Erro ao conectar com a planilha: {e}")
st.stop()

# 3. Tratamento de Dados (Mapeamento exato das colunas do seu Tally)
# Usei os nomes que você me passou na lista anterior
# 3. Tratamento e Mapeamento de Colunas
# Aqui limpamos os nomes das colunas que vêm do Tally para facilitar o uso
df = df_bruto.rename(columns={
'Nome completo': 'nome',
'Sexo (Masculino)': 'sexo_m',
@@ -40,102 +41,115 @@ def load_data():
'Submitted at': 'data_envio'
})

# --- SIDEBAR ---
# --- SIDEBAR (Barra Lateral) ---
st.sidebar.title("🩺 Gestão de Pacientes")
lista_pacientes = df['nome'].unique()
# Garante que a lista de pacientes esteja limpa
lista_pacientes = sorted(df['nome'].dropna().unique())
paciente_selecionado = st.sidebar.selectbox("Selecione o Paciente", lista_pacientes)

# Filtrar dados do paciente específico
dados = df[df['nome'] == paciente_selecionado].iloc[0]

# --- CABEÇALHO ---
st.title(f"Prontuário: {paciente_selecionado}")
st.caption(f"Último envio da Anamnese: {dados['data_envio']}")
st.title(f"Prontuário Digital: {paciente_selecionado}")
st.caption(f"Dados sincronizados via Tally | Última Anamnese: {dados['data_envio']}")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📋 Ficha Técnica", "📐 Medidas Corporais", "📊 Evolução"])
# --- DIVISÃO EM ABAS ---
tab1, tab2, tab3 = st.tabs(["📋 Ficha de Anamnese", "📐 Mapa de Medidas", "📊 Evolução"])

with tab1:
    st.subheader("Resumo Clínico (Tally)")
    c1, c2, c3 = st.columns(3)
    st.subheader("Informações Coletadas no Tally")
    col1, col2, col3 = st.columns(3)

    with c1:
        st.info("🩺 Histórico")
        if str(dados['doenca_sim']).lower() in ['true', '1.0', '1', 'sim']:
            st.error(f"**Doença:** {dados.get('Se sim, qual?', 'Sim (ver planilha)')}")
    with col1:
        st.info("🩺 Condições Clínicas")
        # Checagem flexível para valores 'True', '1' ou 'Sim'
        if str(dados.get('doenca_sim')).lower() in ['true', '1.0', '1', 'sim']:
            st.error(f"**Doença Relatada:** {dados.get('doenca_detalhe', 'Ver na planilha')}")
else:
            st.success("Sem doenças relatadas")
            st.success("Nenhuma doença relatada.")

    with c2:
        st.info("⚠️ Riscos")
        if str(dados['gravida_sim']).lower() in ['true', '1.0', '1', 'sim']:
            st.warning("⚠️ Gestante/Lactante")
        if str(dados['alergia_sim']).lower() in ['true', '1.0', '1', 'sim']:
            st.error(f"**ALERGIA:** {dados.get('alergia_detalhe', 'Sim')}")
    with col2:
        st.info("⚠️ Alertas de Risco")
        if str(dados.get('gravida_sim')).lower() in ['true', '1.0', '1', 'sim']:
            st.warning("⚠️ Paciente Gestante ou Lactante")
        
        if str(dados.get('alergia_sim')).lower() in ['true', '1.0', '1', 'sim']:
            st.error(f"**ALERGIA:** {dados.get('alergia_detalhe', 'Ver na planilha')}")
else:
            st.success("Sem alergias relatadas")
            st.success("Sem alergias conhecidas.")

    with c3:
    with col3:
st.info("🎯 Queixa Principal")
        st.write(dados['queixa'])
        st.write(dados.get('queixa', 'Não informado'))

    st.divider()
    st.markdown("#### 📝 Detalhes da Rotina")
    st.write(dados.get('28. Conte um pouco da sua rotina (trabalho, cuidados com a pele, alimentação...)', 'Informação não disponível.'))

with tab2:
    st.subheader("Mapeamento na Silhueta")
    st.subheader("Marcação Corporal e Facial")

    # Lógica de Silhueta Dinâmica
    # Verifica se a coluna Masculino é verdadeira
    is_masc = str(dados['sexo_m']).lower() in ['true', '1.0', '1', 'sim']
    img_path = "homem.png" if is_masc else "mulher.png"
    # Lógica de Troca de Imagem por Sexo
    is_masculino = str(dados.get('sexo_m')).lower() in ['true', '1.0', '1', 'sim']
    imagem_path = "homem.png" if is_masculino else "mulher.png"

    col_canvas, col_form = st.columns([1.5, 1])
    c_canvas, c_form = st.columns([1.5, 1])

    with col_canvas:
    with c_canvas:
try:
            bg_image = Image.open(img_path)
            bg_image = Image.open(imagem_path)
            st.caption(f"Silhueta exibida: {'Masculina' if is_masculino else 'Feminina'}")
            
canvas_result = st_canvas(
                fill_color="rgba(255, 75, 75, 0.4)",
                fill_color="rgba(255, 75, 75, 0.3)",
stroke_width=2,
stroke_color="#FF4B4B",
background_image=bg_image,
update_streamlit=True,
height=700,
width=450,
drawing_mode="point",
                key="canvas_medidas",
                key="canvas_estetica",
)
except FileNotFoundError:
            st.error(f"Arquivo {img_path} não encontrado no GitHub.")
            st.error(f"⚠️ Erro: O arquivo '{imagem_path}' não foi encontrado no seu GitHub.")

    with col_form:
        st.markdown("### Registrar Medida")
    with c_form:
        st.markdown("### 📝 Nova Medida")
if canvas_result.json_data and canvas_result.json_data["objects"]:
            last_point = canvas_result.json_data["objects"][-1]
            x, y = int(last_point["left"]), int(last_point["top"])
            # Captura a última marcação
            ponto = canvas_result.json_data["objects"][-1]
            x, y = int(ponto["left"]), int(ponto["top"])
            
            st.success(f"📍 Ponto selecionado: X={x}, Y={y}")

            st.markdown(f"📍 **Ponto:** X:{x}, Y:{y}")
            regiao = st.text_input("Região", placeholder="Ex: Abdômen")
            valor = st.number_input("Medida (cm)", step=0.1)
            prega = st.number_input("Prega (mm)", step=0.1)
            regiao = st.text_input("Região do corpo", placeholder="Ex: Abdômen Inferior")
            medida_cm = st.number_input("Medida (cm)", min_value=0.0, step=0.1)
            prega_mm = st.number_input("Prega Cutânea (mm)", min_value=0.0, step=0.1)

            if st.button("Salvar Medida"):
                # Para salvar, você precisa criar uma aba chamada 'Medidas' na planilha
                nova_linha = pd.DataFrame([{
                    "Data": pd.Timestamp.now().strftime("%d/%m/%Y"),
            if st.button("Salvar Medida na Planilha"):
                # Estrutura para salvar na aba 'Medidas'
                nova_medida = pd.DataFrame([{
                    "Data": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"),
"Paciente": paciente_selecionado,
"Regiao": regiao,
                    "Medida": valor,
                    "Prega": prega,
                    "X": x, "Y": y
                    "Medida_cm": medida_cm,
                    "Prega_mm": prega_mm,
                    "Coord_X": x,
                    "Coord_Y": y
}])
                
try:
                    conn.create(worksheet="Medidas", data=nova_linha)
                    st.success("Salvo com sucesso!")
                    # Tenta gravar na aba 'Medidas'
                    conn.create(worksheet="Medidas", data=nova_medida)
st.balloons()
                    st.success("Medida gravada com sucesso!")
except:
                    st.error("Erro ao salvar. Verifique se a planilha está como 'Editor' e se existe a aba 'Medidas'.")
                    st.error("Erro ao salvar. Verifique se a planilha permite edição e se existe uma aba chamada 'Medidas'.")
else:
            st.info("Clique na imagem para marcar.")
            st.info("Clique em uma região da silhueta ao lado para habilitar o formulário de medidas.")

with tab3:
    st.subheader("Histórico")
    st.write("Dados da aba 'Medidas' aparecerão aqui em breve.")
    st.subheader("Acompanhamento de Resultados")
    st.write("Os dados salvos na aba 'Medidas' aparecerão aqui em formato de gráfico em breve.")
