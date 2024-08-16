import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd

class AlunoRepository:
    def __init__(self):
        load_dotenv()

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

        self.db = firestore.client()

    def get_repo_names(self):
        repo_names = []
        docs = self.db.collection('reponames').stream()
        for doc in docs:
            repo_names.append(doc.to_dict().get('name'))
        return repo_names

    def get_alunos_by_repo(self, repo_name):
        alunos = {}
        docs = self.db.collection('reponames').where('name', '==', repo_name).stream()
        
        for doc in docs:
            data = doc.to_dict()
            if 'alunos' in data:
                alunos_data = data['alunos']
                
                # Converte a lista de tuplas para um dicionário
                for aluno_key, aluno_email in alunos_data.items():
                    alunos[aluno_key] = aluno_email
        return alunos

    def carrregar_dailys(self, repo_name):
        dailys = {}
        docs = self.db.collection('reponames').where('name', '==', repo_name).stream()

        # Itera sobre todos os documentos retornados
        for doc in docs:
            data = doc.to_dict()
            if 'alunos' in data:
                # Itera sobre cada aluno no documento
                for aluno_key, aluno_data in data['alunos'].items():
                    if 'dailys' in aluno_data:
                        # Itera sobre cada registro de daily do aluno
                        for daily in aluno_data['dailys']:
                            # Busca o status com base no email do aluno no dicionário daily
                            status = daily.get(aluno_key, 'Não encontrado')
                            date = daily['Data']
                            if date not in dailys:
                                dailys[date] = {}
                            # Adiciona ou atualiza o status do aluno para essa data
                            dailys[date][aluno_key] = status

        # Converte o dicionário em uma lista de dicionários, um para cada data
        dailys_list = []

        for date in sorted(dailys.keys()):
            daily_entry = {'Data': date}
            for aluno_key in dailys[date].keys():
                daily_entry[aluno_key] = dailys[date][aluno_key]
            dailys_list.append(daily_entry)

        return dailys_list

    def carregar_dailys(self, repo_name):
        # Busca os documentos do Firestore para o repositório fornecido
        docs = self.db.collection('reponames').where('name', '==', repo_name).stream()
        
        for doc in docs:
            data = doc.to_dict()
            if 'alunos' in data:
                alunos = data['alunos']
                dailys_existentes = []
                
                # Verifica se cada aluno tem dailys registradas
                for aluno_key, aluno_value in alunos.items():
                    if isinstance(aluno_value, dict) and 'dailys' in aluno_value:
                        for daily in aluno_value['dailys']:
                            dailys_existentes.append(daily)
                
                if dailys_existentes:
                    return dailys_existentes
        
        return None
    

    def dailys(self, repo_name):
        # Carrega as dailys existentes
        dailys_existentes = self.carregar_dailys(repo_name)

        # Inicializa a variável alunos como um dicionário vazio
        alunos = {}

        if not dailys_existentes:
            # Obtém a lista de alunos associados ao repositório
            alunos = self.get_alunos_by_repo(repo_name)
            
            today = datetime.now()
            dates = []
            week_num = 1

            # Gera as datas para as duas semanas (excluindo sábados e domingos)
            for i in range(14):
                day = today + timedelta(days=i)
                if day.weekday() < 5:  # Exclui sábados e domingos
                    dates.append({'Semana': week_num, 'Data': day.strftime("%d/%m/%Y")})
                    if len(dates) % 5 == 0:
                        week_num += 1

            df = pd.DataFrame(dates)

            # Agora 'alunos' deve ser um dicionário
            if isinstance(alunos, dict):
                # Adiciona colunas para cada aluno utilizando apenas os emails
                for aluno_email in alunos.values():
                    df[aluno_email] = ""

                # Exibe o editor de tabela no Streamlit
                edited_df = st.data_editor(df, use_container_width=True, key="editable_table")

                # Botão de salvar as modificações
                if st.button("Salvar"):
                    updated_alunos = {}

                    # Processa as alterações na tabela
                    for aluno_key, aluno_email in alunos.items():
                        daily_list = []
                        for _, row in edited_df.iterrows():
                            daily_list.append({
                                "Data": row['Data'],
                                aluno_email: row[aluno_email]
                            })
                        updated_alunos[aluno_key] = {
                            aluno_email: aluno_email,
                            "dailys": daily_list
                        }

                    # Atualiza o Firestore com os dados modificados
                    docs = self.db.collection('reponames').where('name', '==', repo_name).stream()
                    for doc in docs:
                        update_data = {"alunos": updated_alunos}
                        self.db.collection('reponames').document(doc.id).set(update_data, merge=True)

                    st.success("Dados salvos com sucesso!")
            else:
                st.error("O objeto 'alunos' não é um dicionário.")
        else:
            # Neste ponto, 'alunos' deve ser inicializado para evitar o erro
            alunos = self.get_alunos_by_repo(repo_name)
            
            # Estrutura para armazenar os dados corretamente
            dailys_dict = {}

            # Organize os dados por data e aluno
            for daily in dailys_existentes:
                date = daily['Data']
                for aluno_email, status in daily.items():
                    if aluno_email != 'Data':
                        if date not in dailys_dict:
                            dailys_dict[date] = {}
                        dailys_dict[date][aluno_email] = status
            
            # Converta para DataFrame
            df = pd.DataFrame.from_dict(dailys_dict, orient='index')
            df.reset_index(inplace=True)
            df.rename(columns={'index': 'Data'}, inplace=True)

            edited_df = st.data_editor(df, use_container_width=True, key="editable_table")

            # Botão de salvar as modificações
            if st.button("Salvar"):
                updated_alunos = {}

                # Processa as alterações na tabela
                for aluno_key, aluno_email in alunos.items():
                    daily_list = []
                    for _, row in edited_df.iterrows():
                        daily_list.append({
                            "Data": row['Data'],
                            aluno_email: row.get(aluno_email, '')
                        })
                    updated_alunos[aluno_key] = {
                        aluno_email: aluno_email,
                        "dailys": daily_list
                    }

                # Atualiza o Firestore com os dados modificados
                docs = self.db.collection('reponames').where('name', '==', repo_name).stream()
                for doc in docs:
                    update_data = {"alunos": updated_alunos}
                    self.db.collection('reponames').document(doc.id).set(update_data, merge=True)

                st.success("Dados salvos com sucesso!")



