##############################
# This module contains the scraper that collects various information 
# from corresponding websites. 
##############################

import urllib.request
import urllib.parse
import re
import psycopg2
from pyquery import PyQuery as pq 
import json
import aiohttp
import asyncio
from concurrent.futures import FIRST_COMPLETED

import parser 
import db

dept_dict = []
dept = []
path = ""

def SetPath(p):
    global path 
    path = p

# Helper function to Trim off whitespaces
def Trim(s):
    end = len(s)
    while end > 0:
        end-=1
        if s[end] != " ":
            break
    return s[0:end+1]

# This function invokes all neccesary functions needed to update lecture 
# information in the database to its latest state
def UpdateLecture():
    # db.OpenConnection("../../config")
    # get all lectures listed
    lectures = db.RunQuery("SELECT course_id, term FROM lectures")

    for lec in lectures:
        #get the latest info for the lecture and its discussions
        discussions = ScrapeLectureInfo(Trim(lec[1]), Trim(lec[0]))
        print(discussions[0])
        #update lecture info
        db.updateLec(Trim(lec[0]), Trim(lec[1]), discussions[0])
        #update discussions
        for dis in discussions[1:]:
            print(dis)
            db.updateDis(dis["course_id"], Trim(lec[1]), dis)
        
    db.close_connection()

# helper function to generate URL to get course info based on term and ID
def GetLectureInfoUrl(term, id):

    url = "https://sa.ucla.edu/ro/Public/SOC/Results?t="
        + term
        + "&sBy=classidnumber&id="
        + id
        + "&btnIsInIndex=btn_inIndex"

    return url

# This function will take a class_id and term, 
# and return all lectures for that class occuring in that term  
def ScrapeLectureInfo(term, id):

    url = GetLectureInfoUrl(term, id)
    # Request the webpage
    request = urllib.request.Request(url)
    response = urllib.request.urlopen(request)
    html = response.read().decode()
    #print(html)
    # Pass it into PyQuery for parsing
    query = pq(html, parser='html')
    
    # name
    name = query(".sectionColumn .cls-section p a")
    # status
    stat = query(".statusColumn p")
    stat=stat[1:]
    # waitlist
    waitlist = query(".waitlistColumn p")
    waitlist=waitlist[1:]
    # day
    day = query(".dayColumn p")
    day=day[1:]
    # time
    time = query(".timeColumn")
    time=time[1:]
    # location
    loc = query(".locationColumn")
    loc=loc[1:]
    # instructor
    inst = query(".instructorColumn")
    inst=inst[1:]
    
    lec=[]
    #process scraped info
    for i in range(0, len(name)):
        lec.append(FormatStat(  pq(name[i]).text(), 
                                pq(name[i]).attr("title"),
                                pq(stat[i]).text(), 
                                pq(waitlist[i]).text(), 
                                pq(day[i]).text(), 
                                pq(time[i]).text(), 
                                pq(loc[i]).text(),
                                pq(inst[i]).text()
                            ))
    
    return lec

