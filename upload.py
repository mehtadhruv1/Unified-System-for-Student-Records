from __future__ import print_function

import pandas as pd
import os
import json
from flask import Flask, render_template, redirect, request
from flask_pymongo import PyMongo
from googleapiclient.discovery import build, MediaFileUpload
from httplib2 import Http
from oauth2client import client, file, tools
from werkzeug.utils import secure_filename

import auth

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/myDatabase"
mongo = PyMongo(app)

ALLOWED_EXTENSIONS = set(["jpg", "jpeg", "pdf", "png", "doc"])


def uploadfile():
    file = request.files["File"]
    file_name = request.form.get("file_name")
    file_type = request.form.get("file_type")
    filepath = os.path.realpath(file.filename)
    file_extenstion = file.filename.rsplit(".", 1)[1].lower()
    if file and file_extenstion in ALLOWED_EXTENSIONS:
        filename = secure_filename(file.filename)
    else:
        return "Invalid File Format"
    drive = auth.getCredentials()
    gfolder = "https://drive.google.com/drive/folders/16JMHYtZq-qAZJTuXl5bRtW84uTFNsLwC?usp=sharing"
    gfolder_id = "16JMHYtZq-qAZJTuXl5bRtW84uTFNsLwC"
    roll_no = int(request.form["roll_no"])
    # Call the Drive v3 API
    UPLOAD_FOLDER = "uploadfiles\\"
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    file1 = drive.CreateFile(
        {
            "title": filename,
            "mimeType": "application/pdf",
            "parents": [{"kind": gfolder, "id": gfolder_id}],
        }
    )
    # Create GoogleDriveFile instance with title 'Hello.txt'.

    # Set content of the file from given string.
    file1.SetContentFile(UPLOAD_FOLDER  + filename)
    file1.Upload()
    file_id = file1.get("id")
    student_exist = mongo.db.studentdetails.count_documents({"roll_no": roll_no})

    if student_exist != 0:
        mongo.db.studentdetails.update(
            {"roll_no": roll_no},
            {"$push": {"documents": {"file_name" : file_name, "file_id":file_id, "document_type":file_type }}},
        )
        data = mongo.db.studentdetails.find({"roll_no" : roll_no}, {"_id": 0, "internships" : 1})
        if file_type == "internship":
            for document in data:
                internship_count = document["internships"]
            if internship_count == '-':
                internship_count = 0
            internship_count = int(internship_count) + 1
            mongo.db.studentdetails.update({"roll_no" : roll_no}, {"$set" : {"internships" : internship_count}})
        else:
            data = mongo.db.studentdetails.find({"roll_no" : roll_no},{"documents.document_type": "other"})
            count = 0
            for document in data:
                for file_type in document["documents"]:
                    if file_type["document_type"] == "other":
                        count = count + 1
            mongo.db.studentdetails.update({"roll_no" : roll_no}, {"$set" : {"extracurricular_activities" : count}})



        return "file Upload successful"

    else:
        return "student not found"

def uploadimage(roll_no):
    file = request.files["File"]
    filepath = os.path.realpath(file.filename)
    file_extenstion = file.filename.rsplit(".", 1)[1].lower()
    if file and file_extenstion in ['jpg', 'jpeg', 'png']:
        filename = secure_filename(file.filename)
    else:
        return "Invalid File Format"
    drive = auth.getCredentials()
    gfolder = "https://drive.google.com/drive/u/4/folders/1x0oNCpM1DWHSGmWrAm1LWI05Xws43Wzy?usp=sharing"
    gfolder_id = "1x0oNCpM1DWHSGmWrAm1LWI05Xws43Wzy"
    # Call the Drive v3 API
    UPLOAD_FOLDER = "uploadfiles\\studentimages\\"
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], str(roll_no) + ".jpg"))
    file1 = drive.CreateFile(
        {
            "title": str(roll_no) + ".jpg",
            "mimeType": "image/jpg",
            "parents": [{"kind": gfolder, "id": gfolder_id}],
        }
    )
    # Create GoogleDriveFile instance with title 'Hello.txt'.

    # Set content of the file from given string.
    file1.SetContentFile(UPLOAD_FOLDER  + str(roll_no) + ".jpg")
    file1.Upload()
    file_id = file1.get("id")
    
    return file_id

def downloadfile():
    
    return redirect(
        "https://drive.google.com/uc?export=download&id=1L1VWB6vhWYMNwh7-PLFHe4DJHIBCeWZu"
    )


def uploadInternships(email):
    file = request.files["File"]
    file_name = request.form.get("file_name")
    file_type = request.form.get("file_type")
    filepath = os.path.realpath(file.filename)
    file_extenstion = file.filename.rsplit(".", 1)[1].lower()
    if file and file_extenstion in ['pdf']:
        filename = secure_filename(file.filename)
    else:
        return "Invalid File Format"
    
    #roll_no = int(request.form["roll_no"])
    # Call the Drive v3 API
    drive = auth.getCredentials()
    gfolder = "https://drive.google.com/drive/u/4/folders/1x0oNCpM1DWHSGmWrAm1LWI05Xws43Wzy?usp=sharing"
    gfolder_id = "1x0oNCpM1DWHSGmWrAm1LWI05Xws43Wzy"
    UPLOAD_FOLDER = "uploadfiles\\"
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    file1 = drive.CreateFile(
        {
            "title": filename,
            "mimeType": "application/pdf",
            "parents": [{"kind": gfolder, "id": gfolder_id}],
        }
    )

    file1.SetContentFile(UPLOAD_FOLDER + filename)
    file1.Upload()
    file_id = file1.get("id")
  
    student_data= mongo.db.studentdetails.find_one({"email":email}, {"roll_no":1, "name":1,"branch":1, "current_year":1}) 
    mongo.db.student_activity.insert_one(
            {"roll_no": int(student_data['roll_no']),"name": student_data['name'],"branch": student_data['branch'], "current_year": student_data['current_year'], "file_name" : file_name,"file_type":file_type, "file_id":file_id} )    
    return "file Upload successful"

def deletefile(file_id):
    drive = auth.getCredentials()
    gfolder = "https://drive.google.com/drive/u/4/folders/1x0oNCpM1DWHSGmWrAm1LWI05Xws43Wzy?usp=sharing"
    gfolder_id = "1x0oNCpM1DWHSGmWrAm1LWI05Xws43Wzy"
    file1 = drive.CreateFile({'id':file_id})
    file1.Delete() 
