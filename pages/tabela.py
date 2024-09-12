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
st.title("Seleção de Repositórios e Avaliação Automática")

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

    # Função para obter avaliações de um aluno de uma sprint
    def get_avaliacao_aluno(repo_doc_id, sprint_name, student_email):
        doc = db.collection('reponames').document(repo_doc_id).get()
        if doc.exists:
            data = doc.to_dict()
            sprint_data = data.get(f'sprints.{sprint_name}.alunos.{student_email}', {})
            return sprint_data
        return {}

    # Função para obter artefatos de uma sprint e a média geral de notas
    def get_artifacts(repo_doc_id, sprint_name):
        doc = db.collection('reponames').document(repo_doc_id).get()
        if doc.exists:
            data = doc.to_dict()
            artifacts = data.get(f'sprints.{sprint_name}.artefatos', {})
            media_notas = data.get(f'sprints.{sprint_name}.media_notas', 0)
            return artifacts, media_notas
        return {}, 0

    # Função para calcular a média dos artefatos com base na régua de avaliação
    def calcular_media_artefatos(avaliacao_artefatos):
        if not avaliacao_artefatos:
            return 0
        # Inicializar os valores das categorias
        percent_abaixo = 0
        percent_dentro = 0
        percent_acima = 0
        percent_nao_participou = 0

        # Calcular os percentuais de cada critério
        for artefato_key, artefato in avaliacao_artefatos.items():
            if artefato == "Abaixo do Esperado":
                percent_abaixo += 1
            elif artefato == "Dentro do Esperado":
                percent_dentro += 1
            elif artefato == "Acima do Esperado":
                percent_acima += 1
            elif artefato == "Não Participou":
                percent_nao_participou += 1

        # Converter contagens para percentuais
        total_artefatos = len(avaliacao_artefatos)
        
        if total_artefatos > 0:
            percent_abaixo = percent_abaixo / total_artefatos
            percent_dentro = percent_dentro / total_artefatos
            percent_acima = percent_acima / total_artefatos
            percent_nao_participou = percent_nao_participou / total_artefatos
        else:
            return 0

        # Fórmula adaptada (ponderação dos critérios)
        nota_artefato = (5 * percent_abaixo) + (9 * percent_dentro) + (10 * percent_acima)

        # Se o aluno "Não Participou", aplicar o desconto (1 - percentual de não participação)
        if percent_nao_participou > 0:
            nota_artefato *= (1 - percent_nao_participou)
        # Ajuste final: se a nota for exatamente 10, retornar 9
        if nota_artefato == 10:
            return 9
        return round(nota_artefato, 2)


    # Função para calcular a pontuação dos critérios com base nas porcentagens
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

    def calcular_nota_final(avaliacao_aluno, media_geral):
        # 1. Calculando a média dos artefatos com a nova função corrigida
        media_artefato = calcular_media_artefatos(avaliacao_aluno.get('avaliacao_artefatos', {})) * 0.4

        # 2. Calculando as notas dos critérios e dailys com peso 0.2 cada
        perc_criterio_1 = avaliacao_aluno.get('percent_criterio_1', 0)
        perc_criterio_2 = avaliacao_aluno.get('percent_criterio_2', 0)
        perc_dailys = avaliacao_aluno.get('percent_dailys', 0)

        nota_criterio_1 = calcular_pontuacao_regua(perc_criterio_1) * 0.2
        nota_criterio_2 = calcular_pontuacao_regua(perc_criterio_2) * 0.2
        nota_dailys = calcular_pontuacao_regua(perc_dailys) * 0.2

        # 3. Demérito: penalização para critérios 
        demerito = 0

        if (calcular_pontuacao_regua(perc_criterio_1) <= 7) and (calcular_pontuacao_regua(perc_criterio_1) > 4):
            demerito += 0.25 * nota_criterio_1
        elif (calcular_pontuacao_regua(perc_criterio_1) <= 4) and (calcular_pontuacao_regua(perc_criterio_1) > 0):
            demerito += 0.5 * nota_criterio_1

        if (calcular_pontuacao_regua(perc_criterio_2) <= 7) and (calcular_pontuacao_regua(perc_criterio_2) > 4):
            demerito += 0.25 * nota_criterio_2
        elif (calcular_pontuacao_regua(perc_criterio_2) <= 4) and (calcular_pontuacao_regua(perc_criterio_2) > 0):
            demerito += 0.5 * nota_criterio_2

        if (calcular_pontuacao_regua(perc_dailys) <= 7) and (calcular_pontuacao_regua(perc_dailys) > 4):
            demerito += 0.25 * nota_dailys
        elif (calcular_pontuacao_regua(perc_dailys) <= 4) and (calcular_pontuacao_regua(perc_dailys) > 0):
            demerito += 0.5 * nota_dailys

        # 4. "Ir Além" - aplicando a regra para critérios/dailys e artefatos "Acima do Esperado"
        ir_alem_criterios_bonus = 0
        if 91 <= perc_criterio_1 <= 100:
            ir_alem_criterios_bonus += 0.1
        if 91 <= perc_criterio_2 <= 100:
            ir_alem_criterios_bonus += 0.1
        if 91 <= perc_dailys <= 100:
            ir_alem_criterios_bonus += 0.1

        num_acima_esperado = sum(1 for score in avaliacao_aluno.get('avaliacao_artefatos', {}).values() if score == "Acima do Esperado")

        if num_acima_esperado == 1:
            ir_alem_artefatos_bonus = 0.1
        elif num_acima_esperado == 2:
            ir_alem_artefatos_bonus = 0.25
        elif num_acima_esperado >= 3:
            ir_alem_artefatos_bonus = 0.5
        else:
            ir_alem_artefatos_bonus = 0

        # Garantir que o bônus total de "Ir Além" não ultrapasse 1.0
        ir_alem = min(ir_alem_criterios_bonus + ir_alem_artefatos_bonus, 1.0)

        # 5. Calculando a nota final
        nota_final = max(media_artefato + nota_criterio_1 + nota_criterio_2 + nota_dailys - demerito + ir_alem, 0)

        return round(nota_final, 2), demerito, ir_alem

    # Lista para armazenar o resumo final de alunos e notas
    resumo_final = []
    # Obter os repositórios e mostrar o seletor
    repo_names = get_repo_names()
    selected_repo = st.selectbox("Escolha um repositório:", repo_names)

    # Lista para armazenar o resumo final de alunos e notas
    if selected_repo:
        repo_doc_id = None 
        docs = db.collection('reponames').where('name', '==', selected_repo).stream()
        for doc in docs:
            repo_doc_id = doc.id
            break

    if repo_doc_id:
        selected_sprint = st.selectbox("Escolha uma Sprint:", [f"Sprint_{i+1}" for i in range(5)])
        
        # Obter os alunos e ordenar em ordem alfabética
        student_emails = sorted(get_alunos_by_repo(repo_name=selected_repo))
        
        artifacts, media_geral = get_artifacts(repo_doc_id, selected_sprint)

        if student_emails:
            for student_email in student_emails:
                avaliacao_aluno = get_avaliacao_aluno(repo_doc_id, selected_sprint, student_email)

                if avaliacao_aluno:
                    # Calcular as notas e os valores de mérito e demerito
                    nota_final, demerito, ir_alem = calcular_nota_final(avaliacao_aluno, media_geral)
                    media_artefato = calcular_media_artefatos(avaliacao_aluno.get('avaliacao_artefatos', {}))
                    
                    # Separador visual para cada aluno
                    st.markdown("---")
                    st.subheader(f"Avaliação de {student_email}")
                    
                    # Exibir as informações em uma estrutura clara com caixas de informação
                    st.info(f"**Nota Final:** {nota_final}")
                    st.write(f"**Demérito:** {demerito:.2f}")
                    st.write(f"**Mérito:** {ir_alem:.2f}")
                    
                    # Criar DataFrame para exibir todas as informações de avaliação
                    data = {
                        "Categoria": ["Média de Artefatos", "Participação nas Dailys", "Critério 1", "Critério 2"],
                        "Avaliação": [
                            f"{round(media_artefato, 2)}",  # Média de artefatos calculada
                            f"{avaliacao_aluno.get('percent_dailys', 0)}%",  # Participação nas Dailys
                            f"{avaliacao_aluno.get('percent_criterio_1', 0)}%",  # Participação Critério 1
                            f"{avaliacao_aluno.get('percent_criterio_2', 0)}%"  # Participação Critério 2
                        ]
                    }

                    # Exibir o DataFrame como tabela no Streamlit
                    df = pd.DataFrame(data)
                    st.table(df)
                    
                    # Exibir avaliação detalhada por artefato com descrições
                    st.subheader("Avaliação Detalhada por Artefato")
                    if avaliacao_aluno.get('avaliacao_artefatos'):
                        for artefato, avaliacao in avaliacao_aluno.get('avaliacao_artefatos').items():
                            st.markdown(f"**{artefato}:** {avaliacao}")
                    else:
                        st.write("Nenhuma avaliação de artefato disponível.")
                        
                    # Adicionar a nota ao resumo final para exibir depois
                    resumo_final.append({"Aluno": student_email, "Nota Final": nota_final})
                    
                else:
                    st.warning(f"Não há avaliações cadastradas para {student_email} na {selected_sprint}.")
        else:
            st.warning("Nenhum aluno encontrado para este repositório.")
    else:
        st.error("Repositório não encontrado.")
            
            # Exibir o resumo final de alunos e notas
    if resumo_final:
            st.markdown("---")
            st.subheader("Resumo Final de Alunos e Notas Finais")
            resumo_df = pd.DataFrame(resumo_final)
            st.write(resumo_df)
else:
    st.error("Acesso negado. Por favor, insira um token válido.")

                        
