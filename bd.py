from decimal import Decimal
from datetime import date, datetime
import pymysql, config

class Conexion:
    def __init__(self):
        self.conn = pymysql.connect(host=config.DB_HOST,
                                port=config.DB_PORT,
                                user=config.DB_USER,
                                password=config.DB_PASSWORD,
                                db=config.DB_NAME,
                                local_infile=True,
            cursorclass=pymysql.cursors.DictCursor
        )
        self.cursor = self.conn.cursor()

    def ejecutar(self, query, params=None, auto_commit=True):
        self.cursor.execute(query, params or ())
        if auto_commit:
            self.conn.commit()
        return self.cursor

    def obtener(self, query, params=None):
        self.cursor.execute(query, params or ())
        resultados = self.cursor.fetchall()
        return _parsear_resultados(resultados)

    def cerrar(self):
        self.cursor.close()
        self.conn.close()

# Obtener una instancia de la conexión de forma directa
def obtener_conexion():
    return pymysql.connect(host=config.DB_HOST,
                                port=config.DB_PORT,
                                user=config.DB_USER,
                                password=config.DB_PASSWORD,
                                db=config.DB_NAME,
)

# Funciones auxiliares para el parseo
def _parse_valor(valor):
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    elif isinstance(valor, Decimal):
        return float(valor)
    return valor

def _parsear_resultados(rows):
    return [{k: _parse_valor(v) for k, v in fila.items()} for fila in rows]