from datetime import datetime
import io
import threading
import time
from flask import Flask, jsonify, send_file
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)

mutex_servidor = threading.Lock()

AFORO_MAXIMO = 20000
boletos_actuales = 0
folio_actual = 0

USAR_SINCRONIZACION = True


def generar_pdf_qr(folio, fecha_str):
  buffer = io.BytesIO()
  c = canvas.Canvas(buffer, pagesize=letter)
  c.drawString(100, 750, "Auditorio Plata - Concierto Navideño")
  c.drawString(100, 730, f"Folio: {folio}")
  c.drawString(100, 710, f"Fecha y Hora: {fecha_str}")

  qr = qrcode.make(f"Folio: {folio} | Fecha: {fecha_str}")
  qr_path = f"temp_qr_{folio}.png"
  qr.save(qr_path)

  c.drawImage(qr_path, 100, 550, width=150, height=150)
  c.save()
  buffer.seek(0)
  return buffer


@app.route("/comprar-boleto", methods=["POST"])
def comprar_boleto():
  global boletos_actuales, folio_actual

  if USAR_SINCRONIZACION:
    with mutex_servidor:
      if boletos_actuales >= AFORO_MAXIMO:
        return (
            jsonify({
                "estado": "RECHAZADO",
                "mensaje": "Aforo lleno (Sold Out)",
            }),
            400,
        )

      time.sleep(0.001)
      boletos_actuales += 1
      folio_actual += 1
      mi_folio = folio_actual
  else:
    if boletos_actuales >= AFORO_MAXIMO:
      return (
          jsonify({"estado": "RECHAZADO", "mensaje": "Aforo lleno"}),
          400,
      )

    temp_boletos = boletos_actuales
    temp_folio = folio_actual

    time.sleep(0.01)

    boletos_actuales = temp_boletos + 1
    folio_actual = temp_folio + 1
    mi_folio = folio_actual

    print(
        f"[¡ALERTA DE CONDICIÓN DE CARRERA!] Hilo asignó el folio duplicado:"
        f" {mi_folio}"
    )

  tiempo_respuesta = datetime.now()
  fecha_str = tiempo_respuesta.strftime("%Y-%m-%d %H:%M:%S")
  pdf_buffer = generar_pdf_qr(mi_folio, fecha_str)

  return send_file(
      pdf_buffer,
      as_attachment=True,
      download_name=f"boleto_{mi_folio}.pdf",
      mimetype="application/pdf",
  )


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, threaded=True)