from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import ConfigurationError

from base64 import b64encode, b64decode
from pymongo.operations import UpdateOne
from datetime import datetime
import xml.etree.ElementTree as ET 
import subprocess

port = 4800
app = Flask(__name__)
CORS(app)
mongo_url = "mongodb://localhost:27017"
client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
db_name = client['codeEditor']
code_collection = db_name['codeCollection']

REACT_PROJECT_TEMPLATES = [
    {
        "filePath": "/App.js",
        "code": '''
import React, { useState } from 'react';
import InputForm from './InputForm';
import DisplayText from './DisplayText';

function App() {
  const [text, setText] = useState('');

  const handleTextChange = (newText) => {
    setText(newText);
  };

  return (
    <div className="App">
      <h1>Simple React App</h1>
      <InputForm onTextChange={handleTextChange} />
      <DisplayText text={text} />
    </div>
  );
}

export default App;
'''
    },
    {
        "filePath": "/InputForm.js",
        "code": '''
import React, { useState } from 'react';

function InputForm({ onTextChange }) {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onTextChange(input);
    setInput('');
  };

  return (
    <form onSubmit={handleSubmit}>
      <input 
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Enter some text"
      />
      <button type="submit">Submit</button>
    </form>
  );
}

export default InputForm;
'''
    },
    {
        "filePath": "/DisplayText.js",
        "code": '''
import React from 'react';

function DisplayText({ text }) {
  return (
    <div className="display-text">
      <h2>Text:</h2>
      <p>{text}</p>
    </div>
  );
}

export default DisplayText;
'''
    }
,{
    "filePath": "/styles.css",
        "code": '''
        body {
  font-family: sans-serif;
  -webkit-font-smoothing: auto;
  -moz-font-smoothing: auto;
  -moz-osx-font-smoothing: grayscale;
  font-smoothing: auto;
  text-rendering: optimizeLegibility;
  font-smooth: always;
  -webkit-tap-highlight-color: transparent;
  -webkit-touch-callout: none;
}

h1 {
  font-size: 1.5rem;
}
        '''
},{
    "filePath": "/index.js",
        "code": '''
        import React, { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

import App from "./App";

const root = createRoot(document.getElementById("root"));
root.render(
  <StrictMode>
    <App />
  </StrictMode>
);
        '''
},{
    "filePath": "/public/index.html",
        "code": '''
        <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
        '''
},{
    "filePath": "/package.json",
        "code": '''
        {
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "react-scripts": "^5.0.0"
  },
  "main": "/index.js",
  "devDependencies": {}
}
        '''
}
]

REACT_PROJECT_DEPENDENCIES = {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
}

PYTHON_PROJECT_TEMPLATE = [
    {
        "filePath": "/main.py",
        "code": 'print("Hello world")'
    }
]

WEB_PROJECT_TEMPLATE = [
    {
        "filePath": "/index.html",
        "code": '''
<!DOCTYPE html>
<html>
<head>
  <title>Web Project</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <h1>Hello World</h1>
  <script src="script.js"></script>
</body>
</html>
'''
    },
    {
        "filePath": "/styles.css",
        "code": 'body { font-family: Arial, sans-serif; margin: 20px; }'
    },
    {
        "filePath": "/script.js",
        "code": 'console.log("Hello World");'
    }
]

NODE_PROJECT_TEMPLATE = [
    {
        "filePath": "/index.js",
        "code": '''
const http = require('http');

const hostname = '127.0.0.1';
const port = 3000;

const server = http.createServer((req, res) => {
  res.statusCode = 200;
  res.setHeader('Content-Type', 'text/html');
  res.end('Hello world');
});

server.listen(port, hostname, () => {
  console.log(`Server running at http://${hostname}:${port}/`);
});
'''
    },
]
def generate_project_id():
    """
    Generate a unique project ID based on the current date and time.
    Format: YYYYMMDDHHMMSS (Year, Month, Day, Hour, Minute, Second)
    """
    return datetime.now().strftime("%Y%m%d%H%M%S")

