import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
from pyzbar.pyzbar import decode
from PIL import Image
import av

# Colores
COLOR_VERDE = PatternFill(start_color="00FF00", end_color="00FF00", fill_type="solid")
COLOR_MORADO = PatternFill(start_color="800080", end_color="800080", fill_type="solid")

st.set_page_config(page_title="Inventario Biblioteca", layout="centered")
st.title("📚 Inventario Biblioteca")
st.write("Escanea códigos automáticamente con la cámara y actualiza el inventario.")

# Excel por defecto
DEFAULT_EXCEL = "inventario.xlsx"
import os
from openpyxl import Workbook
if not os.path.exists(DEFAULT_EXCEL):
    wb = Workbook()
    sheet = wb.active
    sheet.title = "Inventario"
    sheet.append(["Codigo", "Titulo", "Autor"])
    sheet.append(["12345", "El Quijote", "Cervantes"])
    sheet.append(["67890", "Cien Años de Soledad", "García Márquez"])
    wb.save(DEFAULT_EXCEL)

uploaded_file = st.file_uploader("Sube tu archivo Excel (opcional)", type=["xlsx"])
excel_path = DEFAULT_EXCEL if not uploaded_file else "inventario.xlsx"
if uploaded_file:
    with open(excel_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

wb = load_workbook(excel_path)
sheet = wb.active
df = pd.read_excel(excel_path)

codigo_columna = None
for col in df.columns:
    if "codigo" in col.lower():
        codigo_columna = col
        break

if not codigo_columna:
    st.error("No se encontró ninguna columna que contenga 'codigo'.")
else:
    codigo_a_fila = {str(row[codigo_columna]): idx+2 for idx, row in df.iterrows()}

    st.subheader("Escanea el código con la cámara")

    class BarcodeScanner(VideoTransformerBase):
        def __init__(self):
            self.last_code = None

        def transform(self, frame):
            img = frame.to_image()
            decoded_objects = decode(img)
            for obj in decoded_objects:
                self.last_code = obj.data.decode("utf-8")
            return frame

    ctx = webrtc_streamer(key="barcode", video_transformer_factory=BarcodeScanner)

    codigo_detectado = None
    if ctx.video_transformer:
        codigo_detectado = ctx.video_transformer.last_code

    if codigo_detectado:
        st.success(f"Código detectado: {codigo_detectado}")

    codigo_manual = st.text_input("Ingresa el código manualmente (opcional)", value=codigo_detectado if codigo_detectado else "")

    if st.button("Actualizar Inventario"):
        if codigo_manual.strip() != "":
            codigo = codigo_manual.strip()
            if codigo in codigo_a_fila:
                fila = codigo_a_fila[codigo]
                celda = f"A{fila}"
                sheet[celda].fill = COLOR_VERDE
                sheet[celda].font = Font(bold=True)
                st.success(f"Código {codigo} encontrado y marcado en verde.")
            else:
                nueva_fila = sheet.max_row + 1
                sheet[f"A{nueva_fila}"] = codigo
                sheet[f"A{nueva_fila}"].fill = COLOR_MORADO
                sheet[f"A{nueva_fila}"].font = Font(bold=True)
                st.warning(f"Código {codigo} agregado como nuevo y marcado en morado.")

            wb.save(excel_path)
        else:
            st.error("Por favor, escanea o ingresa el código manualmente.")

    st.subheader("Inventario actualizado")
    st.dataframe(pd.read_excel(excel_path))

    with open(excel_path, "rb") as f:
        st.download_button("Descargar Excel actualizado", f, file_name="inventario_actualizado.xlsx")
