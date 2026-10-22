class ViajeRepository:

    def __init__(self, connection):
        self.connection = connection

    def obtener_conductor_id_por_usuario(self, usuario_id):
        cursor = self.connection.cursor()
        try:
            sql = "SELECT id FROM conductor WHERE usuario_id = %s"
            cursor.execute(sql, (usuario_id,))
            fila = cursor.fetchone()
            if not fila:
                return None
            # Si el cursor retorna un diccionario (DictCursor) o una tupla:
            return fila["id"] if isinstance(fila, dict) else fila[0]
        finally:
            cursor.close()

    # Ejercicio 8 + Requerimiento de detalle completo (Conductor y Vehículo)
    def obtener_por_id(self, viaje_id):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT
                    v.id, v.origen, v.destino, v.fecha, v.hora,
                    v.cupos, v.precio, v.estado,
                    c.usuario_id AS conductor_usuario_id,
                    u.nombres, u.apellidos,
                    CONCAT(u.nombres, ' ', u.apellidos) AS conductor,
                    u.foto AS conductor_foto,
                    c.calificacion,
                    vh.id AS vehiculo_id,
                    vh.marca AS vehiculo_marca,
                    vh.modelo AS vehiculo_modelo,
                    vh.placa AS vehiculo_placa,
                    vh.color AS vehiculo_color,
                    vh.foto AS vehiculo_foto
                FROM viaje v
                INNER JOIN conductor c ON c.id = v.conductor_id
                INNER JOIN usuario u ON u.id = c.usuario_id
                LEFT JOIN vehiculo vh ON vh.id = v.vehiculo_id
                WHERE v.id = %s
                LIMIT 1
            """
            cursor.execute(sql, (viaje_id,))
            return cursor.fetchone()
        finally:
            cursor.close()

    # Nuevo requerimiento: Obtener la lista de pasajeros asociados al viaje
    def obtener_pasajeros(self, viaje_id):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT 
                    u.id AS usuario_id,
                    u.nombres,
                    u.apellidos,
                    CONCAT(u.nombres, ' ', u.apellidos) AS nombre_completo,
                    u.email,
                    u.foto,
                    r.id AS reserva_id,
                    r.estado AS estado_reserva
                FROM reserva r
                INNER JOIN usuario u ON r.usuario_id = u.id
                WHERE r.viaje_id = %s AND r.estado != 'CANCELADO'
            """
            cursor.execute(sql, (viaje_id,))
            return cursor.fetchall()
        finally:
            cursor.close()

    def crear(self, conductor_id, datos):
        cursor = self.connection.cursor()
        try:
            sql = """
                INSERT INTO viaje (
                    conductor_id, vehiculo_id, origen, destino, fecha,
                    hora, cupos, precio, estado
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'DISPONIBLE')
            """
            cursor.execute(sql, (
                conductor_id,
                datos.get("vehiculo_id"),
                datos["origen"],
                datos["destino"],
                datos["fecha"],
                datos["hora"],
                datos["cupos"],
                datos["precio"]
            ))
            return cursor.lastrowid
        finally:
            cursor.close()

    # Ejercicio 7: Consulta si el conductor ya tiene un viaje en el mismo horario y ruta
    def existe_viaje_duplicado(self, conductor_id, fecha, hora, origen, destino):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT id FROM viaje 
                WHERE conductor_id = %s AND fecha = %s AND hora = %s 
                  AND origen = %s AND destino = %s AND estado != 'CANCELADO'
            """
            cursor.execute(sql, (conductor_id, fecha, hora, origen, destino))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # Ejercicios 1, 2 y 3: Filtros por texto (origen/destino), fecha, estado, precios y cupos
    def listar(self, origen=None, destino=None, fecha=None, estado=None, 
               precio_min=None, precio_max=None, solo_disponibles=False, desde=None):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT
                    v.id, v.origen, v.destino, v.fecha, v.hora,
                    v.cupos, v.precio, v.estado,
                    c.usuario_id AS conductor_usuario_id,
                    CONCAT(u.nombres, ' ', u.apellidos) AS conductor,
                    v.vehiculo_id
                FROM viaje v
                INNER JOIN conductor c ON c.id = v.conductor_id
                INNER JOIN usuario u ON u.id = c.usuario_id
                WHERE 1=1
            """
            params = []
            if origen:
                sql += " AND v.origen LIKE %s"
                params.append(f"%{origen}%")
            if destino:
                sql += " AND v.destino LIKE %s"
                params.append(f"%{destino}%")
            if fecha:
                sql += " AND v.fecha = %s"
                params.append(fecha)
            if estado:
                sql += " AND v.estado = %s"
                params.append(estado)

            # Ejercicio 1: Rango de precios
            if precio_min is not None:
                sql += " AND v.precio >= %s"
                params.append(precio_min)
            if precio_max is not None:
                sql += " AND v.precio <= %s"
                params.append(precio_max)

            # Ejercicio 2: Solo viajes con estado DISPONIBLE y cupos > 0
            if solo_disponibles:
                sql += " AND v.estado = 'DISPONIBLE' AND v.cupos > 0"

            # Ejercicio 3: Fecha mayor o igual a 'desde'
            if desde:
                sql += " AND v.fecha >= %s"
                params.append(desde)

            sql += " ORDER BY v.fecha, v.hora"
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()

    def actualizar(self, viaje_id, datos):
        cursor = self.connection.cursor()
        try:
            sql = """
                UPDATE viaje
                SET origen = %s,
                    destino = %s,
                    fecha = %s,
                    hora = %s,
                    cupos = %s,
                    precio = %s
                WHERE id = %s
            """
            cursor.execute(sql, (
                datos["origen"],
                datos["destino"],
                datos["fecha"],
                datos["hora"],
                datos["cupos"],
                datos["precio"],
                viaje_id
            ))
            return cursor.rowcount
        finally:
            cursor.close()

    def cancelar(self, viaje_id):
        cursor = self.connection.cursor()
        try:
            sql = """
                UPDATE viaje
                SET estado = 'CANCELADO'
                WHERE id = %s
            """
            cursor.execute(sql, (viaje_id,))
            return cursor.rowcount
        finally:
            cursor.close()

    # Ejercicio 4: Listar viajes creados por un conductor específico
    def listar_por_conductor(self, conductor_id):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT id, vehiculo_id, origen, destino, fecha, hora, cupos, precio, estado
                FROM viaje
                WHERE conductor_id = %s
                ORDER BY fecha DESC, hora DESC
            """
            cursor.execute(sql, (conductor_id,))
            return cursor.fetchall()
        finally:
            cursor.close()

    # Ejercicio 5: Actualizar únicamente el campo cupos
    def actualizar_cupos(self, viaje_id, cupos):
        cursor = self.connection.cursor()
        try:
            sql = "UPDATE viaje SET cupos = %s WHERE id = %s"
            cursor.execute(sql, (cupos, viaje_id))
            return cursor.rowcount
        finally:
            cursor.close()

    # Ejercicio 6: Cambiar el estado del viaje
    def actualizar_estado(self, viaje_id, nuevo_estado):
        cursor = self.connection.cursor()
        try:
            sql = "UPDATE viaje SET estado = %s WHERE id = %s"
            cursor.execute(sql, (nuevo_estado, viaje_id))
            return cursor.rowcount
        finally:
            cursor.close()

    # Ejercicio 10: Conteo agrupado con GROUP BY por estado
    def obtener_resumen_estados(self, conductor_id):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT estado, COUNT(*) AS total
                FROM viaje
                WHERE conductor_id = %s
                GROUP BY estado
            """
            cursor.execute(sql, (conductor_id,))
            return cursor.fetchall()
        finally:
            cursor.close()