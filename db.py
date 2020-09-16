##############################
# This module is the interface between the applicaton and database. 
# It allows programs to interact with the database without worrying about 
# details of SQL and connection management.  
##############################

import psycopg2
import json

import os
from dotenv import load_dotenv

# https://brandur.org/postgres-connections

connection = None
cursor = None

class DbCtx:
    def __init__(self):
        self.usr = "" 
        self.passwd = ""
        self.host = ""
        self.port = ""
        self.database = ""

        self.connection = None
        self.curcor = None

    def InitDb(self):
        self._OpenConnection()
    
    def DelDb(self):
        self._CloseConnection()

    # Initializes the tables in the database
    # Make sure there are no tables in the database when running this, otherwise the 
    # function will return an error
    #def RunSql(path):

    # Provided a path to the config file, opens a connection to the database using the 
    # provided configurations
    # Config files should be a text file containing the:
    #   database username
    #   password
    #   IP address
    #   port number
    #   database name
    # in each line 
    def _OpenConnection(self, path="config.env"):
        load_dotenv(verbose=True)
        load_dotenv(path)

        self.usr =       os.environ.get("DB_USR")
        self.passwd =    os.environ.get("DB_PASSWD")
        self.host =      os.environ.get("DB_IP")
        self.port =      os.environ.get("DB_PORT")
        self.database =  os.environ.get("DB_NAME")

        print("Establishing connection with database")
        connection = psycopg2.connect(  user = self.usr,
                                        password = self.passwd,
                                        host = self.host,
                                        port = self.port,
                                        database = self.database)
        # For now assume one cursor per connection
        cursor = connection.cursor()
        print("Established")

    # Closes connection with the database 
    def _CloseConnection(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()
        else:
            print("No open connections")

    # Queries the database, provided a command as a string
    def RunQuery(self, q):
        self.cursor.execute(q)
        result = self.cursor.fetchall()
        self.connection.commit()

        return result

    # Adds a department to the table
    # Ignored if department already exists
    def AddDept(self, mode, dept_id, dept_name):

        result = self.RunQuery("SELECT * FROM departments WHERE dept_name='" + dept_name + "';")

        if len(result) == 0:
            command = "INSERT INTO departments "
                    + "VALUES ("
                    + "'" + mode + "', "
                    + "'" + dept_id + "', "
                    + "'" + dept_name + "') "
                    + "ON CONFLICT (dept_id) DO NOTHING;"
            self.cursor.execute(command)
            self.connection.commit()

    # Given information regarding a course, updates its information in the table
    # If the course does not exist yet, it will be newly created
    def UpdateCourse(course):
        #check if course exists in db
        # chk = "SELECT course_order FROM courses WHERE dept='" + course["dept"] + "' AND course_num='" + course["course_num"] + "';"
        # cursor.execute(chk)
        # result = cursor.fetchall()

        command = """
                INSERT INTO courses
                (
                    dept_id,
                    course_order,
                    course_num,
                    course_title,
                    course_unit_t,
                    course_unit_s,
                    course_unit_e,
                    course_type,
                    course_req,
                    course_grade,
                    course_desc
                )
                VALUES (
                    '{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '{8}', '{9}', '{10}'
                )
                ON CONFLICT (dept_id, course_num, course_title)
                DO UPDATE SET
                    course_order = '{1}'
                    course_unit_t = {4},
                    course_unit_s = {5},
                    course_unit_e = {6},
                    course_type = {7},
                    course_req = {8},
                    course_grade = {9},
                    course_desc = {10}
                WHERE
                    dept_id = {0},
                    course_num = {2},
                    course_title = {3}
                ;
                """.format(
                    course["dept"], 
                    str(course["course_order"]), 
                    course["course_num"], 
                    course["course_title"], 
                    course["course_unit_t"], 
                    course["course_unit_s"], 
                    course["course_unit_e"], 
                    course["course_type"], 
                    json.dumps(course["course_req"]), 
                    course["course_grade"], 
                    course["course_desc"],
                )
                        
        # # if course exist, update it
        # else:
        #     command = "UPDATE courses "
        #     command+= "SET "
        #     command+= "course_order = " + str(result[0][0]) + ", "
        #     command+= "course_num = '" + course["course_num"] + "', "
        #     command+= "course_title = '" + course["course_title"] + "', "
        #     command+= "course_unit = '" + course["course_unit"] + "', "
        #     command+= "course_type='" + course["course_type"] + "', "
        #     command+= "course_req='" + json.dumps(course["course_req"]) + "', "
        #     command+= "course_grade='" + course["course_grade"] + "', "
        #     command+= "course_desc='" + course["course_desc"] + "'" 
        #     command+= "WHERE dept='" + course["dept"] + "' AND course_num='" + course["course_num"] + "';"

        cursor.execute(command)
        connection.commit()

# =======================
# Given an id and term for a lecture, adds it to the table if it does not exist yet
# =======================

def addLecId(dept, num, id, term):

    result = query_db("SELECT * FROM lectures WHERE course_id='" + id + "' AND term = '" + term + "';")

    if len(result) == 0:
        command = "INSERT INTO lectures (dept, course_num, course_id, term)"
        command+="VALUES ("
        command+="'" + dept + "', "
        command+="'" + num + "', "
        command+="'" + id + "', "
        command+="'" + term + "'); "
        cursor.execute(command)
        connection.commit()

# =======================
# Given an id and term for a lecture, adds it to the table if it does not exist yet
# =======================

def addDisId(lec_id, id, term):

    result = query_db("SELECT * FROM discussions WHERE course_id='" + id + "' AND term = '" + term + "';")

    if len(result) == 0:
        command = "INSERT INTO discussions (lec_id, course_id, term)"
        command+="VALUES ("
        command+="'" + lec_id + "', "
        command+="'" + id + "', "
        command+="'" + term + "'); "
        cursor.execute(command)
        connection.commit()

# =======================
# Given an id and term for a lecture, adds it and its information to the table
# This function assumes the lecture record already exists
# =======================

def updateLec(id, term, lec):

    command = "UPDATE lectures "
    command+= "SET "
    command+= "lec_name = '" + lec["sect"] + "', "
    command+= "lec_status = '" + lec["enrollment"]["status"] + "', "
    command+= "lec_capacity = '" + json.dumps(lec["enrollment"]) + "', "
    command+= "lec_w_status ='" + lec["enrollment"]["waitlist"]["status"] + "', "
    command+= "lec_w_capacity ='" + json.dumps(lec["enrollment"]["waitlist"]) + "', "
    command+= "lec_day='" + lec["days"] + "', "
    command+= "lec_time_s='" + lec["time"]["start"] + "',"
    command+= "lec_time_e='" + lec["time"]["end"] + "'," 
    command+= "lec_location='" + lec["location"] + "'," 
    command+= "lec_inst='" + lec["instructor"] + "'"  
    command+= "WHERE course_id='" + id + "' AND term='" +term + "';"

    cursor.execute(command)
    connection.commit()

# =======================
# Given an id and term for a discussion, adds it to the table if it does not exist yet
# =======================

def updateDis(id, term, lec):

    command = "UPDATE discussions "
    command+= "SET "
    command+= "dis_name = '" + lec["sect"] + "', "
    command+= "dis_status = '" + lec["enrollment"]["status"] + "', "
    command+= "dis_capacity = '" + json.dumps(lec["enrollment"]) + "', "
    command+= "dis_w_status ='" + lec["enrollment"]["waitlist"]["status"] + "', "
    command+= "dis_w_capacity ='" + json.dumps(lec["enrollment"]["waitlist"]) + "', "
    command+= "dis_day='" + lec["days"] + "', "
    command+= "dis_time_s='" + lec["time"]["start"] + "',"
    command+= "dis_time_e='" + lec["time"]["end"] + "'," 
    command+= "dis_location='" + lec["location"] + "'," 
    command+= "dis_inst='" + lec["instructor"] + "'"  
    command+= "WHERE course_id='" + id + "' AND term='" +term + "';"

    cursor.execute(command)
    connection.commit()

##########################
# Below are functions to retrieve data from the database in meaningful ways
##########################
# =======================
# Given two course names, returns all courses that exists between them
# example:
#   (MATH 31A, MATH 32B) => [MATH 31A, MATH 31B, MATH 32A, MATH 32B]  
# =======================

def get_course_range(start, end):

    #seperate courses 
    tmp_s = start.split()
    start_dept = tmp_s[0]
    start_num = tmp_s[1]

    tmp_e = end.split()
    end_dept = tmp_e[0]
    end_num = tmp_e[1]

    #check the index number of start course
    chk = "SELECT course_order FROM courses WHERE dept='" + start_dept + "' AND course_num='" + start_num + "';"
    cursor.execute(chk)
    result = cursor.fetchall()
    #print(result)
    start_num = result[0][0]

    #check the index number of end course
    chk = "SELECT course_order FROM courses WHERE dept='" + end_dept + "' AND course_num='" + end_num + "';"
    cursor.execute(chk)
    result = cursor.fetchall()
    #print(result)
    if len(result) == 0:
        print("error")
        return []
    end_num = result[0][0]
    #print(end_num)

    #get course in that range
    chk = "SELECT dept, course_num FROM courses WHERE dept='" + start_dept + "' AND course_order BETWEEN " + str(start_num) + " AND " + str(end_num) + ";"
    cursor.execute(chk)
    result = cursor.fetchall()

    response = []

    for r in result:
        response.append((trim(r[0]) + " " + trim(r[1])))

    return response


# =======================
# Given two course names, returns all courses that exists between them
# example:
#   (MATH 31A, MATH 32B) => [MATH 31A, MATH 31B, MATH 32A, MATH 32B]  
# =======================

def get_course_level(dept, level):


    #check the index number of start course
    chk = "SELECT dept, course_num FROM courses WHERE dept='" + dept + "';"
    cursor.execute(chk)
    result = cursor.fetchall()
    #print(result)

    num_min = 0
    num_max = 0

    if level =="upperdiv":
        num_min = 100
        num_max = 199

    response = []
    
    for res in result:
        number = int(trim_nondigit(res[1]))
        if number >= num_min and number <= num_max:
            response.append(trim(res[0]) + " " + trim(res[1]))

    return response

#helper function to trim off nondigits and whitespaces
def trim_nondigit(s):
    while not s[-1].isdigit():
        s = s[0:-1]
    while not s[0].isdigit():
        s = s[1:]

    return s

#helper function to trim off whitespaces
def trim(s):
    while s[-1] == " ":
        s = s[0:-1]
    return s



