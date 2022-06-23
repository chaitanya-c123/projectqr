from flask import Flask,render_template,redirect,url_for,send_file,send_from_directory,request,flash,Response,session
from flask_bcrypt import Bcrypt
from datetime import datetime
import cv2 as cv
from pyzbar.pyzbar import decode
import mysql.connector
import qrcode
import random
from flask_mail import Mail,Message
from apscheduler.schedulers.background import BackgroundScheduler
import os
app= Flask(__name__)
bcrypt=Bcrypt(app)
sched = BackgroundScheduler({'apscheduler.timezone': 'Asia/Calcutta'})

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME']='chaitanyaqrproject@gmail.com'
app.config['MAIL_PASSWORD']='orhjvyvkwgfcdvhr'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail=Mail(app)

app.config['SECRET_KEY']='thisisasecretkey'
app.secret_key="hello"
otp=random.randint(0000,9999)

def job_fun():
    cnx=mysql.connector.connect(user='root',password='',host='localhost',database='qrproject')
    cursor=cnx.cursor()
    query=("UPDATE room SET available='1'")
    print("HEllo there")
    cursor.execute(query)
    cnx.commit()
    cursor.close()
    cnx.close()

sched.add_job(job_fun,trigger='cron',hour="23",minute="59")
sched.start()

picFolder=os.path.join('static','pics')
app.config['UPLOAD_FOLDER']=picFolder

@app.route('/',methods=['POST','GET'])
def index_():
    admin=os.path.join(app.config['UPLOAD_FOLDER'], 'admin.jpg')
    user=os.path.join(app.config['UPLOAD_FOLDER'], 'user.jpg')
    return render_template("index.html", admin_img=admin, user_img=user)




@app.route('/download',methods=["GET","POST"])
def download_file():
    path="img1.png"
    return send_file(path,as_attachment=True)

@app.route('/userHome',methods=['GET','POST'])
def userHome():
    if "user" in session:
        return render_template('userHome.html')
    else:
        return redirect(url_for('userLogin'))

@app.route('/userLogin',methods=['GET','POST'])
def userLogin():
    if request.method=="POST":
        user=request.form["email"]
        passw=request.form["password"]
        try:
            cnx=mysql.connector.connect(user='root',password='',host='localhost',database='qrproject')
            cursor=cnx.cursor()
            query=("SELECT email,password FROM users WHERE email = %s")
            user1=(user,)
            cursor.execute(query,user1)
            result=cursor.fetchone()
            if result:
                if bcrypt.check_password_hash(result[1], passw):
                    session["user"]=user
                    return redirect(url_for('userHome')) 
                else:
                    flash("Wrong Password!!")
                    return redirect(url_for("userLogin"))
            else:
                flash("No such username exists...Please register yourself")
                return redirect(url_for('userLogin'))     
    
        except mysql.connector.Error as error:
            flash("Failed to get record from MySQL table: {}".format(error))
        finally:
            if cnx.is_connected():
                cursor.close()
                cnx.close()
                print("MySQL connection is closed")
    return render_template('login.html',text="userLogin") 

@app.route('/adminLogin',methods=['GET','POST'])
def adminLogin():
    if request.method=="POST":
        user=request.form["email"]
        passw=request.form["password"]
        try:
            cnx=mysql.connector.connect(user='root',password='',host='localhost',database='qrproject')
            cursor=cnx.cursor()
            query=("SELECT username,password FROM admin WHERE username = %s")
            user1=(user,)
            cursor.execute(query,user1)
            result=cursor.fetchone()
            if result:
                if result[0]==user:
                    if bcrypt.check_password_hash(result[1], passw):
                        session["admin"]=True
                        return redirect(url_for('viewUsers')) 
                    else:
                        flash("Wrong Password!!")
                        return redirect(url_for("adminLogin"))
            else:
                flash("No such username exists!!")
                return redirect(url_for('adminLogin'))     
        
        except mysql.connector.Error as error:
            print("Failed to get record from MySQL table: {}".format(error))
        finally:
            if cnx.is_connected():
                cursor.close()
                cnx.close()
                print("MySQL connection is closed")

    return render_template('login.html',text="adminLogin") 

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=="POST":
        email=request.form["Email"]
        password=request.form["password"]
        fname=request.form["Fname"]
        lname=request.form["Lname"]
        dept=request.form["dept"]
        hashed_password=bcrypt.generate_password_hash(password)
        cnx=mysql.connector.connect(user='root',password='',host='localhost',database='qrproject')
        cursor=cnx.cursor()
        date=datetime.now()
        query=("SELECT user_email from user_details where user_email=%s")
        user1=(email,)
        cursor.execute(query,(user1))
        res=cursor.fetchone()
        if res:
            flash("User already exists")
            return redirect(url_for("register"))
        else:
            query=("INSERT INTO users"
                "(email,password,first_name,last_name,department,date)"
                "VALUES (%s,%s,%s,%s,%s,%s)")
            cursor.execute(query,(email,hashed_password,fname,lname,dept,date))
            cnx.commit()
            cursor.close()
            cnx.close()
            flash("Registration successful")
            return redirect(url_for('viewUsers'))
    return render_template('register.html')    


