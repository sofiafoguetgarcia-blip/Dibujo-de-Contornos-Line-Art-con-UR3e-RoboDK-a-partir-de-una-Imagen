# -*- coding: utf-8 -*-
# Dibujo de contornos (line-art) con UR3e + RoboDK a partir de imagen (gato)
from robodk.robolink import *
from robodk.robomath import *
import cv2
import numpy as np
import math
import os

# ============ PARÁMETROS ============
IMAGE_PATH            = r"C:\Users\itc\Downloads\mandala.jpg"  # <-- Ruta a tu imagen del gato
MAX_ANCHO_MM          = 200.0      # ancho máximo del dibujo en la mesa
ALTURA_Z_DIBUJO       = 15.0       # “lápiz abajo” (mm)
ALTURA_Z_SUBIDA       = ALTURA_Z_DIBUJO + 30.0  # “lápiz arriba”
REDONDEO_DIBUJO_MM    = 2.0        # blend durante el trazo (no en bajadas/subidas)
EPSILON_SIMPLIFY_PX   = 2.0        # tolerancia Douglas-Peucker (px)
DECIMATE_STEP         = 1          # 1 = todos los puntos; 2 = salta 1 de cada 2; etc.
VEL_MM_S              = 60.0
ACEL_MM_S2            = 200.0
NOMBRE_FRAME_BASE     = 'UR3e Base'
NOMBRE_TARGET_CENTRO  = 'Target 1'

# ============ INICIALIZA ROBO DK ============
RDK = Robolink()
RDK.setRunMode(RUNMODE_SIMULATE)
robot = RDK.Item('', ITEM_TYPE_ROBOT);   assert robot.Valid(), "Robot no encontrado"
base  = RDK.Item(NOMBRE_FRAME_BASE, ITEM_TYPE_FRAME); 
if base.Valid(): robot.setFrame(base)
tool  = robot.getLink(ITEM_TYPE_TOOL)
if tool.Valid(): robot.setTool(tool)
t_center = RDK.Item(NOMBRE_TARGET_CENTRO, ITEM_TYPE_TARGET); 
assert t_center.Valid(), f"No se encontró '{NOMBRE_TARGET_CENTRO}'"

joints_iniciales = robot.Joints()   # para volver al final

# ============ UTILIDADES ============
def cargar_edges(path):
    assert os.path.isfile(path), f"No existe la imagen: {path}"
    img  = cv2.imread(path)
    assert img is not None, "OpenCV no pudo leer la imagen"
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Canny (ajusta si hace falta)
    edges = cv2.Canny(gray, 80, 160)         # bordes blancos (255) sobre fondo negro
    # Dilata un poco para “cerrar” trazos finos
    edges = cv2.dilate(edges, np.ones((3,3), np.uint8), iterations=1)
    return edges

def extraer_contornos_edges(edges):
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    # ordenar por longitud descendente (más largos primero)
    contours = sorted(contours, key=lambda c: cv2.arcLength(c, closed=False), reverse=True)
    return contours

def simplificar(contour, epsilon_px=2.0, decimate=1):
    if len(contour) < 2: return None
    approx = cv2.approxPolyDP(contour, epsilon_px, closed=False)
    pts = approx.reshape(-1,2)
    if decimate>1 and len(pts)>decimate:
        pts = pts[::decimate]
    if len(pts) < 2: return None
    return pts

def mm_por_px(img_w, max_ancho_mm):
    return max_ancho_mm / float(img_w)

def px_to_mm_centered(pts_px, img_w, img_h, s):
    cx, cy = img_w/2.0, img_h/2.0
    out=[]
    for x,y in pts_px:
        out.append(((x-cx)*s, -(y-cy)*s))  # invierte eje Y
    return out

def pose_xy(pose_ref, x, y, z):
    p = pose_ref.copy(); p.setPos([x,y,z]); return p

# ============ PROCESADO IMAGEN ============
edges = cargar_edges(IMAGE_PATH)
img_h, img_w = edges.shape[:2]
s = mm_por_px(img_w, MAX_ANCHO_MM)

contours = extraer_contornos_edges(edges)
assert contours, "No se detectaron contornos (revisa thresholds de Canny o la imagen)."

# Filtra contornos que son “marcos” pegados al borde (~tamaño imagen)
contours_filtrados=[]
for c in contours:
    x,y,w,h = cv2.boundingRect(c)
    if w >= img_w*0.98 or h >= img_h*0.98:
        continue
    contours_filtrados.append(c)

assert contours_filtrados, "Todos los contornos parecían marcos. Prueba a recortar la imagen o baja el umbral de Canny."

# Centro/orientación del dibujo: Target 1
pose_center = t_center.Pose()
xc, yc, _  = pose_center.Pos()

# Convierte contornos a trayectorias (poses)
trayectorias=[]
for c in contours_filtrados:
    pts_px = simplificar(c, EPSILON_SIMPLIFY_PX, DECIMATE_STEP)
    if pts_px is None: continue
    pts_mm = px_to_mm_centered(pts_px, img_w, img_h, s)
    tr=[]
    for dx,dy in pts_mm:
        tr.append(pose_xy(pose_center, xc+dx, yc+dy, ALTURA_Z_DIBUJO))
    if len(tr)>=2:
        trayectorias.append(tr)

assert trayectorias, "No quedó ninguna trayectoria válida. Baja EPSILON_SIMPLIFY_PX o DECIMATE_STEP."

# ============ MOVIMIENTO ROBOT ============
try:
    robot.setSpeed(VEL_MM_S); robot.setAcceleration(ACEL_MM_S2)

    # Ir a posición de referencia
    robot.MoveJ(t_center)

    for tr in trayectorias:
        p_first = tr[0]
        x0,y0,_ = p_first.Pos()

        # Aproximación con bolígrafo arriba
        robot.setRounding(0.0)
        robot.MoveL(pose_xy(pose_center, x0, y0, ALTURA_Z_SUBIDA))

        # Bajar (pen down)
        robot.MoveL(p_first)

        # Trazar con blend pequeño
        robot.setRounding(REDONDEO_DIBUJO_MM)
        for p in tr[1:]:
            robot.MoveL(p)

        # Opcional: volver al primer punto SIN blend para cerrar
        robot.setRounding(0.0)
        robot.MoveL(p_first)

        # Subir (pen up)
        robot.MoveL(pose_xy(pose_center, x0, y0, ALTURA_Z_SUBIDA))

    # Volver a la postura inicial
    robot.MoveJ(joints_iniciales)
    print("✔ Contorno(s) dibujado(s) desde imagen (gato).")

except TargetReachError as e:
    print("\n¡ERROR DE ALCANCE!\n", e)
    print("Ajusta MAX_ANCHO_MM, ALTURA_Z_DIBUJO o recoloca Target 1.")
except Exception as e:
    print("Fallo inesperado:", e)