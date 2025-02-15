from datetime import datetime
import traceback
import uuid
from bson import ObjectId
from flask import Flask,g, Response, jsonify, redirect, render_template, request, session, sessions, url_for
# from flask_session import Session
from flask import session
import pymongo

# import application from app
app=Flask(__name__,template_folder='templates')
# app.config['SESSION_TYPE'] = 'filesystem'
# Session(app)

try:
    mongo = pymongo.MongoClient(
        host = 'localhost',
        port = 27017,
        serverSelectionTimeoutMS = 1000
    )
    db = mongo.DineEasy #connect to mongodb1
    mongo.server_info() #trigger exception if cannot connect to db
except:
    print("Error -connect to db")

# # @app.route('/set_tableid/<tableid>')
# def set_tableid(tableid):
#     session['tableid'] = tableid
#     return 'Table ID set in session'

# # @app.route('/get_data')
# def get_data():
#     tableid = session.get('tableid', None)
#     if tableid is not None:
#         return f'Table ID: {tableid}'
#     else:
#         return 'Table ID not found in the session'
    
@app.route('/fun')
def index():
    session['prev_url'] = request.url
    return render_template('index.html')

@app.route('/previous_page')
def previous_page():
    # Redirect to the previous page using the stored URL
    return redirect(session.get('prev_url', url_for('index')))


@app.route('/home/<reservedtable>/<cusineid>', methods=['GET'])
def homepage(reservedtable,cusineid):
  try:
    documents = db.Menu.find().sort("cuisineid",1)
    output=None
    output = [{item: data[item] for item in data if item != '_id'} for data in documents]
    get_food={"cusineid":int(cusineid)}
    documents1 = db.Food.find(get_food).sort("cusineid",1)
    output1=None
    output1 = [{item: data[item] for item in data if item != '_id'} for data in documents1]
    get_table_number={'_id':ObjectId(reservedtable)}
    get_table_number=db.Tables.find_one(get_table_number)
    print("table number",get_table_number)
    
    return render_template('food.html',data=output,additional_data=reservedtable,food=output1,tableNumber=get_table_number["tableNumber"])
  except Exception as ex:
    error_message = str(ex)
    traceback_info = traceback.format_exc()
    print(f"Error Message: {error_message}")
    print(f"Traceback:\n{traceback_info}")
  return None

# @app.route('/login')
# def login():
#   try:
#     return render_template('customer.html')
#     # return jsonify(output)
#   except Exception as ex:
#     error_message = str(ex)
#     traceback_info = traceback.format_exc()
#     print(f"Error Message: {error_message}")
#     print(f"Traceback:\n{traceback_info}")
#   return None

def update_table_to_occupied(table_number):
   get_table_details={"tableNumber":table_number}
   try:
    update_table={
        "$set": {
                    "status":"Occupied"
                }
    }
    db.Tables.find_one_and_update(get_table_details,update_table,return_document=True)
    tableid=db.Tables.find_one(get_table_details)
    response = Response("UPDATED",status=201,mimetype='application/json')
    return tableid["_id"]
   except Exception as ex:
        response = Response("Recorded Error in Update!!",status=500,mimetype='application/json')
        return response 
   
def update_table_to_vaccant(table_number):
   get_table_details={"tableNumber":table_number}
   try:
    update_table={
        "$set": {
                    "status":"Vaccant"
                }
    }
    db.Tables.find_one_and_update(get_table_details,update_table,return_document=True)
    response = Response("UPDATED",status=201,mimetype='application/json')
    return response
   except Exception as ex:
        response = Response("Recorded Error in Update!!",status=500,mimetype='application/json')
        return response
   
def add_order(table_id,inserted_id):
   print("i am in order" )
   now = datetime.now()
   try:
    new_order={
        "table_id":table_id,
        "cust_id":inserted_id,
        "datetime":datetime.now(),
        "items":[],
        "totalPrice":0
    }
    new_id=db.Orders.insert_one(new_order)
    print("here is ur new id ", new_id.inserted_id)
    response = Response("New Record added",status=201,mimetype='application/json')
    return new_id.inserted_id
   except Exception as ex:
    response = Response("Recorded Error in Update!!",status=500,mimetype='application/json')
    print(response)

# @app.route('/addtocart',methods=['GET','POST'])
# def addtocart():
#    if request.method == 'POST':
#       item_name = request.form['itemName']
#       item_price = request.form['price']
#     #   item_object_id = request.form['itemObjectID']
#       try:
#           print("table id",g.table_id)
#       except Exception as ex:
#           pass
#       return redirect(url_for('getfood',data=))
#    else:
#       return render_template('food.html')

def getfoodbycuisineid(cusineid):
  try:
    get_food={"cusineid":int(cusineid)}
    documents = db.Food.find()
    print("documents...............", documents)
    output=None
    output = [{item: data[item] for item in data } for data in documents]
    print(output)
    return output
    # return jsonify(output)
  except Exception as ex:
    error_message = str(ex)
    traceback_info = traceback.format_exc()
    print(f"Error Message: {error_message}")
    print(f"Traceback:\n{traceback_info}")
  return None

