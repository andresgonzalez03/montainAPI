from fastapi import HTTPException
from db import get_connection
from models import *
from passlib.context import CryptContext
from auth import *
from psycopg2.extras import RealDictRow
from typing import cast

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def readAll():
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM usuarios;")
            usuarios = cur.fetchall()
        return usuarios
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión: {e}")
    finally:
        if conn:
            conn.close()


def readById(id_usuarios: int):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "select * from usuarios where id_usuarios = %s;", (id_usuarios,))
            usuario = cur.fetchone()
        return usuario
    except Exception as e:
        return {"status": -1, "message": f"Error de conexión{e}"}
    finally:
        if conn:
            conn.close()


def create(usuario: UsuarioCreate):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            if usuario.contrasena is None:
                raise HTTPException(
                    status_code=400, detail="La contraseña es obligatoria")
            hashed_password = pwd_context.hash(usuario.contrasena)
            cur.execute("INSERT INTO usuarios (nombre, apellido, email, contrasena, fecha_registro, id_suscripciones) "
                        "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_usuarios",
                        (usuario.nombre, usuario.apellido, usuario.email, hashed_password, usuario.fecha_registro, usuario.id_suscripciones))
            resultado = cur.fetchone()
            resultado = cast(RealDictRow, resultado)
            if resultado is None:
                raise HTTPException(
                    status_code=500, detail="Error: No se devolvió ningún ID tras el INSERT.")
            new_id = resultado["id_usuarios"]
        conn.commit()
        return {"message": "Usuario creado correctamente", "id_usuarios": new_id}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()


def update(id_usuario: int, data: dict):
    conn = None
    try:
        campos_permitidos = {"nombre", "apellido", "email"}
        data_filtrada = {k: v for k,
                         v in data.items() if k in campos_permitidos}

        if not data_filtrada:
            raise HTTPException(
                status_code=400, detail="No se proporcionaron datos válidos para actualizar.")

        conn = get_connection()
        with conn.cursor() as cur:
            set_clause = ', '.join(
                [f"{key} = %s" for key in data_filtrada.keys()])
            values = tuple(data_filtrada.values()) + (id_usuario,)

            query = f"UPDATE usuarios SET {set_clause} WHERE id_usuarios = %s"
            cur.execute(query, values)

            if cur.rowcount == 0:
                raise HTTPException(
                    status_code=404, detail="Usuario no encontrado")

        conn.commit()
        return {"message": "Usuario actualizado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()


def update_password_db(id_usuario: int, contrasena_actual: str, nueva_contrasena: str):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT contrasena FROM usuarios WHERE id_usuarios = %s", (id_usuario,))
            resultado = cur.fetchone()
            if resultado is None:
                raise HTTPException(
                    status_code=404, detail="Usuario no encontrado")
            resultado = cast(RealDictRow, resultado)
            if resultado is None:
                raise HTTPException(
                    status_code=500, detail="Error: No se devolvió ningún ID tras el cambio.")
            contrasena_hash = resultado["contrasena"]

            if not pwd_context.verify(contrasena_actual, contrasena_hash):
                raise HTTPException(
                    status_code=401, detail="La contrasena actual es incorrecta")

            nueva_contrasena_hash = pwd_context.hash(nueva_contrasena)

            cur.execute("UPDATE usuarios SET contrasena = %s WHERE id_usuarios = %s",
                        (nueva_contrasena_hash, id_usuario))
            if cur.rowcount == 0:
                raise HTTPException(
                    status_code=404, detail="Usuario no encontrado")

        conn.commit()
        return {"message": "contrasena actualizada correctamente"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()


def login(login_data: LoginRequest) -> dict:
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id_usuarios, contrasena FROM usuarios WHERE email = %s",
                (login_data.email,)
            )
            resultado = cur.fetchone()
            if resultado is None:
                raise HTTPException(
                    status_code=401, detail="Credenciales incorrectas")
            resultado = cast(RealDictRow, resultado)
            id_usuario = resultado["id_usuarios"]
            contrasena_hash = resultado["contrasena"]
            if not pwd_context.verify(login_data.contrasena, contrasena_hash):
                raise HTTPException(
                    status_code=401, detail="Credenciales incorrectas")
            token = crear_token({"sub": id_usuario})
            return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()


def delete(id_usuario: int):
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "delete from usuario where id_usuario = %s", (id_usuario,))
            if cur.rowcount == 0:
                raise HTTPException(
                    status_code=404, detail="Usuario no encontrado")
        conn.commit()
        return {"message": "Usuario eliminada correctamente"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error eliminando suscripción: {str(e)}")
    finally:
        if conn:
            conn.close()
