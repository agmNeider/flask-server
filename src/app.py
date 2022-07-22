from flask import Flask, request
from config.database import getDataBase
import bcrypt
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/users-create', methods = ["POST"])
def CrearUsuario():
    event = request.get_json()
    conn = getDataBase()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email='%s'" % event["email"])
    email_founded = cur.fetchone()
    if email_founded:
        return {"success": False, "message": "Ya Existe un usuario con este Email"}
    password = bcrypt.hashpw(event["password"].encode('utf-8'), bcrypt.gensalt(10))
    cur.execute(
        "INSERT INTO users (firstname, lastname, email, password) VALUES ('%s', '%s', '%s', '%s')" % 
        (event["firstname"], event["lastname"], event["email"], password.decode('utf-8'))
    )
    result = cur.lastrowid
    cur.close()
    conn.close()
    return {"success": True, "data": {"id": result, "firstname": event["firstname"]}}

@app.route('/login', methods = ["POST"])
def LoginUsuario():
    event = request.get_json()
    conn = getDataBase()
    cur = conn.cursor()
    cur.execute("SELECT id, password, firstname, lastname FROM users WHERE email='%s'" % event["email"])
    email_founded = cur.fetchone()
    if not email_founded:
        return {"success": False, "message": "El Usuario No Existe"}
    if bcrypt.checkpw(event["password"].encode('utf-8'), email_founded[1].encode('utf-8')):
        return {
            "success": True,
            "data": {
                "id": email_founded[0],
                "firstname": email_founded[2]
            }
        }
    else: 
        return {
            "success": False,
            "message": "La combinacion Usuario/Contraseña es Incorrecta"
        }

@app.route('/get-products', methods = ["GET"])
def ListProducts():
    conn = getDataBase()
    cur = conn.cursor()
    cur.execute("SELECT id, name, price, discount, image_url FROM products")
    products = cur.fetchall()
    cur.close()
    conn.close()

    prods = []
    for prod in products:
        prods.append({
            "id": prod[0],
            "name": prod[1],
            "price": prod[2],
            "discount": prod[3],
            "image_url": prod[4]
        })

    return {
        "success": True,
        "data": prods
    }

@app.route('/add-to-cart', methods = ["POST"])
def AddToCart():
    event = request.get_json()
    conn = getDataBase()
    cur = conn.cursor()
    cur.execute("INSERT INTO user_product_cart (user_id, product_id) VALUES (%s, %s)" % (event['user_id'], event['product_id']))
    cur.close()
    conn.close()

    return {
        "success": True,
        "data": []
    }

@app.route('/get-products-at-cart/<int:id>', methods = ["GET"])
def GetCartProducts(id):
    conn = getDataBase()
    cur = conn.cursor()
    #SUBCONSULTA
    cur.execute("SELECT id, name, description, price, discount, category, image_url, weight FROM products WHERE id in (SELECT product_id FROM user_product_cart WHERE user_id='%s')" % id)
    res = cur.fetchall()

    prods = []
    for prod in res:
        prods.append({
            "id": prod[0],
            "name": prod[1],
            "description": prod[2],
            "price": prod[3],
            "discount": prod[4],
            "category": prod[5],
            "image_url": prod[6],
            "weight": prod[7]
        })
    cur.close()
    conn.close()

    return {
        "success": True,
        "data": prods
    }

@app.route("/get-cart-info/<int:id>", methods=["GET"])
def GetCardInfo(id):
    conn = getDataBase()
    cur = conn.cursor()
    #SUBCONSULTA
    cur.execute("SELECT sum(price) FROM products WHERE id in (SELECT product_id FROM user_product_cart WHERE user_id=%s)" % id)

    res = cur.fetchone()
    
    return {
        "success": True,
        "data": res
    }

@app.route("/delete-from-cart", methods=["POST"])
def DeleteFromCart():
    event = request.get_json()
    print(event)
    conn = getDataBase()
    cur = conn.cursor()
    #SUBCONSULTA
    cur.execute("DELETE FROM user_product_cart WHERE user_id=%s AND product_id=%s" % (event["user_id"], event["product_id"]))

    return {
        "success": True,
        "data": []
    }

@app.route("/create-purchase", methods=["POST"])
def CreatePurchase():
    event = request.get_json()
    conn = getDataBase()
    cur = conn.cursor()


    cur.execute("UPDATE users SET phone='%s' WHERE id=%s" % (event['phone'], event['user_id']))
    cur.execute("INSERT INTO purchases (user_id, total_amount, payment_method) VALUES (%s, %s, '%s')" % (event['user_id'], event['amount_total'], event['payment_method']))

    id_purchase = cur.lastrowid
    cur.execute("DELETE FROM user_product_cart WHERE user_id=%s" % event['user_id'])

    for prod in event['products']:
        cur.execute("INSERT INTO purchase_product_rel (product_id, purchase_id, amount_total) VALUES (%s, %s, %s)" % (prod['id'], id_purchase, prod['price']))

    return {
        "success": True,
        "data": "Compra Realizada con Exito"
    }

@app.route('/get-purchases/<int:id>', methods = ["GET"])
def GetPurchases(id):
    conn = getDataBase()
    cur = conn.cursor()
    #SUBCONSULTA

    cur.execute("SELECT id, total_amount, purchase_date FROM purchases WHERE user_id=%s" % id)
    purchases = cur.fetchall()

    cur.execute("SELECT pr.purchase_id, p.name, p.price, p.image_url, p.description FROM products AS p INNER JOIN (SELECT product_id, purchase_id FROM purchase_product_rel WHERE purchase_id in (SELECT id FROM purchases WHERE user_id=%s)) AS pr ON p.id=pr.product_id;" % id)
    products = cur.fetchall()

    purchasesData = {}
    for pur in purchases:
        purchasesData[str(pur[0])] = {
            'amount_total': pur[1],
            'purchase_date': pur[2],
            'id': pur[0],
            'products': []
        }
    
    for prod in products:
        if str(prod[0]) in purchasesData:
            purchasesData[str(prod[0])]["products"].append({
                "name": prod[1],
                "price": prod[2],
                "image_url": prod[3],
                "description": prod[4]
            })

    return {
        "success": True,
        "data": list(purchasesData.values())
    }
    
if __name__ == "__main__":
    app.run(host="localhost", port=5000,debug=True)