@app.route('/review_order/<reservedtable>', methods=['POST'])
def review_order(reservedtable):
    global TABLEID
    new_id=add_order(reservedtable,ObjectId())
    print("new order id ",new_id)
    order = []
    print(" this is the value of the table id ",reservedtable)
    get_tableid={"table_id":ObjectId(reservedtable)}
    get_tableid_details={"_id":ObjectId(reservedtable)}
    results=db.Orders.find(get_tableid).sort("datetime",-1).limit(1)
    # for result in results:
    get_orderid={"_id":ObjectId(new_id)}     
    print("the topmost result ",results)  
    documents = db.Food.find()
    print("documents", documents)
    output=None
    output = [{item: data[item] for item in data  } for data in documents]
    # print("this is the menu data", menu_data)
    total_price=0
    for item in output:
        if request.form.get(f'quantity-{item["Name"]}'):
            quantity = int(request.form.get(f'quantity-{item["Name"]}'))
        else:
            quantity=0
        if quantity > 0:
            temp={}
            temp['itemName']=item['Name']
            temp['Quantity']=int(quantity)
            temp['Price']=item['Price']
            temp['CustomerRequest']='Serve Now'
            temp['KitchenStatus']=temp['CustomerRequest']
            total_price+=item['Price']*quantity
            
            order.append(temp)
            print("THESE ARE THE ORDERS",order)
    if order:
        update_order={
            "$set":{
                # "table_id":reservedtable,
                "items":order,
                "totalPrice":round(total_price,2)
            }
        }
        try:
            sort = [("datetime", pymongo.DESCENDING)]
            documents=db.Orders.find_one_and_update(get_orderid,update_order)
            print("this is the document you are talking aboyut",documents)
            results = [{item: data[item] for item in data } for data in results]
            print("this is the update",results)    
        except Exception as ex:
            error_message = str(ex)
            traceback_info = traceback.format_exc()
            print(f"Error Message: {error_message}")
            print(f"Traceback:\n{traceback_info}")
    else:
        return render_template('cart_empty.html',reservedtable=reservedtable)    
    print("these are the orders you are talking about", order)  
    reroute=url_for('view_order',orderid=documents["_id"],reservedtable=reservedtable)
    return redirect(reroute)


@app.route('/view_order/<orderid>/<reservedtable>', methods=['GET'])
def view_order(orderid,reservedtable):
    print("im in view order")
    try:
        get_orderid={"_id":ObjectId(orderid)} 
        results=db.Orders.find_one(get_orderid)
        print(orderid)
        get_table_number={'_id':ObjectId(reservedtable)}
        
        get_table_number=db.Tables.find_one(get_table_number)
        
        return render_template('view_order.html',data=results['items'],totalprice=results['totalPrice'],reservedtable=reservedtable,orderid=orderid,tableNumber=get_table_number["tableNumber"])    
    except Exception as ex:
        print("i am in exception")
        error_message = str(ex)
        traceback_info = traceback.format_exc()
        print(f"Error Message: {error_message}")
        print(f"Traceback:\n{traceback_info}")  


@app.route('/call_waiter/<reservedtable>', methods=['GET', 'POST'])
def call_waiter(reservedtable):
    # if request.method == 'POST':
    # table_id = request.form.get('tableid')

    # Assuming you have a Tables collection with a 'calling' field
    # Update the specific table based on the provided table_id
    db.Tables.update_one({'_id': ObjectId(reservedtable)}, {'$set': {'calling': True}})

    # Redirect to a success page or home page
    # return redirect(url_for('success_page'))

    # return render_template('call_waiter.html')
    
    reroute=url_for('ongoing_order',reservedtable=reservedtable)
    return redirect(reroute)


@app.route('/bill_please/<reservedtable>', methods=['GET', 'POST'])
def bill_please(reservedtable):
    # if request.method == 'POST':
    # table_id = request.form.get('tableid')

    # Assuming you have a Tables collection with a 'calling' field
    # Update the specific table based on the provided table_id
    db.Tables.update_one({'_id': ObjectId(reservedtable)}, {'$set': {'bill': True}})

    # Redirect to a success page or home page
    # return redirect(url_for('success_page'))

    # return render_template('call_waiter.html')
    
    try:
        selected_table_id=reservedtable
        # reservedtable=reservedtable
        print("selected table id ",selected_table_id)
        selected_table_id={"_id":ObjectId(selected_table_id)}
        get_table_details=db.Tables.find_one(selected_table_id)
        orders_ordered=get_table_details["Orders"]
        orders=[]
        order_ids=[]
        serve_now_count=0
        total_price=0.0
        for item in orders_ordered:
            print("order ids in orders of tables",item)
            get_orderid={"_id":ObjectId(item)}   
            get_orders=db.Orders.find_one((get_orderid))
            if get_orders:
                # order_ids.append(get_orders["_id"])
                for food_item in get_orders["items"]:
                    # try:
                    food_item["oid"]=get_orders["_id"]
                    print("oid values aree",food_item["oid"])
                    # except Exception as ex:
                total_price+=get_orders["totalPrice"]
                orders.append(get_orders["items"])
                # serve_now_count = item('KitchenStatus')
                print("the items",orders)
        # return render_template('ongoing_order.html',data=orders)
        # results = db.Orders.find(selected_table_id)
        # waiter_needed = [{item: data[item] for item in data  } for data in results]
        # print(waiter_needed)
        for individual_order in orders:
            for order_in_individual in individual_order:
                if isinstance(order_in_individual,dict):
                    if order_in_individual.get('KitchenStatus')=='Serve Now' or order_in_individual.get('KitchenStatus')=='Preparing':
                        serve_now_count+=1
        return render_template('get_bill_customer.html',data=orders,total_cost=round(total_price,2),reservedtable=reservedtable)
    except Exception as ex:
        error_message = str(ex)
        traceback_info = traceback.format_exc()
        print(f"Error Message: {error_message}")
        print(f"Traceback:\n{traceback_info}")  



    # reroute=url_for('ongoing_order',reservedtable=reservedtable)
    # return redirect(reroute)
        
 
    
