from flask import Flask, render_template, request
import cv2
from pyzbar.pyzbar import decode
import numpy as np
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

app = Flask(__name__)

# Função para processar imagem e detectar QR Code
def processar_qrcode(imagem):
    img = cv2.imdecode(np.fromstring(imagem.read(), np.uint8), cv2.IMREAD_COLOR)
    qr_codes = decode(img)
    for qr in qr_codes:
        return qr.data.decode('utf-8')
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ler_qrcode', methods=['POST'])
def ler_qrcode():
    if 'file' not in request.files:
        return 'Nenhum arquivo enviado', 400
    arquivo = request.files['file']
    if arquivo.filename == '':
        return 'Arquivo inválido', 400
    
    # Processa o QR Code
    url = processar_qrcode(arquivo)
    if url:
        # Inicializa o Selenium WebDriver
        driver_path = 'C:/chromedriver.exe'  # Caminho do seu chromedriver
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service)
        
        # Acessa a URL que foi extraída do QR Code
        driver.get(url)
        
        # Espera alguns segundos para o conteúdo ser carregado
        time.sleep(5)  # Ajuste o tempo de espera conforme necessário

        # Obtém o código HTML da página após o carregamento
        html = driver.page_source

        # Fecha o navegador
        driver.quit()

        # Usa o BeautifulSoup para processar o HTML
        soup = BeautifulSoup(html, 'html.parser')

        # Busca por todas as linhas de tabela <tr>
        linhas = soup.find_all('tr', id=True)

        # Lista para armazenar os dados extraídos
        dados_extraidos = []

        # Itera sobre as linhas da tabela e extrai os dados das colunas
        for linha in linhas:
            txtTit2 = linha.find('span', class_='txtTit2').get_text(strip=True) if linha.find('span', class_='txtTit2') else ''
            Rcod = linha.find('span', class_='RCod').get_text(strip=True).replace("Código: ", "") if linha.find('span', class_='RCod') else ''
            Rqtd = linha.find('span', class_='Rqtd').get_text(strip=True).replace("Qtde.:", "") if linha.find('span', class_='Rqtd') else ''
            RUN = linha.find('span', class_='RUN').get_text(strip=True).replace("UN: ", "") if linha.find('span', class_='RUN') else ''
            Rvlunit = linha.find('span', class_='RvlUnit').get_text(strip=True).replace("Vl. Unit.:", "") if linha.find('span', class_='RvlUnit') else ''
            vl_total = linha.find('span', class_='valor').get_text(strip=True) if linha.find('span', class_='valor') else ''

            # Adiciona os dados extraídos em uma lista
            dados_extraidos.append([txtTit2, Rcod, Rqtd, RUN, Rvlunit, vl_total])

        # Cria um DataFrame com os dados extraídos
        df = pd.DataFrame(dados_extraidos, columns=['Produto', 'Código', 'Quantidade', 'Unidade', 'Valor Unitário', 'Valor Total'])

        # Salva o DataFrame em um arquivo Excel
        df.to_excel('conteudo_estruturado_site.xlsx', index=False)

        # Retorna mensagem de sucesso com os dados extraídos
        return f'QR Code processado. Dados extraídos e salvos no arquivo Excel. URL: {url}'
    
    return 'Nenhum QR Code encontrado', 404

if __name__ == '__main__':
    app.run(debug=True)
