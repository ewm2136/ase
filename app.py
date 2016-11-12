from flask import Flask, render_template, request, redirect
from passlib.hash import sha256_crypt
from random import randint

import pymssql
import sys
import re

app = Flask(__name__)

# server connection
conn = pymssql.connect(server='eats.database.windows.net', \
  user='th2520@eats',\
  password='123*&$eats',\
  database='AERIS')\


# global variables for current logged in user and bill session
user_email = ""
bill_id = -1

def validate_name(name):
  if not re.match("^[A-Za-z0-9 ]*$"):
    return False
  return True

def validate_email(email):
  if not re.match("^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$", email):
    return False
  return True

def validate_price(price):
  if not re.match("^(?=.*\d)\d*(?:\.\d\d)?$", price):
    return False
  return True

@app.route("/")
def main():
  cursor = conn.cursor()
  # cursor.execute("""
  #   CREATE TABLE Test_Users (
  #     FirstName VARCHAR(255) NOT NULL,
  #     LastName VARCHAR(255) NOT NULL,
  #     Email varchar(255) NOT NULL PRIMARY KEY,
  #     Password varchar(255) NOT NULL 
  #   )
  #   """)
  cursor.execute("SELECT * FROM Test_Users")
  data = cursor.fetchall()

  print data # debug print User table

  # # conn.commit()
  # cursor.close()

  # cursor = conn.cursor()

  # #create Item table
  # cursor.execute("""
  #   CREATE TABLE Test_Items(
  #     Email varchar(255) NOT NULL, 
  #     ItemName varchar(255) NOT NULL,
  #     Quantity INT NOT NULL,
  #     Price DECIMAL(10,2) NOT NULL,     
  #     BillId INT NOT NULL,
  #     PRIMARY KEY (Email, ItemName, BillId)
  #   )
  #   """)

  # conn.commit()

  cursor.execute("SELECT * FROM Test_Items")
  data = cursor.fetchall()
  print data

  # cursor = conn.cursor()
  # cursor.execute("""
  #   CREATE TABLE Test_Bill_Users (
  #     billID INT NOT NULL,
  #     Email varchar(255) NOT NULL,
  #     PRIMARY KEY (billID, Email)
  #   )
  #   """)
  # conn.commit()
  
  cursor.execute("SELECT * FROM Test_Bill_Users")
  data = cursor.fetchall()
  print data

  print request.args

  return render_template('index.html')
 


@app.route('/login', methods=['GET', 'POST'])
def login():

  # take email and password from form
  email = request.form['email'].strip()
  password = request.form['password']

  # check fields
  if not email or not password:
    message = "Please enter all login fields."
    return render_template('index.html', response=message)

  # validate email
  if not validate_email(email):
    message = "Invalid email!"
    return render_template('index.html', response=message)

  # set global variable for current logged in user
  global user_email 
  user_email = email

  cursor = conn.cursor()
  cursor.execute("SELECT Password FROM Users WHERE Email=%s", email)

  # email doesn't exist in Users table
  if cursor.rowcount == 0: 
    message= "Sign up first!"
    cursor.close()
    return render_template('index.html', response=message)
  else:
    data = cursor.fetchall()
    cursor.close()

    # login success
    if sha256_crypt.verify(password, data[0][0]): 
      print "Login successful!" #for testing
      ##### need to show username!
        # cursor.execute("SELECT FirstName FROM Users WHERE Email=%s", email)
        # userName = cursor.fetchall()
      #####
      return redirect('bill')

    # login failed
    else: 
      message = "Incorrect password!"
      return render_template('index.html', response=message)



@app.route('/signUp', methods=['GET', 'POST'])
def signup():
  firstName = request.form['firstName'].strip()
  lastName = request.form['lastName'].strip()
  email = request.form['email'].strip()
  password = sha256_crypt.encrypt(request.form['password'])

  # check fields
  if not firstName or not lastName or not email or not password:
    message = "Please enter all signup fields."
    return render_template('index.html', response=message)

  # validate email
  if not isError:
    if not validate_email(email):
      message = "Invalid email!"
      return render_template('index.html', response=message)

  # check if email exists in Users table
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM Users WHERE Email=%s", email)

  # email doesn't exist in Users table
  if cursor.rowcount == 0: 
    cursor.execute("INSERT INTO Users VALUES (%s, %s, %s, %s)", (firstName,lastName, email, password))
    conn.commit()
    cursor.close()
    message = "Your account is registered successfully!"
    return render_template('index.html', response=message)

  # email already exists in Users table
  else: 
    message = "You registered with the same email before."
    cursor.close()
    return render_template('index.html', response=message)