# A helper function to properly format lecture/discussion info
def FormatStat(name, id, stat, waitlist, day, time, loc, inst):

    info={}
    # name
    info["sect"] = name

    # id
    id_begin=id.find("for") + 4
    info["course_id"] = id[id_begin:]
    
    # stat
    s={}
    # if this class has been closed by department
    if stat.find("Closed by") != -1:
        s["status"] = "Closed by Dept"
        s["taken"] = "n/a"
        s["cap"] = "n/a"
    #if the class is active
    else:
        new = stat.find('\n')
        tmp_stat = stat[0:new]
        s["status"] = tmp_stat
        #if there are still slots
        if tmp_stat == "Open":
            line = stat[new:]
            of = line.find("of")
            end = line.find("Enrolled")
            s["taken"] = line[1:of]
            s["cap"] = line[of+3:end-1]
        else:
            line = stat[new:]
            par = line.find("(")
            end = line.find(')')
            s["taken"] = line[par+1:end]
            s["cap"] = line[par+1:end]
    info["enrollment"] = s

    # waitlist
    w={}
    # if there is no waitlist
    if waitlist.find("No") != -1:
        w["status"] = "None"
        w["taken"] = "n/a"
        w["cap"] = "n/a"
    # if the waitlist is full
    elif waitlist.find("Full") != -1:
        w["status"] = "Full"
        par = waitlist.find("(")
        end = waitlist.find(")")
        w["taken"] = waitlist[par+1:end] 
        w["cap"] = waitlist[par+1:end] 
    # id waitlist is open
    else:
        w["status"] = "Open"
        of = waitlist.find("of")
        end = waitlist.find("Taken")
        w["taken"] = waitlist[0:of-1] 
        w["cap"] = waitlist[of+2:end-1]
    s["waitlist"] = w

    info["days"] = day

    # time
    t = {}
    # if time is listed as "varies"
    if time.find("aries") != -1:
        t["start"] = "Varies"
        t["end"] = "Varies"
    # if day was "Not scheduled"
    elif day.find("Not scheduled") != -1:
        t["start"] = "n/a"
        t["end"] = "n/a"
    # otherwise, process time as usual
    else:
        t_line_i = time.find("\n")
        time = time[t_line_i+1:]
        t_line_i = time.find("-")
        t_start = time[0:t_line_i-1]
        t_end = time[t_line_i+1:]
        t["start"] = t_start
        t["end"] = t_end

    info["time"] = t

    # location
    if len(loc) == 0:
        loc = "n/a"
    info["location"] = loc

    # instructor
    info["instructor"] = inst

    return info

# This function will access the databse for all the courses, 
# and for each of them, adds the currently offered lectures and its id to the database
def ScrapeLectures(term):
    asyncio.run(_ScrapeLectureList(term))
    #await scrapeLectureList_1(term)

async def _ScrapeLectureList(term):
    #db.open_connection(path)

    # get a list of every courses
    # for each, get the department, course number, course title, and course units
    courses = db.RunQuery("SELECT dept, course_num, course_title, course_unit FROM courses")
    pending = set()
    
    for c in courses[0:]:
        dept = Trim(c[0])
        dept_id = Trim(c[0]).replace("&", "%26")
        number = Trim(c[1])
        title=Trim(c[2]).replace(" ", "+")
        unit=Trim(c[3])
        # halt loop if thread pool is full
        while len(pending) > 200:
            # check if the tasks are finshed
            done, pending = await asyncio.wait(pending, return_when = FIRST_COMPLETED)

            for d in done:
                ids = d.result()
                for i in ids["ids"]:
                    db.addLecId(ids["dept"], ids["num"], i, term)
        
                    # Initialize info for the lecture, as well as discussions (if applicable)
                    # get the list of lecture + discussions
                    #d_list = ScrapeLectureInfo(term, i)
                    #print(d_list)
                    #we can skip the first element, as it is the lecture itself
                    # iterate through the discussions, and add it tdatabase
                    #for d in d_list[1:]:
                    #    db.addDisId(i, d["course_id"], term)
                #remove the task

           
            # i = 0
            # while i < len(pool):
            #         #print(pool[i].get_stack())
            #         #if a task is done
            #         if pool[i].done():
            #             #get the result and record it
            #             ids = pool[i].result()
            #             for i in ids:
            #                 db.addLecId(Trim(c[0]), Trim(c[1]), i, term)

            #                 # Initialize info for the lecture, as well as discussions (if applicable)
            #                 # get the list of lecture + discussions
            #                 #d_list = ScrapeLectureInfo(term, i)
            #                 #print(d_list)
            #                 #we can skip the first element, as it is the lecture itself
            #                 # iterate through the discussions, and add it tdatabase
            #                 #for d in d_list[1:]:
            #                 #    db.addDisId(i, d["course_id"], term)
            #             #remove the task
            #             pool.pop(i)
            #         else:
            #             i = i + 1
           
        # dept = Trim(c[0])
        # dept_id = Trim(c[0]).replace("&", "%26")
        # number = Trim(c[1])
        # title=Trim(c[2]).replace(" ", "+")
        # unit=Trim(c[3])

        #if number != "33":
        #    continue

        #scrape for corresponding lectures
        
        #TODO make session concurrent, not requests
        #should be easy, just swap the task with resp.text()
        pending.add(asyncio.create_task(ScrapeLectureId(term, dept, dept_id, number, title, unit)))
        #asyncio.run(pool[-1])

        
        #ids = scrapeLectureId(term, dept_id, number, title, unit)
        
        #print(ids)

        #add each id to database
        #for i in ids:
            #db.addLecId(Trim(c[0]), Trim(c[1]), i, term)

            # Initialize info for the lecture, as well as discussions (if applicable)
            # get the list of lecture + discussions
            #d_list = ScrapeLectureInfo(term, i)
            #print(d_list)
            #we can skip the first element, as it is the lecture itself
            # iterate through the discussions, and add it tdatabase
            #for d in d_list[1:]:
                #db.addDisId(i, d["course_id"], term)


    #finish up any reamaining connections
    while len(pending) > 0:
        # check if the tasks are finshed
        done, pending = await asyncio.wait(pending, return_when = FIRST_COMPLETED)

        for d in done:
            ids = d.result()
            for i in ids["ids"]:
                db.addLecId(ids["dept"], ids["num"], i, term)

    print("Finished connection")


    db.close_connection()

