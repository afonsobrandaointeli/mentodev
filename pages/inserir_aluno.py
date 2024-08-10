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
st.title("Inserir Alunos em Repositórios")

# Campo de entrada para o token
token = st.text_input("Insira o token de acesso:")

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
            data = doc.to_dict()
            if 'name' in data:
                repo_names.append(data['name'])
        return repo_names

    # Função para validar e-mails
    def is_valid_email(email):
        return email.endswith("@sou.inteli.edu.br")

    # Obter os nomes dos repositórios
    repo_names = get_repo_names()

    # Dropdown para selecionar um repositório
    selected_repo = st.selectbox("Escolha um repositório:", repo_names)

    # Campos de entrada para inserir até 8 alunos
    aluno1 = st.text_input("Aluno 1")
    aluno2 = st.text_input("Aluno 2")
    aluno3 = st.text_input("Aluno 3")
    aluno4 = st.text_input("Aluno 4")
    aluno5 = st.text_input("Aluno 5")
    aluno6 = st.text_input("Aluno 6")
    aluno7 = st.text_input("Aluno 7")
    aluno8 = st.text_input("Aluno 8")

    # Botão para submeter os alunos
    if st.button("Inserir Alunos"):
        alunos = {
            "aluno1": aluno1,
            "aluno2": aluno2,
            "aluno3": aluno3,
            "aluno4": aluno4,
            "aluno5": aluno5,
            "aluno6": aluno6,
            "aluno7": aluno7,
            "aluno8": aluno8
        }
        
        # Validar e-mails
        invalid_emails = [email for email in alunos.values() if email and not is_valid_email(email)]
        
        if invalid_emails:
            st.error("Todos os e-mails inseridos devem ser válidos e conter '@sou.inteli.edu.br'.")
        else:
            # Filtrar alunos vazios
            alunos = {k: v for k, v in alunos.items() if v}
            
            # Adicionar os alunos ao repositório selecionado
            # Encontrar o documento correspondente ao repositório selecionado
            docs = db.collection('reponames').where('name', '==', selected_repo).stream()
            for doc in docs:
                db.collection('reponames').document(doc.id).set({"alunos": alunos}, merge=True)
            st.success(f"Alunos inseridos no repositório '{selected_repo}' com sucesso!")

    # Exibir o repositório selecionado
    st.write(f"Repositório selecionado: {selected_repo}")
else:
    st.error("Acesso negado. Por favor, insira um token válido.")