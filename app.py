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


@app.route('/restrictUser', methods=['POST'])
def restrictUserFromGroup():
    gId = request.form["gId"] if request.form.get("gId") else None
    userId = request.form["userId"] if request.form.get("userId") else None
    currentUserId = request.form["loggedId"] if request.form.get("loggedId") else None
    restrict = request.form["restrict"] if request.form.get("restrict") else None
    if gId and userId and restrict and currentUserId:
        group = db.groupList.find_one({'gId': gId})
        if group:
            if group['adminId'] == currentUserId:
                if db.groupList.find_one({"gId": gId, "users.id": userId}):
                    db.groupList.update({
                        'gId': gId,
                        'users.id': userId
                    }, {
                        "$set": {"users.$.restrict": True if restrict.lower() == "true" else False}
                    })
                    return json.dumps({"status": 1, "message": "User restriction changed"})
                else:
                    return json.dumps({"status": 0, "message": "Something went wrong"})
            else:
                return json.dumps({"status": 0, "message": "You can't change admin"})
        else:
            return json.dumps({"status": 0, "message": "No group exist"})
    else:
        return json.dumps({"status": 0, "message": "All fields are required"})


@app.route('/addUserToGroup', methods=['POST'])
def addUserToGroup():
    gId = request.form["gId"] if request.form.get("gId") else None
    loggedId = request.form["loggedId"] if request.form.get("loggedId") else None
    shareId = request.form["shareId"] if request.form.get("shareId") else None

    if gId and shareId and loggedId:
        dbUser = db.users.find_one({"shareId": shareId})
        dbGroup = db.groupList.find_one({"gId": gId})
        if dbUser and dbGroup:
            if dbGroup['adminId'] == loggedId:
                if db.groupList.find_one({"gId": gId, "users.id": dbUser['userId']}) is None:
                    db.groupList.update({'gId': gId}, {
                        "$addToSet": {
                            "users": {
                                "id": dbUser['userId'],
                                "restrict": False
                            }
                        }
                    })
                if db.users.find_one({"userId": dbUser['userId'], "groups.gId": gId}) is None:
                    db.users.update({'userId': dbUser['userId']}, {
                        "$addToSet": {
                            "groups": {
                                "gId": gId
                            }
                        }
                    })
                return json.dumps({"status": 1, "message": "User added successfully"})
            else:
                return json.dumps({"status": 0, "message": "You can't add participate"})
        else:
            return json.dumps({"status": 0, "message": "Something went wrong"})
    else:
        return json.dumps({"status": 0, "message": "All fields are required"})


@app.route('/updateMessage', methods=['POST'])
def updateMessage():
    gId = request.form["gId"] if request.form.get("gId") else None
    userId = request.form["loggedId"] if request.form.get("loggedId") else None
    message = request.form["message"] if request.form.get("message") else ""

    if gId and userId:
        group = db.groupList.find_one({"gId": gId, "users.id": userId})
        if group:
            if \
                    db.groupList.find_one({"gId": gId, "users.id": userId}, {"users": {"$elemMatch": {"id": userId}}})[
                        'users'][
                        0]['restrict'] is not True:
                db.groupList.update({'gId': gId}, {'$set': {'message': message}})
                return json.dumps({"status": 1, "message": "message updated successfully"})
            else:
                return json.dumps({"status": 0, "message": "You can't edit this note"})
        else:
            return json.dumps({"status": 0, "message": "Something went wrong"})
    else:
        return json.dumps({"status": 0, "message": "All field are required"})


@app.route('/removeMember', methods=['POST'])
def removeMember():
    gId = request.form["gId"] if request.form.get("gId") else None
    currentUserId = request.form["loggedId"] if request.form.get("loggedId") else None
    userId = request.form["userId"] if request.form.get("userId") else None

    if gId and currentUserId and userId:
        group = db.groupList.find_one({'gId': gId, "users.id": userId})
        if group:
            if group['adminId'] == currentUserId:
                db.groupList.update({'gId': gId}, {'$pull': {'users': {'id': userId}}})
                return json.dumps({"status": 1, "message": "User removed successfully"})
            else:
                return json.dumps({"status": 0, "message": "You can't remove participate"})
        else:
            return json.dumps({"status": 0, "message": "Something went wrong"})
    else:
        return json.dumps({"status": 0, "message": "All field are required"})


