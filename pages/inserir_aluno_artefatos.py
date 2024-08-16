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
            data = doc.to_dict()
            if 'name' in data:
                repo_names.append(data['name'])
        return repo_names

    # Função para obter os artefatos existentes em uma Sprint
    def get_existing_artifacts(repo_doc_id, sprint_name):
        doc = db.collection('reponames').document(repo_doc_id).get()
        if doc.exists:
            data = doc.to_dict()
            sprint_data = data.get(sprint_name, {})
            return sprint_data.get('artefatos', [])
        return []

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
            
            # Encontrar o documento correspondente ao repositório selecionado
            docs = db.collection('reponames').where('name', '==', selected_repo).stream()
            for doc in docs:
                db.collection('reponames').document(doc.id).set({"alunos": alunos}, merge=True)
            st.success(f"Alunos inseridos no repositório '{selected_repo}' com sucesso!")

    # Exibir o repositório selecionado
    st.write(f"Repositório selecionado: {selected_repo}")
    
    st.title("Inserir Artefatos")

    # Inicialize a sessão para armazenar os artefatos e suas descrições
    if 'artifacts' not in st.session_state:
        st.session_state.artifacts = []
    if 'descriptions' not in st.session_state:
        st.session_state.descriptions = []

    # Função para adicionar uma nova caixa de texto para o artefato e sua descrição
    def add_artifact_box():
        st.session_state.artifacts.append("")
        st.session_state.descriptions.append("")

    # Função para remover um artefato e sua descrição
    def remove_artifact(index):
        st.session_state.artifacts.pop(index)
        st.session_state.descriptions.pop(index)

    # Botão para adicionar novas caixas de texto
    if st.button("Adicionar Artefato"):
        add_artifact_box()

    # Exibe todas as caixas de texto para os artefatos e suas descrições
    indexes_to_remove = []
    for i, box in enumerate(st.session_state.artifacts):
        cols = st.columns([3, 2, 1])  # Configura três colunas: uma para o nome, outra para a descrição e outra para o botão de remoção
        with cols[0]:
            st.session_state.artifacts[i] = st.text_input(f"Nome do Artefato {i+1}", value=box, key=f"artifact_{i}")
        with cols[1]:
            st.session_state.descriptions[i] = st.text_area(f"Descrição do Artefato {i+1}", value=st.session_state.descriptions[i], key=f"description_{i}")
        with cols[2]:
            if st.button("Remover", key=f"remove_{i}"):
                indexes_to_remove.append(i)

    # Remova os itens marcados para remoção
    if indexes_to_remove:
        for i in sorted(indexes_to_remove, reverse=True):
            remove_artifact(i)

    # Exibe a lista dos artefatos e suas descrições antes do envio
    st.subheader("Artefatos a serem submetidos:")
    for i, (artifact, description) in enumerate(zip(st.session_state.artifacts, st.session_state.descriptions)):
        if artifact:
            st.write(f"**Artefato {i+1}:** {artifact}")
            st.write(f"**Descrição:** {description}")

    # Seleção da Sprint
    sprint_names = [f"Sprint_{i+1}" for i in range(5)]
    selected_sprint = st.selectbox("Escolha uma Sprint:", sprint_names)
    
    # Botão para submeter os artefatos e suas descrições
    if st.button("Submeter Artefatos"):
        artifacts_data = [{"nome": artifact, "descricao": description} for artifact, description in zip(st.session_state.artifacts, st.session_state.descriptions) if artifact]
        
        if not artifacts_data:
            st.error("Por favor, adicione pelo menos um artefato com descrição antes de submeter.")
        else:
            docs = db.collection('reponames').where('name', '==', selected_repo).stream()
            for doc in docs:
                repo_doc_id = doc.id
                
                # Obter os artefatos existentes e adicionar os novos
                existing_artifacts = get_existing_artifacts(repo_doc_id, selected_sprint)
                combined_artifacts = existing_artifacts + artifacts_data
                
                # Atualizar o documento com a lista combinada de artefatos dentro da sprint selecionada
                sprint_key = f"{selected_sprint}"
                db.collection('reponames').document(repo_doc_id).set({sprint_key: {"artefatos": combined_artifacts}}, merge=True)
            st.success(f"Artefatos inseridos na '{selected_sprint}' do repositório '{selected_repo}' com sucesso!")

    # Seção separada para remover artefatos
    st.title("Remover Artefatos")

    if selected_sprint:
        docs = db.collection('reponames').where('name', '==', selected_repo).stream()
        for doc in docs:
            repo_doc_id = doc.id
            existing_artifacts = get_existing_artifacts(repo_doc_id, selected_sprint)

            if existing_artifacts:
                st.subheader(f"Artefatos na {selected_sprint}:")
                artifacts_to_remove = st.multiselect(
                    "Selecione os artefatos que deseja remover:",
                    [f"{artifact['nome']}: {artifact['descricao']}" for artifact in existing_artifacts]
                )

                if st.button("Remover Artefatos Selecionados"):
                    updated_artifacts = [
                        artifact for artifact in existing_artifacts
                        if f"{artifact['nome']}: {artifact['descricao']}" not in artifacts_to_remove
                    ]
                    
                    # Atualizar a lista de artefatos no Firestore
                    sprint_key = f"{selected_sprint}"
                    db.collection('reponames').document(repo_doc_id).set({sprint_key: {"artefatos": updated_artifacts}}, merge=True)
                    st.success("Artefatos removidos com sucesso!")
            else:
                st.write(f"Não há artefatos cadastrados na {selected_sprint}.")
else:
    st.error("Acesso negado. Por favor, insira um token válido.")
