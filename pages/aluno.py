import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializar o Firebase apenas se ainda não estiver inicializado
if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": os.getenv("TYPE"),
        "project_id": os.getenv("PROJECT_ID"),
        "private_key_id": os.getenv("PRIVATE_KEY_ID"),
        "private_key": os.getenv("PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.getenv("CLIENT_EMAIL"),
        "client_id": os.getenv("CLIENT_ID"),
        "auth_uri": os.getenv("AUTH_URI"),
        "token_uri": os.getenv("TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL")
    })
    firebase_admin.initialize_app(cred)

# Inicializar o Firestore
db = firestore.client()

# Função para obter os nomes da coleção "reponames"
def get_repo_names():
    repo_names = []
    docs = db.collection('reponames').stream()
    for doc in docs:
        data = doc.to_dict()
        if 'name' in data:
            repo_names.append(data['name'])
    return repo_names

# Função para obter os alunos de um repositório (somente e-mails)
def get_alunos_by_repo(repo_name):
    alunos = []
    docs = db.collection('reponames').where('name', '==', repo_name).stream()
    for doc in docs:
        data = doc.to_dict()
        if 'alunos' in data:
            # Verifica se 'alunos' é um dicionário ou lista
            if isinstance(data['alunos'], dict):
                for key, value in data['alunos'].items():
                    # Verifica se o valor é um e-mail (contém "@")
                    if "@" in value:
                        alunos.append(value)
                    elif isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if "@" in sub_value:
                                alunos.append(sub_value)
            elif isinstance(data['alunos'], list):
                for aluno in data['alunos']:
                    if "@" in aluno:
                        alunos.append(aluno)
    return alunos


# Função para obter artefatos de um repositório e sprint selecionado
def get_artifacts(repo_doc_id, sprint_name):
    sprint_key = f"{sprint_name}"
    doc = db.collection('reponames').document(repo_doc_id).get()
    if doc.exists:
        data = doc.to_dict()
        sprint_data = data.get(sprint_key, {})
        if sprint_data and 'artefatos' in sprint_data:
            return sprint_data.get('artefatos', [])
    return []

# Função para salvar a avaliação no banco de dados
def salvar_avaliacao(repo_name, aluno, sprint, dailys, criterio_1, criterio_2, avaliacao_artefatos):
    total_dailys = len(dailys)
    sim_dailys = sum([1 for v in dailys.values() if v == "Sim"])
    perc_dailys = (sim_dailys / total_dailys) * 100 if total_dailys > 0 else 0
    
    total_criterio_1 = len(criterio_1)
    sim_criterio_1 = sum([1 for v in criterio_1.values() if v == "Sim"])
    perc_criterio_1 = (sim_criterio_1 / total_criterio_1) * 100 if total_criterio_1 > 0 else 0
    
    total_criterio_2 = len(criterio_2)
    sim_criterio_2 = sum([1 for v in criterio_2.values() if v == "Sim"])
    perc_criterio_2 = (sim_criterio_2 / total_criterio_2) * 100 if total_criterio_2 > 0 else 0

    docs = db.collection('reponames').where('name', '==', repo_name).stream()
    for doc in docs:
        repo_doc_id = doc.id
        db.collection('reponames').document(repo_doc_id).set({
            f"sprints.{sprint}.alunos.{aluno}": {
                "percent_dailys": perc_dailys,
                "percent_criterio_1": perc_criterio_1,
                "percent_criterio_2": perc_criterio_2,
                "avaliacao_artefatos": avaliacao_artefatos
            }
        }, merge=True)

