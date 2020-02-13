from flask import Flask, render_template, flash, redirect, session
from flask_pymongo import PyMongo
from flask import request
from flask_mail import Mail, Message
from flask_socketio import SocketIO, emit
from jinja2 import Environment, FileSystemLoader
from collections import OrderedDict
import os
from werkzeug.utils import secure_filename
import pandas as pd
import upload
import auth
import re
import sys
from graph import build_line,build_bar,build_pie, build_bar_category, build_bar_batchwise, build_bar_placement
import matplotlib
import datetime
matplotlib.use('Agg')



import random, json

app = Flask(__name__)
app.secret_key = 'Flask App'
app.config["MONGO_URI"] = "mongodb://localhost:27017/myDatabase"
jinja2_env = Environment(loader=FileSystemLoader('views/'), cache_size=0)

mongo = PyMongo(app)

socketio = SocketIO(app)
#config for flask-mail

app.config.update(
	DEBUG=True,
	#EMAIL SETTINGS
	MAIL_SERVER='smtp.gmail.com',
	MAIL_PORT=465,
	MAIL_USE_SSL=True,
	MAIL_USERNAME = 'collegeproject201819@gmail.com',
	MAIL_PASSWORD = 'college-2018'
	)

mail=Mail(app)

#mdefault render for the flask app

# hod array for hod email:
hodemail = ['hodcomp.engg@somaiya.edu', 'hodit.engg@somaiya.edu', 'hodmech.engg@somaiya.edu', 'hodextc.engg@somaiya.edu', 'hodetrx.engg@somaiya.edu']
placementcellemail = ['placementcell@abc.com']
iaiemail = ['iai@somaiya.edu']
examcellemail = ['examcell.engg@somaiya.edu']
@app.route('/registerpage', methods=['POST', 'GET'])
def registration_page():
    return render_template('register.html')

#post method for data insertion in the database


@app.route('/', methods=['POST', 'GET'])
def register_user():
    data = request.get_json()
    if request.method == 'POST' :
        #users_registration is the collection to store the registration details of the user
        #userdetails is the collection for storing the details of the user aka the master collection
        #userotp is the collection for storing the otp for the registration of the user

        #student_registration for student registration
        #faculty_registration for faculty
        registered_student = mongo.db.student_registration.count_documents({'email': data.get("email", "default")})
        registered_faculty = mongo.db.faculty_registration.count_documents({'email': data.get("email", "default")})

        #studentdetails for student
        #facultydetails for faculty

        database_student_users = mongo.db.studentdetails.count_documents({'email': data.get("email", "default")})
        database_faculty_users = mongo.db.facultydetails.count_documents({'email': data.get("email", "default")})

        #studentotp for student
        #facultyotp for faculty

        otp_student_users = mongo.db.studentuserotp.count_documents({'email': data.get("email", "default")})
        otp_faculty_users = mongo.db.facultyuserotp.count_documents({'email': data.get("email", "default")})

        if database_student_users == 0 and database_faculty_users == 0:
            return json.dumps({"status" : "OK", "result" : "user not present in database"})
        else :
            if registered_student == 0  and registered_faculty == 0:
                if database_student_users !=0 and data.get("usertype", "default") != "student":
                    return json.dumps({"status" : "OK", "result" : "incorrect user type"})

                elif database_faculty_users !=0 and data.get("usertype", "default") == "student":
                    return json.dumps({"status" : "OK", "result" : "incorrect user type"})
                
                else :
                    faculty_type = mongo.db.facultydetails.count_documents({'email': data.get("email", "default"), 'usertype' : data.get("usertype", "default")})
                    if faculty_type ==0 and (data.get("usertype", "default") == "faculty" or data.get("usertype", "default") == "admission"):
                        return json.dumps({"status" : "OK", "result" : "incorrect user type"})
                    else :
                        if otp_student_users == 0 and otp_faculty_users == 0 :
                            otp_generated = random.randint(100000,999999)
                            if data.get("usertype", "default") == "student" :
                                mongo.db.studentuserotp.insert_one({'email': data.get("email", "default") ,'otp': otp_generated})
                            
                            else :
                                mongo.db.facultyuserotp.insert_one({'email': data.get("email", "default") ,'otp': otp_generated})
                            msg = Message(
                            "Hello",
                            sender='collegeproject201819@gmail.com',
                            recipients=['rikhgaha1991@gmail.com'])
                            msg.body = " " + str(otp_generated)
                            mail.send(msg)
                            return json.dumps({"status" : "OK", "result" : "otp generated"})
                        else :
                            onetimepasswordclass = data.get("onetimepasswordclass", "default")
                            if onetimepasswordclass == "hidden" :
                                return json.dumps({"status" : "OK", "result" : "show otp"})
                            else :
                                if data.get("usertype", "default") == "student" :
                                    otp_users = mongo.db.studentuserotp.find_one({'email': data.get("email", "default")})
                                else :
                                    otp_users = mongo.db.facultyuserotp.find_one({'email': data.get("email", "default")})
                                # print(otp_users["user_otp"])
                                # return json.dumps({"status" : "OK", "result" : "otp generated and entered"})
                                if str(otp_users["otp"]) == str(data.get("onetimepassword", "default")) :
                                    if data.get("usertype", "default") == "student" :
                                        mongo.db.student_registration.insert_one({'email': data.get("email", "default") ,'password':data.get("password", "default"), 'user_approve_status': 1})
                                        registered_users = mongo.db.student_registration.count_documents({'email': data.get("email", "default")})

                                    else :
                                        if data.get("email", "default") in hodemail or data.get("email","default") in placementcellemail or data.get("email", "default") in iaiemail:
                                            mongo.db.faculty_registration.insert_one({'user_type':data.get("usertype", "default"),'email': data.get("email", "default") ,'password':data.get("password", "default"), 'user_approve_status': 1})        
                                        else :
                                            mongo.db.faculty_registration.insert_one({'user_type':data.get("usertype", "default"),'email': data.get("email", "default") ,'password':data.get("password", "default"), 'user_approve_status': 0}) 
                                        registered_users = mongo.db.faculty_registration.count_documents({'email': data.get("email", "default")})
                                    if registered_users == 0:
                                        return json.dumps({"status" : "OK", "result" : "registration was not successful"})
                                    else :
                                        return json.dumps({"status" : "OK", "result" : "registration successful"})
                                else:
                                    return json.dumps({"status" : "OK", "result" : "otp entered is not correct"})
            else :
                return json.dumps({"status" : "OK", "result" : "user is already registered"})
    else :
        return render_template("register.html")
    
@app.route('/loginpage', methods=['POST', "GET"])
def login_user():
    # data = request.get_json()
    input = None
    email = None
    usertype = None
    if request.method == 'POST' :
        usertype = request.form["usertype"]
        email = request.form["email"]
        password = request.form["password"]
        if usertype == "student" :
            login_user_count = mongo.db.student_registration.count_documents({'email': email ,'password':password})
        else :
            login_user_count = mongo.db.faculty_registration.count_documents({'email': email ,'password':password, 'user_type': usertype})
        if login_user_count == 1 :
            if usertype == "student" :
                approve_status = mongo.db.student_registration.find_one({'email': email ,'password':password})        
            else :
                approve_status = mongo.db.faculty_registration.find_one({'user_type':usertype,'email': email ,'password':password})
            if approve_status["user_approve_status"] == 1 :
                input = "login successful"
                session['email'] = email
                session['usertype'] = usertype
                return redirect('/homepage')
                # return json.dumps({"status" : "OK", "result" : "valid input"})
            else :
                # return json.dumps({"status" : "OK", "result" : "user not approved"})
                input = "user not approved"
        else :
            # return json.dumps({"status" : "OK", "result" : "invalid input"})
            input = "check email id or password or usertype"
        return render_template("login.html" , input = input, email = email, usertype = usertype)
    else :
        return render_template("login.html", input = input, email = email, usertype = usertype)
    

@app.route('/forgotpassword', methods=['POST', 'GET'])
def forgotpassword():
    if request.method == 'POST' :
        data = request.get_json()
        register_student_count = mongo.db.student_registration.count_documents({'email': data.get("email", "default")})
        register_faculty_count = mongo.db.student_registration.count_documents({'email': data.get("email", "default")})
        if register_student_count == 1 or register_faculty_count == 1:
            if data.get("divclass") == "hidden" :
                otp_generated = random.randint(100000,999999)
                if register_student_count == 1:
                    mongo.db.studentuserotp.update({'email': data.get("email", "default") }, {"$set": {'otp': otp_generated}})
                else :
                    mongo.db.facultyuserotp.update({'email': data.get("email", "default") }, {"$set": {'otp': otp_generated}})
                msg = Message(
                "Hello",
                sender='collegeproject201819@gmail.com',
                recipients=['rikhgaha1991@gmail.com'])
                msg.body = " " + str(otp_generated)
                mail.send(msg)
                return json.dumps({"status" : "OK", "result" : "otp generated"})
            else :
                if register_student_count == 1:
                    otp_users = mongo.db.studentuserotp.find_one({'email': data.get("email", "default")})
                else :
                    otp_users = mongo.db.facultyuserotp.find_one({'email': data.get("email", "default")})
                if str(otp_users["otp"]) == str(data.get("otp", "default")) :
                    if register_student_count == 1:
                        mongo.db.student_registration.update_one({'email': data.get("email", "default") }, {"$set": {'password': data.get("password", "default")}})    
                    else :
                        mongo.db.faculty_registration.update_one({'email': data.get("email", "default") }, {"$set": {'password': data.get("password", "default")}})   
                    return json.dumps({"status" : "OK", "result" : "password successfully updated"})
                else :
                    return json.dumps({"status" : "OK", "result" : "invalid otp"})
        else :
            return json.dumps({"status" : "OK", "result" : "invalid email"})
    else :
        return render_template('forgotpassword.html')

@app.route('/homepage', methods = ["GET", "POST"])
def homepage():
    if 'email' in session:
        if 'usertype' in session:
            if session['usertype'] == "student" :
                c = mongo.db.studentdetails.find_one({'email':session['email']}, {'_id' : 0, "Caste":0, "HandiCapped" : 0, "Minority":0, "Other_category" : 0, "placement": 0, "documents": 0, "year_of_admission" : 0, "gaurdian_name" :0, "relation" :0, "local_address" : 0, "gaurdian_local_address" : 0, "permanent_address" : 0, "contact_number_R" : 0, "contact_number_O" : 0, "contact_number_M" : 0, "student_email" : 0, "gaurdian_email" : 0, "blood_group":0, "date_of_birth" : 0, "place_of_birth" : 0, "mother_tounge" :0, "religion" : 0, "competitive_examination" : 0, "competitive_examination_marks" : 0, "SSC_marks" :0, "HSC_marks" : 0, "proctor_name":0, "proctor_email" : 0})
                return render_template('homepagestudent.html', c=c)
            else:
                data_count = mongo.db.studentdetails.count_documents({})
                if data_count % 25 != 0:
                    total_page = data_count/25 + 1
                else:
                    total_page = data_count/25
                start_page = 1
                if session['email'] in hodemail:
                    user = "hod"
                elif session['email'] in placementcellemail:
                    user = "placement"
                elif session['usertype'] == "faculty" and session['email'] not in hodemail and session['email'] not in placementcellemail and session['email'] not in iaiemail:
                    user = "faculty"
                elif session['email'] in iaiemail:
                    user = "iai"
                elif session['email'] in examcellemail:
                    user = "examcell"
                else :
                    user = "admission"
                if request.method == 'POST':
                    flag = 0
                    c = mongo.db.studentdetails.find_one({},{"_id":0 , "Caste":0, "HandiCapped" : 0, "Minority":0, "Other_category" : 0, "placement": 0, "documents": 0, "year_of_admission" : 0, "gaurdian_name" :0, "relation" :0, "local_address" : 0, "gaurdian_local_address" : 0, "permanent_address" : 0, "contact_number_R" : 0, "contact_number_O" : 0, "contact_number_M" : 0, "student_email" : 0, "gaurdian_email" : 0, "blood_group":0, "date_of_birth" : 0, "place_of_birth" : 0, "mother_tounge" :0, "religion" : 0, "competitive_examination" : 0, "competitive_examination_marks" : 0, "SSC_marks" :0, "HSC_marks" : 0, "proctor_name":0, "proctor_email" : 0, "live kt" : 0, "dead kt" : 0, "division" : 0})
                    #	myquery = { "year": request.form.get('year') }
                    choice = request.form.get('choice')
                    print(choice)
                    if "@" in choice:
                        myquery1 = { "email": choice}
                    elif choice.isdigit():
                        myquery1 = { "roll_no": int(choice)}
                    elif choice=="Get All Details":
                        flag = 1
                        myquery1 = {}
                    elif re.search('[a-zA-Z]', choice):
                        myquery1 = { "name": choice}
                    #	form.populate_obj(year)
                    data_count = mongo.db.studentdetails.count_documents(myquery1)
                    if data_count % 25 != 0:
                        total_page = int(data_count/25) + 1
                        print(total_page)
                    else:
                        total_page = int(data_count/25)
                    start_page = 1
                    if flag==1:
                        data = mongo.db.studentdetails.find(myquery1, { "_id" : 0,"Caste":0, "HandiCapped" : 0, "Minority":0, "Other_category" : 0, "placement": 0, "documents": 0, "year_of_admission" : 0, "gaurdian_name" :0, "relation" :0, "local_address" : 0, "gaurdian_local_address" : 0, "permanent_address" : 0, "contact_number_R" : 0, "contact_number_O" : 0, "contact_number_M" : 0, "student_email" : 0, "gaurdian_email" : 0, "blood_group":0, "date_of_birth" : 0, "place_of_birth" : 0, "mother_tounge" :0, "religion" : 0, "competitive_examination" : 0, "competitive_examination_marks" : 0, "SSC_marks" :0, "HSC_marks" : 0, "proctor_name":0, "proctor_email" : 0}).sort("roll_no",1).skip(data_count-25)
                        flag = 0
                    elif flag==0:
                        data = mongo.db.studentdetails.find(myquery1, { "_id" : 0,"Caste":0, "HandiCapped" : 0, "Minority":0, "Other_category" : 0, "placement": 0, "documents": 0, "year_of_admission" : 0, "gaurdian_name" :0, "relation" :0, "local_address" : 0, "gaurdian_local_address" : 0, "permanent_address" : 0, "contact_number_R" : 0, "contact_number_O" : 0, "contact_number_M" : 0, "student_email" : 0, "gaurdian_email" : 0, "blood_group":0, "date_of_birth" : 0, "place_of_birth" : 0, "mother_tounge" :0, "religion" : 0, "competitive_examination" : 0, "competitive_examination_marks" : 0, "SSC_marks" :0, "HSC_marks" : 0, "proctor_name":0, "proctor_email" : 0}).sort("roll_no",1)
                    return render_template('homepage.html', c = c, d = data,d_count = data_count, user = user, start_page = start_page, total_page = total_page)
                else :
                    data_count = mongo.db.studentdetails.count_documents({})
                    c = mongo.db.studentdetails.find_one({}, {"_id" : 0, "Caste":0, "HandiCapped" : 0, "Minority":0, "Other_category" : 0, "placement": 0, "documents": 0, "year_of_admission" : 0, "gaurdian_name" :0, "relation" :0, "local_address" : 0, "gaurdian_local_address" : 0, "permanent_address" : 0, "contact_number_R" : 0, "contact_number_O" : 0, "contact_number_M" : 0, "student_email" : 0, "gaurdian_email" : 0, "blood_group":0, "date_of_birth" : 0, "place_of_birth" : 0, "mother_tounge" :0, "religion" : 0, "competitive_examination" : 0, "competitive_examination_marks" : 0, "SSC_marks" :0, "HSC_marks" : 0, "proctor_name":0, "proctor_email" : 0, "division" : 0, "live kt" : 0, "dead kt" : 0})
                    data = mongo.db.studentdetails.find({},{'_id' : 0, "Caste":0, "HandiCapped" : 0, "Minority":0, "Other_category" : 0, "placement": 0, "documents": 0, "year_of_admission" : 0, "gaurdian_name" :0, "relation" :0, "local_address" : 0, "gaurdian_local_address" : 0, "permanent_address" : 0, "contact_number_R" : 0, "contact_number_O" : 0, "contact_number_M" : 0, "student_email" : 0, "gaurdian_email" : 0, "blood_group":0, "date_of_birth" : 0, "place_of_birth" : 0, "mother_tounge" :0, "religion" : 0, "competitive_examination" : 0, "competitive_examination_marks" : 0, "SSC_marks" :0, "HSC_marks" : 0, "proctor_name":0, "proctor_email" : 0, "division" : 0, "live kt" : 0, "dead kt" : 0}).sort("roll_no",1).skip(data_count-25)
                    return render_template('homepage.html', c = c, d = data,d_count = data_count, user = user, start_page = start_page, total_page = total_page)

    else:
        print('Maha Error')   
    return redirect('/loginpage')

