from fastapi import HTTPException
from db import get_connection
from models import HistorialActividad, Usuario, Ruta
from datetime import datetime, timedelta

def getAll(id_usuario: int):
     conn = None
     try: 
          conn =  get_connection()
          with conn.cursor() as cur:
               consulta = """
        SELECT h.id_ruta, r.nombre_ruta, h.fecha
        FROM historial_actividades h
        JOIN rutas r ON h.id_ruta = r.id_ruta
        WHERE h.id_usuarios = %s
        ORDER BY h.fecha DESC;
        """
               cur.execute(consulta, (id_usuario,))
               historial = cur.fetchall()
               return historial
     except Exception as e:
          print(f"Error al obtener historial: {e}")
          return []
     finally:
          if conn:
               conn.close()
         
def getByRoute(id_usuario: int, nombre_ruta: str):
     conn = None
     try:
          conn = get_connection()
          with conn.cursor() as cur:
               cur.execute("""
               select h.id_ruta, r.nombre_ruta, h.fecha
               from historial_actividades h 
               join rutas r on h.id_ruta = r.id_ruta
               where h.id_usuarios = %s and r.nombre_ruta = %s
               """, (id_usuario, nombre_ruta))
               historial = cur.fetchall()
               if not historial:
                    raise ValueError(f"No hay historial para la ruta '{nombre_ruta}' del usuario {id_usuario}.")
               return historial
     except Exception as e:
          raise Exception(f"Error al obtener el historial: {e}")
     finally:
          if conn:
               conn.close()

def getByDate(id_usuarios: int, fecha_inicio: str = "", fecha_fin: str = "", ordenar: str = "desc", page: int = 1, page_size: int = 10):
    conn = None
    try:
        if not fecha_inicio:
            fecha_inicio = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not fecha_fin:
            fecha_fin = datetime.today().strftime("%Y-%m-%d")

        orden_sql = "DESC" if ordenar.lower() == "desc" else "ASC"
        offset = (page - 1) * page_size  

        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT h.id_ruta, r.nombre_ruta, h.fecha
                FROM historial_actividades h
                JOIN rutas r ON h.id_ruta = r.id_ruta
                WHERE h.id_usuarios = %s 
                AND h.fecha BETWEEN %s AND %s
                ORDER BY h.fecha {orden_sql}
                LIMIT %s OFFSET %s;
            """, (id_usuarios, fecha_inicio, fecha_fin, page_size, offset))
            historial = cur.fetchall()
            if not historial:
                raise ValueError(f"No hay historial en la página {page} para el usuario {id_usuarios}.")
        return historial
    except Exception as e:
        raise Exception(f"Error al obtener historial: {e}")
    finally:
        if conn:
            conn.close()

def create(historial: HistorialActividad):
     try:
          conn = get_connection()
          with conn.cursor() as cur:
               cur.execute("""
                    insert into historial_actividades (id_usuarios, id_ruta, fecha)
                    values (%s, %s, %s)""", (historial.id_usuarios, historial.id_ruta, historial.fecha))
               conn.commit()
          return {"message": "Historial creado correctamente"}
     except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear historial: {e}")
     finally:
        if conn:
            conn.close()