@app.route("/qrGenerate",methods=["GET","POST"])
def qrGenerate():
    if "admin" in session:
        if request.method=="POST":
            num=request.form['RoomNumber']
            
            features=qrcode.QRCode(version=1,box_size=40,border=3)
            features.make(fit=True)
            features.add_data(num)
            generate_image=features.make_image(fill_color="black",back_color="white")
            a="roomno"+num+".png"
            generate_image.save('./static/'+a)
            cnx=mysql.connector.connect(user='root',password='',host='localhost',database='qrproject')
            cursor=cnx.cursor()
            query=("SELECT Room_Number FROM room WHERE Room_Number = %s")
            room=(num,)
            cursor.execute(query,(room))
            res=cursor.fetchall()
            if not res:
                query=("INSERT INTO room"
                    "(room_number,available)"
                    "VALUES (%s,%s)")
                cursor.execute(query,(num,1))
                cnx.commit()
            # else:
            #     print("Already QRcode is generated for this particular Room Please give regenarate")
            cursor.close()
            cnx.close()
            return render_template('converted.html',image_path=a)
        return render_template('qrGenerate.html')
    else:
        return redirect(url_for("adminLogin"))
        

@app.route('/downloads', methods=['POST'])
def downloads():
    if "admin" in session:
        path=request.form["room_no"]
        return send_from_directory('./static',path,as_attachment=True)
    else:
        return redirect(url_for("adminLogin"))

room_no=[0]



def generate_frames():
    capture=cv.VideoCapture(0)
    while True:
        ret,frame=capture.read()
        frame1=frame
        if not ret:
            break
        else:
            ret1,buffer=  cv.imencode('.jpg',frame)
            frame=buffer.tobytes()
            decoded_data=decode(frame1)
            try:
                if decoded_data[0][0]:
                    capture.release()
                    cv.destroyAllWindows()
                    room=str(decoded_data[0][0], 'UTF-8')
                    global room_no
                    room_no[0]=room
                    break
            except:
                pass
        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n'+frame+b'\r\n')
            
            

@app.route('/vedio')
def vedio():
    return Response(generate_frames(),mimetype='multipart/x-mixed-replace;boundary=frame')

@app.route('/enter',methods=["GET","POST"])
def enter():
    if "user" in session:
        if request.method=="POST":
            user=session.get("user")
            if(room_no[0]==0):
                flash("Please scan a QR code")
                return redirect(url_for("enter"))
            else:
                cnx=mysql.connector.connect(user='root',password='',host='localhost',database='qrproject')
                cursor=cnx.cursor()
                rno=room_no[0]
                room_no[0]=0
                rno="102"
                query=("SELECT available from room WHERE room_number=%s")
                rno1=(rno,)
                cursor.execute(query,(rno1))
                res=cursor.fetchone()
                time=datetime.now().time()
                date=datetime.now().date()
                if res:
                    if res[0]==0:
                        cursor.close()
                        cnx.close()
                        flash("Sorry!!Classroom is already occupied, Head into view classroom page","info")
                        return redirect(url_for("userHome"))
                    else:
                        query=("SELECT inside from users WHERE email=%s")
                        user1=(user,)
                        cursor.execute(query,(user1))
                        res1=cursor.fetchone()
                        if res1 and res1[0]==1:
                            cursor.close()
                            cnx.close()
                            flash("You have to exit from previous classroom before entering new one","info")
                            return redirect(url_for('userHome'))
                        else:
                            query=("INSERT INTO user_details"
                                "(user_email,room_number,in_time,date)"
                                "VALUES (%s,%s,%s,%s)")
                            cursor.execute(query,(user,rno,time,date))
                            cnx.commit()
                            query=("UPDATE room SET available='0' WHERE room_number=%s")
                            cursor.execute(query,(rno1))
                            cnx.commit()
                            query=("UPDATE users SET inside='1' WHERE email=%s")
                            cursor.execute(query,(user1))
                            cnx.commit()
                            cursor.close()
                            cnx.close() 
                            flash("Hurray!! You can enter to the class now","info")       
                            return redirect(url_for('userHome'))
                else:
                    flash("This is invalid QR Code,Please scan a valid one","info")
                    cnx.close()
                    cursor.close()
                    return redirect(url_for("enter"))
        else:
            return render_template("scan.html",text="enter")
    else:
        return redirect(url_for("userLogin"))


