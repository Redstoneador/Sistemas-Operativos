from datetime import datetime
import threading
import time
import requests

URL_SERVIDOR = "http://localhost:5000/comprar-boleto"
TOTAL_SOLICITUDES = 100
hilos_activos = 20

barrera = threading.Barrier(hilos_activos)
bitacora_resultados = []
lock_bitacora = threading.Lock()


def spawner_worker(id_hilo, num_peticiones):
  barrera.wait()

  for i in range(num_peticiones):
    inicio = datetime.now()
    estado = "ERROR"

    try:
      response = requests.post(URL_SERVIDOR, timeout=10)
      fin = datetime.now()

      if response.status_code == 200:
        estado = "EXITO"
        nombre_archivo = f"boleto_hilo_{id_hilo}_req_{i}.pdf"
        with open(nombre_archivo, "wb") as f:
          f.write(response.content)
      else:
        estado = "RECHAZADO"
    except Exception as e:
      fin = datetime.now()
      estado = "TIMEOUT"

    with lock_bitacora:
      bitacora_resultados.append({
          "hilo": f"Thread-{id_hilo}",
          "duracion_seg": (fin - inicio).total_seconds(),
          "estado": estado,
      })


def ejecutar_prueba():
  print(
      f"Lanzando {TOTAL_SOLICITUDES} solicitudes usando {hilos_activos}"
      " spammers concurrentes..."
  )
  inicio_global = time.time()

  hilos = []
  peticiones_por_hilo = TOTAL_SOLICITUDES // hilos_activos
  resto = TOTAL_SOLICITUDES % hilos_activos

  for i in range(hilos_activos):
    pets = peticiones_por_hilo + (1 if i < resto else 0)
    if pets > 0:
      t = threading.Thread(target=spawner_worker, args=(i, pets))
      hilos.append(t)
      t.start()

  for t in hilos:
    t.join()

  fin_global = time.time()
  tiempo_total = fin_global - inicio_global

  exitosos = sum(1 for r in bitacora_resultados if r["estado"] == "EXITO")
  cumplio_meta = "SÍ (¡Excelente!)" if tiempo_total <= 60 else "NO"

  print("\n===============================")
  print("      REPORTE DE PRUEBA        ")
  print("===============================")
  print(f"Tiempo Total: {tiempo_total:.2f} segundos")
  print(f"¿Cumplió la meta de 60s?: {cumplio_meta}")
  print(f"Boletos Emitidos con Éxito: {exitosos} / {TOTAL_SOLICITUDES}")
  print("¡Los archivos PDF de los boletos han sido guardados en la carpeta!")
  print("===============================\n")


if __name__ == "__main__":
  ejecutar_prueba()