# BILL PAGE
@app.route('/bill', methods=['GET', 'POST'])
def bill():
  # checks if table is already created, if it is, table is dropped and new table created
  # cursor = conn.cursor()
  # cursor.execute("""
  #   IF OBJECT_ID('Bill_Users', 'U') IS NOT NULL
  #     DROP TABLE Bill_Users
  #   CREATE TABLE Bill_Users (
  #     billID INT NOT NULL,
  #     Email varchar(255) NOT NULL,
  #     PRIMARY KEY (billID, Email)
  #   )
  #   """)
  # cursor.close()

  global user_email

  # find all associated bills in Bill_Users table
  cursor2 = conn.cursor()
  cursor2.execute("SELECT billID, Email FROM Bill_Users WHERE Email=%s", user_email)
  data = cursor2.fetchall()

  Userbill = [dict(BillID=row[0], Email=row[1]) for row in data]

  conn.commit()

  return render_template('bill.html', Userbill=Userbill)



# CREATE BILL
@app.route('/create_bill', methods=['GET', 'POST'])
def create_bill():

  # generate new bill id
  isUnique = False
  while(isUnique == False):
    randomNum = (randint(0,1000))
    cursor1 = conn.cursor()
    result = cursor1.execute("SELECT billID FROM Bill_Users WHERE billID=%d", randomNum)
    if (randomNum != result):
      print "Created bill session!"
      isUnique = True
      cursor1.close()

  # add bill to Bill_Users table
  cursor2 = conn.cursor()
  cursor2.execute("INSERT INTO Bill_Users VALUES (%d, %s)", (randomNum, user_email))
  cursor2.close()
  
  conn.commit()
  
  return redirect('bill')



# DISPLAY BILL
@app.route('/display_bill', methods=['GET', 'POST'])
def display_bill():
  global user_email

  # set global variable for current bill session
  global bill_id
  bill_id = request.form['billId']

  # retrieve all items in Items table associated with email and bill
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM Items WHERE billID=%d", (bill_id))
  data = cursor.fetchall()

  Userbill = [dict(Email=row[0], ItemName=row[1], Quantity=row[2], Price=row[3]) for row in data]

  # retrieve all users in Bill_Users table associated with bill
  cursor1 = conn.cursor()
  cursor1.execute("SELECT * FROM Bill_Users WHERE billID=%d", (bill_id))
  data = cursor1.fetchall()

  cursor2 = conn.cursor()

  Userlist = []

  # retrieve names of users in Users table associated with email
  for row in data:
    cursor2.execute("SELECT * FROM Users WHERE Email=%s", row[1])
    data1 = cursor2.fetchall()
    Userdict = {}
    Userdict["Name"] = data1[0][0]
    Userdict["Email"] = row[1]
    Userlist.append(Userdict)

  conn.commit()

  # bill shows list of items
  return render_template('display_bill.html', Userbill=Userbill, Userlist=Userlist, Billid=bill_id)



# ADD ITEM
@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
  global user_email
  global bill_id

  item_name = request.form['item'].strip()
  quantity = request.form['quantity'].strip()
  price = request.form['price'].strip()

  # check fields
  if not item_name or not quantity or not price:
    return render_template("400.html", message="INVALID INPUT VALUES")
  if not validate_name(item_name) or not quantity.isnumeric() or not validate_price(price):
    return render_template("400.html", message="INVALID INPUT VALUES")
  if (quantity == 0) or (price == 0):
    return render_template("400.html", message="INVALID INPUT VALUES")

  cursor = conn.cursor()
  cursor.execute("INSERT INTO Items VALUES (%s, %s, %d, %d, %d)", (user_email, item_name, quantity, price, bill_id))
  conn.commit()

  # retrieve all items in Items table associated with email and bill
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM Items WHERE billID=%d", (bill_id))
  data = cursor.fetchall()

  Userbill = [dict(Email=row[0], ItemName=row[1], Quantity=row[2], Price=row[3]) for row in data]

  # retrieve all users in Bill_Users table associated with bill
  cursor1 = conn.cursor()
  cursor1.execute("SELECT * FROM Bill_Users WHERE billID=%d", (bill_id))
  data = cursor1.fetchall()

  Userlist = []

  cursor2 = conn.cursor()

  # retrieve names of users in Users table associated with email
  for row in data:
    cursor2.execute("SELECT * FROM Users WHERE Email=%s", row[1])
    data1 = cursor2.fetchall()
    Userdict = {}
    Userdict["Name"] = data1[0][0]
    Userdict["Email"] = row[1]
    Userlist.append(Userdict)

  conn.commit()

  # bill shows list of items
  return render_template('display_bill.html', Userbill=Userbill, Userlist=Userlist, Billid=bill_id)



