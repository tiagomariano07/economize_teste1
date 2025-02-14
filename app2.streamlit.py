import streamlit as st
import cv2
from pyzbar.pyzbar import decode
from PIL import Image

# Função para decodificar o QR Code
def decode_qr_code(image):
    decoded_objects = decode(image)
    for obj in decoded_objects:
        return obj.data.decode("utf-8")
    return None

# Título do app
st.title("Leitor de QR Code")

# Captura de imagem usando a câmera do celular
camera_image = st.camera_input("Tire uma foto do QR Code")

# Quando uma imagem for capturada
if camera_image is not None:
    # Convertendo a imagem capturada para um formato que o OpenCV possa ler
    img = Image.open(camera_image)
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    # Decodificando o QR Code
    qr_data = decode_qr_code(img_cv)
    
    if qr_data:
        st.success(f"QR Code detectado: {qr_data}")
    else:
        st.warning("QR Code não detectado.")
