#import mysql.connector
import sqlite3

#mydb = mysql.connector.connect(
  #host="localhost" #,
  #user="yourusername",
  #password="yourpassword"
#)

#try:
  #cnx = mysql.connector.connect(user='admin',
                                #database='db.sqlite3')
#except mysql.connector.Error as err:
  #if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
    #print("Something is wrong with your user name or password")
  #elif err.errno == errorcode.ER_BAD_DB_ERROR:
    #print("Database does not exist")
  #else:
    #print(err)
#else:
  #cnx.close()

#print(mydb)


# Some code to look at the tables in the sqlite3 database db.sqlite3
#

try:
     
    # Making a connection between sqlite3 
    # database and Python Program
    sqliteConnection = sqlite3.connect('db.sqlite3')
    #sqliteConnection = sqlite3.connect('SQLite_Retrieving_data.db')
     
    # If sqlite3 makes a connection with python
    # program then it will print "Connected to SQLite"
    # Otherwise it will show errors
    print("Connected to SQLite")
 
    # Getting all tables from sqlite_master
    sql_query = """SELECT name FROM sqlite_master 
    WHERE type='table';"""
 
    # Creating cursor object using connection object
    cursor = sqliteConnection.cursor()
     
    # executing our sql query
    cursor.execute(sql_query)
    print("List of tables\n")
     
    # printing all tables list
    print(cursor.fetchall())
    
    
    
except sqlite3.Error as error:
    print("Failed to execute the above query", error)
     
finally:
   
    # Inside Finally Block, If connection is
    # open, we need to close it
    if sqliteConnection:
         
        # using close() method, we will close 
        # the connection
        sqliteConnection.close()
         
        # After closing connection object, we 
        # will print "the sqlite connection is 
        # closed"
        print("the sqlite connection is closed")
        
# Some follow on code to extract rows from known tables
#

TablesOfInterest=['custom_accounts_user', 'custom_accounts_customontologyupload', 'custom_accounts_odrlruleupload']

try:
     
    # Making a connection between sqlite3 
    # database and Python Program
    sqliteConnection = sqlite3.connect('db.sqlite3')
    
    
    
except sqlite3.Error as error:
    print("Failed to reconnect", error)

try:
    for thisTable in TablesOfInterest:
        # Creating a new cursor object using connection object
        cursor = sqliteConnection.cursor()
        sqlite_select_query = """SELECT * from custom_accounts_odrlruleupload"""
        print("THE VALUE OF THE STRING IS " + sqlite_select_query)
        sqlite_select_query = """SELECT * from """ + thisTable
        print("THE VALUE OF THE STRING IS NOW " + sqlite_select_query)
        cursor.execute(sqlite_select_query)
        records = cursor.fetchall()
        print("Total rows in " + thisTable + " are:  ", len(records))
        print("Printing each row")
        for row in records:
            for item in row:
                item_str=str(item)
                print("Row item is :" + str(item_str[0:2000]))
        
        cursor.close()
    
except sqlite3.Error as error:
    print("Failed to execute select", error)
     
finally:
   
    # Inside Finally Block, If connection is
    # open, we need to close it
    if sqliteConnection:
         
        # using close() method, we will close 
        # the connection
        sqliteConnection.close()
         
        # After closing connection object, we 
        # will print "the sqlite connection is 
        # closed"
        print("the sqlite connection is closed")


        