@app.route('/filterpage', methods = ['POST', "GET"])
def filterpage():
    column = None
    data = None
    dept_values = []
    year_values = []    
    if request.method == "POST" :
        data = request.get_json()
        button_type = data[len(data)-2]
        start_current = int(data[len(data)-1])
        if button_type !="Submit" and button_type !="prev" and button_type !="next":
            skip_count = button_type
        else :
            if button_type == "prev":
                skip_count = max(0,start_current-5)
            elif button_type == "next":
                data_count = mongo.db.studentdetails.count_documents({})
                skip_count = min(start_current+5, data_count/25)
            else:
                skip_count = 1
        cgpa1 = float(data[0])
        cgpa2 = float(data[1])
        mongo_query = {}
        mongo_search = {}
        for i in range (2, len(data)-1) :
        	c = check(data[i])
        	if c=="dept":
        		dept_values.append(data[i])
	        elif c=="year":
	        	year_values.append(data[i])
	        else:
	            mongo_query[data[i]] = 1
        mongo_query["_id"] = 0
        # mongo_query['division'] = 1
        # mongo_query['Gender'] = 1
        # mongo_query['cgpa'] = 1
        # mongo_query['internships'] = 1
        # mongo_query['extracurricular_activities'] = 1
        mongo_query['roll_no'] = 1
        mongo_query['name'] = 1
        mongo_query['email'] = 1
        if len(dept_values)==0:
        	dept_values = add_dept()
        if len(year_values)==0:
        	year_values = add_year()
        column = mongo.db.studentdetails.find_one({})
        data = mongo.db.studentdetails.find({"branch" :{"$in": dept_values}, "current_year":{"$in":year_values}, "cgpa": {"$gte":cgpa1, "$lte":cgpa2}}, mongo_query).skip((int(skip_count)-1)*25).limit(25).sort("roll_no", 1)
        data_count = mongo.db.studentdetails.count_documents({"branch" :{"$in": dept_values}, "current_year":{"$in":year_values}, "cgpa": {"$gte":cgpa1, "$lte":cgpa2}})
        json_data = []
        count = 0
        for document in data:
            if document:
                json_data.append(document)
        if data_count % 25 != 0:
            total_page = (data_count - data_count%25)/25 +1
        else:
            total_page = data_count/25
        total_page = int(total_page)
        if button_type == "prev":
            if start_current > 5:
                start_page = start_current -5
            else:
                start_page = 1
        elif button_type == "next":
            if start_current < total_page - 5:
                start_page = start_current + 5
            else:
                start_page = start_current
        else:
            start_page = start_current
        json_data.append(data_count)
        json_data.append(skip_count)
        json_data.append(total_page)
        json_data.append(start_page)
        return json.dumps(json_data)
    else :    
        return render_template('facultyhomepage.html', column=column, data = data)    

def check(data):
	if data=="IT" or data=="COMPS" or data=="ETRX" or data=="EXTC" or data == "MECH":
		return "dept"
	elif data=="FY" or data=="SY" or data =="TY" or data == "LY":
		return "year"
	else:	
		return "others"	

def add_dept():
	dept = ['IT','COMPS','ETRX', 'EXTC', 'MECH']
	return dept

def add_year():
	year = ['FY','SY','TY', 'LY']
	return year	

@socketio.on('disconnect')
def disconnect_user():
    logout_user()
    session.pop('email', None)
    session.pop('usertype', None)

@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('usertype', None)
    return redirect('/loginpage')

@app.route("/examinationdetails", methods = ['POST', "GET"])
def compssubject():
    if request.method == "GET":
        session["exam_start_page"] = 1
        if 'email' in session:
            if 'usertype' in session:
                start_page = session["exam_start_page"]
                if session['email'] in hodemail:
                    user = "hod"
                elif session['email'] in placementcellemail:
                    user = "placement"
                elif session['usertype'] == "faculty" and session['email'] not in hodemail and session['email'] not in placementcellemail and session['email'] not in iaiemail:
                    user = "faculty"
                elif session['email'] in iaiemail:
                    user = "iai"
                else :
                    user = "admission"       
                sem = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
                sub = ["subject1", "subject2", "subject3", "subject4", "subject5", "subject6"]
                c = mongo.db.compssubject.find_one({},{"_id": 0})
                column_name = {}
                column_name["roll_no"] = ""
                for document in c["examination"]:
                    for key in document:
                        column_name[key] = document[key]
                        break
                    break
                data_count = mongo.db.compssubject.count_documents({})
                skip_count = 1
                d = mongo.db.compssubject.find({},{"_id": 0}).skip((int(skip_count)-1)*25).limit(25).sort("roll_no", 1)
                cd = mongo.db.compssubject.find({},{"roll_no": 1, "_id": 0}).skip((int(skip_count)-1)*25).limit(25).sort("roll_no", 1)
                name = mongo.db.studentdetails.find({},{"_id":0}).skip((int(skip_count)-1)*25).limit(25).sort("roll_no", 1)
                if data_count % 25 != 0:
                    total_page = (data_count - data_count%25)/25
                else:
                    total_page = data_count/25
                search_page = 0
                return render_template("examinationdetails.html", c = column_name,d = d, cd= cd, sub = sub, sem = sem, semlength = 8, d_count = data_count, name = name, user = user, start_page = start_page, total_page = total_page, skip_count = skip_count, search_page = search_page)
            else :
                return redirect('/loginpage')
        else :
            return redirect('/loginpage')
    
    else:
        

        if session['email'] in hodemail:
            user = "hod"
        elif session['email'] in placementcellemail:
            user = "placement"
        elif session['usertype'] == "faculty" :
            user = "faculty"
        else:
            user = "admission" 
        sem = []
        sub = []
        sem_none_count = 0
        sub_none_count = 0
        for i in range (1,9) :
            sem.append(request.form.get("sem" + str(i)))
            if sem[i-1] == None:
                sem_none_count+=1
        for j in range (1,7) :
            sub.append(request.form.get("sub" + str(j)))
            if request.form.get("sub" + str(j)) == None:
                sub_none_count +=1
        sem_count = 8 - sem_none_count
        if sem_none_count == 8:
            sem = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
            sem_count = 8
        if sub_none_count == 6:
            sub = ["subject1", "subject2", "subject3", "subject4", "subject5", "subject6"]
        c = mongo.db.compssubject.find_one({},{"_id": 0})
        column_name = {}
        column_name["roll_no"] = ""
        for document in c["examination"]:
            for key in document:
                column_name[key] = document[key]
                break
            break
        search_term = request.form.get("searchTerm")
        if search_term != None:
            data_count = 1
            if search_term.isdigit():
                
                d = mongo.db.compssubject.find({"roll_no" : int(request.form.get("searchTerm"))},{"_id": 0}).sort("roll_no", 1)
                cd = mongo.db.compssubject.find({"roll_no" : int(request.form.get("searchTerm"))},{"roll_no": 1, "_id": 0}).sort("roll_no", 1)
                name = mongo.db.studentdetails.find({"roll_no" : int(request.form.get("searchTerm"))},{"_id":0}).sort("roll_no", 1)
                
            else:
                name = mongo.db.studentdetails.find({"name" : request.form.get("searchTerm")},{"_id":0, "roll_no" : 1}).sort("roll_no", 1)
                roll_no_list = []
                for document in name:
                    roll_no_list.append(document["roll_no"])
                d = mongo.db.compssubject.find({"roll_no" : {"$in" : roll_no_list}},{"_id": 0}).sort("roll_no", 1)
                cd = mongo.db.compssubject.find({"roll_no" : {"$in" : roll_no_list}},{"roll_no": 1, "_id": 0}).sort("roll_no", 1)
                name = mongo.db.studentdetails.find({"roll_no" : {"$in" : roll_no_list}},{"_id":0}).sort("roll_no", 1)
            start_page = 1
            skip_count = 1
            search_page = 1
        else:
            search_page = 0
            skip_count = request.form.get('page_number')
            start_page = session["exam_start_page"]
            if not skip_count.isdigit():
                if skip_count == "Previous 5":
                    skip_count = max(1, start_page-5)
                    session["exam_start_page"] = skip_count
                elif skip_count == "Next 5":
                    data_count = mongo.db.compssubject.count_documents({})
                    if data_count % 25 != 0:
                        total_page = (data_count - data_count%25)/25
                    else:
                        total_page = data_count/25
                    skip_count = min(session["exam_start_page"]+5, total_page-4)
                    session["exam_start_page"] = skip_count
                else:
                    skip_count = start_page

            start_page = int(session["exam_start_page"])
            data_count = mongo.db.compssubject.count_documents({})
            d = mongo.db.compssubject.find({},{"_id": 0}).skip((int(skip_count)-1)*25).limit(25).sort("roll_no", 1)
            cd = mongo.db.compssubject.find({},{"roll_no": 1, "_id": 0}).skip((int(skip_count)-1)*25).limit(25).sort("roll_no", 1)
            name = mongo.db.studentdetails.find({},{"_id":0}).skip((int(skip_count)-1)*25).limit(25).sort("roll_no", 1)
        json_data = {}
        json_data["1"] = column_name
        json_array = []
        # for document in d:
        json_array.append(d)
            # break
        json_data["2"] = json_array

        if data_count % 25 != 0:
            total_page = (data_count - data_count%25)/25
        else:
            total_page = data_count/25
        # print(skip_count)
        return render_template("examinationdetails.html", c = column_name,d = d, cd= cd, sub = sub, sem = sem, semlength = 8, d_count = data_count, name = name, user = user, total_page = total_page, start_page = start_page, skip_count = skip_count, search_page = search_page)

@app.route('/placementdetails', methods=['POST', "GET"])
def placementdata():
    data_count = mongo.db.studentdetails.count_documents({})
    if data_count % 25 != 0:
        total_page = data_count/25 + 1
    else:
        total_page = data_count/25
    start_page = 1
    skip_count = 1
    
    c = mongo.db.studentdetails.find_one({},{"_id":0, "Caste" :0, "HandiCapped" : 0, "Gender":0, "Minority" : 0, "Other_category":0, "documents":0, "cgpa" : 0, "current_year":0, "internships" : 0, "year_of_admission" : 0, "gaurdian_name" :0, "relation" :0, "local_address" : 0, "gaurdian_local_address" : 0, "permanent_address" : 0, "contact_number_R" : 0, "contact_number_O" : 0, "contact_number_M" : 0, "student_email" : 0, "gaurdian_email" : 0, "blood_group":0, "date_of_birth" : 0, "place_of_birth" : 0, "mother_tounge" :0, "religion" : 0, "competitive_examination" : 0, "competitive_examination_marks" : 0, "SSC_marks" :0, "HSC_marks" : 0, "proctor_name":0, "proctor_email" : 0, "division": 0, "freeze" : 0, "extracurricular_activities" : 0, "live kt" : 0, "dead kt" : 0})
    data = mongo.db.studentdetails.find({},{"_id":0, "Caste" :0, "HandiCapped" : 0, "Gender":0, "Minority" : 0, "Other_category":0,"documents":0, "cgpa" : 0, "current_year":0, "internships" : 0, "year_of_admission" : 0, "gaurdian_name" :0, "relation" :0, "local_address" : 0, "gaurdian_local_address" : 0, "permanent_address" : 0, "contact_number_R" : 0, "contact_number_O" : 0, "contact_number_M" : 0, "student_email" : 0, "gaurdian_email" : 0, "blood_group":0, "date_of_birth" : 0, "place_of_birth" : 0, "mother_tounge" :0, "religion" : 0, "competitive_examination" : 0, "competitive_examination_marks" : 0, "SSC_marks" :0, "HSC_marks" : 0, "proctor_name":0, "proctor_email" : 0 , "division": 0, "freeze" : 0, "extracurricular_activities" : 0, "live kt" : 0, "dead kt" : 0 }).skip((int(skip_count)-1)*25).limit(25).sort("roll_no", 1)
    if "usertype" in session:
        if session["usertype"] != "student":
            if session['email'] in hodemail:
                    user = "hod"
            elif session['email'] in placementcellemail:
                user = "placement"
            elif session['usertype'] == "faculty" and session['email'] not in hodemail and session['email'] not in placementcellemail and session['email'] not in iaiemail:
                user = "faculty"
            elif session['email'] in iaiemail:
                user = "iai"
            else :
                user = "admission" 
            companynames = mongo.db.companydetails.find({},{"_id":0, "companyname" :1})
            cnameslist = []
            if companynames != None:
                for document in companynames:
                    for cname in document:
                        for j in range(0,len(document[cname])):
                            cnameslist.append(document[cname][j])

            return render_template('placementdetails.html', c=c, d_count = data_count, d=data, user = user, total_page = total_page, start_page = start_page, skip_count = skip_count, cnameslist = cnameslist)
        else:
            return redirect("/loginpage")
    else :
        return redirect("/loginpage")

