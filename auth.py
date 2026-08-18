
from functools import wraps
from flask import session, redirect, url_for, flash

def login_requerido(f):

    @wraps(f)
    def decorada(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Debes iniciar sesión para acceder a esa página.", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorada

def rol_requerido(rol):
   
    def decorador(f):
        @wraps(f)
        def decorada_por_rol(*args, **kwargs):
            if "usuario_id" not in session:
                flash("Debes iniciar sesión para acceder a esa página.", "danger")
                return redirect(url_for("login"))
            if session.get("usuario_rol") != rol:
                flash("No tienes permisos para acceder a esa página.", "danger")
                return redirect(url_for("inicio"))
            return f(*args, **kwargs)
        return decorada_por_rol 
    return decorador            