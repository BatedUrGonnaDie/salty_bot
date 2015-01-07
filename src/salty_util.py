import os
import json
import psycopg2 as pg
import psycopg2.extras as pge
import urlparse
from datetime import datetime

class db_connection:
    #Class to handle interactions with the DB itself
    #Variable members
    connected = False
    url = None
    connection = None
    cursor = None
    lastReturn = None

    #python methods
    def __init__(self):
        urlparse.uses_netloc.append("postgres")
        self.url = urlparse.urlparse("")
        self.connect()

    def __del__(self):
        self.disconnect()

    def __enter__(self):
        if not self.connected:
            self.connect()

        return self

    def __exit__(self, type_error, value, traceback):
        if value == None:
            self.commit_changes()
            return True
        else:
            self.rollback_changes()
            print type_error, value, traceback
            return False

    #Public methods
    def connect(self):
        if not self.connected:
            try:
                self.connection = pg.connect(
                    database=self.url.path[1:],
                    user=self.url.username,
                    password=self.url.password,
                    host=self.url.hostname,
                    port=self.url.port
                )
                self.cursor = self.connection.cursor()
                self.connected = True
            except:
                pass      

    def disconnect(self):
        self.cursor.close()
        self.connection.close()
        self.connected = False

    def commit_changes(self):
        self.connection.commit()

    def rollback_changes(self):
        self.connection.rollback()

    def get_cursor(self, with_statment_init = None):
        if not self.connected:
            self.connect()

        return salty_cursor(self, with_statment_init)

class salty_cursor:
    #Extended cursor class for saltybot
    #Constant members
    salty_db_link = None
    cursor_link = None

    #Variable members
    last_query = None

    #With statment members
    execute_param_pack = ()
    #Python methods
    def __init__(self, db_link, pack = None):
        self.salty_db_link = db_link
        self.cursor_link = self.salty_db_link.connection.cursor(cursor_factory=pge.RealDictCursor)

        #prepare for with statment initialization. 
        if pack:
            self.execute_param_pack = pack
             

    def __del__(self):
        self.cursor_link.close()

    def __enter__(self):
        if isinstance(self.execute_param_pack, str):
            query_string = self.execute_param_pack
            params = None

        else:
            query_string, params = self.execute_param_pack


        print self.execute_param_pack
        print self.execute(query_string, params)
        return self

    def __exit__(self, type_error, value, traceback):
        if not type_error:
            self.cursor_link.close()
            return True

        else:
            print type_error, value, traceback
            return False

    #Public methods
    def log(self):
        tmp = self.last_query

        self.last_query = self.cursor_link.query

        return tmp

    def execute(self, query_string, params = None):
        if params:
            self.cursor_link.execute(query_string, params)
            self.log()
            return self.cursor_link.statusmessage

        self.cursor_link.execute(query_string)
        self.log()
        return self.cursor_link.statusmessage

    def execute_many(self, query_string, param_list):
        self.cursor_link.executemany(query_string, param_list)
        self.log()
        return 

    def get(self, Amount = 1):
        if Amount == 1:
            return self.cursor_link.fetchone()

        elif Amount > 1:
            return self.cursor_link.fetchmany(Amount)

        else:
            return None

    def get_all(self, is_iterator = False):
        #Plese please only use thie is iterator inside a for loop call
        if is_iterator:
            return self.cursor_link

        else:
            return self.cursor_link.fetchall()

