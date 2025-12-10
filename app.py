import os
import logging
import secrets
from functools import wraps
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, request, session, redirect, render_template, url_for, make_response
from routes.routes import rutas
from models.db_mdl import valida_usuario

app = Flask(__name__, template_folder='templates')
app.register_blueprint(rutas, url_prefix="/api")
app.secret_key = secrets.token_hex(24)

log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True) #

log_file_path = os.path.join(log_dir, 'mi_app.log')

app.logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler(log_file_path, maxBytes=10000, backupCount=1)
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s en %(module)s: %(message)s'
)
file_handler.setFormatter(formatter)

if app.logger.handlers:
    for handler in app.logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            app.logger.removeHandler(handler)

app.logger.addHandler(file_handler)

def nocache(view):
    @wraps(view)
    def no_cache_decorator(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    return no_cache_decorator

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
@nocache
def index():
    app.logger.info('Se accedió a la ruta principal (/) con éxito.')
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    app.logger.info('Se accedió a la ruta principal (/login) con éxito.')
    msg_out = ""
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user_data  = valida_usuario(username, password)

        if user_data :
            session["user_id"] = user_data["id"]
            session["api_key"] = user_data["api_key"]
            session["username"] = user_data["usuario"]
            return redirect(url_for("dashboard"))
        else:
            msg_out = "Usuario o contraseña incorrectos."

    return render_template("login.html", message=msg_out)

@app.route("/usuario", methods=["GET"])
def usuario():
    app.logger.info('Se accedió a la ruta  /usuario valida user y pass.')
    usrnm = request.args.get("usuario")
    passwd = request.args.get("password")

    try:
        dtUsr = valida_usuario(usrnm, passwd)

        if dtUsr:
            return jsonify(dtUsr.to_dict())
    except Exception as e:
        print(f"Error al listar usuarios: {e}")
        return {"error": "Error interno del servidor al listar usuarios. Verifique la DB."}

@app.route("/logout")
def logout():
    app.logger.info('Se accedió a la ruta  /logout cierra sesion.')
    session.pop("user_id", None)
    session.pop("username", None)
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
@nocache
def dashboard():
    app.logger.info('Se accedió a la ruta  /dashboard.')
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)
