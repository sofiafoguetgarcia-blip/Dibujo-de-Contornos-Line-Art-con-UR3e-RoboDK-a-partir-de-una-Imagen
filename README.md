# Dibujo-de-Contornos-Line-Art-con-UR3e-RoboDK-a-partir-de-una-Imagen
Este proyecto permite convertir cualquier imagen (fotografía, dibujo, icono, mandala, etc.) en un conjunto de contornos simplificados, para que un robot UR3e pueda dibujarlos en una superficie utilizando RoboDK.
Convierte:

Imagen → bordes (Canny) → contornos → simplificación → trayectorias → movimientos del robot

Perfecto para realizar line‑art, vinilos, plantillas, mandalas y dibujos estilizados.

🚀 Funcionalidades
✔ Carga una imagen desde disco
✔ La convierte a bordes mediante Canny
✔ Limpia trazos con dilatación morfológica
✔ Extrae todos los contornos con OpenCV
✔ Filtra contornos demasiado grandes (marcos)
✔ Simplifica trayectorias con Douglas‑Peucker
✔ Reescala manteniendo proporciones
✔ Centra el dibujo en un Target de RoboDK
✔ Control del robot (velocidad, aceleración, blend, alturas)
✔ Genera un dibujo ordenado, suave y seguro

# Requisitos
  Python

      Python 3.8+
      OpenCV (pip install opencv-python)
      Numpy
      RoboDK API (pip install robodk)

  RoboDK

    Tener cargado un robot UR3e
    Tener un Frame base llamado: UR3e Base
    Tener un Target llamado: Target 1
    Herramienta configurada en el robot (lápiz, rotulador, etc.)


# Proceso de Imagen

    - Se carga la imagen (mandala.jpg)
    - Conversión a escala de grises
    - Cálculo de bordes con Canny
    - Dilatación para unir líneas
    - Extracción de contornos
    - Simplificación
    - Conversión px → mm
    - Centrado en Target 1


# Movimiento del Robot
  Para cada contorno:

    - El robot sube el lápiz (ALTURA_Z_SUBIDA)
    - Se acerca al inicio del trazo
    - Baja (ALTURA_Z_DIBUJO)
    - Traza toda la trayectoria con blend suave
    - Cierra el ciclo opcionalmente
    - Sube el lápiz
    - Pasa al siguiente contorno

  Al final → vuelve a la posición original.

# Principales parámetros editables
    PythonIMAGE_PATH            = r"C:\...\mandala.jpg"MAX_ANCHO_MM          = 200.0ALTURA_Z_DIBUJO       = 15.0ALTURA_Z_SUBIDA       = ALTURA_Z_DIBUJO + 30.0REDONDEO_DIBUJO_MM    = 2.0EPSILON_SIMPLIFY_PX   = 2.0DECIMATE_STEP         = 1VEL_MM_S              = 60.0ACEL_MM_S2            = 200.0Mostrar más líneas

# Ejecución
  Shellpython lineart_ur3e.pyMostrar más líneas
  RoboDK debe estar abierto y con el UR3e cargado.

# Consejos para mejores resultados

  Prueba imágenes claras y con líneas definidas
  Ajusta Canny si no salen los bordes:
  Pythonedges = cv2.Canny(gray, 60, 120)Mostrar más líneas
  
  Reduce EPSILON_SIMPLIFY_PX si el dibujo se ve demasiado “angular”
  Aumenta DECIMATE_STEP para acelerar el dibujo
  Asegúrate de que Max ancho mm no haga que el robot salga de su workspace
  Recoloca Target 1 según donde quieras el dibujo


# Seguridad
  Este código es para simulación, pero puede ejecutarse en robot real.
  Verifica SIEMPRE:
    ⚠ límites del robot
    
    ⚠ altura mínima para no golpear la mesa
    
    ⚠ herramienta correctamente medida
    
    ⚠ movimientos sin blend en bajadas/subidas
