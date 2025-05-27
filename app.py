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

if __name__ == '__main__':

    app.run(debug=True, port=5000)