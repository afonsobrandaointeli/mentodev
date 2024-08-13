import streamlit as st
import pandas as pd
import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

db = firestore.client()

# Adicionei um campo de entrada só para testar a interatividade da tabela
# Essa tabela deve receber as notas dos alunos na coluna "desempenho" (sempre índice[0] da lista do aluno)

def get_repo_names():
    repo_names = []
    docs = db.collection('reponames').stream()
    for doc in docs:
        repo_names.append(doc.to_dict().get('name'))
    return repo_names

repo_names = get_repo_names()

def get_alunos_by_repo(repo_name_user):
    alunos = []
    docs = db.collection('reponames').where('name', '==', repo_name_user).stream()
    for doc in docs:
        data = doc.to_dict()
        if 'alunos' in data:
            alunos.append(data['alunos'])
            print(alunos)
    return alunos


repo_name_user = st.selectbox("Escolha um repositório:", repo_names)
user_input = st.number_input(label="Coloque a nota do aluno aqui: ", min_value=0.0, max_value=10.0)

get_alunos_by_repo(repo_name_user)

data = {
    "critérios": ["Desempenho", "Demérito", "Ir além", "Nota Final"],
    "aluno 1": ["8.75", "0.90", "0.35", "8.20"],
    "aluno 2": ["5.40", "0.60", "0.20", "5.00"],
    "aluno 3": ["7.90", "0.10", "0.40", "{:.2f}".format(user_input)],
    "aluno 4": ["6.70", "0.20", "0.10", "6.60"],
    "aluno 5": ["7.30", "0.40", "0.20", "7.10"],
    "aluno 6": ["7.30", "0.40", "0.20", "7.10"],
    "aluno 7": ["7.30", "0.40", "0.20", "7.10"],
    "aluno 8": ["7.30", "0.40", "0.20", "7.10"],
}


df = pd.DataFrame(data)

df.set_index("critérios", inplace=True)
df.index.name = "Critérios"

def color_row(row):
    if row.name == "Nota Final":
        return [color_cells(val) for val in row]
    colors = {"Desempenho": "blue", "Demérito": "red", "Ir além": "purple"}
    return [f'background-color: {colors.get(row.name, "")}'] * len(row)

def color_cells(val):
    val = float(val)
    if val < 7:
        return 'background-color: red'
    elif 7 <= val < 8:
        return 'background-color: orange'
    elif 8 <= val < 9:
        return 'background-color: green'
    else:
        return 'background-color: blue'

styled_df = df.style.apply(color_row, axis=1)

st.dataframe(styled_df)