@app.route('/placement_search', methods=['POST'])		
def placement_search():
    if "usertype" in session:
        if session["usertype"] != "student":
            if session['email'] in hodemail:
                    user = "hod"
            elif session['email'] in placementcellemail:
                user = "placement"
            elif session['usertype'] == "faculty" and session['email'] not in hodemail and session['email'] not in placementcellemail and session['email'] not in iaiemail:
                user = "faculty"
            elif session['email'] in iaiemail:
                user = "iai"
            else :
                user = "admission" 
            data_count = mongo.db.studentdetails.count_documents({})
            c = mongo.db.studentdetails.find_one({},{"_id":0, "Caste" :0, "HandiCapped" : 0, "Gender":0, "Minority" : 0, "Other_category":0, "documents":0, "cgpa" : 0, "current_year":0, "internships" : 0, "year_of_admission" : 0, "gaurdian_name" :0, "relation" :0, "local_address" : 0, "gaurdian_local_address" : 0, "permanent_address" : 0, "contact_number_R" : 0, "contact_number_O" : 0, "contact_number_M" : 0, "student_email" : 0, "gaurdian_email" : 0, "blood_group":0, "date_of_birth" : 0, "place_of_birth" : 0, "mother_tounge" :0, "religion" : 0, "competitive_examination" : 0, "competitive_examination_marks" : 0, "SSC_marks" :0, "HSC_marks" : 0, "proctor_name":0, "proctor_email" : 0})
            choice = request.form.get('choice')
            if "@" in choice:
                myquery1 = { "email": choice}
            elif choice.isdigit():
                myquery1 = { "roll_no": int(choice)}
            elif choice=="Get All Details":
                flag = 1
                myquery1 = {}
            elif re.search('[a-zA-Z]', choice):
                myquery1 = { "name": choice}
            data = mongo.db.studentdetails.find(myquery1).sort("roll_no",1)
            start_page = 1
            total_page = 1
            return render_template('placementdetails.html', c = c, d = data, d_count = data_count, user = user, total_page = 1, start_page = 1)
        else:
            return redirect("/loginpage")
    else:
        return redirect("/loginpage")

@app.route('/placementfilter', methods = ['POST'])
def placementfilter():
    column = None
    data = None
    cgpa = None
    cgpa1 = 0.0
    cgpa2 = 0.0
    dept_values = []
    if request.method == "POST" :
        data = request.get_json()
        button_type = data[len(data)-2]
        start_current = int(data[len(data)-1])
        if button_type !="Submit" and button_type !="prev" and button_type !="next":
            skip_count = button_type
        else :
            if button_type == "prev":
                skip_count = max(0,start_current-5)
            elif button_type == "next":
                data_count = mongo.db.studentdetails.count_documents({})
                skip_count = min(start_current+5, data_count/25)
            else:
                skip_count = 1
                start_current = 1

    cgpa1 = float(data[0])
    cgpa2 = float(data[1])
    ctype = str(data[2])
    cname = str(data[3])
    mongo_query = {}
    mongo_search = {}
    for i in range (4, len(data)-2) :
        c = checkplacement(data[i])
        if c=="dept":
            dept_values.append(data[i])
        if c=="ctype":
            ctype_values.append(data[i])
        elif c=="cgpa":
            continue
        else:
            mongo_query[data[i]] = 1
    mongo_query["_id"] = 0
    if len(dept_values)==0:
        dept_values = add_dept()

    if cname!="All":
        cno = checkCompanyType(cname)
        print(cno)
    column = mongo.db.studentdetails.find_one({})
    if cname!="All" :
        if cno==0:
            data = mongo.db.studentdetails.find({"branch":{"$in": dept_values},"placement.0.Non-Dream" :cname,"cgpa":{"$gte":cgpa1, "$lte":cgpa2}},mongo_query).skip((int(skip_count)-1)*25).limit(25).sort("roll_no", 1)
            data_count = mongo.db.studentdetails.count_documents({"branch":{"$in": dept_values},"placement.0.Non-Dream" :cname,"cgpa":{"$gte":cgpa1, "$lte":cgpa2}})
        elif cno==1:
            data = mongo.db.studentdetails.find({"branch":{"$in": dept_values},"placement.1.Dream" :cname,"cgpa":{"$gte":cgpa1, "$lte":cgpa2}},mongo_query).skip((int(skip_count)-1)*25).limit(25).sort("roll_no", 1)
            data_count = mongo.db.studentdetails.count_documents({"branch":{"$in": dept_values},"placement.1.Dream" :cname,"cgpa":{"$gte":cgpa1, "$lte":cgpa2}})
        elif cno==2:
            data = mongo.db.studentdetails.find({"branch":{"$in": dept_values},"placement.2.Super-Dream" :cname,"cgpa":{"$gte":cgpa1, "$lte":cgpa2}},mongo_query).skip((int(skip_count)-1)*25).limit(25).sort("roll_no", 1)
            data_count = mongo.db.studentdetails.count_documents({"branch":{"$in": dept_values},"placement.0.Super-Dream" :cname,"cgpa":{"$gte":cgpa1, "$lte":cgpa2}})

    elif ctype=="All" and cname=="All" or ctype!="All":
        data = mongo.db.studentdetails.find({}, mongo_query).skip((int(skip_count)-1)*25).limit(25).sort("roll_no", 1)  
        data_count = mongo.db.studentdetails.count_documents({})  
    

    json_data = []
    if data_count % 25 != 0:
        total_page = (data_count - data_count%25)/25
    else:
        total_page = data_count/25
    if button_type == "prev":
        if start_current > 5:
            start_page = start_current -5
        else:
            start_page = 1
    elif button_type == "next":
        if start_current < total_page - 5:
            start_page = start_current + 5
        else:
            start_page = start_current
    else:
        start_page = start_current
    for document in data:
        if document:
            json_data.append(document)
    json_data.append(data_count)
    json_data.append(skip_count)
    json_data.append(total_page)
    json_data.append(start_page)
    return json.dumps(json_data)

def checkplacement(data):
	if data=="IT" or data=="COMPS" or data=="ETRX" or data=="EXTC" or data=="MECH":
		return "dept"
	elif data=="F" or data=="S" or data=="T" or data=="L":
		return "year"	
	elif data=="Non-Dream" or data=="Dream" or data=="Super-Dream":
		return "ctype"
	elif data=="cgpa1" or data=="cgpa2":
		return "cgpa"
	else:	
		return "others"	

def checkCompanyType(cname):
    flag = 0
    ndr = mongo.db.companydetails.find_one({"company_type" : "Non-Dream"},{"_id" : 0, "comanyname" : 1})
    if ndr != None:
        for document in ndr:
            if cname in ndr[document]:
                flag = 0
    dr = mongo.db.companydetails.find_one({"company_type" : "Dream"},{"_id" : 0, "comanyname" : 1})
    if dr != None:
        for document in dr:
            if cname in dr[document]:
                flag = 1
    sdr = mongo.db.companydetails.find_one({"company_type" : "Super-Dream"},{"_id" : 0, "comanyname" : 1})
    if sdr != None:
        for document in sdr:
            if cname in sdr[document]:
                flag = 2
    
    return flag

@app.route('/hodapprovepage', methods = ['POST', "GET"])
def hodapprovepage():
    if 'usertype' in session:
        if 'email' in session:
            if session['email'] in hodemail:
                if request.method != 'POST' :
                    branch = mongo.db.facultydetails.find_one({"email" : session["email"]}, {"branch":1})
                    branch_email = mongo.db.facultydetails.find({"branch" : branch["branch"]}, {"email" :1})
                    email = []
                    for document in branch_email:
                        email.append(document["email"])
                    c = mongo.db.faculty_registration.find_one({}, {"_id" : 0, "password" : 0})
                    data = mongo.db.faculty_registration.find({"user_type" : "faculty", "email": {"$in" : email}}, {"_id" : 0, "password" : 0})
                    return render_template('hodapprovepage.html', c = c, d = data)
                else :
                    data = request.get_json()
                    if data[0] == 'approve selected':
                        for k in range(1,len(data)) :
                                mongo.db.faculty_registration.update_one({"email" : data[k], "user_type" : "faculty"}, {"$set" : {"user_approve_status" : 1}})
                    else :
                        for k in range(1,len(data)) :
                                mongo.db.faculty_registration.update_one({"email" : data[k], "user_type" : "faculty"}, {"$set" : {"user_approve_status" : 0}})
                    return json.dumps({"status" : "OK"})
            else:
                return render_template('wronguser.html')
        else :
            return redirect("/loginpage")
    else:
        return redirect("loginpage")

@app.route('/admin', methods = ['GET', "POST"])
def admindetails():
    if "usertype" in session:
        if session["usertype"] == "admission":
            if request.method == 'GET':
                c = mongo.db.studentdetails.find_one({}, {'branch' : 1 ,'Caste' : 1, 'HandiCapped' : 1, 'Gender' : 1, 'Minority' : 1, 'Other_category' : 1, '_id' : 0})
                data = mongo.db.studentdetails.find()
                branchwisecolumn = {}
                castecolumn = ['Open', 'SC', 'ST', 'DT', 'NT', 'OBC', 'SBC', 'ESBC', 'SBCA', 'Muslim', 'Maratha', 'Other']
                handicappedcolumn = ['Ortho', 'Blind', 'Deaf', 'mld/ld']
                minoritycolumn = ['Sikh', 'Jain', 'Buddhist', 'Christian', 'Parsi']
                othercolumn = ['NRI', 'Foriegn', 'JandK']
                branchcolumn = ['COMPS', 'EXTC', 'IT', 'MECH', 'ETRX']
                yearcolumn = ['FY', 'SY', 'TY', 'LY']
                for b in branchcolumn:
                    branchyearwisecolumn = {}
                    for t in yearcolumn:
                        datacolumn = {}
                        for document in castecolumn:
                            datacolumn[document] = {"Male" :mongo.db.studentdetails.count_documents({'Caste' : document, "Gender" : "M", "branch" : b, "current_year" : t}), "Female" :mongo.db.studentdetails.count_documents({'Caste' : document, "Gender" : "F", "branch" : b, "current_year" : t}) }          
                        for document in handicappedcolumn:
                            datacolumn[document] = {"Male" :mongo.db.studentdetails.count_documents({'HandiCapped' : document, "Gender" : "M", "branch" : b, "current_year" : t}), "Female" :mongo.db.studentdetails.count_documents({'HandiCapped' : document, "Gender" : "F", "branch" : b, "current_year" : t}) }          
                        for document in minoritycolumn:
                            datacolumn[document] = {"Male" :mongo.db.studentdetails.count_documents({'Minority' : document, "Gender" : "M", "branch" : b, "current_year" : t}), "Female" :mongo.db.studentdetails.count_documents({'Minority' : document, "Gender" : "F", "branch" : b, "current_year" : t}) }
                        for document in othercolumn:
                            datacolumn[document] = {"Male" :mongo.db.studentdetails.count_documents({'Other_category' : document, "Gender" : "M", "branch" : b, "current_year" : t}), "Female" :mongo.db.studentdetails.count_documents({'Other_category' : document, "Gender" : "F", "branch" : b, "current_year" : t}) }    
                        branchyearwisecolumn[t] = datacolumn      
                    branchwisecolumn[b] = branchyearwisecolumn
                return render_template("adminpage.html", c=castecolumn, d = branchwisecolumn)
            else :
                data = request.get_json()
                castecolumn = []
                handicappedcolumn = []
                minoritycolumn = []
                othercolumn = []
                branchcolumn = []
                yearcolumn = []
                branchwisecolumn = {}
                for d in data:
                    for c in range(0, len(data[d])):
                        if d == 'category':
                            castecolumn.append(data[d][c])
                        elif d == 'handicapped':
                            handicappedcolumn.append(data[d][c])
                        elif d == 'minority':
                            minoritycolumn.append(data[d][c])
                        elif d == 'other':
                            othercolumn.append(data[d][c])
                        elif d == 'branch':
                            branchcolumn.append(data[d][c])
                        elif d == 'year':
                            yearcolumn.append(data[d][c])
                yearofadmission = data["yearofadmission"]
                for b in branchcolumn:
                    branchyearwisecolumn = {}
                    for t in yearcolumn:
                        datacolumn = {}
                        for document in castecolumn:
                            datacolumn[document] = {"Male" :mongo.db.studentdetails.count_documents({'Caste' : document, "Gender" : "M", "branch" : b, "current_year" : t, "year_of_admission" : str(yearofadmission)}), "Female" :mongo.db.studentdetails.count_documents({'Caste' : document, "Gender" : "F", "branch" : b, "current_year" : t, "year_of_admission" : str(yearofadmission)}) }          
                        for document in handicappedcolumn:
                            datacolumn[document] = {"Male" :mongo.db.studentdetails.count_documents({'HandiCapped' : document, "Gender" : "M", "branch" : b, "current_year" : t, "year_of_admission" : str(yearofadmission)}), "Female" :mongo.db.studentdetails.count_documents({'HandiCapped' : document, "Gender" : "F", "branch" : b, "current_year" : t, "year_of_admission" : str(yearofadmission)}) }          
                        for document in minoritycolumn:
                            datacolumn[document] = {"Male" :mongo.db.studentdetails.count_documents({'Minority' : document, "Gender" : "M", "branch" : b, "current_year" : t, "year_of_admission" : str(yearofadmission)}), "Female" :mongo.db.studentdetails.count_documents({'Minority' : document, "Gender" : "F", "branch" : b, "current_year" : t, "year_of_admission" : str(yearofadmission)}) }
                        for document in othercolumn:
                            datacolumn[document] = {"Male" :mongo.db.studentdetails.count_documents({'Other_category' : document, "Gender" : "M", "branch" : b, "current_year" : t, "year_of_admission" : str(yearofadmission)}), "Female" :mongo.db.studentdetails.count_documents({'Other_category' : document, "Gender" : "F", "branch" : b, "current_year" : t, "year_of_admission" : str(yearofadmission)}) }    
                        branchyearwisecolumn[t] = datacolumn      
                    branchwisecolumn[b] = branchyearwisecolumn
                return json.dumps(branchwisecolumn)
        else :
            return render_template("wronguser.html")
    else :
        return redirect("/loginpage")