@app.route('/ongoing_order/<reservedtable>', methods=['GET'])
def ongoing_order(reservedtable):
    # Simulate fetching data from the database
    try:
        get_tableid={"_id":ObjectId(reservedtable)}
        get_table_details=db.Tables.find_one(get_tableid)
        orders_ordered=get_table_details["Orders"]
        orders=[]
        for item in orders_ordered:
            print("order ids in orders of tables",item)
            get_orderid={"_id":ObjectId(item)}   
            get_orders=db.Orders.find_one((get_orderid))
            if get_orders:
                orders.append(get_orders["items"])
                print("the items",item,get_orders["items"])
        return render_template('ongoing_order.html',data=orders,tableid=reservedtable)
    except Exception as ex:
        error_message = str(ex)
        traceback_info = traceback.format_exc()
        print(f"Error Message: {error_message}")
        print(f"Traceback:\n{traceback_info}")  

@app.route('/bill/<reservedtable>/<staffid>', methods=['GET'])
def bill(reservedtable,staffid):
    try:
        selected_table_id={"_id":ObjectId(reservedtable)}
        update_orders={
        "$set":{
            "Orders":[],
            "status":'Vaccant',
            "waiter":"Not Assigned",
            "waiterid":"",
            "calling":False,
            "bill":False
            }
        }
        # print(waiter_needed)
        db.Tables.find_one_and_update(selected_table_id,update_orders,return_document=True)
        # update_table_to_vaccant(reservedtable)
        reroute=url_for('waiter_login',staffid=staffid)
        return redirect(reroute)
        # return True
    except Exception as ex:
        error_message = str(ex)
        traceback_info = traceback.format_exc()
        print(f"Error Message: {error_message}")
        print(f"Traceback:\n{traceback_info}")  


@app.route('/waiter/<staffid>', methods=['GET'])
def waiter_login(staffid):
    try:
        # results = db.Tables.find({
        #     "$or": [
        #         {"waiterid": str(staffid)},
        #         {"waiterid": ""},
        #         {"waiterid": {"$exists": False}},
                
        #     ],
        #     "status": "Occupied"
        # })
        
        results = db.Tables.find()
        
        waiter_needed = [{item: data[item] for item in data  } for data in results]
        if not waiter_needed:
            return " EVERY TABLE IS EITHER OCCUPIED OR NO CUSTOMERS AT TABLE"
        else:
            print("waiter needed",waiter_needed)
            return render_template('waiter_needed.html',tables=waiter_needed,staffid=staffid)
    except Exception as ex:
        error_message = str(ex)
        traceback_info = traceback.format_exc()
        print(f"Error Message: {error_message}")
        print(f"Traceback:\n{traceback_info}")  

@app.route('/kitchen/<staffid>', methods=['GET'])
def kicthen_login(staffid):
    try:
        results = db.Tables.find()
        waiter_needed = [{item: data[item] for item in data  } for data in results]
        print(waiter_needed)
        if waiter_needed:
            return render_template('kitchen_needed.html',tables=waiter_needed)
        else:
            return "SORRY TO SAY !!!! TABLES ARE NOT OCCUPIED BY CUSTOMERS"
    except Exception as ex:
        error_message = str(ex)
        traceback_info = traceback.format_exc()
        print(f"Error Message: {error_message}")
        print(f"Traceback:\n{traceback_info}")  


@app.route('/customer', methods=['GET'])
def customer():
    try:
        results = db.Tables.find({"status": "Vaccant"})
        waiter_needed = [{item: data[item] for item in data  } for data in results]
        print(waiter_needed)
        return render_template('qrcode.html',tableid=waiter_needed[0]["_id"])
    except Exception as ex:
        error_message = str(ex)
        traceback_info = traceback.format_exc()
        print(f"Error Message: {error_message}")
        print(f"Traceback:\n{traceback_info}")  


@app.route('/get_bill/<reservedtable>/<staffid>', methods=['POST'])
def get_bill(reservedtable,staffid):
    try:
        selected_table_id=reservedtable
        # reservedtable=reservedtable
        print("selected table id ",selected_table_id)
        selected_table_id={"_id":ObjectId(selected_table_id)}
        get_table_details=db.Tables.find_one(selected_table_id)
        orders_ordered=get_table_details["Orders"]
        orders=[]
        order_ids=[]
        serve_now_count=0
        total_price=0.0
        for item in orders_ordered:
            print("order ids in orders of tables",item)
            get_orderid={"_id":ObjectId(item)}   
            get_orders=db.Orders.find_one((get_orderid))
            if get_orders:
                # order_ids.append(get_orders["_id"])
                for food_item in get_orders["items"]:
                    # try:
                    food_item["oid"]=get_orders["_id"]
                    print("oid values aree",food_item["oid"])
                    # except Exception as ex:
                total_price+=get_orders["totalPrice"]
                orders.append(get_orders["items"])
                # serve_now_count = item('KitchenStatus')
                print("the items",orders)
        # return render_template('ongoing_order.html',data=orders)
        # results = db.Orders.find(selected_table_id)
        # waiter_needed = [{item: data[item] for item in data  } for data in results]
        # print(waiter_needed)
        for individual_order in orders:
            for order_in_individual in individual_order:
                if isinstance(order_in_individual,dict):
                    if order_in_individual.get('KitchenStatus')=='Serve Now' or order_in_individual.get('KitchenStatus')=='Preparing':
                        serve_now_count+=1
        return render_template('get_bill.html',data=orders,total_cost=round(total_price,2),reservedtable=reservedtable,staffid=staffid)
    except Exception as ex:
        error_message = str(ex)
        traceback_info = traceback.format_exc()
        print(f"Error Message: {error_message}")
        print(f"Traceback:\n{traceback_info}")  



