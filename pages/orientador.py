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

    # Dropdown para selecionar um repositório
    selected_repo = st.selectbox("Escolha um repositório:", repo_names)

    # Exibir o repositório selecionado
    st.write(f"Você selecionou: {selected_repo}")
else:
    st.error("Acesso negado. Por favor, insira um token válido.")