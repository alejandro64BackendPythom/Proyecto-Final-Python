from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.orm import joinedload
from models.db_mdl import get_db, Producto, Mercado, Usuario, is_user_api_key

rutas = Blueprint("rutas", __name__)

def get_api_key_from_request():
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    current_app.logger.info('Ingreso a get_api_key_from_request .')
    return api_key

def require_auth(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_app.logger.info('Ingreso a ecorated_function .')
        api_key = get_api_key_from_request()

        if not api_key:
            current_app.logger.info('Error API key requerida codigo 401.')
            return jsonify({'error': 'API key required'}), 401
        user = is_user_api_key(api_key)

        if not user:
            current_app.logger.info('Acceso no autorizado. API Key inválida codigo 403.')
            return jsonify({'message': 'Acceso no autorizado. API Key inválida.'}), 403
        request.current_user = user
        return f(*args, **kwargs)

    return decorated_function

@rutas.route("/productos", methods=["GET"])
@require_auth
def listar_productos():
    current_app.logger.info('Se accedió a /productos mediante GET a listar productos.')
    try:
        with get_db() as db:
            productos = db.query(Producto).options(joinedload(Producto.origen_mercado)).all()
            current_app.logger.info('listar productos exitoso.')
            return jsonify([p.to_dict() for p in productos]), 200
    except Exception as e:
        current_app.logger.info('Error al listar productos codigo 500.')
        return jsonify({"error": str(e)}), 500

@rutas.route("/productos", methods=["POST"])
def crear_producto():
    current_app.logger.info('Se accedió a /productos mediante  POST a crear producto.')
    data = request.get_json()
    reqFld = ['nombre', 'idOrigen', 'uMedida', 'precio']

    if not all(r in data for r in reqFld):
        current_app.logger.info('Error faltan campos codigo 400.')
        return jsonify({"error": f"Faltan campos: {reqFld}"}), 400

    try:
        with get_db() as db:
            mercado = db.query(Mercado).filter(Mercado.id == data["idOrigen"]).first()
            if not mercado:
                current_app.logger.info('error Ha ingresado un mercado inválido codigo 404.')
                return jsonify({"error": "Ha ingresado un mercado inválido"}), 404

            nProd = Producto(
                nombre = data["nombre"],
                idOrigen = data["idOrigen"],
                uMedida = data["uMedida"],
                precio = data["precio"]
            )

            db.add(nProd)
            db.commit()
            db.refresh(nProd)
            current_app.logger.info('Se creo producto correctamente codigo 201.')
            return jsonify({"Confirmación": "Producto creado", "Producto": nProd.to_dict()}), 201
    except Exception as e:
        current_app.logger.info('Error al crear producto codigo 500.')
        return jsonify({"error": str(e)}), 500

@rutas.route("/productos/<int:idprd>", methods=["PUT"])
def actualizar_producto(idprd):
    current_app.logger.info('Se accedió a /productos mediante  PUT a actualizar producto.')
    data = request.get_json()

    try:
        with get_db() as db:
            prod = db.query(Producto).filter(Producto.id == idprd).first()
            if not prod:
                current_app.logger.info('El producto a modificar no existe codigo 404.')
                return jsonify({"error": "Intenta actualizar un producto que no existe"}), 404

            if "nombre" in data: prod.nombre = data["nombre"]
            if "uMedida" in data: prod.uMedida = data["uMedida"]
            if "precio" in data: prod.precio = data["precio"]

            if "idOrigen" in data:
                mercado = db.query(Mercado).filter(Mercado.id == data["idOrigen"]).first()

                if not mercado:
                    current_app.logger.info('El mercado a modificar no existe codigo 404.')
                    return jsonify({"error": "El mercado a modificar no existe"}), 404

                prod.idOrigen = data["idOrigen"]

            db.commit()
            db.refresh(prod)
            current_app.logger.info('Producto actualizado correctamente codigo 200.')
            return jsonify({"Confirmación": "Producto actualizado", "Producto": prod.to_dict()}), 200

    except Exception as e:
        current_app.logger.info('Error al actualizar producto codigo 500.')
        return jsonify({"error": str(e)}), 500

@rutas.route("/productos/<int:idprd>", methods=["DELETE"])
def eliminar_producto(idprd):
    current_app.logger.info('Se accedió a /productos mediante DELETE a eliminar producto.')
    try:
        with get_db() as db:
            prod = db.query(Producto).filter(Producto.id == idprd).first()
            if not prod:
                current_app.logger.info('Intenta eliminar un producto que no existe codigo 404.')
                return jsonify({"error": "Intenta eliminar un producto que no existe"}), 404

            db.delete(prod)
            db.commit()
            current_app.logger.info('Producto eliminado correctamente codigo 200.')
            return jsonify({"Confirmación": "Producto eliminado"}), 200
    except Exception as e:
        current_app.logger.info('Error al eliminar producto codigo 500.')
        return jsonify({"error": str(e)}), 500

