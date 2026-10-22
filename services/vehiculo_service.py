import os
import mimetypes
from database import get_connection
from repositories.vehiculo_repository import VehiculoRepository

class VehiculoService:
    def obtener_vehiculo(self, vehiculo_id):
        connection = get_connection()
        try:
            repository = VehiculoRepository(connection)
            vehiculo = repository.obtener_por_id(vehiculo_id)

            if vehiculo is None:
                return None, "Vehículo no encontrado", 404

            return vehiculo, "Vehículo obtenido correctamente", 200
        finally:
            connection.close()

    def obtener_foto_vehiculo(self, vehiculo_id):
        connection = get_connection()
        try:
            repository = VehiculoRepository(connection)
            vehiculo = repository.obtener_foto_por_id(vehiculo_id)

            if vehiculo is None:
                return None, None, "Vehículo no encontrado", 404

            nombre_foto = vehiculo.get("foto")
            if not nombre_foto:
                nombre_foto = "default_car.png"

            nombre_seguro = os.path.basename(nombre_foto)

            # Apunta directamente a uploads/vehiculos en la raíz del proyecto
            directorio_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ruta_base = os.path.realpath(os.path.join(directorio_raiz, "uploads", "vehiculos"))
            ruta_archivo = os.path.realpath(os.path.join(ruta_base, nombre_seguro))

            if os.path.commonpath([ruta_base, ruta_archivo]) != ruta_base:
                return None, None, "Ruta de foto no válida", 400

            if not os.path.isfile(ruta_archivo):
                return None, None, "Archivo de foto no encontrado", 404

            mimetype, _ = mimetypes.guess_type(ruta_archivo)
            if mimetype is None or not mimetype.startswith("image/"):
                return None, None, "El archivo almacenado no es una imagen válida", 415

            return ruta_archivo, mimetype, "Foto obtenida correctamente", 200
        finally:
            connection.close()