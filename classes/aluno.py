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

    def carregar_dailys(self, repo_name):
        docs = self.db.collection('reponames').where('name', '==', repo_name).stream()
        
        for doc in docs:
            data = doc.to_dict()
            if 'alunos' in data:
                alunos = data['alunos']
                dailys_existentes = []
                
                for aluno_key, aluno_value in alunos.items():
                    if isinstance(aluno_value, dict) and 'dailys' in aluno_value:
                        for daily in aluno_value['dailys']:
                            dailys_existentes.append(daily)
                
                if dailys_existentes:
                    return dailys_existentes
        
        return None

    def make_dailys(self, repo_name):
        alunos = self.get_alunos_by_repo(repo_name)
        
        today = datetime.now()
        dates = []
        week_num = 1

        for i in range(14):
            day = today + timedelta(days=i)
            if day.weekday() < 5:
                dates.append({'Semana': week_num, 'Data': day.strftime("%d/%m/%Y")})
                if len(dates) % 5 == 0:
                    week_num += 1

        df = pd.DataFrame(dates)

        for aluno_email in alunos.values():
            df[aluno_email] = ""

        edited_df = st.data_editor(df, use_container_width=True, key="editable_table")

        if st.button("Salvar"):
            updated_alunos = {}

            for aluno_key, aluno_email in alunos.items():
                daily_list = []
                for _, row in edited_df.iterrows():
                    status = row.get(aluno_email, '')
                    daily_list.append({
                        "Data": row['Data'],
                        aluno_email: status
                    })
                updated_alunos[aluno_key] = {
                    aluno_email: aluno_email,
                    "dailys": daily_list
                }

            docs = self.db.collection('reponames').where('name', '==', repo_name).stream()
            for doc in docs:
                update_data = {"alunos": updated_alunos}
                self.db.collection('reponames').document(doc.id).set(update_data, merge=True)

            st.success("Dados salvos com sucesso!")
            st.session_state['dailys_created'] = True

    def decision(self, repo_name):
        if 'dailys_created' not in st.session_state:
            st.session_state['dailys_created'] = False

        dailys_existentes = self.carregar_dailys(repo_name)

        if dailys_existentes or st.session_state['dailys_created']:
            dailys_dict = {}

            for daily in dailys_existentes:
                date = daily['Data']
                for aluno_email, status in daily.items():
                    if aluno_email != 'Data':
                        if date not in dailys_dict:
                            dailys_dict[date] = {}
                        dailys_dict[date][aluno_email] = status
            
            df = pd.DataFrame.from_dict(dailys_dict, orient='index')
            df.reset_index(inplace=True)
            df.rename(columns={'index': 'Data'}, inplace=True)

            st.data_editor(df, use_container_width=True, key="editable_table")

        else:
            self.make_dailys(repo_name)