@app.route('/exit',methods=["GET","POST"])
def exit():
    if "user" in session:
        if request.method=="POST":
            user=session.get("user")
            
            if room_no[0]==0:
                flash("Please scan a QR code")
                return redirect(url_for("exit"))
            else:
                cnx=mysql.connector.connect(user='root',password='',host='localhost',database='qrproject')
                cursor=cnx.cursor()
                rno=room_no[0]
                room_no[0]=0
                rno="102"
                query=("SELECT available from room WHERE room_number=%s")
                rno1=(rno,)
                user1=(user,)
                time=datetime.now().time()
                date=datetime.now().date()
                cursor.execute(query,(rno1))
                res=cursor.fetchone()
                t="00:00:00"
                if res:
                    if res[0]==0:
                        query=("SELECT id,user_email from user_details WHERE (room_number=%s AND exit_time=%s AND date=%s)")
                        cursor.execute(query,(rno,t,date))
                        res1=cursor.fetchone()
                        if res1 and res1[1]==user:
                            query=("UPDATE user_details SET exit_time=%s WHERE id=%s")
                            id=res1[0]
                            cursor.execute(query,(time,id))
                            cnx.commit()
                            query=("UPDATE room SET available='1' where room_number=%s")
                            cursor.execute(query,(rno1))
                            cnx.commit()
                            query=("UPDATE users SET inside='0' where email=%s")
                            cursor.execute(query,(user1))
                            cnx.commit()
                            flash("Successfull","info")
                            return redirect(url_for('userHome'))
                        else:
                            flash("You can't exit the class being handled by other staff","info")
                            return redirect(url_for('userHome'))
                    else:
                        flash("You can't exit the class which is not handled by any staff","info")
                        return redirect(url_for('userHome'))
                        

                else:
                    flash("This is invalid QR Code,Please scan a valid one","info")
                    cursor.close()
                    cnx.close()
                    return redirect(url_for("exit"))
        else:
            return render_template("scan.html",text="exit")
    else:
        return redirect(url_for("userLogin"))
    

@app.route("/viewClass",methods=["GET","POST"])
def viewClass():
    if "user" in session:
        cnx=mysql.connector.connect(user='root',password='',host='localhost',database='qrproject')
        cursor=cnx.cursor()
        query=("SELECT * FROM room")
        cursor.execute(query)
        res=cursor.fetchall()
        cursor.close()
        cnx.close()
        if res:
            return render_template("classroom.html",room=res)
    else:
        return redirect(url_for("userLogin"))

@app.route("/viewStaff",methods=["GET","POST"])
def viewStaff():
    if "admin" in session:
        cnx=mysql.connector.connect(user='root',password='',host='localhost',database='qrproject')
        cursor=cnx.cursor()
        query=("SELECT * FROM users")
        cursor.execute(query)
        res=cursor.fetchall()
        cursor.close()
        cnx.close()
        if res:
            return render_template("staff.html",staff=res)
    else:
        return redirect(url_for("adminLogin"))

@app.route("/viewUsers",methods=["GET","POST"])
def viewUsers():
    if "admin" in session:
        cnx=mysql.connector.connect(user='root',password='',host='localhost',database='qrproject')
        cursor=cnx.cursor()
        query=("SELECT id,email,first_name,last_name,department,room_number,in_time,exit_time,user_details.date FROM (user_details,users) WHERE users.email=user_details.user_email")
        cursor.execute(query)
        res=cursor.fetchall()
        cursor.close()
        cnx.close()
        if res:
            return render_template("users.html",users=res)
    else:
        return redirect(url_for("adminLogin"))
    
