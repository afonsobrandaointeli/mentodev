import os
import streamlit as st 

st.title("Seleção de Artefatos")

def select_artifacts():
    artifacts_list = ['Artefato 1', 'Artefato 2', 'Artefato 3', 'Artefato 4', 'Artefato 5']
    selected_artifacts = []
    for artifact in artifacts_list:
        if st.checkbox(artifact):
            selected_artifacts.append(artifact)
    return selected_artifacts

selected_artifacts = select_artifacts()

st.write(f"Você selecionou os Artefatos: {', '.join(selected_artifacts)}")
artifact_radio = st.radio("Deseja avaliar os artefatos selecionados?", ("Sim", "Não"))
try:    
    if artifact_radio == "Sim":
        artifact_scores = {}
        for artifact in selected_artifacts:
            artifact_scores[artifact] = int(st.number_input(f"Digite a Nota do Artefato {artifact}:"))
        average = round(sum(artifact_scores.values()) / len(selected_artifacts), 2)
        st.write(f"A média de notas dos Artefato foi {average}")
    else:
        st.write("Avaliação dos artefatos não realizada")
    pass
except:
    st.write("Nao e possivel realizar a avaliacao sem ao menos um artefato selecionado")
    pass
