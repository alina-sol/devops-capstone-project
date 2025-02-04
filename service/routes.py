from flask import Flask, request, jsonify, url_for
from service.models import db, Account

app = Flask(__name__)

# Ensure you have the database URI and configurations
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:postgres@localhost:5432/postgres"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Route for home page
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the Account Service"}), 200

# Health check route
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "OK"}), 200

# Route for creating an account
@app.route('/accounts', methods=['POST'])
def create_account():
    if request.content_type != 'application/json':
        return jsonify({"message": "Unsupported Media Type"}), 415
    
    # Validate if required fields are present
    if 'name' not in request.json or 'email' not in request.json:
        return jsonify({"message": "Bad request"}), 400

    account_data = request.json
    new_account = Account(name=account_data['name'], email=account_data['email'])
    db.session.add(new_account)
    db.session.commit()

    # Set the Location header to the URL of the newly created account
    location = url_for('get_account', id=new_account.id, _external=True)
    return jsonify(new_account.serialize()), 201, {'Location': location}

# Route for retrieving a single account
@app.route('/accounts/<int:id>', methods=['GET'])
def get_account(id):
    account = Account.query.get(id)
    if account is None:
        return jsonify({"message": "Account not found"}), 404
    return jsonify(account.serialize()), 200

if __name__ == '__main__':
    app.run(debug=True)