# Given a course and its info, this function will return a list of course id's 
# for all lectures offered for the specified term
# This function is async to improve performance

async def ScrapeLectureId(term, dept, dept_id, class_id, class_name, units):

    
    #print("created")

    #https://sa.ucla.edu/ro/Public/SOC/Results?t=
    # 20W
    # &sBy=units
    # &meet_units=4.0
    ## &sName=Computer+Science+%28COM+SCI%29
    # &subj=COM+SCI
    # &crsCatlg=M51A+-+Logic+Design+of+Digital+Systems
    # &catlg=0051A+M
    ## &cls_no=%25&btnIsInIndex=btn_inIndex"
    url = "https://sa.ucla.edu/ro/Public/SOC/Results?t="
        + term
        + "&sBy=units"
    
        + "&meet_units="
        + units

    #url+="&sName="
    #url+=dept_name
    #url+="+%28"
    #url+="%29&"
    
        + "&subj="
        + dept_id

        + "&crsCatlg="
        + class_id
        + "+-+"
        + class_name
    
    # process the catalog number
        + "&catlg="

    # if the catalog number starts with a sequence of letters it must be moved 
    # to the end of the number, seperated by a space.
    # The format is [4 digits][+ or alpha][+][front alpha (if any)]
    front_id_alpha = ""
    rear_id_alpha = ""

    if len(class_id) > 1:
        while class_id[0].isalpha():
            front_id_alpha+=class_id[0]
            class_id = class_id[1:]

        while class_id[-1].isalpha():
            rear_id_alpha=class_id[-1] + rear_id_alpha
            class_id = class_id[0:-1]
        # At this point class_id should only contain digits
        # pad 0's so there are 4 digits
        tmp_l = 4 - len(class_id)
        if tmp_l > 0:
            class_id = ("0" * tmp_l) + class_id

        # add the rear alpha back
        class_id+=rear_id_alpha

        # if there was a front alpha, pad "+" accordingly and add it to the rear
        if len(front_id_alpha) > 0:
            tmp_a = 2 - len(rear_id_alpha)
            class_id+=("+" * tmp_a)
            class_id+=front_id_alpha
        url+=class_id
    else:
        if class_id[0].isalpha():
            url+="0000" + class_id[0]
        else:
            url+="000" + class_id[0]

    #request the webpage
    #request = urllib.request.Request(url)
    #response = urllib.request.urlopen(request)

    #store the result in a string
    #html = response.read().decode()
    ids=[]
    html=""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                html = await resp.text()
                #if resp.status != 200:
                ##    print("Error featch")
                #    return ['000000000']
                #else: 
                #    html = str(r, 'utf-8')
    
    except asyncio.TimeoutError:
        print("Timeout")
        return {"dept":dept, "num":class_id, "ids":['000000000']}
    except:
        print("Error")
        return {"dept":dept, "num":class_id, "ids":['000000000']}
    
    #print(class_id)
    print(dept)
    print(class_id)
    print(url)

    #pass it into PyQuery for parsing
    query = pq(html, parser='html')

    lec_table = query(".class-not-checked")

    for lec in lec_table:
        lec_id = pq(lec).attr('id')
        id_end = lec_id.find("_")

        lec_id = lec_id[0:id_end]
        ids.append(lec_id)

    #print("completed")
    ids = {"dept":dept, "num":class_id, "ids":ids}
        
    return ids

