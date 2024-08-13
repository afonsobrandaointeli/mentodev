import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd

class AlunoRepository:
    def __init__(self):
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

        self.db = firestore.client()

    def get_repo_names(self):
        repo_names = []
        docs = self.db.collection('reponames').stream()
        for doc in docs:
            repo_names.append(doc.to_dict().get('name'))
        return repo_names

    def get_alunos_by_repo(self, repo_name):
        alunos = []
        docs = self.db.collection('reponames').where('name', '==', repo_name).stream()
        for doc in docs:
            data = doc.to_dict()
            if 'alunos' in data:
                alunos.append(data['alunos'])
        return alunos
    
    def dailys(self, repo_name):
        # Obter o documento do repositório
        docs = self.db.collection('reponames').where('name', '==', repo_name).stream()

        # Variáveis para armazenar os dados
        existing_dailys = None  
        alunos = []

        for doc in docs:
            data = doc.to_dict()
            # Verificar se o repositório já tem alunos
            if 'alunos' in data:
                alunos = data['alunos']
            # Verificar se o repositório já tem registros de dailys
            if 'dailys' in data:
                existing_dailys = data['dailys']

        # Se já existir um registro de dailys, carregar os dados
        if existing_dailys:
            # Criar DataFrame a partir dos dados existentes
            df = pd.DataFrame(existing_dailys)
            # Separar as colunas de "Alunos" em colunas individuais
            alunos_data = pd.DataFrame(df['Alunos'].tolist())
            df = df.drop(columns=['Alunos']).join(alunos_data)
        else:
            # Se não existir, criar uma nova tabela
            today = datetime.now()
            dates = []
            week_num = 1
            for i in range(14):  # Duas semanas
                day = today + timedelta(days=i)
                if day.weekday() < 5:  # Exclui sábado e domingo
                    dates.append({'Semana': week_num, 'Data': day.strftime("%d/%m/%Y")})
                if len(dates) == 5:
                    week_num += 1

            # Criar um DataFrame com as colunas 'Semana' e 'Data'
            df = pd.DataFrame(dates)

            # Adicionar colunas para cada aluno com opções "Sim" e "Não"
            for aluno in alunos:
                df[aluno] = ""

        # Exibir a tabela interativa
        edited_df = st.data_editor(df, use_container_width=True, key="editable_table")

        # Botão para salvar os dados
        if st.button("Salvar"):
            # Processar os dados da tabela
            daily_entries = []
            for index, row in edited_df.iterrows():
                data = {
                    "Semana": row['Semana'],
                    "Data": row['Data'],
                    "Alunos": {aluno: row[aluno] for aluno in alunos}
                }
                daily_entries.append(data)

            # Salvar no banco de dados como "Critério de Avaliação - Reuniões Diárias"
            docs = self.db.collection('reponames').where('name', '==', repo_name).stream()
            for doc in docs:
                self.db.collection('reponames').document(doc.id).set({"dailys": daily_entries}, merge=True)

            st.success("Dados salvos com sucesso!")
