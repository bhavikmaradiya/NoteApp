import json
import random

from flask import Flask
from flask import request
from pymongo import MongoClient

app = Flask(__name__)

db = MongoClient("mongodb://127.0.0.1:27017").NoteApp


@app.route('/getUsers', methods=['GET'])
def getUsers():
    usersResponse = []
    users = db.users.find()

    for user1 in users:
        user = {}
        if user1.get("groups"):
            groups = []
            for group in user1["groups"]:
                group1 = db.groupList.find_one({"gId": group["gId"]})
                if group1:
                    groups.append({
                        "adminId": group1["adminId"],
                        "description": group1["description"],
                        "gId": group1["gId"],
                        "message": group1["message"],
                        "name": group1["name"]
                    })
            user["groups"] = groups
        user["emailId"] = user1["emailId"]
        user["groupLimit"] = user1["groupLimit"]
        user["profileUrl"] = user1["profileUrl"]
        user["shareId"] = user1["shareId"]
        user["userId"] = user1["userId"]
        user["userName"] = user1["userName"]
        usersResponse.append(user)
    res = {"status": 1 if users.count() > 0 else 0, "users": usersResponse}
    return json.dumps(res, default=str)


@app.route('/getUsersOfGroup/<gId>', methods=['GET'])
def getUsersOfGroup(gId):
    usersResponse = []
    group = db.groupList.find_one({"gId": gId})
    if group:
        if group.get("users"):
            for user1 in group["users"]:
                user = {"restrict": user1["restrict"],
                        "isAdmin": True if group["adminId"] == user1["id"] else False}
                dbUser = db.users.find_one({"userId": user1["id"]})
                if dbUser:
                    user["emailId"] = dbUser["emailId"]
                    user["groupLimit"] = dbUser["groupLimit"]
                    user["profileUrl"] = dbUser["profileUrl"]
                    user["shareId"] = dbUser["shareId"]
                    user["userId"] = dbUser["userId"]
                    user["userName"] = dbUser["userName"]
                    usersResponse.append(user)
    res = {"status": 1 if len(usersResponse) > 0 else 0, "users": usersResponse}
    return json.dumps(res, default=str)


def createRandomCode():
    chars = [char for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
    string = ""
    for i in range(4):
        string += chars[random.randrange(len(chars))]
    return string


@app.route('/updateUser', methods=['POST'])
def updateUser():
    userId = request.form["userId"] if request.form.get("userId") else None
    userName = request.form["userName"] if request.form.get("userName") else None
    profileUrl = request.form["profileUrl"] if request.form.get("profileUrl") else None
    groupLimit = request.form["groupLimit"] if request.form.get("groupLimit") else None
    user = {}
    if userId is None:
        return json.dumps({"status": 0, "message": "User id is required"})
    dbUser = db.users.find_one({"userId": userId})
    if dbUser is not None:
        user["userName"] = userName if userName else dbUser["userName"]
        user["emailId"] = dbUser["emailId"]
        user["userId"] = dbUser["userId"]
        user["shareId"] = dbUser["shareId"]
        user["groupLimit"] = groupLimit if groupLimit else dbUser["groupLimit"]
        if profileUrl is not None or dbUser.get("profileUrl"):
            user["profileUrl"] = profileUrl if profileUrl else dbUser["profileUrl"]
        db.users.update({'userId': userId}, user)
        return json.dumps({"status": 1, "message": "User updated successfully"})
    else:
        return json.dumps({"status": 0, "message": "No user exist"})


@app.route('/createUser', methods=['POST'])
def insertNewUser():
    userName = request.form["userName"] if request.form.get("userName") else None
    userId = request.form["userId"] if request.form.get("userId") else None
    profileUrl = request.form["profileUrl"] if request.form.get("profileUrl") else None
    groupLimit = request.form["groupLimit"] if request.form.get("groupLimit") else None
    emailId = request.form["emailId"] if request.form.get("emailId") else None
    if userName is None:
        return json.dumps({"status": 0, "message": "Username is required"})
    if userId is None:
        return json.dumps({"status": 0, "message": "User id is required"})
    if emailId is None:
        return json.dumps({"status": 0, "message": "email is required"})
    user = {}
    if profileUrl is not None:
        user["profileUrl"] = profileUrl
    user["groupLimit"] = groupLimit if groupLimit else 5
    user["userId"] = userId
    user["emailId"] = emailId
    user["userName"] = userName
    user["shareId"] = userId[0: 3].upper() + createRandomCode().upper() + userId[1:3].upper()
    dbUser = db.users.find_one({"emailId": emailId})
    if dbUser is None:
        db.users.insert(user)
        return json.dumps({"status": 1, "message": "User inserted successfully"})
    else:
        return json.dumps({"status": 0, "message": "email already taken"})


@app.route('/getUser/<uId>', methods=['GET'])
def getUserById(uId):
    response = {}
    user1 = db.users.find_one({"userId": uId})
    if user1:
        response["status"] = 1
        user = {}
        if user1.get("groups"):
            groups = []
            for group in user1["groups"]:
                group1 = db.groupList.find_one({"gId": group["gId"]})
                if group1:
                    groups.append({
                        "adminId": group1["adminId"],
                        "description": group1["description"],
                        "gId": group1["gId"],
                        "message": group1["message"],
                        "name": group1["name"]
                    })
            user["groups"] = groups
        user["emailId"] = user1["emailId"]
        user["groupLimit"] = user1["groupLimit"]
        user["profileUrl"] = user1["profileUrl"]
        user["shareId"] = user1["shareId"]
        user["userId"] = user1["userId"]
        user["userName"] = user1["userName"]
        response["user"] = user
        return json.dumps(response, default=str)
    else:
        response["status"] = 0
        return json.dumps(response)


if __name__ == '__main__':
    app.run()