# This function scrapes for the list of departments 
def ScrapeDept():

    print("scraping department list...")

    # The main course description page
    url="https://www.registrar.ucla.edu/Academics/Course-Descriptions"
    request = urllib.request.Request(url)
    response  = urllib.request.urlopen(request)
    html = response.read().decode()

    query = pq(html, parser='html')
    dept = []
    i = 0

    db.open_connection(path)
    dept_li = query("a[href *= '/Academics/Course-Descriptions/Course-Details?SA=']")
    # for every department that was found, record its info
    for li in dept_li:
        #get the href of the li 
        href = pq(li).attr('href')
        #get the name contained in the li
        name = pq(li).text()
        
        id_begin = href.find("?SA=")
        id_end = href.find("&")
        id = href[id_begin + 4:id_end]
        id = id.replace('%26','&')

        db.addDept("A", id, name)

    # Manually add some translatons
    # TODO this is more of a hack - get rid of this
    db.addDept("M", 'C&EE', 'Civil Engineering')
    db.addDept("M", 'EC+ENGR', 'Electrical Engineering')
    db.addDept("M", 'C&EE', 'Civil ENGR')
    db.addDept("M", 'EC+ENGR', 'Electrical ENGR')
    db.addDept("M", 'AERO+ENGR', 'Mechanical and Aerospace ENGR')
    db.addDept("M", 'CHEM', 'Chemistry')
    db.addDept("M", 'MAT+SCI', 'Materials Science')
    db.addDept("M", 'SEMITIC', 'SEMITICs')

    db.CloseConnection()

#This is the main scraper that checks all courses offered and records them in the database
def ScrapeCourses():
    
    #scrapeDept()
    db.open_connection(path)

    dept = db.query_db("SELECT dept_id, dept_name FROM departments WHERE mode = 'A'")
    dept_mapping = db.query_db("SELECT dept_id, dept_name FROM departments")

    print("scraping")
    
    #for every department
    for d in dept:

        dept_id = d[0]
        print("scraping " + d[1])

        # obtain a list of every course in that department
        dept_url="https://www.registrar.ucla.edu/Academics/Course-Descriptions/Course-Details?SA="
        # make sure to encode '&' as "%26"
        dept_url+=Trim(dept_id.replace("&", "%26"))
        dept_url+=Trim("&funsel=3")

        dept_request = urllib.request.Request(dept_url)
        dept_response  = urllib.request.urlopen(dept_request)
        print(dept_url)

        # store the result in a string
        html = dept_response.read().decode("utf-8")
        # pass it into PyQuery for parsing
        query = pq(html, parser='html')
        # query a list of courses
        course_div = query(".media-body")

        # for each course
        for i, div in enumerate(course_div, start=1):
            # retrieve description of course
            course_info = parse_desc(pq(div), dept_id, dept_mapping, i)
            print(course_info["course_num"])
            #skip if there is a class with no description
            if course_info["course_title"] == "void":
                print("skipping")
                continue
            #add it to database, skip if it already exists
            db.update_course(course_info)
    #close connection with database
    db.close_connection()

# This function takes a HTML file for a course description, parses it,
# and returns an object containing the formatted info. 