def generate_last_updated_date():
    """Generate the current date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")

def validate_and_process_project(data):
    """
    Validate the incoming project data and add additional keys with default values.
    """
    # Validate required fields
    required_fields = ["projectName", "lang"]
    for field in required_fields:
        if field not in data or not isinstance(data[field], str) or not data[field].strip():
            raise ValueError(f"Invalid or missing '{field}': must be a non-empty string.")

    lang = data["lang"].strip().lower()

    # Determine the file template based on language
    if lang == "python":
        file_sets = PYTHON_PROJECT_TEMPLATE
    elif lang == "webstack":
        file_sets = WEB_PROJECT_TEMPLATE
    elif lang == "react":
        file_sets = REACT_PROJECT_TEMPLATES
    elif lang == "node":
        file_sets = NODE_PROJECT_TEMPLATE
    else:
        raise ValueError(f"Unsupported language '{lang}'. Supported options are: 'python', 'web', 'react'.")

    # Generate `lastUpdatedDate` and add it to the project data
    project = {
        "projectId": generate_project_id(),
        "projectName": data["projectName"].strip(),
        "lang": lang,
        "lastUpdatedDate": generate_last_updated_date(),
        "fileSets": file_sets,
        "dependencies": REACT_PROJECT_DEPENDENCIES if lang == "react" else {}
    }

    return project

@app.route("/add-project", methods=["POST"])
def add_project():
    try:
        data = request.get_json()

        # Validate and process the project data
        project = validate_and_process_project(data)

        # Insert the project into the database
        result = code_collection.insert_one(project)

        if result.inserted_id:
            return jsonify({
                "message": "Project added successfully.",
                "projectId": project["projectId"]
            }), 201
        else:
            return jsonify({"error": "Failed to add the project to the database."}), 500

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({
            "error": "An unexpected error occurred.",
            "details": str(e)
        }), 500

@app.route("/get-projects", methods=["GET"])
def get_projects():
    try:
        # Fetch projects from the database, only retrieving specific fields
        projects = code_collection.find({}, {"_id": 0, "projectId": 1, "projectName": 1, "lang": 1, "lastUpdatedDate": 1})

        # Convert MongoDB cursor to a list of dictionaries
        project_list = list(projects)

        if not project_list:
            return jsonify({"message": "No projects found."}), 404

        return jsonify(project_list), 200

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred.", "details": str(e)}), 500

@app.route("/get-project-details", methods=["POST"])
def get_project_details():
    try:

        data = request.get_json()
        projectId = data.get("projectId")

        if not projectId:
            return jsonify({"error": "projectId is required"}), 400

        project = code_collection.find_one({"projectId": projectId}, {"_id": 0})

        if project:
            return jsonify(project), 200
        else:
            return jsonify({"message": "Project not found."}), 404

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred.", "details": str(e)}), 500

@app.route("/add-file", methods=["POST"])
def add_file():
    try:
        data = request.get_json()

        required_fields = ["projectId", "filePath"]
        for field in required_fields:
            if field not in data or not isinstance(data[field], str) or not data[field].strip():
                raise ValueError(f"Invalid or missing '{field}': must be a non-empty string.")

        projectId = data["projectId"].strip()
        filePath = data["filePath"].strip()
        code = data.get("code", "").strip()  

        # Check if project exists
        project = code_collection.find_one({"projectId": projectId})
        if not project:
            return jsonify({"error": "Project not found."}), 404

        # Check if file already exists in the project
        existing_file = next((f for f in project["fileSets"] if f["filePath"] == filePath), None)
        if existing_file:
            return jsonify({"error": f"File with path '{filePath}' already exists in the project."}), 400

        # Add the new file to the project's fileSets
        new_file = {"filePath": filePath, "code": code}
        result = code_collection.update_one(
            {"projectId": projectId},
            {"$push": {"fileSets": new_file}, "$set": {"lastUpdatedDate": generate_last_updated_date()}}
        )

        if result.modified_count > 0:
            return jsonify({
                "message": "File added successfully.",
                "projectId": projectId,
                "filePath": filePath
            }), 201
        else:
            return jsonify({"error": "Failed to add the file to the project."}), 500

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred.", "details": str(e)}), 500

@app.route("/update-file-code", methods=["POST"])
def update_file_code():
    try:
        data = request.get_json()
        print("data",data)

        # Validate required fields
        required_fields = ["projectId", "filePath", "code"]
        for field in required_fields:
            if field not in data or not isinstance(data[field], str) or not data[field].strip():
                raise ValueError(f"Invalid or missing '{field}': must be a non-empty string.")

        projectId = data["projectId"].strip()
        filePath = data["filePath"].strip()
        new_code = data["code"].strip()

        # Check if project exists
        project = code_collection.find_one({"projectId": projectId})
        if not project:
            return jsonify({"error": "Project not found."}), 404

        # Check if the file exists in the project's fileSets
        print(project["fileSets"],"project[fileSets]")
        file_exists = any(f["filePath"] == filePath for f in project["fileSets"])
        if not file_exists:
            return jsonify({"error": f"File with path '{filePath}' not found in the project."}), 404

        # Update the code in the specific file
        result = code_collection.update_one(
            {"projectId": projectId, "fileSets.filePath": filePath},
            {"$set": {"fileSets.$.code": new_code, "lastUpdatedDate": generate_last_updated_date()}}
        )

        if result.modified_count > 0:
            return jsonify({
                "message": "File code updated successfully.",
                "projectId": projectId,
                "filePath": filePath
            }), 200
        else:
            return jsonify({"error": "Failed to update the file code."}), 500

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred.", "details": str(e)}), 500

@app.route("/rename-file", methods=["POST"])
def rename_file():
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["projectId", "oldFilePath", "newFilePath"]
        for field in required_fields:
            if field not in data or not isinstance(data[field], str) or not data[field].strip():
                raise ValueError(f"Invalid or missing '{field}': must be a non-empty string.")

        projectId = data["projectId"].strip()
        oldFilePath = data["oldFilePath"].strip()
        newFilePath = data["newFilePath"].strip()

        # Check if the project exists
        project = code_collection.find_one({"projectId": projectId})
        if not project:
            return jsonify({"error": "Project not found."}), 404

        # Check if the old file exists
        file_to_rename = next((f for f in project["fileSets"] if f["filePath"] == oldFilePath), None)
        if not file_to_rename:
            return jsonify({"error": f"File with path '{oldFilePath}' not found in the project."}), 404

        # Check if the new file name already exists
        new_file_exists = any(f["filePath"] == newFilePath for f in project["fileSets"])
        if new_file_exists:
            return jsonify({"error": f"File with path '{newFilePath}' already exists in the project."}), 400

        # Update the file's filePath and retain the code content
        result = code_collection.update_one(
            {"projectId": projectId, "fileSets.filePath": oldFilePath},
            {
                "$set": {
                    "fileSets.$.filePath": newFilePath,
                    "lastUpdatedDate": generate_last_updated_date()
                }
            }
        )

        if result.modified_count > 0:
            return jsonify({
                "message": "File renamed successfully.",
                "projectId": projectId,
                "oldFilePath": oldFilePath,
                "newFilePath": newFilePath
            }), 200
        else:
            return jsonify({"error": "Failed to rename the file."}), 500

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred.", "details": str(e)}), 500

@app.route("/delete-file", methods=["POST"])
def delete_file():
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["projectId", "filePath"]
        for field in required_fields:
            if field not in data or not isinstance(data[field], str) or not data[field].strip():
                raise ValueError(f"Invalid or missing '{field}': must be a non-empty string.")

        projectId = data["projectId"].strip()
        filePath = data["filePath"].strip()

        # Check if the project exists
        project = code_collection.find_one({"projectId": projectId})
        if not project:
            return jsonify({"error": "Project not found."}), 404

        # Check if the file exists in the project's fileSets
        file_to_delete = next((f for f in project["fileSets"] if f["filePath"] == filePath), None)
        if not file_to_delete:
            return jsonify({"error": f"File with path '{filePath}' not found in the project."}), 404

        # Remove the file from the project's fileSets
        result = code_collection.update_one(
            {"projectId": projectId},
            {"$pull": {"fileSets": {"filePath": filePath}}, "$set": {"lastUpdatedDate": generate_last_updated_date()}}
        )

        if result.modified_count > 0:
            return jsonify({
                "message": "File deleted successfully.",
                "projectId": projectId,
                "filePath": filePath
            }), 200
        else:
            return jsonify({"error": "Failed to delete the file."}), 500

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred.", "details": str(e)}), 500

@app.route("/delete-project", methods=["POST"])
def delete_project():
    try:
        data = request.get_json()

        # Validate required field
        if "projectId" not in data or not isinstance(data["projectId"], str) or not data["projectId"].strip():
            raise ValueError("Invalid or missing 'projectId': must be a non-empty string.")

        projectId = data["projectId"].strip()

        # Delete the project from the database
        result = code_collection.delete_one({"projectId": projectId})

        if result.deleted_count > 0:
            return jsonify({
                "message": "Project deleted successfully.",
                "projectId": projectId
            }), 200
        else:
            return jsonify({"error": "Project not found or already deleted."}), 404

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred.", "details": str(e)}), 500

@app.route('/execute', methods=['POST'])
def execute_code():
    data = request.get_json()
    print("data",data)
    code = data.get('codeFromEditor', '')
    print("code",code)

    # Write code to a temporary file
    with open('temp_code.py', 'w') as file:
        file.write(code)

    try:
        # Execute the Python file
        result = subprocess.run(['python', 'temp_code.py'], capture_output=True, text=True, check=True)
        output = result.stdout
        print(output,"output")
    except subprocess.CalledProcessError as e:
        output = e.stderr  # Capture error output

    return jsonify({'result': output})

if __name__ == "__main__":
    app.run(port=port,host='0.0.0.0')