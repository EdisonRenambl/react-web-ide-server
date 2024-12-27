from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import ConfigurationError
import random
import traceback
from base64 import b64encode, b64decode
from pymongo.operations import UpdateOne
from datetime import datetime
import os
import xml.etree.ElementTree as ET 
import subprocess
from bson import ObjectId
port = 4800
app = Flask(__name__)
CORS(app)
mongo_url = "mongodb://localhost:27017"
PROJECTS_DIR = "projects"
if not os.path.exists(PROJECTS_DIR):
    os.makedirs(PROJECTS_DIR)

client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
db_name = client['codeEditor']
code_collection = db_name['codeCollection']
userCollection = db_name['users']
projectDetails = db_name['projectDetails']
chatCollection = db_name['chatConvarsations']
internshipCollection = db_name['InternshipDetails']
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

REACT_NATIVE_PROJECT_DEPENDENCIES = {
    "react": {"version":"^18.2.0"},
    "react-native":{"version":"^0.70.5"} 
}

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

HTML_PROJECT_TEMPLATE = [
    {
        "filePath": "/index.html",
        "code": '''
<!DOCTYPE html>
<html>
<head>
  <title>HTML Project</title>
</head>
<body>
  <h1>Hello World</h1>
</body>
</html>
'''
    }
]

CSS_PROJECT_TEMPLATE = [
    {
        "filePath": "/styles.css",
        "code": 'body { font-family: Arial, sans-serif; margin: 20px; }'
    }
]