# Função para gerar a tabela de dailys, critérios e avaliação de artefatos
def exibir_tabela(aluno, df, dailys, criterio_1, criterio_2, avaliacao_artefatos, lista_artefatos):
    opcoes_sim_nao = ["Sim", "Não"]
    avaliacao_opcoes = ["Não Participou", "Abaixo do Esperado", "Dentro do Esperado", "Acima do Esperado"]

    # Exibir Participação na Daily
    st.subheader("Participação na Daily")
    for i in range(len(df)):
        data = df.at[i, 'Data']

        # Daily
        valor_daily = dailys.get(i, "")
        index_daily = opcoes_sim_nao.index(valor_daily) if valor_daily in opcoes_sim_nao else 0
        dailys[i] = st.selectbox(f"{data} - {aluno} (Daily)", opcoes_sim_nao, index=index_daily, key=f"daily_{aluno}_{i}")

    # Exibir Participação no Critério 1
    st.subheader("Participação no Critério 1")
    for i in range(len(df)):
        data = df.at[i, 'Data']

        # Critério 1
        valor_criterio_1 = criterio_1.get(i, "")
        index_criterio_1 = opcoes_sim_nao.index(valor_criterio_1) if valor_criterio_1 in opcoes_sim_nao else 0
        criterio_1[i] = st.selectbox(f"{data} - {aluno} (Critério 1)", opcoes_sim_nao, index=index_criterio_1, key=f"criterio1_{aluno}_{i}")

    # Exibir Participação no Critério 2
    st.subheader("Participação no Critério 2")
    for i in range(len(df)):
        data = df.at[i, 'Data']

        # Critério 2
        valor_criterio_2 = criterio_2.get(i, "")
        index_criterio_2 = opcoes_sim_nao.index(valor_criterio_2) if valor_criterio_2 in opcoes_sim_nao else 0
        criterio_2[i] = st.selectbox(f"{data} - {aluno} (Critério 2)", opcoes_sim_nao, index=index_criterio_2, key=f"criterio2_{aluno}_{i}")

    # Exibir avaliação dos artefatos
    st.subheader(f"Avaliação dos Artefatos para {aluno}")
    if lista_artefatos:
        for artefato in lista_artefatos:
            artefato_nome = artefato['nome'] if isinstance(artefato, dict) and 'nome' in artefato else str(artefato)

            avaliacao = avaliacao_artefatos.get(artefato_nome, "")
            index_avaliacao = avaliacao_opcoes.index(avaliacao) if avaliacao in avaliacao_opcoes else 0
            avaliacao_artefatos[artefato_nome] = st.selectbox(f"Avaliação para o artefato {artefato_nome}", avaliacao_opcoes, index=index_avaliacao, key=f"avaliacao_{artefato_nome}_{aluno}")
    else:
        st.warning(f"Nenhum artefato encontrado para essa sprint.")

# Função para gerar as datas (pulando finais de semana)
def gerar_datas(inicio_sprint):
    hoje = inicio_sprint
    datas = [{"Data": (hoje + timedelta(days=i)).strftime("%d/%m/%Y")} for i in range(14) if (hoje + timedelta(days=i)).weekday() < 5]
    return pd.DataFrame(datas)

# Obter os nomes dos repositórios
repo_names = get_repo_names()
# Selecionar o repositório
selected_repo = st.selectbox("Escolha um repositório:", repo_names)
if selected_repo:
    alunos = get_alunos_by_repo(selected_repo)

    if alunos:
        # Selecionar o aluno (agora pelo e-mail)
        aluno_selecionado = st.selectbox("Escolha um aluno para avaliar:", alunos)

        # Selecionar a sprint
        sprint = st.selectbox("Escolha uma Sprint:", [f"Sprint_{i+1}" for i in range(5)])

        # Obter o ID do repositório
        docs = db.collection('reponames').where('name', '==', selected_repo).stream()
        repo_doc_id = None
        for doc in docs:
            repo_doc_id = doc.id
            break

        # Obter artefatos do repositório e sprint
        lista_artefatos = get_artifacts(repo_doc_id, sprint)

        # Definir o início da sprint
        inicio_sprint = datetime.now() + timedelta(days=(int(sprint.split('_')[-1]) - 1) * 14)

        # Gerar as datas para avaliação (considerando o início da sprint)
        df = gerar_datas(inicio_sprint)

        # Inicializar os valores das dailys, critérios e avaliação de artefatos se não estiverem no session_state
        if aluno_selecionado not in st.session_state:
            st.session_state[aluno_selecionado] = {
                'dailys': {}, 
                'criterio_1': {}, 
                'criterio_2': {},
                'avaliacao_artefatos': {str(artefato['nome']) if isinstance(artefato, dict) and 'nome' in artefato else str(artefato): "" for artefato in lista_artefatos if isinstance(artefato, (str, dict))}
            }

        dailys = st.session_state[aluno_selecionado]['dailys']
        criterio_1 = st.session_state[aluno_selecionado]['criterio_1']
        criterio_2 = st.session_state[aluno_selecionado]['criterio_2']
        avaliacao_artefatos = st.session_state[aluno_selecionado]['avaliacao_artefatos']

        # Exibir a tabela para avaliação
        exibir_tabela(aluno_selecionado, df, dailys, criterio_1, criterio_2, avaliacao_artefatos, lista_artefatos)

        # Botão para salvar a avaliação
        if st.button("Salvar Avaliação"):
            salvar_avaliacao(selected_repo, aluno_selecionado, sprint, dailys, criterio_1, criterio_2, avaliacao_artefatos)
            st.success(f"Avaliação de {aluno_selecionado} salva com sucesso na {sprint}!")

    else:
        st.warning("Nenhum aluno encontrado para este repositório.")
else:
    st.write("Selecione um repositório.")