@app.route('/admin_panel', methods=['GET'])
def admin_panel():
    # Render the admin_panel.html template for GET requests
    return render_template('admin_panel.html')




#MODIFICATIONS TO THE TABLES


@app.route('/modify_table', methods=['POST'])
def modify_table():
    selected_action = request.form.get('tables-action')
    if selected_action == 'add-tables':
        return redirect(url_for('add_tables'))
    elif selected_action == 'delete-tables':
        return redirect(url_for('delete_tables'))
    elif selected_action == 'edit-tables':
        return redirect(url_for('edit_fetched_tables'))
    elif selected_action == 'view-tables':
        return redirect(url_for('view_tables'))
    
    # Render the admin_panel.html template for GET requests
    return render_template('admin_panel.html')


# New route to view tables
@app.route('/view-tables')
def view_tables():
    # Retrieve all tables from the database
    all_tables = db.Tables.find()
    return render_template('view_tables.html', tables=all_tables)


@app.route('/add-tables',methods=['POST','GET'])
def add_tables():
    # Add logic for handling the "Add Tables" action
    if request.method == 'POST':
        table_number = request.form.get('table-number')
        capacity = int(request.form.get('capacity'))

        # Validate the form data, you may add more validation based on your requirements

        # Insert the data into the 'Tables' collection
        db.Tables.insert_one({
            'tableNumber': table_number,
            'capacity': capacity,
            'status': 'Vaccant',  # Assuming a default status
            'waiter': 'Not Assigned',
            'Orders':[],
            'waiterid':"",# Assuming a default waiter,
            'calling':False,
            'bill':False
        })

        # Redirect to a success page or home page
        return render_template('admin_panel.html')
        
    # return render_template('add_tables.html')
    return render_template('add_tables.html')

@app.route('/delete-tables',methods=['POST','GET'])
def delete_tables():
    # Add logic for handling the "Delete Tables" action
    if request.method == 'POST':
        table_number_to_delete = request.form.get('table-number')

        # Validate the form data, you may add more validation based on your requirements

        # Delete the table based on the table number
        db.Tables.delete_one({'tableNumber': table_number_to_delete})

        # Redirect to a success page or home page
        return render_template('admin_panel.html')

    return render_template('delete_tables.html')
    # return render_template('delete_tables.html')

@app.route('/edit-fetched-tables',methods=['GET','POST'])
def edit_fetched_tables():
    if request.method=='POST':
        tableNumber=int(request.form.get('table-number'))
        get_table={'tableNumber':tableNumber}
        results=db.Tables.find_one(get_table)
        return render_template('edit_tables.html',table=results)
    return render_template('get_tables.html')

@app.route('/edit-tables',methods=['POST','GET'])
def edit_tables():
    # Add logic for handling the "Edit Tables" action
    
    if request.method=='POST':
        tableNumber=int(request.form.get('table-number'))
        updated_data = {
            'tableNumber': int(request.form.get('table-number')),
            'capacity': int(request.form.get('capacity')),
            'status': request.form.get('status'),
            'waiter': request.form.get('waiter'),
            # Add more fields as needed
        }

        # Update the table data in your database using the provided table_number
        db.Tables.update_one({'tableNumber': tableNumber}, {'$set': updated_data})

        return render_template('admin_panel.html')

    return render_template('edit_tables.html')
    
    # Update the table data in your database using the provided table_id
    # Replace this with your logic to update the table data

    # return redirect(url_for('view-tables'))
    # return render_template('edit_tables.html')

# MODIFICATIONS TO STAFF

@app.route('/modify_staff', methods=['POST'])
def modify_staff():
    selected_action = request.form.get('staff-action')
    if selected_action == 'add-satff':
        return redirect(url_for('add_staff'))
    elif selected_action == 'delete-staff':
        return redirect(url_for('delete_staff'))
    elif selected_action == 'edit-staff':
        return redirect(url_for('edit_fetched_staff'))
    elif selected_action == 'view-staff':
        return redirect(url_for('view_staff'))

    # Render the admin_panel.html template for GET requests
    return render_template('admin_panel.html')


@app.route('/view-staff', methods=['GET'])
def view_staff():
    staff_list = db.Staff.find()
    return render_template('view_staff.html', staff_list=staff_list)

