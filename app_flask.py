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
from urllib.parse import urlparse

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ""
    extracted_data = []

    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file:
                try:
                    img = Image.open(file)
                    print("Imagem carregada com sucesso.")
                    
                    # Decodificando os QR Codes
                    decoded_objects = decode(img)
                    print(f"QR Codes decodificados: {decoded_objects}")
                    
                    url = ""
                    for obj in decoded_objects:
                        if obj.type == 'QRCODE':
                            url = obj.data.decode('utf-8')
                            print(f"QR Code detectado com URL: {url}")
                            break
                    
                    if not url:
                        message = "QR Code não contém uma URL válida."
                        print(message)
                    else:
                        # Verificar se a URL extraída é válida
                        if not urlparse(url).scheme:
                            message = "A URL extraída não é válida."
                            print(message)
                        else:
                            # Chama a função de extração de dados da URL
                            extracted_data = extract_data_from_url(url)
                            message = "Dados salvos com sucesso!"
                            print(message)
                
                except Exception as e:
                    message = f"Erro ao processar o QR Code: {str(e)}"
                    print(message)

    return render_template('index.html', message=message)

# Função de extração de dados da URL
def extract_data_from_url(url):
    options = Options()
    options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))  # Aguarda a tabela carregar
        html = driver.page_source

    except Exception as e:
        print(f"Erro ao acessar a URL: {e}")
        return f"Erro ao acessar a URL: {e}"
    
    finally:
        driver.quit()

    soup = BeautifulSoup(html, 'html.parser')
    linhas = soup.find_all('tr', id=True)
    dados_extraidos = []

    text_divs = soup.find_all('div', class_='text')
    emissao_tag = soup.find('strong', text=' Emissão: ')
    
    for linha in linhas:
        nome_estabelecimento_item = soup.find('div', id='u20').get_text(strip=True) if soup.find('div', id='u20') else 'Não encontrado'
        descricao_item = linha.find('span', class_='txtTit2').get_text(strip=True) if linha.find('span', class_='txtTit2') else ''
        valor_unit = linha.find('span', class_='RvlUnit').get_text(strip=True).replace("Vl. Unit.:", "") if linha.find('span', class_='RvlUnit') else ''
        endereco = soup.find('div', class_='text').get_text(strip=True) if soup.find('div', class_='text') else 'Endereço não encontrado'
        endereco = endereco.replace("\n\t\t,\n\t\t", "-")

        emissao_text = emissao_tag.find_next_sibling(text=True).strip()
        emissao_text = ' '.join(emissao_text.split()[:2])
        data = emissao_text

        for i, div in enumerate(text_divs):
            if "CNPJ" in div.get_text():
                if i + 1 < len(text_divs):
                    endereco = text_divs[i + 1].get_text(strip=True)
                    
                break

        dados_extraidos.append([descricao_item, valor_unit, data, nome_estabelecimento_item, endereco])

    with open('output.json', 'w') as json_file:
        json.dump(dados_extraidos, json_file)

    save_data_accumulative(dados_extraidos)  

    return dados_extraidos    

# Função para salvar os dados acumulados
def save_data_accumulative(dados_extraidos):
    # Caminho absoluto do arquivo
    file_path = os.path.join(os.getcwd(), 'dados_extraidos.json')  # Caminho absoluto

    # Lê os dados existentes, se houver
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try:
                existing_data = json.load(f)
                print(f"Dados existentes: {existing_data}")
            except json.JSONDecodeError:
                existing_data = []
                print("Erro ao carregar dados existentes. Criando um novo arquivo.")
    else:
        existing_data = []
        print("Arquivo não encontrado. Criando novo arquivo.")

    # Acumula os dados de forma única, mas só remove se TODOS os itens forem idênticos
    for new_item in dados_extraidos:
        if new_item not in existing_data:
            print(f"Adicionando novo item: {new_item}")
            existing_data.append(new_item)
        else:
            print(f"Item já existe: {new_item}")

    # Formata os dados antes de salvar (isso pode ser ajustado conforme necessário)
    formatted_data = []
    for item in existing_data:
        formatted_item = [value.title() if isinstance(value, str) else value for value in item]
        formatted_data.append(formatted_item)

    # Salva os dados acumulados
    with open(file_path, 'w') as f:
        json.dump(formatted_data, f, indent=4)
        print("Dados salvos no arquivo dados_extraidos.json:")
        print(formatted_data)  # Verifica o conteúdo dos dados salvos


@app.route('/pesquisa', methods=['POST','GET'])
def pesquisa():
    extracted_data = []
    try:
        with open('dados_extraidos.json', 'r') as f:
            extracted_data.extend(json.load(f))
    except Exception as e:
        print("Erro ao carregar dados_extraidos.json:", e)
    try:
        with open('lista_11_estab.json', 'r') as f:
            extracted_data.extend(json.load(f))
    except Exception as e:
        print("Erro ao carregar lista_11_estab.json:", e)

    pesquisa = request.form.get('pesquisa', '').lower()  

    if pesquisa:
        filtered_data = [item for item in extracted_data if pesquisa in item[0].lower()]
    else:
        filtered_data = extracted_data

    return render_template('pesquisa.html', data=filtered_data)

# Rota para a página inicial

@app.route('/reset_data', methods=['POST'])
def reset_data():
    
    with open('lista_11_estab.json', 'w') as f:
        json.dump([], f)
    with open('dados_extraidos.json', 'w') as f:
        json.dump([], f)

    return redirect(url_for('pesquisa'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)