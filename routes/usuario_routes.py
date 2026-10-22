from flask import Blueprint, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.usuario_service import UsuarioService
from utils.response import success_response, error_response

usuario_bp = Blueprint("usuarios", __name__)

@usuario_bp.route("/api/perfil", methods=["GET"])
@jwt_required()
def obtener_perfil():
    usuario_id = get_jwt_identity()
    service = UsuarioService()
    data, message, http_code = service.obtener_perfil(usuario_id)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)

@usuario_bp.route("/api/perfil/foto", methods=["GET"])
@jwt_required()
def obtener_foto_perfil():
    """Devuelve la foto del usuario autenticado mediante JWT."""
    usuario_id = get_jwt_identity()
    service = UsuarioService()

    try:
        ruta_archivo, mimetype, message, http_code = service.obtener_foto_perfil(usuario_id)

        if ruta_archivo is None:
            return error_response(message, http_code)

        response = send_file(
            ruta_archivo,
            mimetype=mimetype,
            as_attachment=False,
            conditional=True
        )
        response.headers["Cache-Control"] = "private, max-age=300"
        return response

    except Exception as ex:
        print(f"ERROR FOTO PERFIL: {ex}")
        return error_response("No fue posible obtener la foto de perfil", 500)

@usuario_bp.route("/api/usuarios/<int:usuario_id>/foto", methods=["GET"])
def obtener_foto_usuario_por_id(usuario_id):
    """Devuelve la foto de cualquier usuario por su ID (usado para ver al conductor o pasajeros)."""
    service = UsuarioService()
    try:
        ruta_archivo, mimetype, message, http_code = service.obtener_foto_perfil(usuario_id)

        if ruta_archivo is None:
            return error_response(message, http_code)

        response = send_file(
            ruta_archivo,
            mimetype=mimetype,
            as_attachment=False,
            conditional=True
        )
        response.headers["Cache-Control"] = "public, max-age=86400"
        return response

    except Exception as ex:
        print(f"ERROR FOTO USUARIO: {ex}")
        return error_response("No fue posible obtener la foto del usuario", 500)