JS_PROJECT_TEMPLATE = [
    {
        "filePath": "/script.js",
        "code": 'console.log("Hello World");'
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

REACTNATIVE_PROJECT_TEMPLAETE = [
    {
        "filePath": "App.js",
        "code":'''
import React from 'react';
import { Text, View, StyleSheet } from 'react-native';

const App = () => {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>Hello World!</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f0f0f0',
  },
  text: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
});

export default App;
'''
    },
    {
        "filePath":"package.json",
        "code":'''
{
  "dependencies": {
    "react": "^18.0.0",
    "react-native": "^0.71.0"
  },
  "devDependencies": {
    "@babel/core": "^7.19.6",
    "@babel/preset-env": "^7.19.4",
    "@babel/preset-react": "^7.18.6",
    "babel-jest": "^28.1.0",
    "jest": "^28.1.0"
  },
  "jest": {
    "preset": "react-native"
  }
}
'''
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
    {
        "filePath":"/package.json",
        "code":'''
{
  "dependencies": {},
  "scripts": {
    "start": "node index.js"
  },
  "main": "index.js",
  "devDependencies": {}
}'''
    }
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
    print("data form valudation",data)
    """
    Validate the incoming project data and add additional keys with default values.
    """
    required_fields = ["projectName", "lang"]
    for field in required_fields:
        if field not in data or not isinstance(data[field], str) or not data[field].strip():
            raise ValueError(f"Invalid or missing '{field}': must be a non-empty string.")

    lang = data["lang"].strip().lower()

    if lang == "python":
        file_sets = PYTHON_PROJECT_TEMPLATE
    elif lang == "webstack":
        file_sets = WEB_PROJECT_TEMPLATE
    elif lang == "react":
        file_sets = REACT_PROJECT_TEMPLATES
    elif lang == "node":
        file_sets = NODE_PROJECT_TEMPLATE
    elif lang == "react-native":
        file_sets = REACTNATIVE_PROJECT_TEMPLAETE
    else:
        raise ValueError(f"Unsupported language '{lang}'. Supported options are: 'python', 'webstack', 'react', 'node'.")

    project = {
        "projectId": data["projectId"] if data.get("projectId") else generate_project_id(),
        "projectName": data["projectName"].strip(),
        "lang": lang,
        "lastUpdatedDate": generate_last_updated_date(),
        "fileSets": file_sets,
        "dependencies": (
            REACT_PROJECT_DEPENDENCIES if lang == "react" else 
            REACT_NATIVE_PROJECT_DEPENDENCIES if lang == "react-native" else 
            {}
        )
    }


    if lang == "node":
        project["dataStatus"] = "retrieved",
        project["port"] = 4000

    return project

@app.route("/add-project", methods=["POST"])
def add_project():
    try:
        data = request.get_json()

        project = validate_and_process_project(data)

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
        projects = code_collection.find({}, {"_id": 0, "projectId": 1, "projectName": 1, "lang": 1, "lastUpdatedDate": 1})

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
        print("project id from",projectId)
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
        print("data", data)

        required_fields = ["projectId", "filePath", "code"]
        for field in required_fields:
            if field not in data or not isinstance(data[field], str) or not data[field].strip():
                raise ValueError(f"Invalid or missing '{field}': must be a non-empty string.")

        projectId = data["projectId"].strip()
        filePath = data["filePath"].strip()
        new_code = data["code"].strip()

        project = code_collection.find_one({"projectId": projectId})
        if not project:
            return jsonify({"error": "Project not found."}), 404

        print(project["fileSets"], "project[fileSets]")
        file_exists = any(f["filePath"] == filePath for f in project["fileSets"])
        if not file_exists:
            return jsonify({"error": f"File with path '{filePath}' not found in the project."}), 404

        update_data = {
            "fileSets.$.code": new_code,
            "lastUpdatedDate": generate_last_updated_date()
        }
        print(" ", project.get("lang"))
        if project.get("lang") == "node":
            update_data["dataStatus"] = "new"
            update_data["logs"] = {"output": [], "error": []}

        result = code_collection.update_one(
            {"projectId": projectId, "fileSets.filePath": filePath},
            {"$set": update_data}
        )

        if result.modified_count > 0:
            if project.get("lang") == "python":
                current_directory = os.getcwd() 
                local_file_path = os.path.join(current_directory, filePath)
                print("Resolved local file path:", local_file_path)

                dir_path = os.path.dirname(local_file_path)
                if dir_path: 
                    try:
                        os.makedirs(dir_path, exist_ok=True)
                        print(f"Directories created (or already exist): {dir_path}")
                    except Exception as e:
                        return jsonify({"error": f"Failed to create directories: {str(e)}"}), 500

                try:
                    with open(local_file_path, "w") as file:
                        file.write(new_code)  
                    print(f"File '{local_file_path}' created and written successfully.")
                except Exception as e:
                    return jsonify({"error": f"Failed to write file: {str(e)}"}), 500

                try:
                    execution_result = subprocess.run(
                        ["python", local_file_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    output = execution_result.stdout
                    error = execution_result.stderr
                except Exception as exec_err:
                    return jsonify({
                        "message": "File code updated and saved, but script execution failed.",
                        "error": str(exec_err)
                    }), 500

                return jsonify({
                    "message": "File code updated and script executed successfully.",
                    "projectId": projectId,
                    "filePath": filePath,
                    "executionOutput": output,
                    "executionError": error
                }), 200
            else:
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

        required_fields = ["projectId", "oldFilePath", "newFilePath"]
        for field in required_fields:
            if field not in data or not isinstance(data[field], str) or not data[field].strip():
                raise ValueError(f"Invalid or missing '{field}': must be a non-empty string.")

        projectId = data["projectId"].strip()
        oldFilePath = data["oldFilePath"].strip()
        newFilePath = data["newFilePath"].strip()

        project = code_collection.find_one({"projectId": projectId})
        if not project:
            return jsonify({"error": "Project not found."}), 404

        file_to_rename = next((f for f in project["fileSets"] if f["filePath"] == oldFilePath), None)
        if not file_to_rename:
            return jsonify({"error": f"File with path '{oldFilePath}' not found in the project."}), 404

        new_file_exists = any(f["filePath"] == newFilePath for f in project["fileSets"])
        if new_file_exists:
            return jsonify({"error": f"File with path '{newFilePath}' already exists in the project."}), 400

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

        required_fields = ["projectId", "filePath"]
        for field in required_fields:
            if field not in data or not isinstance(data[field], str) or not data[field].strip():
                raise ValueError(f"Invalid or missing '{field}': must be a non-empty string.")

        projectId = data["projectId"].strip()
        filePath = data["filePath"].strip()

        project = code_collection.find_one({"projectId": projectId})
        if not project:
            return jsonify({"error": "Project not found."}), 404

        file_to_delete = next((f for f in project["fileSets"] if f["filePath"] == filePath), None)
        if not file_to_delete:
            return jsonify({"error": f"File with path '{filePath}' not found in the project."}), 404

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

        if "projectId" not in data or not isinstance(data["projectId"], str) or not data["projectId"].strip():
            raise ValueError("Invalid or missing 'projectId': must be a non-empty string.")

        projectId = data["projectId"].strip()

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


@app.route('/get_endpoint_IP', methods=['POST'])
def get_endpoint_IP():
    data = request.get_json()
    print("json data is ",data)
    project_id = data.get("projectId")

    if not project_id:
        return jsonify({"error": "Missing projectId"}), 400

    project = code_collection.find_one({"projectId": project_id})

    if not project:
        return jsonify({"error": "Project not found"}), 404

    logs = project.get("logs", "No logs available")

    return jsonify({
        "projectId": project["projectId"],
        "projectName": project["projectName"],
        "logs": logs
    })



@app.route('/allocate_project_for_users', methods=['POST'])
def allocate_project_for_users():
    data = request.get_json()
    print("data is", data)
    userId = data.get("userId")
    print("userid is", userId)
    internshipID = data.get("internshipID")

    if not userId:
        return jsonify({"error": "Missing userId"}), 400

    userDetails = userCollection.find_one({"userId": userId}, {"_id": 0, "internship": 1})
    if not userDetails:
        return jsonify({"error": "No user found"}), 404

    


@app.route('/get_project_by_User', methods=['POST'])
def get_project_by_user():
    data = request.get_json()
    print("data is", data)
    userId = data.get("userId")
    internId = data.get("internId")
    print("data from the ",int(internId))
    if not userId:
        return jsonify({"error": "Missing userId"}), 400

    projectData = userCollection.find_one({"userId": userId}, {"_id": 0, "internship": 1})
    print(projectData)
    if not projectData:
        return jsonify({"error": "No user found"}), 404

    internship_match = next(
            (item for item in projectData["internship"] if item.get("internshipID") == int(internId)), None
        )

    if not internship_match:
        return jsonify({"error": "No internship found"}), 404
    
    return jsonify({"projectData": internship_match}), 200


@app.route('/get_chat', methods=['POST'])
def get_chat():
    data = request.get_json()
    print("data is", data)
    userId = data.get("userId")
    projectId = data.get("projectId")
    print("userid is ", userId, "projectid is", projectId)
    if not userId:
        return jsonify({"error": "Missing userId"}), 400

    userData = chatCollection.find_one({"userId": userId, "projectId": projectId}, {"_id": 0, "messages": 1})
    print("user data is", userData)
    if not userData:
        return jsonify({"error": "No user found"}), 404

    messages = userData.get("messages")

    if not messages:
        return jsonify({"error": "No messages found"}), 404

    return jsonify({"messages": messages}), 200

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    print("data is", data)
    userId = data.get("userId")
    projectId = data.get("projectId")
    message = data.get("message")

    if not userId:
        return jsonify({"error": "Missing userId"}), 400

    userData = chatCollection.find_one({"userId": userId, "projectId": projectId}, {"_id": 0, "messages": 1})

    if not userData:
        new_document = {
            "userId": userId,
            "projectId": projectId,
            "messages": [
               message
            ]
        }
        chatCollection.insert_one(new_document)
        return jsonify({"message": "New document created and message stored successfully"}), 201

    chatCollection.update_one(
        {"userId": userId, "projectId": projectId},
        {"$push": {
            "messages": message
        }}
    )
    return jsonify({"message": "Message sent successfully"}), 200


def serialize_document(doc):
    import bson
    if not doc:
        return doc
    return {
        key: str(value) if isinstance(value, bson.ObjectId) else value
        for key, value in doc.items()
    }


@app.route("/applyintern", methods=["POST"])
def apply_intern():
    try:
        data = request.json
        user_id = str(data.get("userId"))
        intern_id = data.get("internId")

        if not user_id or not intern_id:
            return jsonify({"error": "Missing userId or internId", "status": False}), 400

        user = userCollection.find_one({"userId": user_id}, {"internship": 1})

        internship_match = next(
            (item for item in user["internship"] if item.get("internshipID") == intern_id), None
        )

        if not internship_match:
            userCollection.update_one(
                {"userId": user_id},
                {"$push": {"internship": {"internshipID": intern_id, "projects": []}}}
            )
            user = userCollection.find_one({"userId": user_id}, {"internship": 1})
            internship_match = next(
                (item for item in user["internship"] if item.get("internshipID") == intern_id), None
            )

        if internship_match and internship_match.get("projects"):
            return jsonify({
                "internshipId": intern_id,
                "message": "Internship already has projects assigned",
                "internship": internship_match,
                "status": False
            }), 200

        projects_cursor = projectDetails.find_one({"ProjectID": intern_id})
        if not projects_cursor:
            return jsonify({"error": "No projects found for this internship ID", "status": False}), 200

        all_projects = projects_cursor.get("projects", [])

        easy_projects = [p for p in all_projects if p.get("difficultLevel", 0) <= 30]
        medium_projects = [p for p in all_projects if 30 < p.get("difficultLevel", 0) <= 70]
        hard_projects = [p for p in all_projects if p.get("difficultLevel", 0) > 70]

        random.shuffle(easy_projects)
        random.shuffle(medium_projects)
        random.shuffle(hard_projects)

        selected_easy = easy_projects[:2]
        selected_medium = medium_projects[:2]
        selected_hard = hard_projects[:1]

        selected_projects = selected_easy + selected_medium + selected_hard

        if not selected_projects:
            return jsonify({"error": "No matching projects found", "status": False}), 200

        projects_list = []
        lock_status_set = False  
        stored_projects = []  

        for project in selected_projects:
            project_data = {
                "projectTitle": project.get("projectTitle", "Unnamed Project"),
                "projectId": project.get("project_Id"),
                "projects": project.get("folders", []),
                "difficultLevel": project.get("difficultLevel", 0),
                "lockStatus": True, 
                "projectProgress": 0
            }

            if not lock_status_set and project in selected_easy:
                project_data["lockStatus"] = False
                lock_status_set = True

            projects_list.append(project_data)

            for folder in project.get("folders", []):
                folder_data = {
                    "projectName": project.get("projectTitle", "Unnamed Project"),
                    "projectId": folder.get("folderID"),
                    "lang": folder.get("folder")
                }

                try:
                    processed_project = validate_and_process_project(folder_data)
                    print("Processed project:", processed_project)
                    code_collection.insert_one(processed_project)
                    stored_projects.append(processed_project)
                except ValueError as e:
                    print(f"Error processing folder: {e}")

        userCollection.update_one(
            {"userId": user_id, "internship.internshipID": intern_id},
            {"$set": {"internship.$.projects": projects_list}}
        )

        return jsonify({
            "message": "Projects allocated and processed successfully",
            "internshipId": intern_id,
            "status": True
        }), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "An error occurred", "message": str(e), "status": False}), 500


@app.route('/user/internDetail', methods=['GET'])
def intern_detail():
    userId = request.args.get("userId")
    if not userId:
        return jsonify({"error": "Missing userId"}), 400

    projectData = userCollection.find_one({"userId": userId}, {"_id": 0, "internship": 1})

    print(projectData)
    if not projectData:
        return jsonify({"error": "No user found"}), 404

    return jsonify({ "status": True, "internship":projectData }), 200

@app.route('/updateInternship', methods=['GET'])
def update_internship():

    internshipData = list(internshipCollection.find({}, {"_id": 0}))

    if not internshipData:
        return jsonify({"error": "No internship found"}), 404

    return jsonify({"status": True, "internships": internshipData}), 200


@app.route('/execute', methods=['POST'])
def execute_code():
    data = request.get_json()
    print("data",data)
    code = data.get('codeFromEditor', '')
    print("code",code)

    with open('temp_code.py', 'w') as file:
        file.write(code)

    try:
        result = subprocess.run(['python', 'temp_code.py'], capture_output=True, text=True, check=True)
        output = result.stdout
        print(output,"output")
    except subprocess.CalledProcessError as e:
        output = e.stderr  

    return jsonify({'result': output})


from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import subprocess
import json
from datetime import datetime
import traceback
import sys

app = Flask(__name__)
CORS(app)

# Configuration
PROJECTS_DIR = "code_projects"
OUTPUT_DIR = "code_outputs"

# Create necessary directories
for directory in [PROJECTS_DIR, OUTPUT_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

def create_project_directories(project_id):
    """Create project directories if they don't exist"""
    project_dir = os.path.join(PROJECTS_DIR, project_id)
    output_dir = os.path.join(OUTPUT_DIR, project_id)
    
    for directory in [project_dir, output_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    return project_dir, output_dir

def save_output(project_id, output_data):
    """Save execution output to a file"""
    _, output_dir = create_project_directories(project_id)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"output_{timestamp}.json")
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    return output_file

@app.route('/execute-code', methods=['POST'])
def execute_code():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        project_id = data.get('projectId')
        code = data.get('code')
        print("project id ",project_id)
        print("code id ",code)
        if not all([project_id, code]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Create project directories
        project_dir, _ = create_project_directories(project_id)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"code_{timestamp}.py"
        file_path = os.path.join(project_dir, file_name)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)

        try:
            result = subprocess.run(
                [sys.executable, file_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            output_data = {
                'timestamp': timestamp,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'file_name': file_name
            }

            output_file = save_output(project_id, output_data)

            history = get_execution_history(project_id)

            return jsonify({
                'current_output': output_data,
                'execution_history': history,
                'file_path': file_path
            })

        except subprocess.TimeoutExpired:
            error_data = {
                'timestamp': timestamp,
                'error': 'Execution timeout',
                'stderr': 'Code execution exceeded 30 second timeout limit',
                'file_name': file_name
            }
            save_output(project_id, error_data)
            return jsonify(error_data), 408

    except Exception as e:
        error_data = {
            'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        if project_id:
            save_output(project_id, error_data)
        return jsonify(error_data), 500

def get_execution_history(project_id):
    output_dir = os.path.join(OUTPUT_DIR, project_id)
    if not os.path.exists(output_dir):
        return []

    history = []
    for file_name in sorted(os.listdir(output_dir), reverse=True)[:10]:  # Get last 10 executions
        if file_name.endswith('.json'):
            with open(os.path.join(output_dir, file_name), 'r') as f:
                history.append(json.load(f))
    
    return history

@app.route('/get-execution-history/<project_id>', methods=['GET'])
def execution_history(project_id):
    try:
        history = get_execution_history(project_id)
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-code/<project_id>/<file_name>', methods=['GET'])
def get_code(project_id, file_name):
    try:
        file_path = os.path.join(PROJECTS_DIR, project_id, file_name)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        return jsonify({
            'code': code,
            'file_name': file_name
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(port=port,host='0.0.0.0')