from flask import Flask, jsonify, request

app = Flask(__name__)

items = [
    {"id": 1, "name": "Apple", "price": 0.5},
    {"id": 2, "name": "Banana", "price": 0.3},
    {"id": 3, "name": "Cherry", "price": 1.0},
]

# Home route
@app.route("/")
def home():
    return jsonify({"message": "Welcome to the Food Shop API!"})

# Get all items
@app.route("/items", methods=["GET"])
def get_items():
    return jsonify(items)

# Get a specific item by ID
@app.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = next((item for item in items if item["id"] == item_id), None)
    if item:
        return jsonify(item)
    return jsonify({"error": "Item not found"}), 404

# Add a new item
@app.route("/items", methods=["POST"])
def add_item():
    data = request.json
    new_item = {
        "id": len(items) + 1,
        "name": data.get("name"),
        "price": data.get("price"),
    }
    items.append(new_item)
    return jsonify(new_item), 201

# Update an item
@app.route("/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    data = request.json
    item = next((item for item in items if item["id"] == item_id), None)
    if item:
        item["name"] = data.get("name", item["name"])
        item["price"] = data.get("price", item["price"])
        return jsonify(item)
    return jsonify({"error": "Item not found"}), 404

# Delete an item
@app.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    global items
    items = [item for item in items if item["id"] != item_id]
    return jsonify({"message": "Item deleted"}), 200

if __name__ == "__main__":
    app.run(debug=True)