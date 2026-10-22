from datetime import datetime, date, time, timedelta
from database import get_connection
from repositories.viaje_repository import ViajeRepository

class ViajeService:
    def _serializar_fila(self, fila):
        """Convierte objetos date, time o timedelta de MySQL a string para evitar errores con JSON."""
        if not fila:
            return fila
        for clave, valor in fila.items():
            if isinstance(valor, (datetime, date, time)):
                fila[clave] = valor.isoformat()
            elif isinstance(valor, timedelta):
                total_seconds = int(valor.total_seconds())
                horas = total_seconds // 3600
                minutos = (total_seconds % 3600) // 60
                fila[clave] = f"{horas:02d}:{minutos:02d}"
        return fila

    def crear(self, usuario_id, datos):
        obligatorios = ["origen", "destino", "fecha", "hora", "cupos", "precio"]

        if any(campo not in datos for campo in obligatorios):
            return None, "Faltan datos obligatorios", 400

        if int(datos["cupos"]) <= 0:
            return None, "Los cupos deben ser mayores que cero", 400

        if float(datos["precio"]) < 0:
            return None, "El precio no puede ser negativo", 400

        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            conductor_id = repository.obtener_conductor_id_por_usuario(usuario_id)
            if conductor_id is None:
                return None, "El usuario no posee perfil de conductor", 403

            if repository.existe_viaje_duplicado(
                conductor_id, datos["fecha"], datos["hora"], datos["origen"], datos["destino"]
            ):
                return None, "Ya existe un viaje registrado para el mismo origen, destino, fecha y hora", 409

            viaje_id = repository.crear(conductor_id, datos)
            connection.commit()
            return {"viaje_id": viaje_id}, "Viaje creado correctamente", 201
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def listar(self, filtros):
        p_min = filtros.get("precio_min")
        p_max = filtros.get("precio_max")
        desde = filtros.get("desde")

        val_min, val_max = None, None
        try:
            if p_min is not None:
                val_min = float(p_min)
            if p_max is not None:
                val_max = float(p_max)
        except ValueError:
            return None, "Los valores de precio_min y precio_max deben ser numéricos", 400

        if val_min is not None and val_max is not None and val_min > val_max:
            return None, "precio_min no puede ser mayor que precio_max", 400

        if desde:
            try:
                datetime.strptime(desde, "%Y-%m-%d")
            except ValueError:
                return None, "El formato del parámetro 'desde' debe ser YYYY-MM-DD", 400

        solo_disponibles = str(filtros.get("solo_disponibles")).lower() in ("true", "1")

        connection = get_connection()
        try:
            repository = ViajeRepository(connection)

            viajes = repository.listar(
                origen=filtros.get("origen"),
                destino=filtros.get("destino"),
                fecha=filtros.get("fecha"),
                estado=filtros.get("estado"),
                precio_min=val_min,
                precio_max=val_max,
                solo_disponibles=solo_disponibles,
                desde=desde
            )

            viajes = [self._serializar_fila(v) for v in viajes]
            return viajes, "Viajes obtenidos correctamente", 200
        finally:
            connection.close()

    def listar_mios(self, usuario_id):
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            conductor_id = repository.obtener_conductor_id_por_usuario(usuario_id)
            if conductor_id is None:
                return None, "El usuario no posee perfil de conductor", 403

            viajes = repository.listar_por_conductor(conductor_id)
            viajes = [self._serializar_fila(v) for v in viajes]
            return viajes, "Viajes del conductor obtenidos correctamente", 200
        finally:
            connection.close()

    def obtener(self, viaje_id):
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)

            if viaje is None:
                return None, "Viaje no encontrado", 404

            viaje = self._serializar_fila(viaje)
            pasajeros = repository.obtener_pasajeros(viaje_id)
            viaje["pasajeros"] = pasajeros

            return viaje, "Viaje obtenido correctamente", 200
        finally:
            connection.close()

    def obtener_lista_pasajeros(self, viaje_id):
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)

            if viaje is None:
                return None, "Viaje no encontrado", 404

            pasajeros = repository.obtener_pasajeros(viaje_id)
            return pasajeros, "Pasajeros obtenidos correctamente", 200
        finally:
            connection.close()

    def actualizar(self, usuario_id, viaje_id, datos):
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)

            if viaje is None:
                return None, "Viaje no encontrado", 404

            if str(viaje["conductor_usuario_id"]) != str(usuario_id):
                return None, "No puede modificar un viaje de otro conductor", 403

            if viaje["estado"] in ("FINALIZADO", "CANCELADO"):
                return None, "El estado actual no permite modificar el viaje", 409

            repository.actualizar(viaje_id, datos)
            connection.commit()
            return {"viaje_id": viaje_id}, "Viaje actualizado correctamente", 200
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def actualizar_cupos(self, usuario_id, viaje_id, datos):
        if "cupos" not in datos:
            return None, "Debe enviar el campo 'cupos'", 400

        try:
            cupos = int(datos["cupos"])
        except (ValueError, TypeError):
            return None, "El campo cupos debe ser un número entero", 400

        if cupos < 0:
            return None, "Los cupos no pueden ser menores que cero", 400

        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)

            if viaje is None:
                return None, "Viaje no encontrado", 404

            if str(viaje["conductor_usuario_id"]) != str(usuario_id):
                return None, "No puede modificar un viaje de otro conductor", 403

            if viaje["estado"] in ("FINALIZADO", "CANCELADO"):
                return None, f"No se pueden modificar cupos en un viaje con estado {viaje['estado']}", 409

            repository.actualizar_cupos(viaje_id, cupos)
            connection.commit()
            return {"viaje_id": viaje_id, "cupos": cupos}, "Cupos actualizados correctamente", 200
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def actualizar_estado(self, usuario_id, viaje_id, datos):
        nuevo_estado = datos.get("estado")
        estados_validos = ("DISPONIBLE", "COMPLETO", "FINALIZADO", "CANCELADO")

        if not nuevo_estado or nuevo_estado not in estados_validos:
            return None, f"Estado inválido. Permitidos: {list(estados_validos)}", 400

        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)

            if viaje is None:
                return None, "Viaje no encontrado", 404

            if str(viaje["conductor_usuario_id"]) != str(usuario_id):
                return None, "No puede modificar el estado de un viaje de otro conductor", 403

            estado_actual = viaje["estado"]
            if estado_actual == "CANCELADO":
                return None, "Un viaje cancelado no puede cambiar de estado", 409

            if estado_actual == "FINALIZADO" and nuevo_estado != "FINALIZADO":
                return None, "Un viaje finalizado no puede ser reactivado", 409

            repository.actualizar_estado(viaje_id, nuevo_estado)
            connection.commit()
            return {"viaje_id": viaje_id, "estado": nuevo_estado}, "Estado actualizado correctamente", 200
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def cancelar(self, usuario_id, viaje_id):
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            viaje = repository.obtener_por_id(viaje_id)

            if viaje is None:
                return None, "Viaje no encontrado", 404

            if str(viaje["conductor_usuario_id"]) != str(usuario_id):
                return None, "No puede cancelar un viaje de otro conductor", 403

            if viaje["estado"] == "FINALIZADO":
                return None, "No se puede cancelar un viaje que ya está finalizado", 409

            if viaje["estado"] == "CANCELADO":
                return None, "El viaje ya se encuentra cancelado", 409

            repository.cancelar(viaje_id)
            connection.commit()
            return {"viaje_id": viaje_id}, "Viaje cancelado correctamente", 200
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def obtener_resumen(self, usuario_id):
        connection = get_connection()
        try:
            repository = ViajeRepository(connection)
            conductor_id = repository.obtener_conductor_id_por_usuario(usuario_id)
            if conductor_id is None:
                return None, "El usuario no posee perfil de conductor", 403

            resumen = repository.obtener_resumen_estados(conductor_id)
            return resumen, "Resumen obtenido correctamente", 200
        finally:
            connection.close()