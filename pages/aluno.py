import streamlit as st
import pandas as pd
from classes.aluno import AlunoRepository

aluno_repo = AlunoRepository()

st.title("Seleção de Repositórios")

repo_names = aluno_repo.get_repo_names()

selected_repo = st.selectbox("Escolha um repositório:", repo_names)

st.write(f"Você selecionou: {selected_repo}")

alunos = aluno_repo.get_alunos_by_repo(selected_repo)

# Exibir a lista de alunos em uma tabela
if alunos:
    st.subheader(f"Alunos encontrados no repositório '{selected_repo}':")
    
    # Verificar se 'alunos' é um dicionário e se contém dados
    if isinstance(alunos, dict) and alunos:

        aluno_repo.decision(selected_repo)
else:
    st.write("Nenhum aluno encontrado para este repositório.")


