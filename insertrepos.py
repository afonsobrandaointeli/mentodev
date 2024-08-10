import firebase_admin
from firebase_admin import credentials, firestore

# Inicializar o Firebase com a chave do serviço
cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred)

# Inicializar o Firestore
db = firestore.client()

# Lista de nomes para adicionar à coleção "reponames"
repo_names = [
    "Inteli-College/2024-2A-T04-SI11-G01",
    "Inteli-College/2024-2A-T14-IN03-G04",
    "Inteli-College/2024-2A-T11-IN03-G01",
    "Inteli-College/2024-2A-T06-ES09-G01",
    "Inteli-College/2024-2A-T04-SI11-G04",
    "Inteli-College/2024-2A-T07-CC07-G04",
    "Inteli-College/2024-2A-T12-IN03-G04",
    "Inteli-College/2024-2A-T05-CC09-G03",
    "Inteli-College/2024-2A-T07-CC07-G03",
    "Inteli-College/2024-2A-T07-CC07-G01",
    "Inteli-College/2024-2A-T04-SI11-G03",
    "Inteli-College/2024-2A-T06-ES09-G02",
    "Inteli-College/2024-2A-T02-EC11-G05",
    "Inteli-College/2024-2A-T10-SI07-G04",
    "Inteli-College/2024-2A-T03-ES11-G03",
    "Inteli-College/2024-2A-T06-ES09-G03",
    "Inteli-College/2024-2A-T05-CC09-G02",
    "Inteli-College/2024-2A-T08-EC07-G02",
    "Inteli-College/2024-2A-T11-IN03-G04",
    "Inteli-College/2024-2A-T10-SI07-G03",
    "Inteli-College/2024-2A-T08-EC07-G01",
    "Inteli-College/2024-2A-T09-ES07-G04",
    "Inteli-College/2024-2A-T14-IN03-G05",
    "Inteli-College/2024-2A-T04-SI11-G02",
    "Inteli-College/2024-2A-T13-IN03-G03",
    "Inteli-College/2024-2A-T03-ES11-G04",
    "Inteli-College/2024-2A-T09-ES07-G02",
    "Inteli-College/2024-2A-T12-IN03-G05",
    "Inteli-College/2024-2A-T14-IN03-G02",
    "Inteli-College/2024-2A-T14-IN03-G03",
    "Inteli-College/2024-2A-T12-IN03-G02",
    "Inteli-College/2024-2A-T10-SI07-G05",
    "Inteli-College/2024-2A-T13-IN03-G04",
    "Inteli-College/2024-2A-T02-EC11-G01",
    "Inteli-College/2024-2A-T03-ES11-G05",
    "Inteli-College/2024-2A-T09-ES07-G05",
    "Inteli-College/2024-2A-T07-CC07-G05",
    "Inteli-College/2024-2A-T13-IN03-G02",
    "Inteli-College/2024-2A-T05-CC09-G04",
    "Inteli-College/2024-2A-T09-ES07-G01",
    "Inteli-College/2024-2A-T07-CC07-G02",
    "Inteli-College/2024-2A-T08-EC07-G05",
    "Inteli-College/2024-2A-T02-EC11-G02",
    "Inteli-College/2024-2A-T01-CC11-G02",
    "Inteli-College/2024-2A-T01-CC11-G04",
    "Inteli-College/2024-2A-T01-CC11-G01",
    "Inteli-College/2024-2A-T08-EC07-G04",
    "Inteli-College/2024-2A-T13-IN03-G01",
    "Inteli-College/2024-2A-T01-CC11-G05",
    "Inteli-College/2024-2A-T11-IN03-G03",
    "Inteli-College/2024-2A-T14-IN03-G01",
    "Inteli-College/2024-2A-T11-IN03-G02",
    "Inteli-College/2024-2A-T10-SI07-G02",
    "Inteli-College/2024-2A-T12-IN03-G01",
    "Inteli-College/2024-2A-T02-EC11-G04",
    "Inteli-College/2024-2A-T09-ES07-G03",
    "Inteli-College/2024-2A-T04-SI11-G05",
    "Inteli-College/2024-2A-T10-SI07-G01",
    "Inteli-College/2024-2A-T05-CC09-G01",
    "Inteli-College/2024-2A-T07-CC07-G06",
    "Inteli-College/2024-2A-T03-ES11-G01",
    "Inteli-College/2024-2A-T03-ES11-G02",
    "Inteli-College/2024-2A-T08-EC07-G03",
    "Inteli-College/2024-2A-T02-EC11-G03",
    "Inteli-College/2024-2A-T01-CC11-G03",
    "Inteli-College/2024-2A-T12-IN03-G03"
]

# Adicionar cada nome como um documento na coleção "reponames"
for repo_name in repo_names:
    repo_data = {'name': repo_name}
    db.collection('reponames').add(repo_data)

print("Documentos adicionados à coleção 'reponames'.")