class textutils:
    #Class is intended to be used to send things into the textutils table
    #Constant members
    TABLE_NAME = "textutils"
    DB_LINK = None
    #Variable members
    cursor = False

    #Python methods
    def __init__(self, db_connection_obj):
        #start up method
        self.DB_LINK = db_connection_obj
        ## Cursor object for sending querys to the DB table
        self.cursor = self.DB_LINK.get_cursor
        self.q_cursor = self.DB_LINK.get_cursor()

    def __del__(self):
        #clean up method
        #Cursor cleans up itself in it's __del__ method, Need input on if I should explicity delete the object
        del self.cursor #Anyway this cleans up the cursor
        
    #Public methods
    def send_dict(self, txt_obj):
        if "twitch_name" in txt_obj and "user_id" not in txt_obj:
            print "Looking up twitch name..."
            txt_obj["user_id"] = self.get_user_id(txt_obj["twitch_name"])

            if txt_obj["user_id"] > 0:
                print "found user \"{}\" with \"user_id\": {}".format(txt_obj["twitch_name"], txt_obj["user_id"])

            else:
                print "[Error] user \"{}\" not found".format(txt_obj["twitch_name"])

        #print txt_obj Debug call

        return self.send(txt_obj["user_id"], txt_obj["type"], txt_obj["reviewed"], txt_obj["text"], txt_obj["created_at"], txt_obj["updated_at"])

    def send(self, _user_id, text_type, is_reviewed, _text, creation_time, update_time):
        if text_type not in ["Quote", "Pun"]:
            raise NameError("Text type must be either \"Quote\" or \"Pun\"")
            

        query_string = """INSERT INTO {_TABLE_NAME}(user_id, type, reviewed, text, created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s)
        """.format(_TABLE_NAME=self.TABLE_NAME)
        
        return self.q_cursor.execute(query_string, (_user_id, text_type, is_reviewed, _text, creation_time, update_time))
        
    def get_user_id(self, twitch_name):
        #TODO
        print self.cursor.execute("""SELECT id FROM users WHERE twitch_name==%s""", (twitch_name))
        return self.cursor.get_all()

    #Contant utilites section
    ##I made this function to add quotes to the DB if it gets cleared by accadent or on purpose (from files)
    def INSERT_ALL_QUOTES(self):
        ##Temporary
        files_directory_location = "../textutils/"
        totalUserDict = {}

        with self.cursor("""SELECT twitch_name, id FROM users ORDER BY id ASC""") as users_request:

            for user in users_request.get_all(True):
                print user["twitch_name"],"ID is :",user["id"]

                for text_type in ["quote", "pun"]:
                    for switch in ["", "_review"]:
                        try:
                            with open(files_directory_location+"{user}_{type}{review_switch}.txt".format(user=user["twitch_name"], type=text_type, review_switch=switch)) as fin:
                                #print fin Debug print
                                for text_line in fin:
                                    user_dict = {
                                        'user_id'    : user["id"],
                                        'type'       : text_type.title(),
                                        'reviewed'   : (True if switch == "" else False),
                                        'text'       : unicode(text_line[:-1], errors="ignore"),
                                        'created_at' : datetime.utcnow(),
                                        'updated_at' : datetime.utcnow()
                                    }

                                    #print user_dict
                                    print self.send_dict(user_dict)

                        except IOError, e:
                            print e.filename, "failed to open...\nContinuing...\n"

        self.DB_LINK.commit_changes()
                    
    def READ_ALL_QUOTES(self, twitch_name = None, format = None, write_to_file=False):
        files_directory_location = "../JSON_DOCS/"

        tmp = self.cursor()
        tmp.execute("SELECT * FROM textutils")

        if write_to_file:
            with open(files_directory_location+"textutils.json", 'w') as fout:
                fout.write(json.dumps(tmp.get_all(), default=str))

        else:
            for i in tmp.get_all(True):
                print i
                print

def insertAllQuotes():
    TotalJsonDict = {}

    listOfUsers = dbcon.getall("""SELECT twitch_name, id FROM users""")

    for user in listOfUsers:
        try:
            print  "Printing for", user["twitch_name"]

            for mtype,ztype,tftype in zip(["quote","quote_review","pun","pun_review"],["Quote","Quote","Pun","Pun"],[True,False,True,False]):
                usertext = []
                for line in open("../textutils/{}_{}.txt".format(user["twitch_name"], mtype)):
                    
                    user_dict = {
                        'user_name' : user["twitch_name"],
                        'user_id' : user['id'],
                        'type' : ztype,
                        'reviewed' : tftype,
                        'text' : unicode(line[:-2], errors='ignore'),
                        'created_at' : datetime.utcnow(),
                        'updated_at' : datetime.utcnow()
                    }
                    print "{user_name}".format(user_name = user_dict["user_name"])
                    
                    usertext.append(user_dict)
                    table.send_dict(user_dict)


                    #dbcon.cursor.execute("""INSERT INTO quotes(user_id, type, reviewed, text, created_at, updated_at) VALUES(%s,%s,%s,%s,%s,%s)""",
                    #with open('tmp.txt','w') as fout:
                    #    fout.write(str(user['id'], ztype, tftype, unicode(line[:-2], errors='ignore'), datetime.utcnow(),datetime.utcnow()))
                TotalJsonDict[user['twitch_name']] = usertext
        except IOError, e:
            print "Error [",e,"]"
    with open('tmp.json', 'w') as fout:
        fout.write(json.dumps(TotalJsonDict, default=str, indent = 4))
    
main_connection = db_connection()
textTable = textutils(main_connection)
