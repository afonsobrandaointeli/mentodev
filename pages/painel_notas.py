# import streamlit as st
# import pandas as pd

# # Criando um campo de entrada para testar a interatividade da tabela
# user_input = st.number_input(label="Coloque a nota do aluno aqui: ", min_value=0.0, max_value=10.0)

# # definindo os dados
# data = {
#     "critérios": ["Desempenho", "Demérito", "Ir além", "Nota Final"],
#     "aluno 1": [f"{user_input}", "2", "31", "12"],
#     "aluno 2": ["12", "22", "32", "12"],
#     "aluno 3": ["13", "23", "33", "12"]
# }
# # criando o dataframe
# df = pd.DataFrame(data)

# # redefinindo a coluna de index do df
# # df.set_index("critérios", inplace=True)
# # df.index.name = "Critérios"

# # visualizar dataframe
# st.write("# Vendo uma matriz personalizada")

# def to_color_cell(row):
#     return 'background-color: blue'

# df = df.style.apply(to_color_cell, axis=0)

# st.dataframe(df)

import streamlit as st
import pandas as pd

# Criando um campo de entrada para testar a interatividade da tabela
user_input = st.number_input(label="Coloque a nota do aluno aqui: ", min_value=0.0, max_value=10.0)

# Definindo os dados
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

# Criando o DataFrame
df = pd.DataFrame(data)

# Redefinindo a coluna de índice do DataFrame
df.set_index("critérios", inplace=True)
df.index.name = "Critérios"

# Função de coloração para a linha específica
def color_row(row):
    if row.name == "Nota Final":
        return [color_cells(val) for val in row]
    colors = {"Desempenho": "blue", "Demérito": "red", "Ir além": "purple"}
    return [f'background-color: {colors.get(row.name, "")}'] * len(row)

# Função de coloração para células
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

# Aplicando a estilização
styled_df = df.style.apply(color_row, axis=1)

# Exibindo no Streamlit
st.dataframe(styled_df)