@app.route("/studentmarks", methods = ['POST', "GET"])
def studentmarks():
    if 'email' in session:
        if 'usertype' in session:
            if session["usertype"] == "student":
                roll_no = mongo.db.studentdetails.find_one({"email": session["email"]}, {"_id" : 0, "roll_no":1})
                c = mongo.db.compssubject.find_one({"examination.0.sem.0.sem": "I"},{"_id": 0})
                column_name = {}
                column_name["roll_no"] = ""
                for document in c["examination"]:
                    for key in document:
                        column_name[key] = document[key]
                        break
                    break
                d = mongo.db.compssubject.find({"roll_no" : roll_no["roll_no"]},{"_id": 0})
                cd = mongo.db.compssubject.find({"roll_no" : roll_no["roll_no"]},{"roll_no": 1, "_id": 0})
                return render_template("studentmarkssubject.html", c = column_name,d = d, cd= cd)
            else :
                return render_template("wronguser.html")
        else :
                return redirect('/loginpage')
    else :
                return redirect('/loginpage')
    
def allowed_file(filename):
    ALLOWED_EXTENSIONS = set(['xlsx', 'xls', 'pdf', 'png', 'jpg', 'csv'])
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/studentdataupload', methods=['POST', "GET"])
def studentdataupload():
    if "usertype" in session:
        if session['email'] in hodemail:
            user = "hod"
            if 'hodcomp.engg@somaiya.edu' == session['email']:
                hodtype = "COMPS"
            elif 'hodit.engg@somaiya.edu' == session['email']: 
                hodtype = "IT"
            elif 'hodmech.engg@somaiya.edu' == session['email']:
                hodtype = "MECH"
            elif 'hodextc.engg@somaiya.edu' == session['email']:
                hodtype = "EXTC"
            else:
                hodtype = "ETRX"
    else:
        hodtype = None
    if request.method == "GET":
        s = {}
        if "email" in session:
            if "usertype" in session:
                if session["email"] not in hodemail and session['email'] not in placementcellemail :
                    subject = mongo.db.facultydetails.find({"email":session["email"]},{"_id":0, "sub" : 1})
                    s = subject[0]
                    print(len(s))
                    return render_template("studentdataupload.html", s = s)
                elif session["email"] in hodemail :
                    s = {}

                    sub = mongo.db.hodsubjects.find_one({"hodtype" : hodtype}, {"_id" : 0, "sub" : 1})
                    for subject in sub:
                        s["sub"] = sub[subject]
                    return render_template("studentdatahodupload.html", s = s)
                else :
                    return render_template("wronguser.html")
            else :
                return redirect('/loginpage')
        else :
                return redirect('/loginpage')

    else:
        mongo.db.temp.drop()
        file = request.files['File']
        name = request.form.get("subject")
        uploadtype = request.form.get("upload")
        subjectcontent = request.form.get("subjectcontent")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
        else:
            return "invalid document selected"
        # if not allowed_file(file.filename):
        #     return "Invalid File Format"
        file_extenstion = filename.rsplit('.', 1)[1].lower()
        if file_extenstion=="xlsx" or file_extenstion=="xls":
            df = pd.read_excel(file)
            df.to_csv('output.csv', encoding='utf-8')
            flag = 0
            for i in range(0,len(df.columns)):
                a = df.columns[i].lower()
                a = ''.join(filter(str.isalnum, a))
                count = mongo.db.header.count_documents({'pc':a})
                if count == 1:
                    doc = mongo.db.header.find_one({'pc':a})
                    df.columns.values[i] = doc["name"]
                else:
                    n = "Column "+df.columns[i]+" not found. Please try vith a valid column name"
                    flag = 1
                    break
            if flag == 1:
                return render_template('error_page.html',z=n)

            records_ = df.to_dict(orient = 'records')
            mongo.db.temp.insert_many(records_ )

            headercheck = headersstudentdataupload(df)
            if headercheck == "OK" :
            # if session["email"] in hodemail:
            # if uploadtype=="marks":
                for i in range(0,8) :
                    for j in range(1,7):
                        mongo_query = 'examination.' + str(i) + '.sem' + '.' + str(j) + '.subject' + str(j) + '.name'
                        c = mongo.db.compssubject.count_documents({mongo_query : name})
                        if c != 0:
                            break
                    if c!=0:
                        break
            
                da = mongo.db.temp.find({},{"_id":0})
                mongo_querysubject = 'examination.' + str(i) + '.sem' + '.' + str(j) + '.subject' + str(j) + "." + str(subjectcontent)
                for document in da:
                    mongo.db.compssubject.update_one({"roll_no" : document["roll_no"], mongo_query: name},{"$set" :{mongo_querysubject : document["marks"]}})
                    # else :
                    #     semester = request.form.get("semester")
                    #     da = mongo.db.temp.find({},{"_id":0})
                    #     mongo_query = "examination." + str(semester) + ".sem.0.gpa"  
                    #     for document in da:
                    #         mongo.db.compssubject.update_one({"roll_no" : document["roll_no"]},{"$set" :{mongo_query: document["gpa"] }})
                    #         gpa = mongo.db.compssubject.find_one({"roll_no" : document["roll_no"]})
                    #         count = 0
                    #         cgpa = 0
                    #         for doc in gpa["examination"]:
                    #             for sem in doc["sem"]:
                    #                 if isinstance(sem["gpa"], float) == True:
                    #                     count = count + 1 
                    #                     cgpa = cgpa + sem["gpa"]
                    #                 break
                    #         cgpa = cgpa/count
                    #         mongo.db.studentdetails.update_one({"roll_no" : document["roll_no"]}, {"$set" : {"cgpa" : cgpa}})

                                


                mongo.db.temp.drop()
                
                s = None
                if "email" in session:
                    if "usertype" in session:
                        if session["email"] not in hodemail and session["email"] not in placementcellemail:
                            subject = mongo.db.facultydetails.find({"email":session["email"]},{"_id":0, "sub" : 1})
                            s = subject[0]
                            return render_template("studentdataupload.html", s = s)
                        elif session["email"] in hodemail :
                            s = {}
                            # s["sub"] = ['COMPS 1', 'COMPS 2', 'COMPS 3', 'COMPS 4', 'IT 1', 'IT 2', 'IT 3', 'EXTC 1', 'EXTC 2', 'EXTC 3', 'EXTC 4', 'EXTC 5']
                            sub = mongo.db.hodsubjects.find_one({"hodtype" : hodtype}, {"_id" : 0, "sub" : 1})
                            for subject in sub:
                                s["sub"] = sub[subject]
                            return render_template("studentdatahodupload.html", s = s)
                        else :
                            return render_template("wronguser.html")

                    else :
                        return redirect('/loginpage')
                else :
                    return redirect('/loginpage')
            
            else:
                return headercheck
        
        else:
            return "Only xlsx and xls format is supported"

def headersstudentdataupload(df):
    h = ["roll_no","name","subject_name","subject_code","marks"]
    present = "Column not present : "
    remove = "Remove column : "
    present_count = 0
    remove_count = 0
    for i in h:
        flag1 = 0
        for j in df:
            if i==j:
                flag1 = 1
        if flag1==0:
            present = present + i + " "
            present_count = present_count + 1

    for i in df:
        flag1 = 0
        for j in h:
            if i==j:
                flag1 = 1
        if flag1==0:
            remove = remove + i + " "
            remove_count = remove_count + 0
    
    k = "OK"
    
    if present_count > 0 :
        k =  present
        if remove_count > 0:
            k = k + remove

    if remove_count > 0  :
        k = remove
        if present_count > 0:
            k = k + present
    
    
    return k

def headers(df):
    h = ["roll_no","name","email","branch","division","current_year","Caste","HandiCapped","Gender","Minority","Other_category","cgpa","year_of_admission","gaurdian_name","relation","local_address","gaurdian_local_address","permanent_address","contact_number_R","contact_number_O","contact_number_M","student_email","gaurdian_email","blood_group","date_of_birth","place_of_birth","mother_tounge","religion","competitive_examination","competitive_examination_marks","SSC_marks","HSC_marks","proctor_name","proctor_email","internships","freeze","extracurricular_activities", "dead kt", "live kt"]
    present = "Column not present : "
    remove = "Remove column : "
    present_count = 0
    remove_count = 0
    for i in h:
        flag1 = 0
        for j in df:
            if i==j:
                flag1 = 1
        if flag1==0:
            present = present + i + " "
            present_count = present_count + 1

    for i in df:
        flag1 = 0
        for j in h:
            if i==j:
                flag1 = 1
        if flag1==0:
            remove = remove + i + " "
            remove_count = remove_count + 0
    
    k = "OK"
    
    if present_count > 0 :
        k =  present
        if remove_count > 0:
            k = k + remove

    if remove_count > 0  :
        k = remove
        if present_count > 0:
            k = k + present
    
    
    return k

@app.route('/profdata', methods=['POST', "GET"])		
def profdata():
    if "email" in session:
        if session["email"] in hodemail:
            branch = mongo.db.facultydetails.find_one({"email": session["email"]}, {"_id": 0})
            if request.form.get('submit') == "Add":
                email = request.form.get('prof')
                sub = request.form.get('sub')
                profcount = mongo.db.facultydetails.count_documents({"email":email, "branch" : branch["branch"]})
                if email!="" or sub!="":
                    name = mongo.db.facultydetails.find_one({"email":email},{"_id":0, "name":1, "email" : 1})
                    prof_count = mongo.db.subjprof.count_documents({"sub":sub,"name":name['name']})
                    if prof_count == 0 and profcount>0:
                        mongo.db.subjprof.update_one({"sub":sub},{"$push":{"name":name["name"]}},True) #upsert is set to true
        #	Updating faculty collection
                    prof_count1 = mongo.db.facultydetails.count_documents({"sub":sub,"email":email})
                    profcount = mongo.db.facultydetails.count_documents({"email":email, "branch" : branch["branch"]})
                    if prof_count1 == 0 and profcount > 0:
                        mongo.db.facultydetails.update({"email":email},{"$push":{"sub":sub}},True) #upsert is set to true				

            elif request.form.get('submit') == "Remove":
                name = []
                name.append(request.form.get('prof'))
                sub1 = []
                sub1.append(request.form.get('sub'))
                name1 = request.form.get('prof')
                sub = request.form.get('sub')
                if name!="" or sub!="":
                    mongo.db.subjprof.update({"sub":sub},{"$pull":{"name":{"$in":name}}})
                    mongo.db.facultydetails.update({"name":name1},{"$pull":{"sub":{"$in":sub1}}})

            elif request.form.get('submit') == "Drop":
                sub = request.form.get('sub')
                sub1 = []
                sub1.append(request.form.get('sub'))
                if sub!="":
                    mongo.db.subjprof.remove({"sub":sub})
                    while mongo.db.facultydetails.find_one({"sub":sub}):
                        c = mongo.db.facultydetails.find_one({"sub":sub},{"email":1,"_id":0})
                        mongo.db.facultydetails.update_one({"email":c["email"]},{"$pull":{"sub":{"$in":sub1}}})

        #Removine the key sub in faculty
            a = mongo.db.facultydetails.find({"sub":{"$exists":True}})
            for each in a:
                if not each["sub"]:
                    mongo.db.facultydetails.update({"email":each["email"]},{"$unset":{"sub":1}})

            c = mongo.db.subjprof.find_one({},{"_id":0})
            data = mongo.db.subjprof.find({},{"_id":0})
            if not c or not data:
                return render_template('tempprofdata.html')	
            else:
                return render_template('profdata.html',c=c,d=data)	
        
        else :
            return render_template('wronguser.html')
    else:
        return redirect('/loginpage')

