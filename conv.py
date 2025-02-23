import pandas as pd
import json
import re

# Função para formatar preços
def formatar_preco(preco):
    if isinstance(preco, str):  # Se o preço for uma string
        preco = preco.replace('.', ',')  # Substitui ponto por vírgula
        preco = preco.replace('\u00a0', ' ')  # Remove o espaço não separável
        preco = re.sub(r'[^0-9,]', '', preco)  # Remove tudo que não for número ou vírgula
    elif isinstance(preco, (int, float)):  # Se for número, converte para string e formata
        preco = f"{preco:.2f}".replace('.', ',')  # Formata para 2 casas decimais e troca ponto por vírgula
    return preco

# Função para limpar e formatar texto (remover espaços extras, caracteres não imprimíveis)
def limpar_texto(texto):
    # Verifica se o valor é uma string
    if isinstance(texto, str):
        texto = texto.replace('\u00a0', ' ').strip()  # Remove o espaço não separável
        texto = re.sub(r'[^\x00-\x7F]+', '', texto)  # Remove caracteres não ASCII
        texto = texto.replace(',','')
        return texto
    # Se for um objeto Timestamp, converte para string (caso seja uma data)
    elif isinstance(texto, pd.Timestamp):
        return texto.strftime('%d/%m/%Y %H:%M')  # Converte para string no formato desejado
    return texto

# Carregar o arquivo Excel
excel_file = 'base_de_dados2.xlsx'

# Ler a planilha específica
df = pd.read_excel(excel_file, sheet_name='BASE_DE_DADOS', header=0)

# Filtrar as colunas desejadas
colunas_desejadas = ['PRODUTO', 'PRECO', 'DATA', 'ESTABELECIMENTO', 'ENDERECO']

# Lista para armazenar os dados no formato desejado
data_json = []

# Limpar os nomes das colunas (remover espaços extras e tornar tudo maiúsculas)
df.columns = df.columns.str.strip()  # Remove espaços e coloca em maiúsculas

# Verificar se as colunas desejadas existem na sheet
if all(col in df.columns for col in colunas_desejadas):
    # Filtrar apenas as colunas desejadas
    df_filtrado = df[colunas_desejadas]

    # Converter para uma lista de listas (cada linha será uma lista)
    for index, row in df_filtrado.iterrows():
        produto = limpar_texto(row['PRODUTO'])  # Limpar produto
        preco = formatar_preco(row['PRECO'])  # Formatar o preço
        data = limpar_texto(row['DATA'])  # Limpar data
        estabelecimento = limpar_texto(row['ESTABELECIMENTO'])  # Limpar nome do estabelecimento
        endereco = limpar_texto(row['ENDERECO'])  # Limpar endereço
        data_json.append([produto, preco, data, estabelecimento, endereco])
else:
    print(f"A planilha não contém as colunas esperadas: {df.columns.tolist()}")

# Salvar o resultado em um arquivo JSON
with open('lista_11_estab.json', 'w') as json_file:
    json.dump(data_json, json_file, indent=4)

print("Conversão concluída!")
