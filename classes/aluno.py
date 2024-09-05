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

                for aluno_key, aluno_value in alunos_data.items():
                    if isinstance(aluno_value, dict):
                        for email in aluno_value.keys():
                            alunos[aluno_key] = email
                    else:
                        alunos[aluno_key] = aluno_value
        return alunos

    def make_dailys(self, repo_name, aluno_selecionado):
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

        # Persistir valores digitados em session_state para não reiniciar
        if aluno_selecionado not in st.session_state:
            st.session_state[aluno_selecionado] = {'dailys': {}, 'criterio_1': {}, 'criterio_2': {}}

        edited_data = st.session_state[aluno_selecionado]['dailys']
        criterios_data = {
            'criterio_1': st.session_state[aluno_selecionado]['criterio_1'],
            'criterio_2': st.session_state[aluno_selecionado]['criterio_2']
        }

        # Usando dropdowns para evitar a atualização constante
        for i in range(len(df)):
            if i not in edited_data:
                edited_data[i] = ""
            if i not in criterios_data['criterio_1']:
                criterios_data['criterio_1'][i] = ""
            if i not in criterios_data['criterio_2']:
                criterios_data['criterio_2'][i] = ""

            # Campo para "Daily"
            valor_daily = st.selectbox(f"{df.at[i, 'Data']} - {aluno_selecionado} (Daily)",
                                       options=["", "sim", "não", "nao"],
                                       index=["", "sim", "não", "nao"].index(edited_data[i]),
                                       key=f"daily_{aluno_selecionado}_{i}")
            st.session_state[aluno_selecionado]['dailys'][i] = valor_daily

            # Critério 1
            valor_criterio_1 = st.selectbox(f"{df.at[i, 'Data']} - {aluno_selecionado} (Critério 1)",
                                            options=["", "sim", "não", "nao"],
                                            index=["", "sim", "não", "nao"].index(criterios_data['criterio_1'][i]),
                                            key=f"criterio1_{aluno_selecionado}_{i}")
            st.session_state[aluno_selecionado]['criterio_1'][i] = valor_criterio_1

            # Critério 2
            valor_criterio_2 = st.selectbox(f"{df.at[i, 'Data']} - {aluno_selecionado} (Critério 2)",
                                            options=["", "sim", "não", "nao"],
                                            index=["", "sim", "não", "nao"].index(criterios_data['criterio_2'][i]),
                                            key=f"criterio2_{aluno_selecionado}_{i}")
            st.session_state[aluno_selecionado]['criterio_2'][i] = valor_criterio_2

        if st.button("Salvar Avaliação"):
            updated_alunos = {}

            daily_list = []
            for i, row in df.iterrows():
                status = st.session_state[aluno_selecionado]['dailys'][i]
                daily_list.append({
                    "Data": row['Data'],
                    aluno_selecionado: status
                })
            updated_alunos[aluno_selecionado] = {
                aluno_selecionado: aluno_selecionado,
                "dailys": daily_list,
                "criterio_1": st.session_state[aluno_selecionado]['criterio_1'],
                "criterio_2": st.session_state[aluno_selecionado]['criterio_2']
            }

            docs = self.db.collection('reponames').where('name', '==', repo_name).stream()
            for doc in docs:
                update_data = {"alunos": updated_alunos}
                self.db.collection('reponames').document(doc.id).set(update_data, merge=True)

            st.success("Dados salvos com sucesso!")
            st.session_state['dailys_created'] = True

        # Contagem de "sim" e "não"
        total_sim = sum([1 for value in edited_data.values() if value == "sim"])
        total_nao = sum([1 for value in edited_data.values() if value in ["não", "nao"]])

        total_sim_criterio_1 = sum([1 for value in criterios_data['criterio_1'].values() if value == "sim"])
        total_nao_criterio_1 = sum([1 for value in criterios_data['criterio_1'].values() if value in ["não", "nao"]])

        total_sim_criterio_2 = sum([1 for value in criterios_data['criterio_2'].values() if value == "sim"])
        total_nao_criterio_2 = sum([1 for value in criterios_data['criterio_2'].values() if value in ["não", "nao"]])

        st.write(f"Total para {aluno_selecionado} (Daily): Sim = {total_sim}, Não = {total_nao}")
        st.write(f"Total para {aluno_selecionado} (Critério 1): Sim = {total_sim_criterio_1}, Não = {total_nao_criterio_1}")
        st.write(f"Total para {aluno_selecionado} (Critério 2): Sim = {total_sim_criterio_2}, Não = {total_nao_criterio_2}")

    def decision(self, repo_name):
        if 'dailys_created' not in st.session_state:
            st.session_state['dailys_created'] = False

        aluno_selecionado = st.selectbox("Escolha um aluno para avaliar:", list(self.get_alunos_by_repo(repo_name).values()))
        self.make_dailys(repo_name, aluno_selecionado)
