import os
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Token de autenticação
AUTH_TOKEN = os.getenv("AUTH_TOKEN")

# Função para verificar o token
def check_auth(token):
    return token == AUTH_TOKEN

# Inicializar Firebase apenas se ainda não estiver inicializado
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

# Inicializar Firestore
db = firestore.client()

# Streamlit UI
st.title("Seleção de Repositórios e Avaliação")

# Token input
token = st.text_input("Insira o token de acesso:", type="password")

if check_auth(token):
    # Função para obter nomes dos repositórios
    def get_repo_names():
        repo_names = []
        docs = db.collection('reponames').stream()
        for doc in docs:
            repo_names.append(doc.to_dict().get('name'))
        return repo_names

    # Função para obter artefatos de um repositório e sprint selecionado
    def get_artifacts(repo_doc_id, sprint_name):
        sprint_key = f"{sprint_name}"
        doc = db.collection('reponames').document(repo_doc_id).get()
        if doc.exists:
            data = doc.to_dict()
            sprint_data = data.get(sprint_key, {})
            if sprint_data and 'artefatos' in sprint_data:
                return sprint_data.get('artefatos', []), sprint_data.get('media_notas')
        return [], None

   # Função para obter alunos de um repositório
    def get_students(repo_doc_id):
        doc = db.collection('reponames').document(repo_doc_id).get()
        if doc.exists:
            data = doc.to_dict()
            alunos = data.get('alunos', {})
            emails = []
            for aluno_key, aluno_value in alunos.items():
                # Verifica se a chave (aluno_key) contém "@" e é um e-mail válido
                if "@" in aluno_key:
                    emails.append(aluno_key)
                elif isinstance(aluno_value, dict):
                    # Se aluno_value for um dicionário, procura por uma chave que seja um e-mail
                    for key in aluno_value:
                        if "@" in key:
                            emails.append(key)
            return emails
        return []
    # Função para normalizar o e-mail para usar no Firestore
    def normalize_email(email):
        return email.replace('.', '_').replace('@', '_')

    # Função para salvar a nota final do aluno no banco de dados
    def save_student_grade(repo_doc_id, sprint_name, student_email, grade):
        normalized_email = normalize_email(student_email)
        # Atualizar o documento com a nota final do aluno
        db.collection('reponames').document(repo_doc_id).update({
            f"{sprint_name}.alunos.{normalized_email}.nota_final": grade
        })

    # Obter nomes dos repositórios para seleção
    repo_names = get_repo_names()
    selected_repo = st.selectbox("Escolha um repositório:", repo_names)
    
    # Verificar se algum repositório foi selecionado
    if selected_repo:
        # Obter o ID do documento do repositório
        repo_doc_id = None
        docs = db.collection('reponames').where('name', '==', selected_repo).stream()
        for doc in docs:
            repo_doc_id = doc.id
            break

        # Se o repositório foi encontrado
        if repo_doc_id:
            selected_sprint = st.selectbox("Escolha uma Sprint:", [f"Sprint_{i+1}" for i in range(5)])

            # Obter alunos e artefatos
            student_emails = get_students(repo_doc_id)
            selected_student_email = st.selectbox("Escolha um aluno (por e-mail):", student_emails)
            artifacts_list, media_artifacts = get_artifacts(repo_doc_id, selected_sprint)

            if artifacts_list:
                st.subheader(f"Avaliação de Artefatos do Repositório {selected_repo} da {selected_sprint}")

                # Seletor de participação para cada artefato
                artifact_scores = {}
                for i, artifact in enumerate(artifacts_list):
                    participation = st.selectbox(
                        f"Selecione a participação no Artefato {artifact['nome']}:",
                        ["Não Participou", "Abaixo do Esperado", "Dentro do Esperado", "Acima do Esperado"],
                        key=f"participation_{i}"
                    )
                    artifact_scores[artifact['nome']] = {
                        "Não Participou": 0,
                        "Abaixo do Esperado": 3,
                        "Dentro do Esperado": 5,
                        "Acima do Esperado": 9
                    }[participation]

                st.subheader("Avaliação dos Critérios")

                # Seletor de score para cada critério
                criterio_scores = {}
                for i in range(3):
                    criterio = st.selectbox(
                        f"Selecione a avaliação do Critério {i+1}:",
                        [
                            "Sem Evidência - 0",
                            "Insuficiente - 1",
                            "Insuficiente - 2",
                            "Insuficiente - 3",
                            "Básico - 4",
                            "Básico - 5",
                            "Intermediário - 6",
                            "Intermediário - 7",
                            "Intermediário - 8",
                            "Intermediário - 8.5",
                            "Avançado - 9"
                        ],
                        key=f"criterio_{i}"
                    )
                    criterio_scores[i] = float(criterio.split('-')[-1].strip())

                # Calcular a nota final
                if st.button("Calcular Nota Final"):
                    # Média dos Artefatos (do Firestore)
                    media_artefato = media_artifacts if media_artifacts else 0
                    peso_participacao = sum(artifact_scores.values()) / (len(artifact_scores) * 9)  # Normalização para 0-1
                    nota_artefato_final = media_artefato * peso_participacao * 0.4

                    # Notas dos critérios
                    notas_criterios = []
                    demerito_total = 0
                    for score in criterio_scores.values():
                        nota_criterio = score * 0.2
                        if score == 3:
                            demerito_total += 0.5
                        elif score == 0:  # Sem Evidência
                            nota_criterio = 0  # Sem Evidência não gera nota, e também não gera demerito.
                        notas_criterios.append(nota_criterio)

                    nota_criterios_final = sum(notas_criterios)

                    # Mérito (Ir Além) limitado a 1.0
                    ir_alem = min(
                        0.1 * sum(1 for score in artifact_scores.values() if score == 9) + 
                        0.25 * sum(1 for score in criterio_scores.values() if score == 9), 
                        1.0
                    )

                    # Nota Final não pode ser negativa
                    nota_final = max(nota_artefato_final + nota_criterios_final - demerito_total + ir_alem, 0)
                    nota_final = round(nota_final, 2)

                    # Salvar a nota final do aluno no Firestore
                    if selected_student_email:
                        save_student_grade(repo_doc_id, selected_sprint, selected_student_email, nota_final)

                    # Construir tabela de resultados
                    data = {
                        "Critério": ["Artefatos"] + [f"Critério {i+1}" for i in range(3)] + ["Nota Final"],
                        "Nota": [round(nota_artefato_final, 2)] + [round(nota, 2) for nota in notas_criterios] + [nota_final],
                        "Demerito": ["-" if i > 0 else round(demerito_total, 2) for i in range(4)] + ["-"],
                        "Ir Além": ["-" if i > 0 else round(ir_alem, 2) for i in range(4)] + ["-"],
                        "Nota Final": ["-" for _ in range(4)] + [nota_final],
                        "Média Artefatos": [media_artefato] + ["-" for _ in range(3)] + ["-"],
                    }

                    df = pd.DataFrame(data)
                    st.write("Resultados:")
                    st.table(df)

            else:
                st.warning(f"Não há artefatos cadastrados na {selected_sprint} do repositório {selected_repo}.")
        else:
            st.error("Repositório não encontrado.")
else:
    st.error("Acesso negado. Por favor, insira um token válido.")