@app.route("/administrator", methods = ["GET", 'POST'])
def administrator():
    if "usertype" in session:
        if session["usertype"] == "admission":
            if request.method == "POST":
                # read excel of student details
                mongo.db.studentdetailstemp.drop()
                file = request.files['studentdetailsfile']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                # if not allowed_file(file.filename):
                #     return "Invalid File Format"
                file_extenstion = filename.rsplit('.', 1)[1].lower()
                if file_extenstion=="xlsx" or file_extenstion=="xls":
                    df = pd.read_excel(file)
                    df.to_csv('output.csv', encoding='utf-8')
                    flag = 0
                    for i in range(0,len(df.columns)):
                        a = df.columns[i].lower()
                        a = ''.join(filter(str.isalnum, a))
                        count = mongo.db.header.count_documents({'pc':a})
                        if count == 1:
                            doc = mongo.db.header.find_one({'pc':a})
                            df.columns.values[i] = doc["name"]
                        else:
                            n = "Column "+df.columns[i]+" not found. Please try vith a valid column name"
                            flag = 1
                            break
                    if flag == 1:
                        return render_template('error_page.html',z=n)
                    c = headers(df.columns)
                    if c!= "OK" :
                        return c
                    else:
                        records_ = df.to_dict(orient = 'records')
                        mongo.db.studentdetailstemp.insert_many(records_ )
                else:
                    return "only xlsx and xls format is supported"

                # read excel of student subjects
                # mongo.db.studentsubjectstemp.drop()
                # file = request.files['studentsubjectsfile']
                # if file and allowed_file(file.filename):
                #     filename = secure_filename(file.filename)
                # if not allowed_file(file.filename):
                #     return "Invalid File Format"
                # file_extenstion = filename.rsplit('.', 1)[1].lower()
                # if file_extenstion=="xlsx" or file_extenstion=="xls":
                #     df = pd.read_excel(file)
                #     df.to_csv('output.csv', encoding='utf-8')
                #     # flag = 0
                #     # for i in range(0,len(df.columns)):
                #     #     a = df.columns[i].lower()
                #     #     a = ''.join(filter(str.isalnum, a))
                #     #     count = mongo.db.header.count_documents({'pc':a})
                #     #     if count == 1:
                #     #         doc = mongo.db.header.find_one({'pc':a})
                #     #         df.columns.values[i] = doc["name"]
                #     #     else:
                #     #         n = "Column "+df.columns[i]+" not found. Please try vith a valid column name"
                #     #         flag = 1
                #     #         break
                #     # if flag == 1:
                #     #     return render_template('error_page.html',z=n)
                #     records_ = df.to_dict(orient = 'records')
                #     mongo.db.studentsubjectstemp.insert_many(records_ )
                
                # read excel of subject contents
                # mongo.db.subjectscontenttemp.drop()
                # file = request.files['subjectcontentsfile']
                # if file and allowed_file(file.filename):
                #     filename = secure_filename(file.filename)
                # if not allowed_file(file.filename):
                #     return "Invalid File Format"
                # file_extenstion = filename.rsplit('.', 1)[1].lower()
                # if file_extenstion=="xlsx" or file_extenstion=="xls":
                #     df = pd.read_excel(file)
                #     df.to_csv('output.csv', encoding='utf-8')
                #     # flag = 0
                #     # for i in range(0,len(df.columns)):
                #     #     a = df.columns[i].lower()
                #     #     a = ''.join(filter(str.isalnum, a))
                #     #     count = mongo.db.header.count_documents({'pc':a})
                #     #     if count == 1:
                #     #         doc = mongo.db.header.find_one({'pc':a})
                #     #         df.columns.values[i] = doc["name"]
                #     #     else:
                #     #         n = "Column "+df.columns[i]+" not found. Please try vith a valid column name"
                #     #         flag = 1
                #     #         break
                #     # if flag == 1:
                #     #     return render_template('error_page.html',z=n)
                #     records_ = df.to_dict(orient = 'records')
                #     mongo.db.subjectcontenttemp.insert_many(records_ )
                
                #insert into compssubject
                branch = ['COMPS', 'IT', 'EXTC', 'MECH', 'ETRX']
                for b in branch:
                    s = mongo.db.studentsubjectstemp.find({"branch" : b},{"_id": 0}).sort("sem", 1)
                    for document in s:
                        j = []
                        du = OrderedDict()
                        for key in document:
                            l = {}
                            d = mongo.db.subjectcontenttemp.find({},{'_id':0})
                            if "sem" in key:
                                du[key] = document[key]
                                j.append(du)
                            elif "gpa" in key:
                                du[key] = document[key]
                            if "subject" in key :  
                                for doc in d: 
                                    subject = OrderedDict()
                                    subject["name"] = document[key]
                                    subject.update(doc)
                                    l[key] = subject
                            if l != {} :
                                j.append(l)
                        for key in document:
                            e = {}
                            if "sem" in key:
                                e[key] = j
                            if e != {} :
                                mongo.db.subject.insert_one(e)
                    d = mongo.db.studentdetailstemp.find({"branch" : b}, {"_id" : 0})
                    for document in d:
                        document["placement"] = [{"Non-Dream" : "-", "Package" : "-"}, {"Dream" : "-", "Package" : "-"}, {"Super-Dream" : "-", "Package" : "-"}]
                        c = mongo.db.studentdetails.count_documents({"roll_no" : document["roll_no"]})
                        if c == 0:
                            mongo.db.studentdetails.insert_one(document)
                    d = mongo.db.studentdetailstemp.find({"branch" : b}, {"roll_no": 1, "_id" : 0})
                    # mongo.db.compssubject.drop()
                    for document in d:
                        for key in document:
                            e = {}
                            e[key] = document[key]
                        j = []
                        c = mongo.db.subject.find({},{"_id" : 0})
                        for l in c:
                            j.append(l)
                        e["examination"] = j
                        c = mongo.db.compssubject.count_documents({"roll_no" : document["roll_no"]})
                        if c == 0: 
                            mongo.db.compssubject.insert_one(e)
                    mongo.db.subject.drop()
                mongo.db.studentdetailstemp.drop()
                # mongo.db.studentsubjectstemp.drop()
                # mongo.db.subjectcontenttemp.drop()
                return render_template("/administratorpage.html")
            else :
                return render_template("/administratorpage.html")
        else :
            return render_template("wronguser.html")
    else :
        return redirect("/loginpage")

@app.route('/uploadplacement', methods = ['POST', "GET"])
def uploadplacement():
    if "email" in session:
        if session["email"] in placementcellemail:
            if request.method == "GET":
                return render_template("placementupload.html")
            else:
                mongo.db.placementtemp.drop()
                file = request.files['File']
                ctype = request.form.get("ctype")
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                # if not allowed_file(file.filename):
                #     return "Invalid File Format"
                file_extenstion = filename.rsplit('.', 1)[1].lower()
                if file_extenstion=="xlsx" or file_extenstion=="xls":
                    df = pd.read_excel(file)
                    df.to_csv('output.csv', encoding='utf-8')
                    flag = 0
                    for i in range(0,len(df.columns)):
                        a = df.columns[i].lower()
                        a = ''.join(filter(str.isalnum, a))
                        count = mongo.db.header.count_documents({'pc':a})
                        if count == 1:
                            doc = mongo.db.header.find_one({'pc':a})
                            df.columns.values[i] = doc["name"]
                        else:
                            n = "Column "+df.columns[i]+" not found. Please try vith a valid column name"
                            flag = 1
                            break
                    if flag == 1:
                        return render_template('error_page.html',z=n)
                    records_ = df.to_dict(orient = 'records')
                    mongo.db.placementtemp.insert_many(records_ )
                    if ctype=="Non-Dream":
                        i = 0
                    elif ctype=="Dream":
                        i = 1
                    elif ctype=="Super-Dream":
                        i = 2
                    # mongo_query = 'placement.' + str(i)
                    da = mongo.db.placementtemp.find({},{"_id":0})
                    mongo_query_name = 'placement.' + str(i) + '.' + ctype
                    mongo_query_pkg = 'placement.' + str(i) + '.Package'
                    for document in da:
                        count_company_type = mongo.db.companydetails.count_documents({"company_type" : ctype})
                        if count_company_type != 0:
                            company_names = mongo.db.companydetails.find_one({"company_type" : ctype}, {"_id" : 0, "companyname" : 1})
                            for document_company in company_names:
                                if document["Company Name"] not in company_names[document_company]:
                                    mongo.db.companydetails.update_one({"company_type" : ctype}, {"$push" : {"companyname" : document["Company Name"]}})
                        else:
                            mongo.db.companydetails.insert_one({"company_type" : ctype, "companyname" : [document["Company Name"]]})
                        mongo.db.studentdetails.update_one({"roll_no" : document["roll_no"], "freeze" : 0},{"$set" :{mongo_query_name : document["Company Name"],mongo_query_pkg : document["Package"]}})
                        mongo.db.temp.drop()
                    c = mongo.db.studentdetails.find_one({'email':'a@abc.com'},{"_id":0})
                    data = mongo.db.studentdetails.find({},{"_id":0})
                    return redirect("/placementdetails")
                
                else:
                    return "Only xlsx and xls format is supported"
        else :
            return render_template("wronguser.html")
    else :
        return redirect("/loginpage")

@app.route("/uploaddocument", methods=["GET", "POST"])
def upload_document():
    if "email" in session:
        return render_template("upload_pdf.html")
    else:
        return redirect("/loginpage")

@app.route("/upload", methods=['GET', "POST"])
def upload_file():
    if "email" in session :
        if request.method == "POST":
            return upload.uploadfile()
        else:
            return redirect("/uploaddocument")
    else:
        return redirect("/loginpage")

@app.route("/downloadfile")
def download_file():
    if "email" in session:
        return upload.downloadfile()
    else:
        return redirect("/loginpage")

@app.route("/studentdetails/<roll_no>")
def student_details(roll_no):
    if "email" in session:
        data = mongo.db.studentdetails.find({"roll_no":int(roll_no)}, {"_id": 0})
        c = mongo.db.compssubject.find_one({"examination.0.sem.0.sem": "I"},{"_id": 0})
        column_name = {}
        column_name["roll_no"] = ""
        for document in c["examination"]:
            for key in document:
                column_name[key] = document[key]
                break
            break
        d = mongo.db.compssubject.find({"roll_no" : int(roll_no)},{"_id": 0})
        cd = mongo.db.compssubject.find({"roll_no" : int(roll_no)},{"roll_no": 1, "_id": 0})
        return render_template("studentinfo.html", data = data, c=column_name, d=d, cd = cd)
    else:
        return redirect("/loginpage")

@app.route("/updatesubject", methods = ['POST', "GET"])
def updatesubjects():
    if request.method == "GET":
        if "usertype" in session:
            if session['email'] in hodemail:
                user = "hod"
                if 'hodcomp.engg@somaiya.edu' == session['email']:
                    hodtype = "COMPS"
                elif 'hodit.engg@somaiya.edu' == session['email']: 
                    hodtype = "IT"
                elif 'hodmech.engg@somaiya.edu' == session['email']:
                    hodtype = "MECH"
                elif 'hodextc.engg@somaiya.edu' == session['email']:
                    hodtype = "EXTC"
                else:
                    hodtype = "ETRX"
                return render_template("updatesubject.html", user = user, usertype = hodtype)
            elif session["usertype"] == "admission":
                user = "admission"
                usertype = "admin"
                return render_template("updatesubject.html", user = user, usertype = usertype)
            else:
                return render_template("wronguser.html")

    else:
        if "usertype" in session:
            if session['email'] in hodemail:
                user = "hod"
                if 'hodcomp.engg@somaiya.edu' == session['email']:
                    hodtype = "COMPS"
                elif 'hodit.engg@somaiya.edu' == session['email']: 
                    hodtype = "IT"
                elif 'hodmech.engg@somaiya.edu' == session['email']:
                    hodtype = "MECH"
                elif 'hodextc.engg@somaiya.edu' == session['email']:
                    hodtype = "EXTC"
                else:
                    hodtype = "ETRX"

        else :
            hodtype = None
        branch = request.form.get("branch")
        sem = request.form.get("semester")

        mongo.db.studentdetailstemp.drop()
        file = request.files['students']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
        # if not allowed_file(file.filename):
        #     return "Invalid File Format"
        file_extenstion = filename.rsplit('.', 1)[1].lower()
        if file_extenstion=="xlsx" or file_extenstion=="xls":
            df = pd.read_excel(file)
            df.to_csv('output.csv', encoding='utf-8')
            flag = 0
            for i in range(0,len(df.columns)):
                a = df.columns[i].lower()
                a = ''.join(filter(str.isalnum, a))
                count = mongo.db.header.count_documents({'pc':a})
                if count == 1:
                    doc = mongo.db.header.find_one({'pc':a})
                    df.columns.values[i] = doc["name"]
                else:
                    n = "Column "+df.columns[i]+" not found. Please try vith a valid column name"
                    flag = 1
                    break
            if flag == 1:
                return render_template('error_page.html',z=n)
            records_ = df.to_dict(orient = 'records')
            mongo.db.studentdetailstemp.insert_many(records_ )
    
        else:
            return "Only xlsx and xls format is supported"

        mongo.db.studentsubjectstemp.drop()
        file = request.files['subjects']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
        file_extenstion = filename.rsplit('.', 1)[1].lower()
        if file_extenstion=="xlsx" or file_extenstion=="xls":
            df = pd.read_excel(file)
            df.to_csv('output.csv', encoding='utf-8')
            flag = 0
            for i in range(0,len(df.columns)):
                a = df.columns[i].lower()
                a = ''.join(filter(str.isalnum, a))
                count = mongo.db.header.count_documents({'pc':a})
                if count == 1:
                    doc = mongo.db.header.find_one({'pc':a})
                    df.columns.values[i] = doc["name"]
                else:
                    n = "Column "+df.columns[i]+" not found. Please try vith a valid column name"
                    flag = 1
                    break
            if flag == 1:
                return render_template('error_page.html',z=n)
            records_ = df.to_dict(orient = 'records')
            mongo.db.studentsubjectstemp.insert_many(records_ )

        else:
            return "Only xlsx and xls format is supported"
        

        students = mongo.db.studentdetailstemp.find({}, {"roll_no" : 1})
        for document in students:
            subjects = mongo.db.studentsubjectstemp.find({})
            for data in subjects:
                for i in range(1,7):
                    query = "examination." + str(sem) + ".sem." + str(i) + ".subject" + str(i) + ".name"
                    query_value = "subject" + str(i)
                    student_freeze = mongo.db.studentdetails.count_documents({"roll_no": document["roll_no"], "branch" : branch, "freeze" : 0})
                    if student_freeze !=0 :
                        mongo.db.compssubject.update_one({"roll_no": document["roll_no"]}, {"$set": {query: data[query_value]}})
                        mongo.db.studentdetails.update_one({"roll_no": document["roll_no"], "branch" : branch}, {"$set": {"current_year" :data["current_year"]}})
        
        subjects = mongo.db.studentsubjectstemp.find_one({})
        for data in subjects:
            if data in ['subject1','subject2','subject3','subject4','subject5','subject6']:
                sub = subjects[data]
                sub_presence = mongo.db.hodsubjects.count_documents({"hodtype" : hodtype,"sub" : sub})
                if sub_presence == 0:
                    mongo.db.hodsubjects.update_one({"hodtype" : hodtype},{"$push" : {"sub" : sub}})

        if "usertype" in session:
            if session['email'] in hodemail:
                user = "hod"
                if 'hodcomp.engg@somaiya.edu' == session['email']:
                    hodtype = "COMPS"
                elif 'hodit.engg@somaiya.edu' == session['email']: 
                    hodtype = "IT"
                elif 'hodmech.engg@somaiya.edu' == session['email']:
                    hodtype = "MECH"
                elif 'hodextc.engg@somaiya.edu' == session['email']:
                    hodtype = "EXTC"
                else:
                    hodtype = "ETRX"
                return render_template("updatesubject.html", user = user, usertype = hodtype)
            elif session["usertype"] == "admission":
                user = "admission"
                usertype = "admin"
                return render_template("updatesubject.html", user = user, usertype = usertype)
            else:
                return render_template("wronguser.html")

