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
                
                # Itera sobre o dicionário de alunos e extrai apenas os emails
                for aluno_key, aluno_value in alunos_data.items():
                    if isinstance(aluno_value, dict):
                        # Tenta extrair o email do aluno, ignorando a chave 'dailys'
                        for key, value in aluno_value.items():
                            if key != 'dailys':
                                alunos[aluno_key] = value
            
        return alunos if isinstance(alunos, dict) else {}


        
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
                            print(f"Daily: {daily}")
                            print(f"Data: {daily['Data']}")
                            print(f"Aluno: {aluno_key}")
                            # Busca o status com base no email do aluno no dicionário daily
                            status = daily.get(aluno_key, 'Não encontrado')
                            print(f"Status: {status}")
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
        
        print(f"Dailys carregadas: {dailys_list}")
        return dailys_list





    def dailys(self, repo_name):
        dailys_existentes = self.carrregar_dailys(repo_name)

        if not dailys_existentes:
            print("Nenhuma daily encontrada. Criando uma nova tabela.")
            alunos = self.get_alunos_by_repo(repo_name)
            
            today = datetime.now()
            dates = []
            week_num = 1
            for i in range(14):
                day = today + timedelta(days=i)
                if day.weekday() < 5:  # Exclui sábados e domingos
                    dates.append({'Semana': week_num, 'Data': day.strftime("%d/%m/%Y")})
                    if len(dates) == 5:
                        week_num += 1

            df = pd.DataFrame(dates)

            # Adicionar colunas para cada aluno, usando apenas os emails
            if isinstance(alunos, dict):
                for aluno_email in alunos.values():
                    df[aluno_email] = ""

                # Exibe o editor de tabela no Streamlit
                edited_df = st.data_editor(df, use_container_width=True, key="editable_table")

                # Botão de salvar as modificações
                if st.button("Salvar"):
                    updated_alunos = {}
                    for aluno_key, aluno_email in alunos.items():
                        daily_list = []
                        for index, row in edited_df.iterrows():
                            daily_list.append({
                                "Data": row['Data'],
                                aluno_email: row[aluno_email]
                            })
                        updated_alunos[aluno_key] = {
                            aluno_email: aluno_email,
                            "dailys": daily_list
                        }

                    # Atualizar o Firestore com os dados modificados
                    docs = self.db.collection('reponames').where('name', '==', repo_name).stream()
                    for doc in docs:
                        update_data = {"alunos": updated_alunos}
                        self.db.collection('reponames').document(doc.id).set(update_data, merge=True)

                    st.success("Dados salvos com sucesso!")
            else:
                st.error("O objeto 'alunos' não é um dicionário.")
        else:
            print("Dailys encontradas. Exibindo tabela existente.")
            df = pd.DataFrame(dailys_existentes)
            st.write(df)
            st.write("Dailys já existentes para esta sprint.")


