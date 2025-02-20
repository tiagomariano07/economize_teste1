from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from pyzbar.pyzbar import decode
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

app = Flask(__name__)

# Função para salvar os dados extraídos de forma acumulativa e sem duplicação
def save_data_accumulative(new_data):
    # Verifica se o arquivo JSON já existe
    if os.path.exists('dados_extraidos.json'):
        # Se o arquivo já existe, lê os dados existentes
        with open('dados_extraidos.json', 'r') as f:
            existing_data = json.load(f)
    else:
        # Caso o arquivo não exista, inicia uma lista vazia
        existing_data = []

    # Remove duplicatas, mantendo apenas os valores únicos
    existing_data_set = set(tuple(item) for item in existing_data)
    new_data_set = set(tuple(item) for item in new_data)

    # Une os dados existentes com os novos dados, sem duplicatas
    all_data = list(existing_data_set.union(new_data_set))

    # Salva os dados acumulados no arquivo JSON
    with open('dados_extraidos.json', 'w') as f:
        json.dump(all_data, f)

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ""
    extracted_data = []

    if request.method == 'POST' and 'file' in request.files:
        # Recebe a imagem do QR Code
        file = request.files['file']
        
        if file:
            # Abrir a imagem do QR Code usando Pillow
            img = Image.open(file)
            decoded_objects = decode(img)
            
            # Extrair a URL do QR Code
            url = ""
            for obj in decoded_objects:
                if obj.type == 'QRCODE':
                    url = obj.data.decode('utf-8')
                    break
            
            if not url:
                return "QR Code não contém uma URL válida."

            # Processar a URL extraída do QR Code
            options = Options()
            options.add_argument("--headless")  # Executa sem abrir o navegador
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)

            try:
                # Acessa a página
                driver.get(url)

                # Aguarda o carregamento da tabela de produtos
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )

                # Obtém o código HTML da página
                html = driver.page_source

            finally:
                # Fecha o navegador
                driver.quit()

            # Processa o HTML com BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            # Buscar todas as linhas de produtos na tabela
            linhas = soup.find_all('tr', id=True)

            dados_extraidos = []

            # Encontrar todas as divs com a classe 'text'
            text_divs = soup.find_all('div', class_='text')

            # Itera sobre as linhas da tabela e extrai os dados
            for linha in linhas:
                # Busca o nome do estabelecimento (fora do loop, pois é um único valor)
                nome_estabelecimento_item = soup.find('div', id='u20').get_text(strip=True) if soup.find('div', id='u20') else 'Não encontrado'
                
                # Extrair o valor do produto
                descricao_item = linha.find('span', class_='txtTit2').get_text(strip=True) if linha.find('span', class_='txtTit2') else ''
                
                # Extrair o valor unitário
                valor_unit = linha.find('span', class_='RvlUnit').get_text(strip=True).replace("Vl. Unit.:", "") if linha.find('span', class_='RvlUnit') else ''
                
                # Extrair o endereço (fora do loop, pois é uma informação fixa)
                endereco = soup.find('div', class_='text').get_text(strip=True) if soup.find('div', class_='text') else 'Endereço não encontrado'

                for i, div in enumerate(text_divs):
                    if "CNPJ" in div.get_text():  # Se encontrar o CNPJ
                        if i + 1 < len(text_divs):  # Se houver um próximo div (o endereço)
                            endereco = text_divs[i + 1].get_text(strip=True)
                            endereco = endereco.replace(", ,", "-")
                        break

                # Adiciona os dados extraídos à lista
                dados_extraidos.append([descricao_item, valor_unit, nome_estabelecimento_item, endereco])

            extracted_data = dados_extraidos

            # Salvar os dados extraídos em um arquivo JSON sem duplicações
            save_data_accumulative(extracted_data)

            message = "Dados salvos com sucesso!"
    
    return render_template('index.html', message=message)

@app.route('/pesquisa', methods=['GET', 'POST'])
def pesquisa():
    # Carregar os dados do arquivo JSON
    with open('dados_extraidos.json', 'r') as f:
        extracted_data = json.load(f)

    # Filtrar os itens com base na pesquisa do usuário
    pesquisa = request.form.get('pesquisa', '').lower()

    # Se houver pesquisa, filtre os dados
    if pesquisa:
        filtered_data = [item for item in extracted_data if pesquisa in item[0].lower()]  # Filtra pela descrição do produto
    else:
        filtered_data = extracted_data

    return render_template('pesquisa.html', data=filtered_data)


@app.route('/reset', methods=['POST'])
def reset_data():
    # Apagar o conteúdo do arquivo JSON
    with open('dados_extraidos.json', 'w') as f:
        json.dump([], f)  # Escreve uma lista vazia no arquivo

    return redirect(url_for('pesquisa'))  # Redireciona para a página de pesquisa


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)