@app.route("/proctorform/<roll_no>", methods=["GET", 'POST'])
def proctorform(roll_no):
    if "email" in session:
        student_details = mongo.db.studentproctorform.find_one({"roll_no" : int(roll_no)},{"_id" : 0})
        if student_details != None:
            return render_template("viewproctorform.html", student_details = student_details) 
        else:
            return "no details found"    
    else:
        return redirect("/loginpage")

# @app.route("/proctorformupdate", methods=["GET", 'POST'])
# def proctorformupdate():
#     student_details = mongo.db.studentdetails.find_one({}, {"_id" : 0})
#     return render_template("proctorformupdate.html", student_details = student_details)

@app.route("/facultydetailsupdate", methods=["GET", 'POST'])
def facultydetailsupdate():
    if "email" in session:
        if session["email"] in hodemail:
            branch = mongo.db.facultydetails.find_one({"email": session["email"]}, {"_id" :0, "branch" : 1})
            if request.method != 'POST':
                branch = mongo.db.facultydetails.find_one({"email": session["email"]}, {"_id" :0, "branch" : 1})
                faculty_header = mongo.db.facultydetails.find_one({}, {"_id" : 0, "sub" : 0})
                faculty_list = mongo.db.facultydetails.find({"branch" : branch["branch"]},{"_id" : 0, "sub" : 0})
                return render_template("facultydetailsupdate.html", faculty_header = faculty_header,faculty_list = faculty_list)

            else:
                mongo.db.facultydetailstemp.drop()
                file = request.files['facultylist']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                # if not allowed_file(file.filename):
                #     return "Invalid File Format"
                file_extenstion = filename.rsplit('.', 1)[1].lower()
                if file_extenstion=="xlsx" or file_extenstion=="xls":
                    df = pd.read_excel(file)
                    df.to_csv('output.csv', encoding='utf-8')
                    flag = 0
                    for i in range(0,len(df.columns)):
                        a = df.columns[i].lower()
                        a = ''.join(filter(str.isalnum, a))
                        count = mongo.db.header.count_documents({'pc':a})
                        if count == 1:
                            doc = mongo.db.header.find_one({'pc':a})
                            df.columns.values[i] = doc["name"]
                        else:
                            n = "Column "+df.columns[i]+" not found. Please try vith a valid column name"
                            flag = 1
                            break
                    if flag == 1:
                        return render_template('error_page.html',z=n)
                    
                    headercheck = headersfacultydetailsupdate(df)

                    if headercheck != "OK" :
                        return headercheck
                    else:
                        records_ = df.to_dict(orient = 'records')
                        mongo.db.facultydetailstemp.insert_many(records_ )
                        facultylist = mongo.db.facultydetailstemp.find({},{"_id" : 0})
                        for document in facultylist:
                            facultycount = mongo.db.facultydetails.count_documents({"email": document["email"], "branch" : branch["branch"]})
                            if facultycount != 0:
                                mongo.db.facultydetails.update_one({"email" : document["email"] , "branch" : branch["branch"]},{"$set": {"name" : document["name"], "branch" : document["branch"]}})
                            else:
                                if document["branch"] == branch["branch"]:
                                    mongo.db.facultydetails.insert_one(document)
                
                else:
                    return "only xlsx, xls format is supported"
                faculty_header = mongo.db.facultydetails.find_one({}, {"_id" : 0, "sub" : 0})
                faculty_list = mongo.db.facultydetails.find({"branch" : branch["branch"]},{"_id" : 0, "sub" : 0})
                return render_template("facultydetailsupdate.html", faculty_header = faculty_header,faculty_list = faculty_list)

        else:
            return redirect("/loginpage")
    else:
        return rediract("/loginpage")

def headersfacultydetailsupdate(df):
    h = ["name","email","usertype","branch"]
    present = "Column not present : "
    remove = "Remove column : "
    present_count = 0
    remove_count = 0
    for i in h:
        flag1 = 0
        for j in df:
            if i==j:
                flag1 = 1
        if flag1==0:
            present = present + i + " "
            present_count = present_count + 1

    for i in df:
        flag1 = 0
        for j in h:
            if i==j:
                flag1 = 1
        if flag1==0:
            remove = remove + i + " "
            remove_count = remove_count + 0
    
    k = "OK"
    
    if present_count > 0 :
        k =  present
        if remove_count > 0:
            k = k + remove

    if remove_count > 0  :
        k = remove
        if present_count > 0:
            k = k + present
    
    
    return k
@app.route("/freezestudent", methods = ["GET", 'POST'])
def freezestudent():
    if "usertype" in session:
        if session["usertype"] == "admission":
            if request.method == "GET":
                skip_count = 1
                data_count = mongo.db.studentdetails.count_documents({})
                c = mongo.db.studentdetails.find_one({},{"_id" : 0, "name" : 1, "email" : 1, "roll_no" : 1, "freeze" : 1, "branch" : 1, "year_of_admission" : 1})
                d = mongo.db.studentdetails.find({},{"_id" : 0, "name" : 1, "email" : 1, "roll_no" : 1, "freeze" : 1, "branch" : 1, "year_of_admission" : 1}).sort("roll_no", 1).skip((int(skip_count)-1)*50).limit(50).sort("roll_no", 1)
                return render_template("freezestudent.html", c = c, d = d, data_count = data_count)
            else:
                skip_count = request.form.get("page")
                if skip_count == None:
                    skip_count = 1
                yearofadmission = request.form.get("yearofadmission")
                if yearofadmission == "Year":
                    data_count = mongo.db.studentdetails.count_documents({})
                    c = mongo.db.studentdetails.find_one({},{"_id" : 0, "name" : 1, "email" : 1, "roll_no" : 1, "freeze" : 1, "branch" : 1, "year_of_admission" : 1})
                    d = mongo.db.studentdetails.find({},{"_id" : 0, "name" : 1, "email" : 1, "roll_no" : 1, "freeze" : 1, "branch" : 1, "year_of_admission" : 1}).sort("roll_no", 1).skip((int(skip_count)-1)*50).limit(50).sort("roll_no", 1)
                else:
                    data_count = mongo.db.studentdetails.count_documents({"year_of_admission" : yearofadmission})
                    c = mongo.db.studentdetails.find_one({},{"_id" : 0, "name" : 1, "email" : 1, "roll_no" : 1, "freeze" : 1, "branch" : 1, "year_of_admission" : 1})
                    d = mongo.db.studentdetails.find({"year_of_admission" : yearofadmission},{"_id" : 0, "name" : 1, "email" : 1, "roll_no" : 1, "freeze" : 1, "branch" : 1, "year_of_admission" : 1}).sort("roll_no", 1).skip((int(skip_count)-1)*50).limit(50).sort("roll_no", 1)
                return render_template("freezestudent.html", c = c, d = d, data_count = data_count, yearofadmission = yearofadmission)
        
        else:
            return redirect("/loginpage")
    else:
        return redirect("/loginpage")
    
    

@app.route("/freezestudentfilter", methods = ["POST"])
def freezestudentfilter():
    data = request.get_json()
    if data[0] == "freeze":
        mongo.db.studentdetails.update_many({"email" : {"$in" : data}}, {"$set": {"freeze" : 1}})
    else:
        mongo.db.studentdetails.update_many({"email" : {"$in" : data}}, {"$set": {"freeze" : 0}})
    return json.dumps({"status" : "OK"})

@app.route("/studentoftheyear", methods = ["GET", 'POST'])
def studentoftheyear():
    if "email" in session:
        if session["email"] in hodemail:
            if request.method == "GET":
                return render_template("/studentoftheyear.html")
            else:
                mongo.db.temp.drop()
                data = request.get_json()
                currentyear = data[0]
                cgpa = data[1]
                internships = data[2]
                extracurricular = data[3]
                data = mongo.db.studentdetails.find({"current_year": currentyear, "cgpa" : {"$gte" : float(cgpa)}, "internships" : {"$gte" : int(internships)}, "extracurricular_activities" : {"$gte" : int(extracurricular)}},{"roll_no":1, "email" :1, "branch":1, "current_year":1, "cgpa" :1, "internships" :1, "extracurricular_activities" : 1,"_id":0})
                json_data = []
                for document in data:
                    if document:
                        print(document)
                        points = document["cgpa"]*0.4 + document["internships"]*0.3 + document["extracurricular_activities"]*0.3
                        mongo.db.temp.insert_one({"roll_no" : document["roll_no"], "points" : points})
                
                data_points = mongo.db.temp.find({}).sort("roll_no", 1).limit(5)
                for document in data_points:
                    if document:
                        student = mongo.db.studentdetails.find({"roll_no" : document["roll_no"]},{"roll_no":1, "email" :1, "branch":1, "current_year":1, "_id":0})
                        for document_student in student:
                            if document_student:
                                json_data.append(document_student)
                return json.dumps(json_data)
        
        else:
            return redirect("/loginpage")
    else:
        return redirect("/loginpage")

@app.route('/dataselection', methods = ["GET", 'POST'])
def dataselection():
    if "email" in session:
        if request.method == "GET":
            if session['email'] in hodemail:
                user = "hod"
            elif session['email'] in placementcellemail:
                user = "placement"
            elif session['usertype'] == "faculty" and session['email'] not in hodemail and session['email'] not in placementcellemail and session['email'] not in iaiemail:
                user = "faculty"
            elif session['email'] in iaiemail:
                user = "iai"
            elif session['email'] in examcellemail:
                user = "examcell"
            else :
                user = "admission"
            return render_template("dataselection.html", user = user)
        else:
            radiofordata = request.form.get("radiofordata")
            if radiofordata == "gpaplot":
                gpagte9 = 0
                gpa8_9 = 0
                gpa7_8 = 0
                gpa6_7 = 0
                gpalt6 = 0
                year = request.form.get("year")
                semester = request.form.get("semester")
                branch = request.form.get("branch")
                student = mongo.db.studentdetails.find({"current_year":year, "branch" : branch}, {"roll_no":1, "_id":0})
                mongo_query = "examination." + str(semester) + ".sem.0.gpa" 
                for document in student:
                    countgpagte9 = mongo.db.compssubject.count_documents({"roll_no": document["roll_no"], mongo_query : {"$gte" : 9}})
                    countgpa8_9 = mongo.db.compssubject.count_documents({"roll_no": document["roll_no"], mongo_query : {"$gte" : 8, "$lt":9}})
                    countgpa7_8 = mongo.db.compssubject.count_documents({"roll_no": document["roll_no"], mongo_query : {"$gte" : 7, "$lt" : 8}})
                    countgpa6_7 = mongo.db.compssubject.count_documents({"roll_no": document["roll_no"], mongo_query : {"$gte" : 6, "$lt" : 7}})
                    countgpalt6 = mongo.db.compssubject.count_documents({"roll_no": document["roll_no"], mongo_query : {"$lt" : 6}})
                    gpagte9 = gpagte9 + countgpagte9
                    gpa8_9 =  gpa8_9 + countgpa8_9
                    gpa7_8 =  gpa7_8 + countgpa7_8
                    gpa6_7 =  gpa6_7 + countgpa6_7
                    gpalt6 =  gpalt6 + countgpalt6

                means_gpagte9 = [gpagte9]
                std_gpagte9 = [0]

                means_gpa8_9 = [gpa8_9]
                std_gpa8_9 = [0]

                means_gpa7_8 = [gpa7_8]
                std_gpa7_8 = [0]

                means_gpa6_7 = [gpa6_7]
                std_gpa6_7 = [0]

                means_gpalt6 = [gpalt6]
                std_gpalt6 = [0]
                    

                bar_url=build_bar(means_gpagte9, means_gpa8_9, means_gpa7_8, means_gpa6_7, means_gpalt6 ,
                std_gpagte9, std_gpa8_9, std_gpa7_8, std_gpa6_7, std_gpalt6 )
                return render_template('bardisplay.html',bar_graph=bar_url)
            
            elif radiofordata == "admissionsplot":
                date = datetime.datetime.now()
                date_array = []
                this_year = date.year
                for i in range(0,5):
                    date_array.append(str(this_year-i) + "-" + str(this_year-2000-i+1))
                
                print(date_array)
                year0 = mongo.db.studentdetails.count_documents({"year_of_admission" : str(date_array[0])})
                year1 = mongo.db.studentdetails.count_documents({"year_of_admission" : str(date_array[1])})
                year2 = mongo.db.studentdetails.count_documents({"year_of_admission" : str(date_array[2])})
                year3 = mongo.db.studentdetails.count_documents({"year_of_admission" : str(date_array[3])})
                year4 = mongo.db.studentdetails.count_documents({"year_of_admission" : str(date_array[4])})

                means_year0 = [year0]
                std_year0 = [0]

                means_year1 = [year1]
                std_year1 = [0]

                means_year2 = [year2]
                std_year2 = [0]

                means_year3 = [year3]
                std_year3 = [0]

                means_year4 = [year4]
                std_year4 = [0]            

                bar_url=build_bar(means_year0, means_year1, means_year2, means_year3, means_year4 ,
                std_year0, std_year1, std_year2, std_year3, std_year4 )
                return render_template('bardisplay.html',bar_graph=bar_url)

            elif radiofordata == "categoryplot":
                yearofadmission = request.form.get("yearofadmission")
                Open = mongo.db.studentdetails.count_documents({"year_of_admission": yearofadmission, "Caste" : "Open"})
                SCST = mongo.db.studentdetails.count_documents({"year_of_admission": yearofadmission,"Caste" : "SC"}) + mongo.db.studentdetails.count_documents({"year_of_admission": yearofadmission,"Caste" : "ST"})
                DTNT = mongo.db.studentdetails.count_documents({"year_of_admission": yearofadmission,"Caste" : "DT"}) + mongo.db.studentdetails.count_documents({"year_of_admission": yearofadmission,"Caste": "NT"})
                OBCSBC = mongo.db.studentdetails.count_documents({"year_of_admission": yearofadmission,"Caste" : "OBC"}) + mongo.db.studentdetails.count_documents({"year_of_admission": yearofadmission,"Caste" : "SBC"})
                ESBCSBCA = mongo.db.studentdetails.count_documents({"year_of_admission": yearofadmission,"Caste" : "ESBC"}) + mongo.db.studentdetails.count_documents({"year_of_admission": yearofadmission,"Caste" : "SBCA"})
                Muslim = mongo.db.studentdetails.count_documents({"year_of_admission": yearofadmission,"Caste" : "Muslim"})
                Maratha = mongo.db.studentdetails.count_documents({"year_of_admission": yearofadmission,"Caste" : "Maratha"})
                Other = mongo.db.studentdetails.count_documents({"year_of_admission": yearofadmission,"Caste" : "Other"})

                bar_url = build_bar_category(Open, SCST, DTNT, OBCSBC, ESBCSBCA, Muslim, Maratha, Other)
                return render_template('bardisplay.html',bar_graph=bar_url)

            elif radiofordata == "batchwiseplot":
                year = request.form.get("year")
                comps = mongo.db.studentdetails.count_documents({"current_year": year, "branch" : "COMPS"})
                it = mongo.db.studentdetails.count_documents({"current_year": year, "branch" : "IT"})
                etrx = mongo.db.studentdetails.count_documents({"current_year": year, "branch" : "ETRX"})
                extc = mongo.db.studentdetails.count_documents({"current_year": year, "branch" : "EXTC"})
                mech = mongo.db.studentdetails.count_documents({"current_year": year, "branch" : "MECH"})

                bar_url = build_bar_batchwise(comps, it, etrx, extc, mech)
                return render_template('bardisplay.html',bar_graph=bar_url)

            elif radiofordata == "placementplot":
                year = request.form.get("yearofpassing")

                nd = mongo.db.studentdetails.count_documents({"year_of_passing" : year, "placement.0.Package" :{"$gt" : 0}})
                d = mongo.db.studentdetails.count_documents({"year_of_passing" : year, "placement.1.Package" :{"$gt" : 0}})
                sd = mongo.db.studentdetails.count_documents({"year_of_passing" : year, "placement.2.Package" :{"$gt" : 0}})

                bar_url = build_bar_placement(nd, d, sd)
                return render_template('bardisplay.html', bar_graph = bar_url)
    
    else:
        return redirect("/loginpage")




