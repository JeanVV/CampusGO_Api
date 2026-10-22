from flask import Blueprint, send_file
from flask_jwt_extended import jwt_required
from services.vehiculo_service import VehiculoService
from utils.response import success_response, error_response

vehiculo_bp = Blueprint("vehiculos", __name__)

@vehiculo_bp.route("/api/vehiculos/<int:vehiculo_id>", methods=["GET"])
@jwt_required()
def obtener_vehiculo(vehiculo_id):
    service = VehiculoService()
    data, message, http_code = service.obtener_vehiculo(vehiculo_id)

    if data is None:
        return error_response(message, http_code)

    return success_response(data, message, http_code)

@vehiculo_bp.route("/api/vehiculos/<int:vehiculo_id>/foto", methods=["GET"])
def obtener_foto_vehiculo(vehiculo_id):
    service = VehiculoService()
    try:
        ruta_archivo, mimetype, message, http_code = service.obtener_foto_vehiculo(vehiculo_id)

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
        return error_response(f"No fue posible obtener la foto del vehículo: {str(ex)}", 500)