# Flask API to render the add_staff.html page for adding staff
@app.route('/add-staff', methods=['GET', 'POST'])
def add_staff():
    if request.method == 'POST':
        # Retrieve form data
        new_staff_id = str(uuid.uuid4())

        username = request.form.get('username')
        password = request.form.get('password')
        phone = request.form.get('phone')
        email = request.form.get('email')
        role = request.form.get('role')

        # Create a new staff dictionary
        new_staff = {
            'username': username,
            'pswd': password,
            'phn': phone,
            'mailid': email,
            'role': role,
            "id":new_staff_id
            
            # Add more fields as needed
        }

        # Insert the new staff into the database
        db.Staff.insert_one(new_staff)

        # Redirect to the admin panel or wherever appropriate
        return render_template('admin_panel.html')

    # Render the add_staff.html template for GET requests
    return render_template('add_staff.html')

# Flask API to render the delete_staff.html page for deleting staff
@app.route('/delete-staff', methods=['POST', 'GET'])
def delete_staff():
    # Add logic for handling the "Delete Staff" action
    if request.method == 'POST':
        staff_id_to_delete = request.form.get('staff-id')

        # Validate the form data, you may add more validation based on your requirements

        # Delete the staff based on the staff ID
        db.Staff.delete_one({'id': staff_id_to_delete})

        # Redirect to a success page or staff view
        return render_template('admin_panel.html')

    return render_template('delete_staff.html')



@app.route('/edit-staff', methods=['GET', 'POST'])
def edit_staff():
    if request.method == 'POST':
        staff_id = request.form.get('staff-id')
        get_staff = {'id': staff_id}
        results = db.Staff.find_one(get_staff)
        return render_template('edit_staff.html', staff=results)
    return render_template('get_staff.html')

# Flask API to render the edit_staff.html page for editing staff
@app.route('/edit-fetched-staff', methods=['POST', 'GET'])
def edit_fetched_staff():
    if request.method == 'POST':
        staff_id = request.form.get('staff-id')
        get_staff = {'id': staff_id}
        results = db.Staff.find_one(get_staff)
        return render_template('edit_staff.html', staff=results)
    return render_template('get_staff.html')


#MODIFICATIONS TO THE TABLES

@app.route('/modify-menu', methods=['POST'])
def modify_menu():
    selected_action = request.form.get('menu-action')
    if selected_action == 'add-menu':
        return redirect(url_for('add_menu'))
    elif selected_action == 'delete-menu':
        return redirect(url_for('delete_menu'))
    elif selected_action == 'edit-menu':
        return redirect(url_for('edit_menu'))
    elif selected_action == 'view-menu':
        return redirect(url_for('view_menu'))

    # Render the admin_panel.html template for GET requests
    return render_template('admin_panel.html')

@app.route('/view-menu', methods=['GET'])
def view_menu():
    menu_list = db.Food.find()
    return render_template('view_menu.html', menu_list=menu_list)


@app.route('/edit-menu', methods=['GET','POST'])
def edit_menu():
    if request.method=='POST':
        itemName=request.form.get('item-name')
        get_menu={'Name':itemName}
        results=db.Food.find_one(get_menu)
        return render_template('edit_menu.html',menu=results)
    return render_template('get_menu.html')

# Route to handle the form submission for editing menu items
@app.route('/edit-menu-fetched-food', methods=['POST','GET'])
def edit_menu_name_fetched():
    # Add logic for handling the "Edit Menu" action
    if request.method == 'POST':
        item_name = request.form.get('item-name')
        updated_data = {
            'Name': item_name,
            'description': request.form.get('description'),
            'Price': float(request.form.get('price')),
            'imageUrl': request.form.get('image-url'),
            # Add more fields as needed
        }

        # Update the menu item data in your database using the provided item_name
        db.Food.update_one({'Name': item_name}, {'$set': updated_data})

        return render_template('admin_panel.html')

    return render_template('edit_menu.html')


@app.route('/add-menu', methods=['GET', 'POST'])
def add_menu():
    if request.method == 'POST':
        # Retrieve form data
        item_name = request.form.get('item-name')
        price = float(request.form.get('price'))
        description = request.form.get('description')
        image_url = request.form.get('image-url')
        cusineid = int(request.form.get('cuisine-id'))

        # Create a new menu item dictionary
        new_menu_item = {
            'Name': item_name,
            'Price': price,
            'description': description,
            'imageURL': image_url,
            'rating':5.0,
            'availability':'Available',
            'cusineid':cusineid
            # Add more fields as needed
        }

        # Insert the new menu item into the database
        db.Food.insert_one(new_menu_item)

        # Redirect to the menu page or wherever appropriate
        return render_template('admin_panel.html')
        
    # Render the add_menu.html template for GET requests
    return render_template('add_menu.html')


@app.route('/delete-menu', methods=['POST', 'GET'])
def delete_menu():
    # Add logic for handling the "Delete Menu" action
    if request.method == 'POST':
        item_name_to_delete = request.form.get('item-name')

        # Validate the form data, you may add more validation based on your requirements

        # Delete the menu item based on the item name
        db.Food.delete_one({'Name': item_name_to_delete})

        # Redirect to a success page or menu view
        return render_template('admin_panel.html')
        
    return render_template('delete_menu.html')

#MODIFICATIONS TO CATEGORY 