@app.route('/line')
def line():
	data=mongo.db.studentdetails.find().limit(10)
	x=[]
	y=[]
	for s in data:
		x.append(s['roll_no'])
		y.append(s['cgpa'])

	line_url=build_line(x,y)
	return render_template('linedisplay.html',line_graph=line_url)

@app.route('/gradesheetgenerate', methods=['GET', "POST"])
def gradesheetgenerate():
    if "email" in session:
        if session["email"] in examcellemail:
            if request.method == 'GET' :
                return render_template('gradesheetgenerate.html')
            else:
                semester = request.form.get("semester")
                branch = request.form.get("branch")
                examination_month = request.form.get("examination_month")
                examination_year = request.form.get("examination_year")
                examinationcategory_count = mongo.db.examinationcellcategory.count_documents({"semester" : semester, "branch" : branch, "examination_month" : examination_month, "examination_year" : examination_year})
                total_students = int(request.form.get("total_students"))
                if examinationcategory_count == 0:
                    total_subjects = request.form.get("total_subjects")
                    out_of_marks = int(request.form.get("out_of_marks"))
                    subject_code = []
                    subject_name = []
                    subject_category = []
                    subject_category_maximum = []
                    subject_category_minimum = []
                    for i in range (1, int(total_subjects)+1):
                        num = str(i)
                        sub_code = request.form.get("code" + num)
                        sub_name = request.form.get("subname" + num)
                        sub_category = request.form.get("category" + num)
                        subject_code.append(sub_code)
                        subject_name.append(sub_name)
                        if sub_category == "category 1":
                            subject_category.append(["ESE","CA","Tot1","TW"])
                            subject_category_maximum.append(['60','40','100','25'])
                            subject_category_minimum.append(['60','40','100','10'])
                        elif sub_category == "category 2":
                            subject_category.append(["ESE","CA","Tot1"])
                            subject_category_maximum.append(['60','40','100'])
                            subject_category_minimum.append(['60','40','100'])
                        elif sub_category == "category 3":
                            subject_category.append(["TW", "PRA", "Tot2"])
                            subject_category_maximum.append(['25','25','50'])
                            subject_category_minimum.append(['10','10','20'])
                        elif sub_category == "category 4":
                            subject_category.append(["TW", "ORA", "Tot2"])
                            subject_category_maximum.append(['25','25','50'])
                            subject_category_minimum.append(['10','10','20'])
                        else:
                            subject_category.append(["TW"])
                            subject_category_maximum.append(['50'])
                            subject_category_minimum.append(['20'])

                        session["sub_code"] = subject_code
                        session["sub_name"] = subject_name
                        session["sub_category"] = subject_category
                        session["total_students"] = total_students
                        session["exam_semester"] = request.form.get("semester")
                        session["branch"] = request.form.get("branch")
                        session["examination_month"] = request.form.get("examination_month")
                        session["examination_year"] = request.form.get("examination_year")
                    mongo.db.examinationcellcategory.insert_one({"semester" : semester, "branch" : branch, "examination_month" : examination_month, "examination_year" : examination_year, "sub_code" : subject_code, "sub_name" : subject_name, "sub_category" : subject_category, "sub_category_maximum" : subject_category_maximum, "sub_category_minimum" : subject_category_minimum, "out_of_marks" : out_of_marks})
                    
                    return render_template('gradesheet.html', sub_code = subject_code, sub_name = subject_name, sub_category = subject_category, max = subject_category_maximum, min = subject_category_minimum, total_students = total_students, out_of_marks = out_of_marks)
                
                else :
                    subjectdetails = mongo.db.examinationcellcategory.find_one({"semester" : semester, "branch" : branch, "examination_month" : examination_month, "examination_year" : examination_year}, {"_id" :0})
                    session["sub_code"] = subjectdetails["sub_code"]
                    session["sub_name"] = subjectdetails["sub_name"]
                    session["sub_category"] = subjectdetails["sub_category"]
                    session["total_students"] = total_students
                    session["exam_semester"] = subjectdetails["semester"]
                    session["branch"] = subjectdetails["branch"]
                    session["examination_month"] = subjectdetails["examination_month"]
                    session["examination_year"] = subjectdetails["examination_year"]
                    out_of_marks = subjectdetails["out_of_marks"]
                    return render_template('gradesheet.html', sub_code = subjectdetails["sub_code"], sub_name = subjectdetails["sub_name"], sub_category = subjectdetails["sub_category"], max = subjectdetails["sub_category_maximum"], min = subjectdetails["sub_category_minimum"], total_students = total_students, out_of_marks = out_of_marks)
        else:
            return render_template("wronguser.html")
    else:
        return redirect("/loginpage")

@app.route("/gradesheet", methods=["POST"])
def gradesheet():
    if "email" in session:
        if session["email"] in examcellemail:
            if "sub_category" in session:
                sub_category = session["sub_category"]
                sub_code = session["sub_code"]
                sub_name = session["sub_name"]
                total_students = session["total_students"]
                exam_semester = session["exam_semester"]
                branch = session["branch"]
                examination_month = session["examination_month"]
                examination_year = session["examination_year"]
                student = {}
                for k in range (0, total_students):
                    subject = {}
                    for i in range (0, len(sub_category)):
                        marks_obtained = []
                        letter_grade = []
                        grade_points = []
                        credits_points = []
                        totalcreditscore = []
                        for j in range (0, len(sub_category[i])):
                            for l in range (0, 5):
                                index = "(" + str(l) + ", " + str(k) + ", " + str(i) + ", " + str(j) + ")" 
                                if l == 0:
                                    marks_obtained.append(request.form.get(index))
                                elif l == 1:
                                    if sub_category[i][j] == "TW" or sub_category[i][j] == "Tot1" or sub_category[i][j] == "Tot2" or sub_category[i][j] == "PRA" or sub_category[i][j] == "ORA":
                                        letter_grade.append(request.form.get(index))
                                else :
                                    if sub_category[i][j] == "TW" or sub_category[i][j] == "Tot1" or sub_category[i][j] == "Tot2":
                                        if sub_category[i][j] == "TW":
                                            if "PRA" not in sub_category[i] and "ORA" not in sub_category[i]:
                                                if l==2:
                                                    grade_points.append(request.form.get(index))
                                                elif l==3:
                                                    credits_points.append(request.form.get(index))
                                                else:
                                                    totalcreditscore.append(request.form.get(index))

                                        else:
                                            if l==2:
                                                grade_points.append(request.form.get(index))
                                            elif l==3:
                                                credits_points.append(request.form.get(index))
                                            else:
                                                totalcreditscore.append(request.form.get(index))
                        subject[sub_name[i]] = {"sub_code": sub_code[i],"marks_obtained" : marks_obtained, "letter_grade" : letter_grade, "grade_points" : grade_points, "credits_points" : credits_points, "totalcreditscore" : totalcreditscore}
                    student_k_name = "Student_name" + str(k)
                    student_k_roll = "Student_roll" + str(k)
                    student_k_total = "Student_total" + str(k)
                    student_k_clear_status = "Student_clear_status" + str(k)
                    student_k_credits = "Student_credits" + str(k)
                    student_k_SGPI = "Student_SGPI" + str(k)
                    student_k_CG = "Student_CG" + str(k)
                    mongo.db.examinationcell.delete_one({"roll_no" : int(request.form.get(student_k_roll)), "branch" : branch, "exam_semester" :exam_semester, "examination_month" : examination_month, "examination_year" : examination_year})
                    mongo.db.examinationcell.insert_one({"roll_no" : int(request.form.get(student_k_roll)), "name" : request.form.get(student_k_name), "branch" : branch, "exam_semester" :exam_semester, "examination_month" : examination_month, "examination_year" : examination_year, "exam_data" : subject, "student_total" : int(request.form.get(student_k_total)), "student_clear_status" : request.form.get(student_k_clear_status), "student_credits" : int(request.form.get(student_k_credits)), "student_SGPI" : request.form.get(student_k_SGPI), "student_CG" : int(request.form.get(student_k_CG))})
                    
                    student_count = mongo.db.studentdetails.count_documents({"roll_no" : int(request.form.get(student_k_roll))})
                    if student_count > 0:
                        student_gpa = mongo.db.examinationcell.find({"roll_no" : int(request.form.get(student_k_roll))}, {"_id" : 0, "student_SGPI" : 1})
                        cgpa = 0
                        count = 0
                        for e_document in student_gpa:
                            for e_entry in e_document:
                                cgpa = cgpa + int(e_document[e_entry])
                                count = count + 1
                        if count > 0:
                            cgpa = cgpa/count
                        else:
                            cgpa = 0
                        mongo.db.studentdetails.update_one({"roll_no" : int(request.form.get(student_k_roll)), "freeze" : 0}, {"$set" : {"cgpa" : cgpa}})                        
                        student_exam = mongo.db.examinationcell.find({"roll_no" : int(request.form.get(student_k_roll))}, {"_id" : 0, "exam_data" : 1})
                        kt_count = 0
                        for exam_student in student_exam:
                            for e_entry in exam_student:
                                for e_subject in exam_student[e_entry]:
                                    for grade_subject in exam_student[e_entry][e_subject]["letter_grade"]:
                                        if grade_subject == "FF":
                                            get_kt_collection_count = mongo.db.studentkt.count_documents({"roll_no" : int(request.form.get(student_k_roll))})
                                            if get_kt_collection_count == 0:
                                                mongo.db.studentkt.insert_one({"roll_no" : int(request.form.get(student_k_roll))}, {"ktsubjects" : []})
                                            kt_count = kt_count + 1

                        # kt_count_present = mongo.db.studentdetails.find_one({"roll_no" : int(request.form.get(student_k_roll))}, {"_id" : 0, "live kt" : 1, "dead kt" : 1})
                        # live_kt = kt_count_present["live kt"]
                        # dead_kt = kt_count_present["dead kt"]
                        # if live_kt > kt_count:
                        #     dead_kt = dead_kt + live_kt 
                        #     dead_kt = dead_kt - kt_count
                        mongo.db.studentdetails.update_one({"roll_no" : int(request.form.get(student_k_roll)), "freeze" : 0}, {"$set" : {"live kt" : kt_count}})
                    
                return redirect("/gradesheetgenerate")
            
            else:
                return render_template("wronguser.html")
        else:
            return redirect("/loginpage")


@app.route("/checkexaminationcategory", methods = ["POST"])
def checkexaminationcategory():
    if "email" in session:
        if session["email"] in examcellemail:
            data = request.get_json()
            examinationcategory_count = mongo.db.examinationcellcategory.count_documents(data)
            if examinationcategory_count == 0:
                return json.dumps({"status" : "OK"})
            else:
                return json.dumps({"status" : "present"})
        else:
            return render_template("wronguser.html")
    else:
        return redirect("/loginpage")

@app.route("/getgradesheet", methods = ["GET", "POST"])
def getgradesheet():
    if "email" in session:
        if session["email"] in examcellemail:
            if request.method == "GET":
                return render_template("getgradesheet.html")
            else:
                semester = request.form.get("semester")
                branch = request.form.get("branch")
                examination_month = request.form.get("examination_month")
                examination_year = request.form.get("examination_year")
                students = mongo.db.examinationcell.find({"exam_semester" : semester, "branch" : branch, "examination_month" :examination_month, "examination_year" : examination_year},{"_id" : 0, "semester" : 0, "branch" : 0, "examination_month" : 0, "examination_year" : 0})
                students_count = mongo.db.examinationcell.count_documents({"exam_semester" : semester, "branch" : branch, "examination_month" :examination_month, "examination_year" : examination_year})
                examination_details = mongo.db.examinationcellcategory.find_one({"semester" : semester, "branch" : branch, "examination_month" :examination_month, "examination_year" : examination_year})
                return render_template("downloadgradesheet.html", students= students, sub_code = examination_details["sub_code"], sub_name = examination_details["sub_name"], sub_category = examination_details["sub_category"], max = examination_details["sub_category_maximum"], min = examination_details["sub_category_minimum"], out_of_marks = examination_details["out_of_marks"], total_students = students_count)
        else:
            return render_template("wronguser.html")
    else:
        return redirect("/loginpage")

