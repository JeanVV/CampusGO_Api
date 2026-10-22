class VehiculoRepository:
    def __init__(self, connection):
        self.connection = connection

    def obtener_por_id(self, vehiculo_id):
        cursor = self.connection.cursor()
        try:
            sql = """
                SELECT id, conductor_id, marca, modelo, placa, color, asientos, foto
                FROM vehiculo
                WHERE id = %s
                LIMIT 1
            """
            cursor.execute(sql, (vehiculo_id,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def obtener_foto_por_id(self, vehiculo_id):
        cursor = self.connection.cursor()
        try:
            sql = "SELECT id, foto FROM vehiculo WHERE id = %s LIMIT 1"
            cursor.execute(sql, (vehiculo_id,))
            return cursor.fetchone()
        finally:
            cursor.close()