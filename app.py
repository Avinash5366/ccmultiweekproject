from flask import Flask, render_template, request, redirect, url_for,flash
import pymysql
import boto3
import json
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
import os
import botocore

ACCESS_KEY = "AKIAXCNOJD2YA65NSG56"
SECRET_KEY ="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"


ENDPOINT="avidatabase.c5egpajiiqtk.us-east-1.rds.amazonaws.com"
PORT=3306
USR="admin"
PASSWORD="171536680"
DBNAME="users"


app = Flask(__name__)
app.secret_key = SECRET_KEY
# Replace with your actual AWS S3 credentials and bucket information
AWS_ACCESS_KEY_ID = 'AKIAXCNOJD2YA65NSG56'
AWS_SECRET_ACCESS_KEY = 'KhP4gBAKRW9UcAbeVR4pVGLi4KDKGTiR+uFda4F0'
AWS_REGION = 'us-east-1'
BUCKET_NAME = 'avinashbucket123'

s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                  region_name=AWS_REGION)

@app.route('/', methods=["GET", "POST"])
def main():
     print("request.method======",request.method)
     if request.method == "POST":
        email = request.form.get("username")
        password = request.form.get("password")
        print('login---',email,password)
        conn = pymysql.connect(host=ENDPOINT, user=USR, password=PASSWORD,database=DBNAME)
        cur = conn.cursor()
        print('--------------------------------------------------------')
        users = cur.execute("SELECT * FROM users WHERE email = %s AND pWd = %s", (email, password))
        print("-------=-=-=---=-===========",users)
        if users:
            return  redirect("/uploadpage")
        else:
            return 'login failes'
     else:
         return render_template("login.html")

@app.route('/uploadpage', methods=["GET", "POST"])
def loadpage():
       return render_template("uploadpage.html")
    

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'fileToUpload' not in request.files:
            return "No file part"

        file = request.files['fileToUpload']

        if file.filename == '':
            return "No selected file"

        filename = file.filename
        s3.upload_fileobj(file, BUCKET_NAME, filename)

        return "File uploaded successfully"

    except botocore.exceptions.NoCredentialsError:
        return "AWS credentials not found. Please check your configuration."
    except Exception as e:
        return str(e)

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        print('----------------------',password)

        # Check if the passwords match
        if password != confirm_password:
            flash("error", "Passwords do not match")
            return redirect("/register")

        try:
            print('----------------------try ------------------')
            # Connect to the AWS RDS database
            conn = pymysql.connect(host=ENDPOINT, user=USR, password=PASSWORD,database=DBNAME)
            cur = conn.cursor()
            print("connected to DB")
            

            create_table_query = '''CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                first_name VARCHAR(150) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email VARCHAR(50) NOT NULL UNIQUE,
                pWd VARCHAR(100) NOT NULL
            )'''
            cur.execute(create_table_query)
            conn.commit()
            print('table created')

            # Insert the user details into the database
            cur.execute("INSERT INTO users (first_name, last_name, email, pWd) VALUES (%s, %s, %s, %s)",
                        (first_name, last_name, email, password))
            conn.commit()

            flash("success", "Registration successful! You can now log in.")
            return redirect("/")
        except Exception as e:
            flash("error", "An error occurred while registering. Please try again.")
            print("Database connection failed due to {}".format(e))
            return redirect("/register")
    else:
        return render_template("register.html") 

@app.route('/add', methods=["POST"])
def add():
    email = request.form.get("email")
    password= request.form.get("password")
    desc=request.form.get("description")
  #  imagepath=request.form.get("imagefilepath")
    f = request.files['file']
    filename=f.filename.split("\\")[-1]
    f.save(secure_filename(filename))
    #filename=imagepath.split("\\")[-1]

    client= boto3.client("s3",
    aws_access_key_id="AKIAXCNOJD2YA65NSG56",
aws_secret_access_key="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",

)
    client.upload_file(filename, "applab1", "images/"+filename,ExtraArgs={'GrantRead': 'uri="http://acs.amazonaws.com/groups/global/AllUsers"'})

    conn =  pymysql.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO userdetails(email,password,description,imagelocation) VALUES('"+email+"','"+password+"','"+desc+"', '"+filename+"');")
    print("Insert Success")
    conn.commit()
    os.remove(filename)

    lambda_client = boto3.client('lambda',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name='us-east-2')

    lambda_payload={"email":email}
    lambda_client.invoke(FunctionName='lambdaSNS', 
                     InvocationType='Event',
                     Payload=json.dumps(lambda_payload))

    return redirect("/")