# REMOVE ITEM
@app.route('/remove_item', methods=['GET', 'POST'])
def remove_item():
  global user_email
  global bill_id

  item_name = request.form['ItemName']

  cursor = conn.cursor()
  cursor.execute("DELETE FROM Items WHERE Email=%s AND ItemName=%s AND billID=%d", (user_email, item_name, bill_id))
  conn.commit()

  # retrieve all items in Items table associated with email and bill
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM Items WHERE billID=%d", (bill_id))
  data = cursor.fetchall()

  Userbill = [dict(Email=row[0], ItemName=row[1], Quantity=row[2], Price=row[3]) for row in data]

  # retrieve all users in Bill_Users table associated with bill
  cursor1 = conn.cursor()
  cursor1.execute("SELECT * FROM Bill_Users WHERE billID=%d", (bill_id))
  data = cursor1.fetchall()

  Userlist = []

  cursor2 = conn.cursor()
  
  # retrieve names of users in Users table associated with email
  for row in data:
    cursor2.execute("SELECT * FROM Users WHERE Email=%s", row[1])
    data1 = cursor2.fetchall()
    Userdict = {}
    Userdict["Name"] = data1[0][0]
    Userdict["Email"] = row[1]
    Userlist.append(Userdict)

  conn.commit()

  # bill shows list of items
  return render_template('display_bill.html', Userbill=Userbill, Userlist=Userlist, Billid=bill_id)



# ADD FRIEND
@app.route('/add_friend', methods=['GET', 'POST'])
def add_friend():
  global user_email
  global bill_id

  Femail = request.form['Friend_email'].strip()
  billid = request.form['Billid'].strip()

  # check fields
  if not Femail or not billid:
    return render_template("400.html", message="INVALID INPUT VALUES")
  if not validate_email(Femail) or not billid.isnumeric():
    return render_template("400.html", message="INVALID INPUT VALUES")

  # get user from Users table
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM Users WHERE Email=%s", (Femail))
  data = cursor.fetchall()
  conn.commit()

  # add user into Bill_Users table
  cursor = conn.cursor()
  cursor.execute("INSERT INTO Bill_Users VALUES (%d, %s)", (billid, Femail))
  conn.commit()

  # retrieve all items in Items table associated with email and bill
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM Items WHERE billID=%d", (bill_id))
  data = cursor.fetchall()

  Userbill = [dict(Email=row[0], ItemName=row[1], Quantity=row[2], Price=row[3]) for row in data]

  # retrieve all users in Bill_Users table associated with bill
  cursor1 = conn.cursor()
  cursor1.execute("SELECT * FROM Bill_Users WHERE billID=%d", (bill_id))
  data = cursor1.fetchall()

  Userlist = []

  cursor2 = conn.cursor()

  # retrieve names of users in Users table associated with email
  for row in data:
    cursor2.execute("SELECT * FROM Users WHERE Email=%s", row[1])
    data1 = cursor2.fetchall()
    Userdict = {}
    Userdict["Name"] = data1[0][0]
    Userdict["Email"] = row[1]
    Userlist.append(Userdict)

  conn.commit()

  # bill shows list of items
  return render_template('display_bill.html', Userbill=Userbill, Userlist=Userlist, Billid=bill_id)



# SPLIT COST
@app.route('/split_cost', methods=['GET', 'POST'])
def split_cost():
  global user_email
  global bill_id

  tip = request.form['Tip'].strip()
  post_tax = request.form['Total'].strip()

  if not tip or not post_tax:
    return render_template("400.html", message = "INVALID INPUT VALUES")
  if not validate_price(tip) or not validate_price(post_tax):
    return render_template("400.html", message = "INVALID INPUT VALUES")

  tip = float(tip)
  post_tax = float(post_tax)

  # retrieve all items associated with email and bill
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM Items WHERE billID=%d", (bill_id))
  data = cursor.fetchall()

  Userbill = [dict(Email=row[0], ItemName=row[1], Quantity=row[2], Price=row[3]) for row in data]

  pre_tax = 0.0
  user_total = 0.0
  for item in Userbill:
	  print item
	  if item['Email'] == user_email:
	  	user_total += (float(item['Price']) * int(item['Quantity']))
	  pre_tax += (float(item['Price']) * int(item['Quantity']))

  print post_tax
  print pre_tax
  print user_total

  if ((user_total > post_tax) or (user_total > pre_tax)):
    return render_template("400.html", message = "USER BILL GREATER THAN TOTAL BILL")

  user_total = ((user_total / pre_tax) * post_tax) * (1 + tip)
  user_total = ("%.2f" % user_total)
  print user_total

  return render_template('split_cost.html', Cost=user_total)

if __name__ == "__main__":
	app.run(debug=True, threaded=True)