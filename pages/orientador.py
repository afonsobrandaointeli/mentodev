import os
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Token de autenticação
AUTH_TOKEN = os.getenv("AUTH_TOKEN")

# Função para verificar o token
def check_auth(token):
    return token == AUTH_TOKEN

# Título da aplicação
st.title("Avaliação de Artefatos")

# Campo de entrada para o token
token = st.text_input("Insira o token de acesso:", type="password")

# Verificar o token
if check_auth(token):
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
            repo_names.append(doc.to_dict().get('name'))
        return repo_names

    # Função para obter os artefatos da sprint selecionada
    def get_artifacts(repo_name, sprint_name):
        sprint_key = f"{sprint_name}"
        docs = db.collection('reponames').where('name', '==', repo_name).stream()
        for doc in docs:
            data = doc.to_dict()
            sprint_data = data.get(sprint_key, {})
            return sprint_data.get('artefatos', []), doc.id
        return [], None

    # Função para carregar as notas existentes de artefatos
    def load_existing_artifact_scores(repo_doc_id, sprint_name):
        sprint_key = f"{sprint_name}"

        # Obter o documento da coleção
        repo_doc = db.collection('reponames').document(repo_doc_id).get()
        if repo_doc.exists:
            repo_data = repo_doc.to_dict()

            # Verificar se a sprint e artefatos existem
            if sprint_key in repo_data and 'artefatos' in repo_data[sprint_key]:
                return repo_data[sprint_key]['artefatos']
        
        return []

    # Função para salvar as notas e a média na sprint
    def save_artifact_scores(repo_doc_id, sprint_name, artifacts, artifact_scores):
        sprint_key = f"{sprint_name}"

        # Carregar artefatos existentes e as notas previamente atribuídas
        existing_artifacts = load_existing_artifact_scores(repo_doc_id, sprint_name)

        # Atualizar os artefatos com as novas notas, mantendo as anteriores
        updated_artifacts = []
        for artifact in artifacts:
            artifact_name = artifact['nome']
            if artifact_name in artifact_scores:
                # Se o artefato já tem uma nota nova, atualize-a
                artifact['nota'] = artifact_scores[artifact_name]
            else:
                # Caso contrário, mantenha a nota existente, se houver
                existing_artifact = next((a for a in existing_artifacts if a['nome'] == artifact_name), None)
                if existing_artifact and 'nota' in existing_artifact:
                    artifact['nota'] = existing_artifact['nota']
            updated_artifacts.append(artifact)

        # Calcular a média das notas
        total_score = sum(artifact.get('nota', 0) for artifact in updated_artifacts)
        average_score = round(total_score / len(updated_artifacts), 2) if updated_artifacts else 0

        # Preparar os dados para atualização
        updates = {
            f"{sprint_key}.artefatos": updated_artifacts,
            f"{sprint_key}.media_notas": average_score
        }

        # Realizar a atualização no Firestore
        db.collection('reponames').document(repo_doc_id).update(updates)

    # Obter os nomes dos repositórios
    repo_names = get_repo_names()

    # Dropdown para selecionar um repositório e sprint
    selected_repo = st.selectbox("Escolha um repositório:", repo_names)
    select_sprint = st.selectbox("Escolha uma Sprint:", [f"Sprint_{i+1}" for i in range(5)])
    
    st.title(f"Seleção de Artefatos do Repositório {selected_repo} da {select_sprint}")

    # Buscar artefatos do banco de dados
    artifacts_list, repo_doc_id = get_artifacts(selected_repo, select_sprint)
    
    if artifacts_list:
        st.write(f"Artefatos disponíveis na {select_sprint} do repositório {selected_repo}:")

        # Carregar as notas existentes para exibir
        existing_artifacts = load_existing_artifact_scores(repo_doc_id, select_sprint)

        # Seleção de artefatos da sprint para avaliação
        selected_artifacts = []
        artifact_scores = {}
        for i, artifact in enumerate(artifacts_list):
            # Buscar nota existente (se houver)
            existing_artifact = next((a for a in existing_artifacts if a['nome'] == artifact['nome']), None)
            # Conversão do initial_score para float
            initial_score = float(existing_artifact['nota']) if existing_artifact and 'nota' in existing_artifact else 0.0

            if st.checkbox(f"{artifact.get('nome')}: {artifact.get('descricao')}"):
                selected_artifacts.append(artifact)
                artifact_scores[artifact['nome']] = st.number_input(
                    f"Digite a Nota do Artefato {artifact['nome']}:",
                    value=initial_score,  # Exibe a nota existente, se houver, agora como float
                    min_value=0.0,
                    max_value=10.0,
                    step=0.01,
                    key=f"nota_{artifact['nome']}_{i}"  # Chave única para cada número de entrada
                )
        if st.button("Submeter Notas"):
            if selected_artifacts and repo_doc_id:
                save_artifact_scores(repo_doc_id, select_sprint, selected_artifacts, artifact_scores)
                st.success(f"Notas submetidas com sucesso!")
            else:
                st.error("Selecione pelo menos um artefato e atribua uma nota.")
    else:
        st.write(f"Não há artefatos cadastrados na {select_sprint} do repositório {selected_repo}.")
else:
    st.error("Acesso negado. Por favor, insira um token válido.")