@app.route('/modify-category', methods=['POST'])
def modify_category():
    selected_action = request.form.get('category-action')
    if selected_action == 'add-category':
        return redirect(url_for('add_category'))
    elif selected_action == 'delete-category':
        return redirect(url_for('delete_category'))
    elif selected_action == 'edit-category':
        return redirect(url_for('edit_category'))
    elif selected_action == 'view-category':
        return redirect(url_for('view_categories'))


    # Render the admin_panel.html template for GET requests
    return render_template('admin_panel.html')

@app.route('/view-categories', methods=['GET'])
def view_categories():
    categories = db.Menu.find()
    return render_template('view_categories.html', categories=categories)


@app.route('/edit-category', methods=['GET', 'POST'])
def edit_category():
    if request.method == 'POST':
        category_name = request.form.get('category-name')
        get_category = {'cuisinename': category_name}
        results = db.Menu.find_one(get_category)
        return render_template('edit_category.html', category=results)
    return render_template('get_category.html')


# Route to handle the form submission for editing categories
@app.route('/edit-fetched-category', methods=['POST', 'GET'])
def edit_category_name_fetched():
    # Add logic for handling the "Edit Category" action
    if request.method == 'POST':
        category_name = request.form.get('category-name')
        updated_data = {
            'cuisinename': category_name,
            # Add more fields as needed
        }

        # Update the category data in your database using the provided category_name
        db.Menu.update_one({'Name': category_name}, {'$set': updated_data})

        return render_template('admin_panel.html')

    return render_template('edit_category.html')


