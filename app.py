import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify

try:
    cred = credentials.Certificate("firebase-credentials.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    USUARIOS_COLLECTION = "usuario"
    print("Firebase Admin SDK inicializado correctamente.")
except Exception as e:
    print(f"Error inicializando Firebase Admin SDK: {e}")
    db = None

def obtener_acerca_usuario(correo_electronico):
    if not db:
        return None, "Firestore no inicializado"
    try:
        query = db.collection("acerca_usuario").where("id_usuario", "==", correo_electronico).limit(1)
        docs = query.stream()
        doc = next(docs, None)
        if doc is None:
            return None, "Documento acerca_usuario no encontrado"
        
        data = doc.to_dict()
        result = {
            "aptitudes": data.get("aptitudes", []),
            "carrera": data.get("carrera", ""),
            "categorias_interes": data.get("categorias_interes", ""),
            "palabras_clave": data.get("palabras_clave", ""),
            "semestre": data.get("semestre", 0),
            "sobre_mi": data.get("sobre_mi", "")
        }
        return result, None
    except Exception as e:
        return None, str(e)


def obtener_configuracion(correo_electronico):
    if not db:
        return None, "Firestore no inicializado"
    try:
        query = db.collection("configuracion").where("id_usuario", "==", correo_electronico).limit(1)
        docs = query.stream()
        doc = next(docs, None)
        if doc is None:
            return None, "Documento configuracion no encontrado"

        data = doc.to_dict()
        result = {
            "is_disponibilidad": data.get("is_disponibilidad", False),
            "is_notificacion": data.get("is_notificacion", False),
            "is_visibilidad": data.get("is_visibilidad", False),
        }
        return result, None
    except Exception as e:
        return None, str(e)


app = Flask(__name__)

@app.route('/usuario', methods=['POST'])
def create_usuario():
    if not db:
        return jsonify({"error": "Firestore no inicializado"}), 500
    try:
        data = request.get_json()
        
        required_fields = ['correo', 'nombres', 'contraseña'] 
        if not data or not all(field in data for field in required_fields):
            return jsonify({"error": f"Faltan datos. Campos requeridos: {', '.join(required_fields)}"}), 400

        user_id = data['correo']
        
        doc_ref = db.collection(USUARIOS_COLLECTION).document(user_id)
        if doc_ref.get().exists:
            return jsonify({"error": f"El usuario con correo '{user_id}' ya existe"}), 409

        usuario_data_to_save = data.copy()
        usuario_data_to_save['id_usuario'] = user_id

        doc_ref.set(usuario_data_to_save)
        
        return jsonify({"id": user_id, **usuario_data_to_save}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/usuario', methods=['GET'])
def get_usuarios():
    if not db:
        return jsonify({"error": "Firestore no inicializado"}), 500
    try:
        usuarios_ref = db.collection(USUARIOS_COLLECTION)
        docs = usuarios_ref.stream()

        usuarios_list = []
        for doc in docs:
            usuario_data = doc.to_dict()
            usuario_data['id_documento'] = doc.id
            usuarios_list.append(usuario_data)
        
        return jsonify(usuarios_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/usuario/<id_usuario_o_correo>', methods=['GET'])
def get_usuario(id_usuario_o_correo):
    if not db:
        return jsonify({"error": "Firestore no inicializado"}), 500
    try:
        doc_ref = db.collection(USUARIOS_COLLECTION).document(id_usuario_o_correo)
        doc = doc_ref.get()

        if doc.exists:
            usuario_data = doc.to_dict()
            usuario_data['id_documento'] = doc.id
            return jsonify(usuario_data), 200
        else:
            return jsonify({"error": "Usuario no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/usuario/<id_usuario_o_correo>', methods=['PUT'])
def update_usuario(id_usuario_o_correo):
    if not db:
        return jsonify({"error": "Firestore no inicializado"}), 500
    try:
        data_to_update = request.get_json()
        if not data_to_update:
            return jsonify({"error": "No se proporcionaron datos para actualizar"}), 400

        doc_ref = db.collection(USUARIOS_COLLECTION).document(id_usuario_o_correo)
        doc = doc_ref.get()

        if not doc.exists:
            return jsonify({"error": "Usuario no encontrado para actualizar"}), 404
        
        if 'correo' in data_to_update and data_to_update['correo'] != id_usuario_o_correo:
            return jsonify({"error": "No se puede cambiar el correo (ID del documento) de esta forma."}), 400
        if 'id_usuario' in data_to_update and data_to_update['id_usuario'] != id_usuario_o_correo:
             return jsonify({"error": "No se puede cambiar el id_usuario (ID del documento) de esta forma."}), 400
        
        doc_ref.update(data_to_update)
        
        updated_doc = doc_ref.get().to_dict()
        updated_doc['id_documento'] = id_usuario_o_correo

        return jsonify(updated_doc), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/usuario/<id_usuario_o_correo>', methods=['DELETE'])
def delete_usuario(id_usuario_o_correo):
    if not db:
        return jsonify({"error": "Firestore no inicializado"}), 500
    try:
        doc_ref = db.collection(USUARIOS_COLLECTION).document(id_usuario_o_correo)
        doc = doc_ref.get()

        if not doc.exists:
            return jsonify({"error": "Usuario no encontrado para eliminar"}), 404

        doc_ref.delete()
        return jsonify({"message": "Usuario eliminado correctamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login_usuario():
    if not db:
        return jsonify({"error": "Firestore no inicializado"}), 500
    try:
        data = request.get_json()
        correo = data.get("correo")
        contraseña = data.get("contraseña")

        if not correo or not contraseña:
            return jsonify({"error": "Faltan el correo o la contraseña"}), 400

        doc_ref = db.collection(USUARIOS_COLLECTION).document(correo)
        doc = doc_ref.get()
        if not doc.exists:
            return jsonify({"error": "Usuario no encontrado"}), 404

        user_data = doc.to_dict()
        if user_data.get("contraseña") != contraseña:
            return jsonify({"error": "Contraseña incorrecta"}), 401

        return jsonify({"message": "Inicio de sesión exitoso", "usuario": user_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
@app.route('/recuperar-contrasena', methods=['POST'])
def recuperar_contrasena():
    if not db:
        return jsonify({"error": "Firestore no inicializado"}), 500
    try:
        data = request.get_json()
        correo = data.get("correo")

        if not correo:
            return jsonify({"error": "Correo no proporcionado"}), 400

        doc_ref = db.collection(USUARIOS_COLLECTION).document(correo)
        doc = doc_ref.get()
        if not doc.exists:
            return jsonify({"error": "Usuario no encontrado"}), 404

        return jsonify({
            "message": f"Simulación: instrucciones de recuperación de contraseña enviadas a '{correo}'"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/noticias', methods=['GET'])
def listar_noticias():
    if not db:
        return jsonify({"error": "Firestore no inicializado"}), 500
    try:
        noticias_ref = db.collection("noticia")
        docs = noticias_ref.stream()
        noticias = []
        for doc in docs:
            noticia = doc.to_dict()
            noticia['id'] = doc.id
            noticias.append(noticia)
        return jsonify(noticias), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/noticia/<noticia_id>/reaccion', methods=['POST'])
def modificar_reaccion(noticia_id):
    if not db:
        return jsonify({"error": "Firestore no inicializado"}), 500
    try:
        data = request.get_json()
        accion = data.get("accion")  # "agregar" o "quitar"

        if accion not in ["agregar", "quitar"]:
            return jsonify({"error": "Acción inválida, debe ser 'agregar' o 'quitar'"}), 400

        noticia_ref = db.collection("noticia").document(noticia_id)
        noticia_doc = noticia_ref.get()

        if not noticia_doc.exists:
            return jsonify({"error": "Noticia no encontrada"}), 404

        noticia_data = noticia_doc.to_dict()
        reacciones = noticia_data.get("reacciones", 0)

        if accion == "agregar":
            reacciones += 1
        elif accion == "quitar" and reacciones > 0:
            reacciones -= 1

        noticia_ref.update({"reacciones": reacciones})

        return jsonify({"message": "Reacción actualizada", "reacciones": reacciones}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/usuario/<correo_electronico>/acerca', methods=['GET'])
def get_acerca_usuario(correo_electronico):
    data, error = obtener_acerca_usuario(correo_electronico)
    if error:
        return jsonify({"error": error}), 404
    return jsonify(data), 200

@app.route('/usuario/<correo_electronico>/configuracion', methods=['GET'])
def get_configuracion_usuario(correo_electronico):
    data, error = obtener_configuracion(correo_electronico)
    if error:
        return jsonify({"error": error}), 404
    return jsonify(data), 200


if __name__ == '__main__':

    app.run(debug=True, port=5000)