@app.route('/makeAdmin', methods=['POST'])
def makeAdmin():
    gId = request.form["gId"] if request.form.get("gId") else None
    currentUserId = request.form["loggedId"] if request.form.get("loggedId") else None
    userId = request.form["userId"] if request.form.get("userId") else None

    if gId and currentUserId and userId:
        group = db.groupList.find_one({'gId': gId})
        if group:
            if group['adminId'] == currentUserId:
                db.groupList.update({'gId': gId}, {'$set': {'adminId': userId}})
                return json.dumps({"status": 1, "message": "Admin changed successfully"})
            else:
                return json.dumps({"status": 0, "message": "You can't change admin"})
        else:
            return json.dumps({"status": 0, "message": "No group exist"})
    else:
        return json.dumps({"status": 0, "message": "All field are required"})


@app.route('/createNote', methods=['POST'])
def createNote():
    adminId = request.form["adminId"] if request.form.get("adminId") else None
    name = request.form["name"] if request.form.get("name") else None
    description = request.form["description"] if request.form.get("description") else None
    message = request.form["message"] if request.form.get("message") else None
    profile = request.form["profile"] if request.form.get("profile") else None

    if adminId and name and description:
        dbUser = db.users.find_one({"userId": adminId})
        if dbUser:
            gId = dbUser["userName"][0:2].upper() + name[0: 2].upper() + createRandomCode().upper() + \
                  adminId[1: 4].upper()
            dbGroupList = db.groupList.find({"adminId": adminId})
            if dbGroupList.count() < dbUser["groupLimit"]:
                if db.groupList.find_one({"gId": gId}) is None:
                    db.groupList.insert({
                        "adminId": adminId,
                        "gId": gId,
                        "name": name,
                        "description": description,
                        "message": message if message else "",
                        "profile": profile if profile else ""
                    })
                    db.groupList.update({'gId': gId}, {
                        "$addToSet": {
                            "users": {
                                "id": adminId,
                                "restrict": False
                            }
                        }
                    })
                    db.users.update({'userId': adminId}, {
                        "$addToSet": {
                            "groups": {
                                "gId": gId
                            }
                        }
                    })
                    return json.dumps({"status": 1, "message": "Group created successfully"})
                else:
                    return json.dumps({"status": 0, "message": "Already created"})
            elif dbGroupList.count() == dbUser["groupLimit"] or dbGroupList.count() > dbUser["groupLimit"]:
                return json.dumps({"status": 0, "message": "You are reached group limit"})


@app.route('/updateUser', methods=['POST'])
def updateUser():
    userId = request.form["userId"] if request.form.get("userId") else None
    userName = request.form["userName"] if request.form.get("userName") else None
    profileUrl = request.form["profileUrl"] if request.form.get("profileUrl") else None
    groupLimit = request.form["groupLimit"] if request.form.get("groupLimit") else None
    if userId is None:
        return json.dumps({"status": 0, "message": "User id is required"})
    if db.users.find_one({"userId": userId}) is not None:
        if profileUrl is not None:
            db.users.update({'userId': userId}, {"$set": {"profileUrl": profileUrl}})
        if userName is not None:
            db.users.update({'userId': userId}, {"$set": {"userName": userName}})
        if groupLimit is not None:
            db.users.update({'userId': userId}, {"$set": {"groupLimit": int(groupLimit)}})

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
    user = {"profileUrl": profileUrl if profileUrl else "", "groupLimit": int(groupLimit) if groupLimit else 5,
            "userId": userId, "emailId": emailId, "userName": userName,
            "shareId": userId[0: 3].upper() + createRandomCode().upper() + userId[1:3].upper()}

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
