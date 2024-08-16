import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os
import json
import os

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Token de autenticação
AUTH_TOKEN = os.getenv("AUTH_TOKEN")

def check_auth(token):
    return token == AUTH_TOKEN

token = st.text_input("Insira o token de acesso:", type="password")

if check_auth(token):
# Criar dicionário de credenciais a partir das variáveis de ambiente
    cred_data = {
        "type": os.getenv("TYPE"),
        "project_id": os.getenv("PROJECT_ID"),
        "private_key_id": os.getenv("PRIVATE_KEY_ID"),
        "private_key": os.getenv("PRIVATE_KEY").replace('\\n', '\n'),
        "client_email": os.getenv("CLIENT_EMAIL"),
        "client_id": os.getenv("CLIENT_ID"),
        "auth_uri": os.getenv("AUTH_URI"),
        "token_uri": os.getenv("TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL")
    }

    # Inicializar Firebase apenas se ainda não estiver inicializado
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(cred_data)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Erro ao configurar Firebase: {e}")
            st.stop()

    # Conectar ao Firestore
    db = firestore.client()

    st.title("Navegador de Dados do Firebase")

    # Função para buscar dados do Firestore
    def fetch_data(collection_name):
        try:
            docs = db.collection(collection_name).stream()
            data = [doc.to_dict() for doc in docs]
            return data
        except Exception as e:
            st.error(f"Erro ao buscar dados: {e}")
            return []

    # Selecionar coleção para visualizar
    collection_name = st.text_input("Nome da Coleção", "reponames")

    if st.button("Buscar Dados"):
        if collection_name:
            data = fetch_data(collection_name)
            if data:
                st.write(data)
            else:
                st.write("Nenhum dado encontrado ou coleção não existe.")
        else:
            st.error("Por favor, insira o nome da coleção.")
else:
    st.error("Acesso negado. Por favor, insira um token válido.")