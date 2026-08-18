from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import Config
from models import db, Producto, ProductoFisico, ProductoDigital, ProductoPerecible, Usuario
from auth import login_requerido, rol_requerido

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# --- RUTAS DE LA SEMANA 1 (Catálogo y Detalle) ---
@app.route("/")
def inicio():
    productos = Producto.query.filter_by(activo=True).all()
    return render_template("index.html", productos=productos)

@app.route("/producto/<int:producto_id>")
def detalle_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    return render_template("detalle.html", producto=producto)


# --- RUTAS DE AUTENTICACIÓN (Registro, Login, Logout) ---
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        if Usuario.query.filter_by(email=email).first():
            flash("Ya existe una cuenta con ese correo.", "danger")
            return render_template("registro.html")
        
        usuario = Usuario(nombre=request.form["nombre"], email=email, rol="cliente")
        usuario.set_password(request.form["password"])
        db.session.add(usuario)
        db.session.commit()
        flash("Cuenta creada correctamente. Ya puedes iniciar sesión.", "success")
        return redirect(url_for("login"))
    return render_template("registro.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.check_password(password):
            session["usuario_id"] = usuario.id
            session["usuario_nombre"] = usuario.nombre
            session["usuario_rol"] = usuario.rol
            flash(f"¡Bienvenido, {usuario.nombre}!", "success")
            return redirect(url_for("inicio"))
        else:
            flash("Correo o contraseña incorrectos.", "danger")
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("inicio"))

@app.route("/productos/nuevo/fisico", methods=["GET", "POST"])
@rol_requerido("admin")
def nuevo_producto_fisico():
    if request.method == "POST":
        try:
            producto = ProductoFisico(
                codigo=request.form["codigo"],
                nombre=request.form["nombre"],
                precio_base=float(request.form["precio_base"]),
                stock=int(request.form["stock"]),
                peso_kg=float(request.form["peso_kg"]),
                costo_envio_por_kg=float(request.form["costo_envio_por_kg"]),
            )
            db.session.add(producto)
            db.session.commit()
            flash(f"Producto físico '{producto.nombre}' creado correctamente.", "success")
            return redirect(url_for("inicio"))
        except ValueError:
            flash("Revisa que los campos numéricos tengan valores válidos.", "danger")
            db.session.rollback()
        except Exception:
            db.session.rollback()
            flash("Ocurrió un error. Verifica que el código no esté repetido.", "danger")
    return render_template("nuevo_fisico.html")

@app.route("/productos/nuevo/digital", methods=["GET", "POST"])
@rol_requerido("admin")
def nuevo_producto_digital():
    if request.method == "POST":
        try:
            producto = ProductoDigital(
                codigo=request.form["codigo"],
                nombre=request.form["nombre"],
                precio_base=float(request.form["precio_base"]),
                stock=int(request.form["stock"]),
                licencia=request.form["licencia"],
            )
            db.session.add(producto)
            db.session.commit()
            flash(f"Producto digital '{producto.nombre}' creado correctamente.", "success")
            return redirect(url_for("inicio"))
        except ValueError:
            flash("Revisa que los campos numéricos tengan valores válidos.", "danger")
            db.session.rollback()
        except Exception:
            db.session.rollback()
            flash("Ocurrió un error. Verifica que el código no esté repetido.", "danger")
    return render_template("nuevo_digital.html")

@app.route("/productos/nuevo/perecible", methods=["GET", "POST"])
@rol_requerido("admin")
def nuevo_producto_perecible():
    if request.method == "POST":
        try:
            producto = ProductoPerecible(
                codigo=request.form["codigo"],
                nombre=request.form["nombre"],
                precio_base=float(request.form["precio_base"]),
                stock=int(request.form["stock"]),
                dias_para_vencer=int(request.form["dias_para_vencer"]),
            )
            db.session.add(producto)
            db.session.commit()
            flash(f"Producto perecible '{producto.nombre}' creado correctamente.", "success")
            return redirect(url_for("inicio"))
        except ValueError:
            flash("Revisa que los campos numéricos tengan valores válidos.", "danger")
            db.session.rollback()
        except Exception:
            db.session.rollback()
            flash("Ocurrió un error. Verifica que el código no esté repetido.", "danger")
    return render_template("nuevo_perecible.html")

@app.route("/productos/<int:producto_id>/editar", methods=["GET", "POST"])
@rol_requerido("admin")
def editar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    if request.method == "POST":
        try:
            producto.nombre = request.form["nombre"]
            producto.precio_base = float(request.form["precio_base"])
            producto.stock = int(request.form["stock"])
            db.session.commit()
            flash(f"Producto '{producto.nombre}' actualizado correctamente.", "success")
            return redirect(url_for("detalle_producto", producto_id=producto.id))
        except ValueError:
            flash("Revisa que los campos numéricos tengan valores válidos.", "danger")
            db.session.rollback()
    return render_template("editar.html", producto=producto)

@app.route("/productos/<int:producto_id>/eliminar", methods=["POST"])
@rol_requerido("admin")
def eliminar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    producto.activo = False
    db.session.commit()
    flash(f"Producto '{producto.nombre}' desactivado del catálogo.", "success")
    return redirect(url_for("inicio"))


# --- RUTAS DEL CARRITO DE COMPRAS (Exclusivas para clientes con sesión) ---

@app.route("/carrito")
@login_requerido
def ver_carrito():
    carrito = session.get("carrito", {})
    productos_en_carrito = []
    total_general = 0.0

    for producto_id_str, cantidad in carrito.items():
        producto = Producto.query.get(int(producto_id_str))
        if producto:
            precio = producto.precio_final()
            subtotal = precio * cantidad
            total_general += subtotal
            productos_en_carrito.append({
                "producto": producto,
                "cantidad": cantidad,
                "subtotal": subtotal
            })

    return render_template("carrito.html", items=productos_en_carrito, total=total_general)

@app.route("/carrito/agregar/<int:producto_id>", methods=["POST"])
@login_requerido
def agregar_carrito(producto_id):
    # Validar que el usuario sea cliente y no admin si lo deseas, o permitirlo
    producto = Producto.query.get_or_404(producto_id)
    
    # Obtenemos o creamos el diccionario del carrito en la sesión
    carrito = session.get("carrito", {})
    
    str_id = str(producto_id)
    if str_id in carrito:
        carrito[str_id] += 1
    else:
        carrito[str_id] = 1
        
    session["carrito"] = carrito
    flash(f"Se agregó '{producto.nombre}' al carrito.", "success")
    return redirect(url_for("ver_carrito"))

@app.route("/carrito/eliminar/<int:producto_id>", methods=["POST"])
@login_requerido
def eliminar_del_carrito(producto_id):
    carrito = session.get("carrito", {})
    str_id = str(producto_id)
    
    if str_id in carrito:
        pop_val = carrito.pop(str_id)
        session["carrito"] = carrito
        flash("Producto eliminado del carrito.", "info")
        
    return redirect(url_for("ver_carrito"))

if __name__ == "__main__":
    app.run(debug=True)