@app.route('/mainpage',methods=["GET"])
def mainpage():
    email= request.args.get('email')
    password= request.args.get('password')
    print(email,password)
    try:
            conn =  pymysql.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME)
            cur = conn.cursor()
            qry= "SELECT * FROM userdetails Where email ='"+email+"' AND password = '"+password+"';"
            print(qry)
            cur.execute("SELECT * FROM userdetails;")
            query_results = cur.fetchall()
            print(query_results)
            cur.execute("SELECT * FROM userdetails Where email ='"+email+"' AND password = '"+password+"';")
            query_results = cur.fetchall()
            print(query_results)
            if len(query_results)==1:
               return render_template("mainpage.html")
            else:
                return redirect("/notfound")
    except Exception as e:
            print("Database connection failed due to {}".format(e))
            return redirect("/")

@app.route('/search',methods=["POST"])
def search():
    email = request.form.get("email")
    print(email)
    return redirect("viewdetails/"+str(email))

@app.route('/viewdetails/<email>')
def viewdetails(email):

    try:
            conn =  pymysql.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME)
            cur = conn.cursor()
            cur.execute("SELECT * FROM userdetails Where email ='"+email+"';")
            conn.commit()
            query_results = cur.fetchall()
            print(query_results)
            client = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
            url = client.generate_presigned_url('get_object',
                                        Params={
                                            'Bucket': 'applab1',
                                            'Key': 'images/'+str(query_results[0][3]),
                                        },                                  
                                        ExpiresIn=3600)
            url=str(url).split('?')[0]
            item={'email':query_results[0][0],'password':query_results[0][1],'desc':query_results[0][2],'link':url}
            print(item)
            return render_template("viewdetails.html", item=item)        
    except Exception as e:
            print("Database connection failed due to {}".format(e))
            return redirect("/")

@app.route('/initialize')
def initialize():
    try:
        print("INITIALIZING DATABASE")
        conn =  pymysql.connect(host=ENDPOINT, user=USR, password=PASSWORD, database=DBNAME)
        cur = conn.cursor()
        try:
            cur.execute("DROP TABLE userdetails;")
            print("table deleted")
        except Exception as e:
            print("cannot delete table")
        cur.execute("CREATE TABLE userdetails(email VARCHAR(20), password VARCHAR(20), description VARCHAR(50), imagelocation VARCHAR(50));")
        print("table created")
        cur.execute("INSERT INTO userdetails(email,password,description,imagelocation) VALUES('test1@gmail.com','password','this is a desc', 'Default.png');")
        print("Insert Success")
        cur.execute("INSERT INTO userdetails(email,password,description,imagelocation) VALUES('test2@gmail.com','password','this is a desc', 'Default.png');")
        print("Insert Success")
        cur.execute("INSERT INTO userdetails(email,password,description,imagelocation) VALUES('test3@gmail.com','password','this is a desc', 'Default.png');")
        print("Insert Success")
        cur.execute("INSERT INTO userdetails(email,password,description,imagelocation) VALUES('test4@gmail.com','password','this is a desc', 'Default.png');")
        print("Insert Success")
        conn.commit()

        cur.execute("SELECT * FROM userdetails;")
        query_results = cur.fetchall()
        print(query_results)
        return redirect("/")
    except Exception as e:
        print("Database connection failed due to {}".format(e))
        return redirect("/")


if __name__=="__main__":
    app.run(debug=True)