def ParseDesc(html, major="", dept=[], num = 0):

    #C = Course()
    s={}

    query = pq(html, parser='html')
    s["dept"] = major #.replace("+", "-")

    title = query("h3").text()  #find the course title

    id_end = title.find(".")    
    c_id = title[0:id_end]      #get course ID 
    
    s["course_order"] = num

    #scrape for the course id

    s["course_num"] = c_id
    #print(c_id)

    name = title[id_end + 2:]   #get course title 
    
    s["course_title"] = name.replace("'", "''")

    #scrape course units
    unit_p = query("p").eq(0).text()
    unit="" 
    unit_end = unit_p.find(":")

    #change formatting depending on whether if units are fixed or varibale
    if unit_p.find("to") != -1:
        unit2_end = unit_p.find("to")
        unit = unit_p[unit_end+2:unit2_end-1]
        #unit+=".0"
        unit+="-"
        unit+=unit_p[unit2_end+3:]
        #unit+=".0"
    elif unit_p.find("or") != -1:
        unit2_end = unit_p.find("or")
        unit = unit_p[unit_end+2:unit2_end-1]
        #unit+=".0"
        unit+="/"
        unit+=unit_p[unit2_end+3:]
        #unit+=".0"
    else:
        unit = unit_p[unit_end+2:]
        #unit+=".0"
    
    s["course_unit"] = unit

    #scrape course description
    desc_p = query("p").eq(1).text()

    #if there is a description (some courses have no description)
    if len(desc_p) > 0:

        #handle cases where description starts with a disclaimer
        if desc_p[0] == '(':
            e = desc_p.find(')')
            desc_p = desc_p[e:]

        #handle cases where description starts with another disclaimer
        if desc_p[0] == '(':
            e = desc_p.find(')')
            desc_p = desc_p[e:]

        #get the next sentence, which should state the type of the course
        type_end = desc_p.find(".")
        type_tmp = desc_p[0:type_end]

        c_type = ""

        #get the type of course
        types = ['Laboratory','Lecture','Seminar','Tutorial']
        for t in types:
            if type_tmp.find(t) != -1:
                c_type = t

        s["course_type"] = c_type

       

        desc_p = desc_p[type_end+1:]
        
        #find the sentence that has the requisites
        req_begin = desc_p.find("equisites: ")
        if req_begin == -1:
            req_begin = desc_p.find("equisite: ")
            if req_begin != -1:
                req_begin = req_begin + 11
        else:
            req_begin = req_begin + 12

        #call parser if there is a requisite
        if req_begin != -1:
            
            #req_tmp = desc_p[req_begin + 11:]
            req_end = desc_p.find(".")
            """
            ====PREREQ PARSER DISBALED FOR NOW======
            result = parser.parseReq(req_tmp[0:req_end], major, dept)
            
            if result == []:
                print(c_id)
                print(req_tmp[0:req_end])
                print(parser.tokenizeReq(req_tmp[0:req_end], dept))
                print("Req parsing error:\t" + c_id)

            s["course_req"] = parser.formatList(result)
            desc_p = desc_p[req_end+2:]
            """
            s["course_req"] = "pending"

            

        else:
            s["course_req"] = "none"
            #s+=","
        

        #get the last sentence, which contains info about the grading scheme
        #iterate backwards from the end to find the second last period
        itr = 2
        while len(desc_p) - itr >= 0 and desc_p[len(desc_p) - itr] != '.':
            itr = itr + 1

        grading_p = desc_p[len(desc_p) - itr + 1:]
        scheme=""

        if grading_p.find("etter") != -1:
            scheme+="L" 
        if grading_p.find("P/NP") != -1:
            scheme+="P" 
        if grading_p.find("S/U") != -1:
            scheme+="S" 
        
        s["course_grade"] = scheme

        desc_tmp = desc_p[0:len(desc_p) - itr + 1]
        desc_tmp = desc_tmp.replace("'", "''")
        

        s["course_desc"] = desc_tmp

    else:
        s["course_title"] = "void"

    return s