@app.route('/add-category', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        # Retrieve form data
        category_name = request.form.get('category-name')
        image_url = request.form.get('category-image-url')

        # Create a new category dictionary
        new_category = {
            'cuisinename': category_name,
            'imageUrl':image_url
            # Add more fields as needed
            
        }

        # Insert the new category into the database
        db.Menu.insert_one(new_category)

        # Redirect to the admin panel or wherever appropriate
        return render_template('admin_panel.html')

    # Render the add_category.html template for GET requests
    return render_template('add_category.html')


@app.route('/delete-category', methods=['POST', 'GET'])
def delete_category():
    # Add logic for handling the "Delete Category" action
    if request.method == 'POST':
        category_name_to_delete = request.form.get('category-name')

        # Validate the form data, you may add more validation based on your requirements

        # Delete the category based on the category name
        db.Menu.delete_one({'cuisinename': category_name_to_delete})

        # Redirect to a success page or admin panel
        return render_template('admin_panel.html')

    return render_template('delete_category.html')

# MODIFICATIONS TO ORDERS

@app.route('/modify-order', methods=['POST'])
def modify_order():
    selected_action = request.form.get('order-action')
    if selected_action == 'order-action':
        return redirect(url_for('view_orders_admin'))
    # Render the admin_panel.html template for GET requests
    return render_template('admin_panel.html')


@app.route('/view-orders', methods=['GET','POST'])
def view_orders_admin():
    today = datetime.utcnow()
    start_of_day = datetime(today.year, today.month, today.day)
    end_of_day = start_of_day.replace(hour=23, minute=59, second=59)

    # Filter and sort today's orders
    today_orders = db.Orders.find({
        'datetime': {'$gte': start_of_day, '$lte': end_of_day}
    }).sort('datetime', 1)
    orders = [{item: data[item] for item in data  } for data in today_orders]

    tables=db.Tables.find()
    tables = [{item: data[item] for item in data  } for data in tables]
    
    
    return render_template('view_orders_admin.html', orders=orders,tables=tables)



@app.route('/waiter_delivery/<staffid>', methods=['POST'])
def waiter_delivery(staffid):
    try:
        selected_table_id = request.form['selected_table_id']
        print("selected table id ",selected_table_id)
        reservedtable=selected_table_id
        selected_table_id={"_id":ObjectId(selected_table_id)}
        get_table_details=db.Tables.find_one(selected_table_id)
        orders_ordered=get_table_details["Orders"]
        orders=[]
        order_ids=[]
        serve_now_count=0
        for item in orders_ordered:
            print("order ids in orders of tables",item)
            get_orderid={"_id":ObjectId(item)}   
            get_orders=db.Orders.find_one((get_orderid))
            if get_orders:
                order_ids.append(get_orders["_id"])
                orders.append(get_orders["items"])
                # serve_now_count = item('KitchenStatus')
                print("the items",item,get_orders["items"])
        # return render_template('ongoing_order.html',data=orders)
        # results = db.Orders.find(selected_table_id)
        # waiter_needed = [{item: data[item] for item in data  } for data in results]
        # print(waiter_needed)
        for individual_order in orders:
            for order_in_individual in individual_order:
                if order_in_individual.get('KitchenStatus')=='Serve Now' or order_in_individual.get('KitchenStatus')=='Preparing':
                    serve_now_count+=1
            # if individual_order['KitchenStatus'] == 'Serve Now':
                # pass
            
        # serve_now_count += sum(1 for individual_order in orders if individual_order['KitchenStatus'] == 'Serve Now')
        return render_template('waiter_delivery.html',data=orders,serve_now_count=serve_now_count,reservedtable=ObjectId(reservedtable),staffid=staffid)
    except Exception as ex:
        error_message = str(ex)
        traceback_info = traceback.format_exc()
        print(f"Error Message: {error_message}")
        print(f"Traceback:\n{traceback_info}")  

@app.route('/kitchen_delivery_form_collector', methods=['GET','POST'])
def kitchen_delivery_form_collector():
    try:
        selected_table_id = ObjectId(request.form['selected_table_id'])
        reroute=url_for('kitchen_delivery',reservedtable=selected_table_id)
        return redirect(reroute)
    except Exception as ex:
        error_message = str(ex)
        traceback_info = traceback.format_exc()
        print(f"Error Message: {error_message}")
        print(f"Traceback:\n{traceback_info}")  



@app.route('/kitchen_delivery/<reservedtable>', methods=['GET','POST'])
def kitchen_delivery(reservedtable):
    try:
        # selected_table_id = request.form['selected_table_id']
        # print("selected_table_id",selected_table_id)
        print("kicthen in dleivery",reservedtable)
        selected_table_id=reservedtable
        reservedtable=ObjectId(reservedtable)
        print("selected table id ",selected_table_id)
        selected_table_id={"_id":ObjectId(selected_table_id)}
        get_table_details=db.Tables.find_one(selected_table_id)
        orders_ordered=get_table_details["Orders"]
        orders=[]
        order_ids=[]
        serve_now_count=0
        for item in orders_ordered:
            print("order ids in orders of tables",item)
            get_orderid={"_id":ObjectId(item)}   
            get_orders=db.Orders.find_one((get_orderid))
            if get_orders:
                # order_ids.append(get_orders["_id"])
                for food_item in get_orders["items"]:
                    # try:
                    food_item["oid"]=get_orders["_id"]
                    print("oid values aree",food_item["oid"])
                    # except Exception as ex:
                orders.append(get_orders["items"])
                # serve_now_count = item('KitchenStatus')
                print("the items",orders)
        # return render_template('ongoing_order.html',data=orders)
        # results = db.Orders.find(selected_table_id)
        # waiter_needed = [{item: data[item] for item in data  } for data in results]
        # print(waiter_needed)
        for individual_order in orders:
            for order_in_individual in individual_order:
                if isinstance(order_in_individual,dict):
                    if order_in_individual.get('KitchenStatus')=='Serve Now' or order_in_individual.get('KitchenStatus')=='Preparing':
                        serve_now_count+=1
            # if individual_order['KitchenStatus'] == 'Serve Now':
                # pass
            
        # serve_now_count += sum(1 for individual_order in orders if individual_order['KitchenStatus'] == 'Serve Now')
        return render_template('kitchen_delivery.html',data=orders,serve_now_count=serve_now_count,reservedtable=reservedtable)
    except Exception as ex:
        error_message = str(ex)
        traceback_info = traceback.format_exc()
        print(f"Error Message: {error_message}")
        print(f"Traceback:\n{traceback_info}")  

    
@app.route('/food_status_modify/<reservedtable>', methods=['POST'])
def food_status_modify(reservedtable):
    get_tableid={"_id":ObjectId(reservedtable)}
    results=db.Tables.find(get_tableid)
    kitchen_action_needed = [{item: data[item] for item in data  } for data in results]
    print("kitchen action orders",kitchen_action_needed)
    for food in kitchen_action_needed:
        for order in food["Orders"]:
            get_orderid={"_id":ObjectId(order)}
            orders=db.Orders.find(get_orderid)
            if orders:
                individual_orders = [{item: data[item] for item in data  } for data in orders]
                for ind in individual_orders:
                    for item in ind["items"]:
                        print(request.form.get(f'item_name-{item["itemName"]}'),request.form.get(f'kitchen-status-{item["itemName"]}'))
                        if item.get("itemName")==request.form.get(f'item_name-{item["itemName"]}') and 'Ready'==request.form.get(f'kitchen-status-{item["itemName"]}'):
                            print("food item that is beign changed",item["itemName"])
                            item["KitchenStatus"]='Ready'
                    update_order={
                                "$set":{
                                    # "table_id":reservedtable,
                                    "items":ind["items"]
                                }
                            }
                    try:
                        sort = [("datetime", pymongo.DESCENDING)]
                        # results=results.get_json()
                        documents=db.Orders.find_one_and_update(get_orderid,update_order,return_document=True,sort=sort)
                        
                        # print(type(reservedtable))
                        # results=db.Orders.find_one(get_tableid)
                        # results = next(pymongo.CursorType, None)
                        # results=db.Tables.find(get_tableid)
                        # results = [{item: data[item] for item in data } for data in documents]
                        # print("this is the update",results)    
                    except Exception as ex:
                        error_message = str(ex)
                        traceback_info = traceback.format_exc()
                        print(f"Error Message: {error_message}")
                        print(f"Traceback:\n{traceback_info}")
        reroute=url_for('kitchen_delivery',reservedtable=reservedtable)
        return redirect(reroute)

                
        
        
        
        
        
    
    
    
    
    

    
    


@app.route('/confirm_order/<reservedtable>/<orderid>', methods=['POST'])
def confirm_order(reservedtable,orderid):
    global TABLEID
    order = []
    print(" this is the value of the table id ",reservedtable)
    get_tableid={"table_id":ObjectId(reservedtable)}
    get_tableid_details={"_id":ObjectId(reservedtable)}
    get_order_id={"_id":ObjectId(orderid)}
    results=db.Orders.find(get_order_id)
    print("the topmost result ",results)
    try:
        table_result=db.Tables.find_one(get_tableid_details)
        print("table_result",table_result)
        # table_output = table_result
        # for tables in table_result:
        get_current_orders=table_result.get("Orders")
        if get_current_orders:
            get_current_orders.append(ObjectId(orderid))
        else:
            get_current_orders=[ObjectId(orderid)]
        # for item in table_output:
        # table_result=jsonify(table_result)
        # temp_orders=table_result["Orders"]
        # if temp_orders:     
        add_order_id={
        "$set":{
            "Orders":get_current_orders,
            "status":"Occupied"
            }
        }
        # print("get order id ", get_order_id["_id"])
        print("these are the new order ids",get_current_orders)
        db.Tables.find_one_and_update(get_tableid_details,add_order_id,return_document=True)
    except Exception as ex:
        error_message = str(ex)
        traceback_info = traceback.format_exc()
        print(f"Error Message: {error_message}")
        print(f"Traceback:\n{traceback_info}")  
                    
    # menu_data = getfoodbycuisineid(request.form['cuisineid'])
    documents = db.Food.find()
    print("documents", documents)
    output=None
    output = [{item: data[item] for item in data  } for data in documents]
    # print("this is the menu data", menu_data)
    for item in output:
        print("this is an item name ",item["Name"])
        if request.form.get(f'quantity-{item["Name"]}'):
            quantity = int(request.form.get(f'quantity-{item["Name"]}'))
            print("quantity we got ",quantity,item['Name'])
        else:
            quantity=0
        if quantity > 0:
            temp={}
            temp['itemName']=item['Name']
            temp['Quantity']=int(quantity)
            temp['Price']=item['Price']*quantity
            temp['CustomerRequest']=request.form.get(f'crequest-{item["Name"]}')
            temp['KitchenStatus']='Serve Now'
            order.append(temp)
            print("THESE ARE THE ORDERS",order)
    if order:
        update_order={
            "$set":{
                # "table_id":reservedtable,
                "items":order
            }
        }
        try:
            sort = [("datetime", pymongo.DESCENDING)]
            # results=results.get_json()
            documents=db.Orders.find_one_and_update(get_order_id,update_order,return_document=True,sort=sort)
            # print(type(reservedtable))
            # results=db.Orders.find_one(get_tableid)
            # results = next(pymongo.CursorType, None)
            results = [{item: data[item] for item in data } for data in results]
            print("this is the update",results)    
        except Exception as ex:
            error_message = str(ex)
            traceback_info = traceback.format_exc()
            print(f"Error Message: {error_message}")
            print(f"Traceback:\n{traceback_info}") 
    cust_id=None
    for result in results:
        cust_id = result.get("cust_id")
    return redirect(url_for('homepage',reservedtable=reservedtable,cusineid=1))
    
    

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get the form data
        cust_name = request.form['cust_name']
        cust_pswd = request.form['cust_pswd']
        # cust_phn = request.form['cust_phn']
        # staff_role = request.form['staff_role']
        # print(cust_mail,cust_name,cust_phn)
        # tableid=update_table_to_occupied(int(table_number))
        # TABLEID=tableid
        # print("this is the table iddd..............",TABLEID)
        # g.tableid=tableid
        # set_tableid(tableid=tableid)
        try:
           get_staff_details={"username":cust_name,"pswd":cust_pswd}
           documents=db.Staff.find(get_staff_details)
           if documents:
            try:
                output = [{item: data[item] for item in data  } for data in documents ]
                print(output)
                # data=dict()
                # data['cust_name']=cust_name
                
                # data['cust_pswd']=cust_pswd
                # # data['cust_phn']=cust_phn
                # print("data", data)
                # #insert customer record
                # insert_result=db.Customer.insert_one(data)
                # inserted_id=insert_result.inserted_id
                # new_id=add_order(tableid,inserted_id)
                # response = Response("New Record added",status=201,mimetype='application/json')
                # return redirect(url_for('homepage',reservedtable=tableid))
                if output[0]["role"]=='waiter':
                    reroute=url_for('waiter_login',staffid=str(output[0]["_id"]))
                    return redirect(reroute)
                else:
                    reroute=url_for('kicthen_login',staffid=str(output[0]["_id"]))
                    return redirect(reroute)
            except Exception as ex:
                error_message = str(ex)
                traceback_info = traceback.format_exc()
                print(f"Error Message: {error_message}")
                print(f"Traceback:\n{traceback_info}")
           else:
                # add_order(tableid,documents["_id"])
                return "Incorrect username pswd or role selected"
        except Exception as ex:
            error_message = str(ex)
            traceback_info = traceback.format_exc()
            print(f"Error Message: {error_message}")
            print(f"Traceback:\n{traceback_info}")         
        # Pass the form data to the 'getcustomerdetails' route
    return render_template('staff_login.html')




@app.route('/getfood/<cusineid>/<reservedtable>', methods=['GET'])
def getfood(cusineid,reservedtable):
  try:
    # get_movie={"title":moviename}
    get_food={"cusineid":int(cusineid)}
    documents = db.Food.find(get_food)
    print("documents", documents)
    output=None
    output = [{item: data[item] for item in data  } for data in documents if data.get("cusineid")==int(cusineid)]
    print(output)
    return render_template('food.html',data=output,reservedtable=reservedtable)
    # return jsonify(output)
  except Exception as ex:
    error_message = str(ex)
    traceback_info = traceback.format_exc()
    print(f"Error Message: {error_message}")
    print(f"Traceback:\n{traceback_info}")
  return None

if __name__=="__main__":
    app.run(debug=True)

TABLEID=None