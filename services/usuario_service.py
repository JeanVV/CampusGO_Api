import os
import mimetypes
from database import get_connection
from repositories.usuario_repository import UsuarioRepository

class UsuarioService:
    def obtener_perfil(self, usuario_id):
        connection = get_connection()
        try:
            repository = UsuarioRepository(connection)
            usuario = repository.buscar_por_id(usuario_id)

            if usuario is None:
                return None, "Usuario no encontrado", 404

            if usuario["estado"] != "ACTIVO":
                return None, "El usuario se encuentra inactivo", 403

            data = {
                "usuario_id": usuario["id"],
                "email": usuario["email"],
                "nombres": usuario["nombres"],
                "apellidos": usuario["apellidos"],
                "rol": usuario["rol"],
                "estado": usuario["estado"],
                "fecha_registro": (
                    usuario["fecha_registro"].isoformat()
                    if usuario["fecha_registro"] is not None
                    else None
                )
            }

            return data, "Perfil obtenido correctamente", 200
        finally:
            connection.close()

    def obtener_foto_perfil(self, usuario_id):
        connection = get_connection()
        try:
            repository = UsuarioRepository(connection)
            usuario = repository.obtener_foto_por_usuario(usuario_id)

            if usuario is None:
                return None, None, "Usuario no encontrado", 404

            if usuario["estado"] != "ACTIVO":
                return None, None, "El usuario se encuentra inactivo", 403

            nombre_foto = usuario.get("foto")
            if not nombre_foto:
                nombre_foto = "default.png"

            nombre_seguro = os.path.basename(nombre_foto)

            # Apunta directamente a uploads/perfiles en la raíz del proyecto
            directorio_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ruta_base = os.path.realpath(os.path.join(directorio_raiz, "uploads", "perfiles"))
            ruta_archivo = os.path.realpath(os.path.join(ruta_base, nombre_seguro))

            if os.path.commonpath([ruta_base, ruta_archivo]) != ruta_base:
                return None, None, "Ruta de foto no válida", 400

            if not os.path.isfile(ruta_archivo):
                return None, None, "Archivo de foto no encontrado", 404

            mimetype, _ = mimetypes.guess_type(ruta_archivo)
            if mimetype is None or not mimetype.startswith("image/"):
                return None, None, "El archivo almacenado no es una imagen válida", 415

            return ruta_archivo, mimetype, "Foto de perfil obtenida correctamente", 200
        finally:
            connection.close()