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
    st.subheader(f"Alunos no repositório '{selected_repo}':")
    
    # Verificar se alunos é um dicionário e se contém dados
    if isinstance(alunos, dict) and alunos:
        # Criar uma lista para armazenar os dados dos alunos
        data = []

        # Ordenar e processar os alunos
        sorted_alunos = sorted(alunos.items(), key=lambda x: int(x[0].replace("aluno", "")))
        
        for chave, nome in sorted_alunos:
            numero = int(chave.replace("aluno", ""))
            data.append({"ID": numero, "Nome": nome})
        
        # Converter a lista de dados em um DataFrame
        df = pd.DataFrame(data)
        
        # Centralizar a tabela usando CSS
        table_html = df.to_html(index=False)
        centered_table = f"""
        <div style="display: flex; justify-content: center;">
            {table_html}
        </div>
        """
        
        st.write(centered_table, unsafe_allow_html=True)

        st.subheader("Tabela de dailys da sprint")

        aluno_repo.dailys(selected_repo)
    else:
        st.write("Dados de alunos inválidos ou vazios.")
else:
    st.write("Nenhum aluno encontrado para este repositório.")
