import uuid
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from contextlib import contextmanager
from urllib.parse import quote
from werkzeug.security import check_password_hash
from flask import current_app


# ----------------------------------------------------
# Configuración de la Base de Datos y el Modelo
# ----------------------------------------------------

# ¡IMPORTANTE!: Reemplaza 'usuario', 'clave', 'host' y 'nombre_db' con tus credenciales reales de MySQL.
# Asegúrate de haber instalado 'PyMySQL' (pip install PyMySQL).
DATABASE_USER = "dbflaskinacap"
DATABASE_PASSWD = quote("1N@C@P_alumn05")
DATABASE_HOST = "mysql.flask.nogsus.org"
DATABASE_NAME = "api_alumnos"
DATABASE_URL = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWD}@{DATABASE_HOST}/{DATABASE_NAME}"
# DATABASE_URL = f"mysql+pymysql://dbflaskinacap:P_alumn05@mysql.flask.nogsus.org/api_alumnos"

# Inicializa el motor de la base de datos
engine = create_engine(DATABASE_URL)

# Base declarativa que será la madre de todas nuestras clases de modelos
Base = declarative_base()

# ----------------------------------------------------
# Definición de la clase de la tabla (función que genera la tabla usuario)
# ----------------------------------------------------
class Usuario(Base):
    __tablename__ = 'vave_usuario'

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(Text(100000), index=True)
    apellido = Column(String(150), index=True)
    usuario = Column(String(50), index=True)
    clave = Column(String(255), index=True)
    api_key = Column(String(250), index=True)

    def to_dict(self):
        return {"id": self.id, "nombre": self.nombre, "apellido": self.apellido,
                "usuario": self.usuario, "clave": self.clave, "api_key": self.api_key}

class Mercado(Base):
    __tablename__ = 'vave_mercados'
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), index=True)

    productos = relationship("Producto", back_populates="origen_mercado", cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "nombre": self.nombre}

class Producto(Base):
    __tablename__ = 'vave_productos'

    id = Column(Integer, primary_key=True, index=True)
    idOrigen = Column(Integer, ForeignKey('vave_mercados.id'), nullable=False, index=True)
    nombre = Column(String(150), index=True)
    uMedida = Column(String(100), index=True)
    precio = Column(Integer, index=True)

    origen_mercado = relationship("Mercado", back_populates="productos")

    def to_dict(self):
        return {"id": self.id, "idOrigen": self.idOrigen, "nombre": self.nombre,
                "uMedida": self.uMedida, "precio": self.precio,
                # Incluimos el nombre del mercado para facilitar la lectura en el frontend
                "origen_mercado": self.origen_mercado.nombre if self.origen_mercado else None
                }


# ----------------------------------------------------
# Sesiones locales para interactuar con la DB
# ----------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ----------------------------------------------------
# Función de Control de Conexión (Context Manager)
# ----------------------------------------------------

@contextmanager
def get_db():
    """
    Función que controla la conexión a la base de datos (sesión).
    Garantiza que la sesión se cierre correctamente después de su uso.
    """
    db = SessionLocal()
    try:
        # Entrega la sesión de DB al bloque 'with'
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


# ----------------------------------------------------
# Función de Inicialización
# ----------------------------------------------------

"""
TODO(Función de Inicialización)
"""

# ----------------------------------------------------
# Funciones de consultas
# ----------------------------------------------------

def valida_usuario(usrname, passwd):
    current_app.logger.info(f"Intentando validar usuario: {usrname}")
    try:
        with get_db() as db:
            user = db.query(Usuario).filter(Usuario.usuario == usrname).first()

            if user:

                if check_password_hash(user.clave, passwd):
                    user.api_key = uuid.uuid4().hex
                    db.commit()
                    current_app.logger.info(f"Usuario {usrname} validado con éxito.")
                    return {"id": user.id, "api_key": user.api_key, "usuario": user.usuario}
                else:
                    current_app.logger.warning(f"Fallo de validación para el usuario: {usrname}")
                    return False
            return False

    except Exception as e:
        current_app.logger.error(f"Error en la base de datos al validar usuario {usrname}: {e}", exc_info=True)
        print(f"Lib: models.py. Func: valida_usuario. Error: {e}")
        return False

def is_user_api_key(api_key):

    with get_db() as db:
        user = db.query(Usuario).filter(Usuario.api_key == api_key).first()
        if user:
            current_app.logger.error(f"se valida api_key")
            return user
        current_app.logger.error(f"no se encuentra valida api_key")
        return None

def generate_api_key():
    current_app.logger.error(f"se genera api_key")
    return uuid.uuid4().hex