@app.route("/index")
def index():
    return render_template("index.html")
    
@app.route("/changePass",methods=["GET","POST"])
def changePass():
    if "user" in session:
        if request.method=="POST":
            oldPass=request.form["oldPass"]
            newPass=request.form["newPass"]
            user=session["user"]
            user1=(user,)
            cnx=mysql.connector.connect(user='root',password='',host='localhost',database='qrproject')
            cursor=cnx.cursor()
            query=("SELECT email,password FROM users WHERE email=%s")
            cursor.execute(query,(user1))
            res=cursor.fetchone()
            if res:
                if bcrypt.check_password_hash(res[1], oldPass):
                        hashed_password=bcrypt.generate_password_hash(newPass)
                        query=("UPDATE users SET password=%s WHERE email=%s")
                        cursor.execute(query,(hashed_password,user))
                        cnx.commit()
                        cursor.close()
                        cnx.close()
                        flash("Password changed successfully")
                        return redirect(url_for("userHome"))
                else:
                    flash("Incorrect Old password. Please enter appropriate password")
                    return redirect(url_for("changePass"))
            else:
                flash("Sorry for inconvinience, please try again")
                return redirect(url_for("changePass"))
        else:
            return render_template("changePass.html")
    else:
        return redirect(url_for("userLogin"))

@app.route("/usage",methods=["POST","GET"])
def usage():
    if "user" in session:
        cnx=mysql.connector.connect(user='root',password='',host='localhost',database='qrproject')
        cursor=cnx.cursor()
        query=("SELECT * from user_details WHERE user_email=%s")
        user=session["user"]
        user1=(user,)
        cursor.execute(query,(user1))
        res=cursor.fetchall()
        cursor.close()
        cnx.close()
        if res:
            return render_template("usage.html",users=res)
    else:
        return redirect(url_for("userLogin"))

@app.route("/mail",methods=["GET","POST"])
def mail_verify():
    if request.method=="POST":
        email=request.form['mail']
        user1=(email,)
        cnx=mysql.connector.connect(user='root',password='',host='localhost',database='qrproject')
        cursor=cnx.cursor()
        query=("SELECT email FROM users WHERE email=%s")
        cursor.execute(query,(user1))
        res=cursor.fetchone()
        if res:
            msg=Message('OTP',sender="chaitanyaqrproject@gmail.com",recipients=[email])
            msg.body=str(otp)
            mail.send(msg)
            return render_template("otp.html",mail=email)
        else:
            flash("No such username exists..Please enter valid username")
            return redirect(url_for("mail_verify"))
    else:
        return render_template("mail.html")

@app.route("/otp",methods=["POST","GET"])
def otp_verify():
    if request.method=="POST":
        new_otp=request.form['otp']
        mail=request.form['userId']
        if otp==int(new_otp):
            return render_template("forgotPass.html",mail=mail)
        else:
            flash("U have entered wrong OTP!!Please try again")
            return redirect(url_for("mail_verify"))


@app.route("/forgotPass",methods=["POST","GET"])
def forgotPass():
    if request.method=="POST":
        password=request.form["pass"]
        userId=request.form["userId"]
        cnx=mysql.connector.connect(user='root',password='',host='localhost',database='qrproject')
        cursor=cnx.cursor()
        hashed_password=bcrypt.generate_password_hash(password)
        query=("UPDATE users SET password=%s WHERE email=%s")
        cursor.execute(query,(hashed_password,userId))
        cnx.commit()
        cursor.close()
        cnx.close()
        return redirect(url_for("userLogin"))

@app.route("/adminclass")
def adminclass():
    cnx=mysql.connector.connect(user='root',password='',host='localhost',database='qrproject')
    cursor=cnx.cursor()
    query=("SELECT * FROM room")
    cursor.execute(query)
    res=cursor.fetchall()
    cursor.close()
    cnx.close()
    if res:
        return render_template("adminclass.html",room=res)

@app.route('/logout',methods=["POST","GET"])
def user_logout():
    session.pop("user",None)
    return redirect(url_for("userLogin"))

@app.route('/Admin_logout',methods=["POST","GET"])
def admin_logout():
    session.pop("admin",None)
    return redirect(url_for("adminLogin"))




if __name__=='__main__':
    app.run(debug=True)
