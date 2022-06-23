import mysql.connector
from flask import Flask
from flask_bcrypt import Bcrypt
app= Flask(__name__)
bcrypt=Bcrypt(app)

app.config['SECRET_KEY']='thisisasecretkey'
passw="admin@123"

hashed_password=bcrypt.generate_password_hash(passw)
user="chaitanyamc001@gmail.com"
cnx=mysql.connector.connect(user='root',password='',host='localhost',database='qrproject')
cursor=cnx.cursor()
id=cursor.lastrowid
query=("INSERT INTO admin"
        "(username,password)"
        "VALUES (%s,%s)")
cursor.execute(query,(user,hashed_password))
cnx.commit()
cursor.close()
cnx.close()

if __name__=='__main__':
    app.run(debug=True)