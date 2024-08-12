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
st.title("Seleção de Repositórios")

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

    # Obter os nomes dos repositórios
    repo_names = get_repo_names()

    # Dropdown para selecionar um repositório e sprint
    selected_repo = st.selectbox("Escolha um repositório:", repo_names)
    select_sprint = st.selectbox("Escolha uma Sprint:", ["Sprint 1", "Sprint 2", "Sprint 3", "Sprint 4", "Sprint 5"])
    
    st.title(f"Seleção de Artefatos do Repositório{selected_repo} da {select_sprint}")
    # Seleção de artefatos da sprint
    def select_artifacts():
        artifacts_list = ['Artefato 1', 'Artefato 2', 'Artefato 3', 'Artefato 4', 'Artefato 5']
        selected_artifacts = []
        for artifact in artifacts_list:
            if st.checkbox(artifact):
                selected_artifacts.append(artifact)
        return selected_artifacts

    selected_artifacts = select_artifacts()

    st.write(f"Você selecionou os Artefatos: {', '.join(selected_artifacts)}")
    artifact_radio = st.radio("Deseja avaliar os artefatos selecionados?", ("Sim", "Não"))
    try:    
            if artifact_radio == "Sim":
                artifact_scores = {}
                for artifact in selected_artifacts:
                    artifact_scores[artifact] = int(st.number_input(f"Digite a Nota do Artefato {artifact}:"))
                average = round(sum(artifact_scores.values()) / len(selected_artifacts), 2)
                st.write(f"A média de notas dos Artefato foi {average}")
            else:
                st.write("Avaliação dos artefatos não realizada")
    except:
            st.write("Não é possível realizar a avaliação sem ao menos um artefato selecionado")
else:
    st.error("Acesso negado. Por favor, insira um token válido.")