app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.route("/viewproctorform")
def viewproctorform():
    if "email" in session:
        if session["usertype"] == "student":
            student_rollno = mongo.db.studentdetails.find_one({"email" : session["email"]}, {"_id" : 0, "roll_no" : 1})
            proctorformdetails = mongo.db.studentproctorform.find_one({"roll_no" : student_rollno["roll_no"]},{"_id" : 0})
            if proctorformdetails == None:
                return redirect("/newproctorformentry")
            else:
                src = "https://drive.google.com/thumbnail?id=" + str(proctorformdetails["img_id"])
                return render_template("viewproctorform.html", student_details = proctorformdetails, src_image = src)
        else:
            return render_template("wronguser.html")
    else:
        return redirect("/loginpage")

@app.route("/newproctorformentry", methods = ["GET" , 'POST'])
def newproctorformentry():
    if "email" in session:
        if session["usertype"] == "student":
            student_rollno = mongo.db.studentdetails.find_one({"email" : session["email"]}, {"_id" : 0, "roll_no" : 1})
            proctorformdetails = mongo.db.studentproctorform.find_one({"roll_no" : student_rollno["roll_no"]},{"_id" : 0})
            proctordetails = mongo.db.studentdetails.find_one({"roll_no" : student_rollno["roll_no"]}, {"_id" : 0, "proctor_name" : 1, "proctor_email" : 1})
            if request.method == "GET" and proctorformdetails == None:
                roll_no = mongo.db.studentdetails.find_one({"email" : session["email"]}, {"_id":0, "roll_no" : 1})
                return render_template("newproctorform.html", student_details = roll_no, proctor_details = proctordetails)
            elif request.method == "POST":
                file_id = upload.uploadimage(student_rollno["roll_no"])
                student_details = mongo.db.studentproctorform.insert_one({"year_of_admission" : request.form.get("year_of_admission"), "branch"  : request.form.get("branch"), "current_year" : request.form.get("current_year"),
                "division" : request.form.get("division"), "roll_no" : student_rollno["roll_no"], "contact_number_R" : request.form.get("contact_number_R"), "name" : request.form.get("name"), "relation" : request.form.get("relation"),
                "gaurdian_name" : request.form.get("gaurdian_name"), "local_address" : request.form.get("local_address"), "gaurdian_local_address" : request.form.get("gaurdian_local_address"), "permanent_address" : request.form.get("permanent_address"),
                "contact_number_O" : request.form.get("contact_number_O"), "contact_number_M" : request.form.get("contact_number_M"), "student_email" : request.form.get("student_email"), "gaurdian_email" : request.form.get("gaurdian_email"),
                "blood_group" : request.form.get("blood_group"), "HandiCapped" : request.form.get("HandiCapped"), "date_of_birth" : request.form.get("date_of_birth") , "place_of_birth" : request.form.get("place_of_birth"), "mother_tounge" : request.form.get("mother_tounge"),
                "religion" : request.form.get("relgion"), "competitive_examination" : request.form.get("competetive_examination") , "competitive_examination_marks" : request.form.get("competitive_examination_marks"),
                "SSC_marks" : request.form.get("SSC_marks"), "HSC_marks" : request.form.get("HSC_marks"), "proctor_name" : proctordetails["proctor_name"], "proctor_email" : proctordetails["proctor_email"], "img_id" : file_id, "edit_flag" : 0})
                file = request.files["File"]
                UPLOAD_FOLDER = "static\\studentimages\\"
                app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], str(student_rollno["roll_no"]) + ".jpg"))
                return redirect("/viewproctorform")
            else:
                return "wrong request"
        else:
            return render_template("wronguser.html")
    else:
        return redirect("/loginpage")

@app.route("/editproctorform", methods=["GET", 'POST'])
def editproctorform():
    if "email" in session:
        if session["usertype"] == "student":
            student_rollno = mongo.db.studentdetails.find_one({"email" : session["email"]}, {"_id" : 0, "roll_no" : 1})
            proctorformdetails = mongo.db.studentproctorform.find_one({"roll_no" : student_rollno["roll_no"]},{"_id" : 0})
            proctordetails = mongo.db.studentdetails.find_one({"roll_no" : student_rollno["roll_no"]}, {"_id" : 0, "proctor_name" : 1, "proctor_email" : 1})
            if proctorformdetails["edit_flag"] == 0:
                return "cannot edit kindly ask the proctor to enable editing"
            else:
                if request.method == "GET" :
                    return render_template("editproctorform.html", student_details = proctorformdetails)
                else:
                    if request.form.get("File") == None:
                        file_id = upload.uploadimage(student_rollno["roll_no"])
                    else:
                        fileid = mongo.db.studentproctorform.find_one({"roll_no" : student_rollno["roll_no"]}, {"_id" : 0, "img_id" : 1})
                        file_id = fileid["img_id"]
                    student_details = mongo.db.studentproctorform.update_one({"roll_no" : student_rollno["roll_no"]}, {"$set" : {"year_of_admission" : request.form.get("year_of_admission"), "branch"  : request.form.get("branch"), "current_year" : request.form.get("current_year"),
                    "division" : request.form.get("division"), "roll_no" : student_rollno["roll_no"], "contact_number_R" : request.form.get("contact_number_R"), "name" : request.form.get("name"), "relation" : request.form.get("relation"),
                    "gaurdian_name" : request.form.get("gaurdian_name"), "local_address" : request.form.get("local_address"), "gaurdian_local_address" : request.form.get("gaurdian_local_address"), "permanent_address" : request.form.get("permanent_address"),
                    "contact_number_O" : request.form.get("contact_number_O"), "contact_number_M" : request.form.get("contact_number_M"), "student_email" : request.form.get("student_email"), "gaurdian_email" : request.form.get("gaurdian_email"),
                    "blood_group" : request.form.get("blood_group"), "HandiCapped" : request.form.get("HandiCapped"), "date_of_birth" : request.form.get("date_of_birth") , "place_of_birth" : request.form.get("place_of_birth"), "mother_tounge" : request.form.get("mother_tounge"),
                    "religion" : request.form.get("relgion"), "competitive_examination" : request.form.get("competetive_examination") , "competitive_examination_marks" : request.form.get("competitive_examination_marks"),
                    "SSC_marks" : request.form.get("SSC_marks"), "HSC_marks" : request.form.get("HSC_marks"), "proctor_name" : proctordetails["proctor_name"], "proctor_email" : proctordetails["proctor_email"], "img_id" : file_id, "edit_flag" : 0}})
                    return redirect("/viewproctorform")

@app.route("/studentlistproctor", methods = ["GET", 'POST'])
def studentlistproctor():
    if "email" in session:
        if session["usertype"] == "faculty" or session["usertype"] == "hod":
            if request.method == "GET":
                list_key = mongo.db.studentdetails.find_one({"proctor_email" : session["email"]}, {"_id" : 0, "roll_no" : 1, "name" : 1, "email" : 1})
                students_list = mongo.db.studentdetails.find({"proctor_email" : session["email"]}, {"_id" : 0, "roll_no" : 1, "name" : 1, "email" : 1}).sort("roll_no", 1)
                students_count = mongo.db.studentdetails.count_documents({"proctor_email" : session["email"]})
                edit_flag = []
                if students_list != None:
                    for document in students_list:
                        student_edit_flag = mongo.db.studentproctorform.find_one({"roll_no" : document["roll_no"]}, {"_id" : 0, "edit_flag" : 1})
                        if student_edit_flag == None:
                            edit_flag.append("Entry not found")
                        else:
                            edit_flag.append(student_edit_flag["edit_flag"])

                students_list = mongo.db.studentdetails.find({"proctor_email" : session["email"]}, {"_id" : 0, "roll_no" : 1, "name" : 1, "email" : 1}).sort("roll_no", 1)
                if session['email'] in hodemail:
                    user = "hod"
                else:
                    user = "faculty"
                return render_template("studentlistproctor.html", c = list_key, d = students_list, edit_flag = edit_flag, count = students_count,iterator = zip(students_list, edit_flag), user = user)
            else:
                data = request.get_json()
                if data[0] == "allow edit":
                    for k in range (1, len(data)):
                        student_presence = mongo.db.studentproctorform.find_one({"roll_no" : int(data[k])})
                        if student_presence != None:
                            mongo.db.studentproctorform.update_one({"roll_no" : int(data[k])}, {"$set" : {"edit_flag" : 1}})
                else:
                    for l in range (1, len(data)):
                        student_presence = mongo.db.studentproctorform.find_one({"roll_no" : int(data[l])})
                        if student_presence != None:
                            mongo.db.studentproctorform.update_one({"roll_no" : int(data[l])}, {"$set" : {"edit_flag" : 0}})
                return json.dumps({"status" : "OK"})
        


@app.route("/assignproctor", methods = ["GET", 'POST'])
def assignproctor():
    if "email" in session:
        if session["email"] in hodemail:
            branch = mongo.db.facultydetails.find_one({"email" : session["email"]}, {"_id" : 0, "branch" : 1})
            faculty_email = mongo.db.facultydetails.find({"branch" : branch["branch"]}, {"_id": 0 , "name" : 1 , "email" : 1}).sort("name", 1)
            fname = []
            femail = []
            count = 0
            for document in faculty_email:
                fname.append(document["name"])
                femail.append(document["email"])
                count = count + 1
            if request.method == "GET" :
                return render_template("assignproctor.html", name = fname, email = femail, count = count)
            else:
                email = request.form.get("name")
                name = fname[femail.index(email)]
                mongo.db.studentnamestemp.drop()
                file = request.files['File']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                else:
                    return "invalid document selected"
                # if not allowed_file(file.filename):
                #     return "Invalid File Format"
                file_extenstion = filename.rsplit('.', 1)[1].lower()
                if file_extenstion=="xlsx" or file_extenstion=="xls":
                    df = pd.read_excel(file)
                    df.to_csv('output.csv', encoding='utf-8')
                    records_ = df.to_dict(orient = 'records')
                    mongo.db.studentnamestemp.insert_many(records_ )
                
                students = mongo.db.studentnamestemp.find({},{"roll_no" : 1, "_id" : 0})
                for document in students:
                    mongo.db.studentdetails.update_one({"roll_no" : document["roll_no"], "branch" : branch["branch"]}, {"$set" : {"proctor_name" : name, "proctor_email" : email}})
                return render_template("assignproctor.html", name = fname, email = femail, count = count)
                

@app.route('/uploadCertificates', methods=["GET", "POST"])
def upload_internship():
    if 'email' in session and 'usertype' in session:
            if session['usertype'] == "student" :
                if request.method == "GET" : 
                    return render_template('upload_internship.html')
                else:
                    return upload.uploadInternships(session['email'])
            else:
                # print("wrong user")
                return render_template("wronguser.html")
    else:
         return render_template('login.html')

# @app.route("/uploadInternship", methods=["POST"])
# def upload_internshipCertificate():
#     if 'email' in session and  'usertype' in session:
#             if session['usertype'] == "student" :
#                 # print('Student internship '+session['email'])
#                 return upload.uploadInternships(session['email'])
#             else:
#                 return render_template("wronguser.html")

@app.route("/approveInternships", methods=["GET", "POST"])
def approve_internships():
    if 'email' in session and  'usertype' in session:
            if session['usertype'] == "faculty" :
                if session['email'] in hodemail:
                    user = "hod"
                else:
                    user = "faculty"
                if request.method == 'GET':

                    # print('Faculty approve internship '+session['email'])
                    
                    faculty_details=mongo.db.facultydetails.find_one({"email":session['email']},{"branch":1, "internship_coordinator":1})
                    # print("Faculty details\n")
                    # for temp in faculty_details:
                    #     print(faculty_details[temp])

                    if int(faculty_details['internship_coordinator'])==1:
                        row=mongo.db.student_activity.find_one({},{"_id":0,"branch":0})
                        # print(" Row \n")
                        #for temp in row:
                            #print(temp)
                        
                        studentInternships=mongo.db.student_activity.find({"branch":faculty_details['branch'], "file_type" : "internship"},{"_id":0,"branch":0})
                        # print("\n record")
                        # temp in studentInternships:
                            #print(temp)
                    
                    roll_no_list = mongo.db.studentdetails.find({"proctor_email" : session["email"]}, {"_id" : 0, "roll_no" : 1})
                    roll_no = []
                    for student in roll_no_list:
                        roll_no.append(student["roll_no"])
                    studentextracurricular=mongo.db.student_activity.find({"roll_no" : {"$in" : roll_no}, "branch":faculty_details['branch'], "file_type":"extra-curriculars"},{"_id":0,"branch":0})

                    return render_template('approveInternships.html',row=row, data=studentInternships, studentextracurricular = studentextracurricular, user = user)
                        
                else:
                    
                    data = request.get_json()
                    # print("recieved from approve internships\n")
                    # print(data)
                    if data[0] == 'approve selected':
                        for k in range(1,len(data)) :
                                student_details=mongo.db.student_activity.find_one({"file_id" : data[k]},{"roll_no":1, "file_name":1, "file_type" : 1})
                                Student_internship = mongo.db.studentdetails.find_one({"roll_no": student_details['roll_no']}, {"internships": 1, "extracurricular_acivities" : 1})
                                # print("\n student internship \n")
                                # for temp in Student_internship:
                                #     print(temp)
                                if student_details["file_type"] == "internship" :
                                    internship_count = Student_internship["internships"]
                                    if internship_count == '-':
                                        internship_count = 0
                                    internship_count = int(internship_count) + 1
                                    mongo.db.studentdetails.update_one({"roll_no":student_details['roll_no']}, {"$set": {"internships": internship_count},"$push": {"documents": {"file_name":student_details['file_name'] ,"file_id": data[k], "document_type":"internship"}}})
                                else:
                                    count = Student_internship["extracurricular_acivities"]
                                    if count == '-':
                                        count = 0
                                    count = int(count) + 1
                                    mongo.db.studentdetails.update_one({"roll_no":student_details['roll_no']}, {"$set": {"extracurricular_activities": count},"$push": {"documents": {"file_name":student_details['file_name'] ,"file_id": data[k], "document_type":"internship"}}})
                                mongo.db.student_activity.remove({"file_id" : data[k]})


                    else :
                        for k in range(1,len(data)) :
                                mongo.db.student_activity.remove({"file_id" : data[k]})
                                upload.deletefile(data[k])
                       
                    return json.dumps({"status" : "OK"})

    else:
        return render_template('login.html')                
            


if __name__ == "__main__":
    app.run(debug=True)
    app.jinja_env.filters['zip'] = zip