import os
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

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

# Inicializar Firestore
db = firestore.client()

# Função para normalizar o e-mail, substituindo "." e "@" por "_"
def normalize_email(email):
    return email.replace('.', '_').replace('@', '_')

# Função para obter nomes dos repositórios
def get_repo_names():
    repo_names = []
    docs = db.collection('reponames').stream()
    for doc in docs:
        repo_names.append(doc.to_dict().get('name'))
    return repo_names

# Função para obter alunos de um repositório
def get_students(repo_doc_id):
    doc = db.collection('reponames').document(repo_doc_id).get()
    if doc.exists:
        data = doc.to_dict()
        alunos = data.get('alunos', {})
        emails = []
        for aluno_key, aluno_value in alunos.items():
            if isinstance(aluno_value, str):  # Se for uma string (e-mail diretamente)
                emails.append(aluno_value)
            elif isinstance(aluno_value, dict):  # Se for um dicionário, verificamos as chaves
                for key in aluno_value:
                    if "@" in key:
                        emails.append(key)
        return emails
    return []

# Função para obter avaliações de um aluno de uma sprint (sem normalizar e-mail)
def get_avaliacao_aluno(repo_doc_id, sprint_name, student_email):
    doc = db.collection('reponames').document(repo_doc_id).get()
    if doc.exists:
        data = doc.to_dict()
        # Buscar os dados do aluno com o e-mail diretamente
        sprint_data = data.get(f'sprints.{sprint_name}.alunos.{student_email}', {})
        if sprint_data:
            return sprint_data
    return {}

# Função para salvar a nota final do aluno no Firestore (usando um campo regularizado)
def save_student_grade(repo_doc_id, sprint_name, student_email, grade):
    normalized_email = normalize_email(student_email)
    # Atualizar o documento criando um campo regularizado para as notas
    db.collection('reponames').document(repo_doc_id).update({
        f"sprints.{sprint_name}.alunos_regularizados.{normalized_email}.nota_final": grade
    })

# Função para calcular a média dos artefatos
def calcular_media_artefatos(avaliacao_artefatos):
    if not avaliacao_artefatos:
        return 0
    total_score = 0
    for avaliacao in avaliacao_artefatos.values():
        score = {"Não Participou": 0, "Abaixo do Esperado": 3, "Dentro do Esperado": 5, "Acima do Esperado": 9}[avaliacao]
        total_score += score
    max_score = len(avaliacao_artefatos) * 9
    return total_score / max_score if max_score > 0 else 0

# Função para calcular a nota final
def calcular_nota_final(avaliacao_aluno):
    media_artefato = calcular_media_artefatos(avaliacao_aluno.get('avaliacao_artefatos', {})) * 0.4

    def calcular_pontuacao_regua(porcentagem):
        if porcentagem == 0:
            return 0
        elif 1 <= porcentagem <= 10:
            return 1
        elif 11 <= porcentagem <= 25:
            return 2
        elif 26 <= porcentagem <= 40:
            return 3
        elif 41 <= porcentagem <= 50:
            return 4
        elif 51 <= porcentagem <= 60:
            return 5
        elif 61 <= porcentagem <= 70:
            return 6
        elif 71 <= porcentagem <= 80:
            return 7
        elif 81 <= porcentagem <= 85:
            return 8
        elif 86 <= porcentagem <= 90:
            return 8.5
        elif 91 <= porcentagem <= 100:
            return 9
        return 0

    perc_criterio_1 = avaliacao_aluno.get('percent_criterio_1', 0)
    perc_criterio_2 = avaliacao_aluno.get('percent_criterio_2', 0)
    perc_dailys = avaliacao_aluno.get('percent_dailys', 0)

    nota_criterio_1 = calcular_pontuacao_regua(perc_criterio_1) * 0.2
    nota_criterio_2 = calcular_pontuacao_regua(perc_criterio_2) * 0.2
    nota_dailys = calcular_pontuacao_regua(perc_dailys) * 0.2

    demerito = 0
    if calcular_pontuacao_regua(perc_criterio_1) == 3:
        demerito += 0.5
    if calcular_pontuacao_regua(perc_criterio_2) == 3:
        demerito += 0.5

    ir_alem = min(
        0.1 * sum(1 for score in avaliacao_aluno.get('avaliacao_artefatos', {}).values() if score == "Acima do Esperado") + 
        0.25 * (1 if calcular_pontuacao_regua(perc_criterio_1) == 9 else 0) + 
        0.25 * (1 if calcular_pontuacao_regua(perc_criterio_2) == 9 else 0), 
        1.0
    )

    nota_final = max(media_artefato + nota_criterio_1 + nota_criterio_2 + nota_dailys - demerito + ir_alem, 0)
    return round(nota_final, 2)

# Obter os repositórios e mostrar o seletor
repo_names = get_repo_names()
selected_repo = st.selectbox("Escolha um repositório:", repo_names)

# Verificar se algum repositório foi selecionado
if selected_repo:
    repo_doc_id = None
    docs = db.collection('reponames').where('name', '==', selected_repo).stream()
    for doc in docs:
        repo_doc_id = doc.id
        break

    if repo_doc_id:
        selected_sprint = st.selectbox("Escolha uma Sprint:", [f"Sprint_{i+1}" for i in range(5)])
        student_emails = get_students(repo_doc_id)

        if student_emails:
            selected_student_email = st.selectbox("Escolha um aluno (por e-mail):", student_emails)
            avaliacao_aluno = get_avaliacao_aluno(repo_doc_id, selected_sprint, selected_student_email)

            if avaliacao_aluno:
                nota_final = calcular_nota_final(avaliacao_aluno)
                media_artefato = calcular_media_artefatos(avaliacao_aluno.get('avaliacao_artefatos', {}))

                # Adicionar artefatos à tabela
                artefatos_avaliados = avaliacao_aluno.get('avaliacao_artefatos', {})
                artefato_data = {
                    "Artefato": [],
                    "Score": []
                }

                for artefato, avaliacao in artefatos_avaliados.items():
                    artefato_data["Artefato"].append(artefato)
                    artefato_data["Score"].append(avaliacao)

                artefato_df = pd.DataFrame(artefato_data)

                # Exibir artefatos
                st.subheader("Avaliação de Artefatos:")
                st.table(artefato_df)

                # Criar DataFrame para exibir todas
                                # Criar DataFrame para exibir todas as informações na tabela
                data = {
                    "Categoria": ["Média de Artefatos", "Participação nas Dailys", "Critério 1", "Critério 2", "Nota Final"],
                    "Avaliação": [
                        f"{round(media_artefato * 100, 2)}%", 
                        f"{avaliacao_aluno.get('percent_dailys', 0)}%", 
                        f"{avaliacao_aluno.get('percent_criterio_1', 0)}%", 
                        f"{avaliacao_aluno.get('percent_criterio_2', 0)}%", 
                        f"{nota_final}"
                    ]
                }

                df = pd.DataFrame(data)
                st.subheader("Resumo da Avaliação:")
                st.write(df)

                # Mostrar a nota final e a opção de salvar abaixo da tabela
                if st.button("Salvar Nota Final"):
                    save_student_grade(repo_doc_id, selected_sprint, selected_student_email, nota_final)
                    st.success(f"Nota final de {nota_final} salva com sucesso para o aluno {selected_student_email}.")

            else:
                st.warning(f"Não há avaliações cadastradas para {selected_student_email} na {selected_sprint}.")
        else:
            st.warning("Nenhum aluno encontrado para este repositório.")

