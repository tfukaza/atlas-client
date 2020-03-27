
import json
import parser 
import tool
import re 
import yaml

class Agent:
    def __init__(self, name):
        self.req = []         # list of required courses/agents
        #self.taken = []         # list of completed courses
        #self.chk = None        # function to evaluate requirement (leaf only)

        #self.unit = 0           # number of taken units  
        #self.course = 0         # number of taken courses
        self.rules=[]
        self.name = name
        self.rules = []

        self.upd = None          # function to update above status


class OptAgent:
    def __init__(self, name):
        #self.agent = []         # list of required courses/agents
        #self.root_agent = []
        #self.rules = []
        self.options = [] #["", [], [], []] 
        self.name = name
       
        self.upd = None          # function to update above status

# Root agents are agents that have customized functions to evaluate major progress
# Unlike leaf agents, which operate on course, root agents operate on leaf agents

class RootAgent:
    def __init__(self, name):
        self.ref = []
        self.rules = []
        self.isClosed = False

        self.upd = None          # function to update status
        self.name = name

class RuleAgent:
    def __init__(self, name):
        self.ref = []           #list of parameters
        self.name = name



def rec_print(result, depth = 0):

    print("".join(["\t" * depth]), end=" ")
    print("REQ:")

    for r in result:

        print("".join(["\t" * depth]), end=" ")
        print("Agent: " + r.name)


        if isinstance(r, OptAgent):
            print("".join(["\t" * depth]), end=" ")
            print("OPT: " + r.name)
            #depth = depth + 1
            for o in r.options:
                print("".join(["\t" * depth]), end=" ")
                print("option: " + o[0])
                rec_print(o[1], depth + 1)
                print("".join(["\t" * depth]), end=" ")
                grp_print(o[2], depth + 1)
        else:
            #print("".join(["\t" * depth]), end=" ")
            #print("param: " + r.name)
            for rule in r.rules:
                print("".join(["\t" * depth]), end=" ")
                print(rule.name)
                print("".join(["\t" * depth]), end=" ")
                print(rule.ref)
            print("".join(["\t" * depth]), end=" ")
            print(r.req)
            print("".join(["\t" * depth]), end=" ")
            print(r.chk)
            print("".join(["\t" * depth]), end=" ")
            print(r.upd)
        
        print("".join(["\t" * depth]), end=" ")
        print("---")

def grp_print(result, depth = 0):

    for g in result:
        print("".join(["\t" * depth]), end=" ")
        print("GROUP: " + g.name)
        for r in g.ref:
            print("".join(["\t" * depth]), end=" ")
            print("ref:" + r)

def parse(path, cred):

    indent = 0
    pre_indent = 0

    parser.build_mapping(cred)

    with open(path + "/req.yml","r") as file:

      
        req = yaml.safe_load(file)
       
        result = parse_req_yml(req["master"], "")

        # with open("req.js","w") as output:
        #     parse_write(output, result)
        
        with open(path + "/req.json","w") as output:
            parse_write_json(output, result)

        with open(path + "/desc.json","w") as output:
            list_of_req = parse_req_yml_json(req["master"], "")
            map_of_req = {}
            map_of_req["master"] = list_of_req  
            output.write(json.dumps(map_of_req, indent=4))

        
        # with open("req.html","w") as output:
        #     output.write(""" 
        #         <!DOCTYPE html>
        #         <html>
        #         <body>

        #         <form>
        #         Courses: <textarea id="list" type="text" name="courses"></textarea>
        #         <button type="button" onclick="chkProgress()">Submit</button>
        #         </form>            
        #     """)
        #     output.write(result[4])
        #     output.write(""" 
        #         </body>
        #         </html>
        #         <style>
        #             div{
        #                 background-color: aqua;
        #                 border: red 1px solid;
        #                 padding:10px;
        #             }
        #             .done{
        #                 background-color: green;
        #             }
        #             .hide{
        #                 display:none;
        #             }
        #         </style>
        #         <script src = "../scrape.js"></script>
        #         <script src = "../atlasAudit.js"></script>
        #         <script src = "comsci.js"></script>
        #         <script src = "../checkProgress.js"></script>
        #     """)
        #     output.write("""
        #         <script>
        #         function select_opt(element, value){
                
        #             let e = element.parentNode.firstChild;
        #             do{
        #                 if (e.classList.contains(value)){
        #                     e.classList.remove("hide");
        #                 }
        #                 else if (!e.classList.contains("sel")){
        #                     e.classList.add("hide");
        #                 }
        #             }
        #             while(e = e.nextSibling)

        #         }
        #         </script>
        #         """)



def parse_req_yml_json(req, req_name):

    req_list = []
    #group = []
    l = 0
    print(req)
    for item in req:
        
        #GROUP
        if "GROUP" in item:

            tmp_map = {}
            tmp_map["type"] = "GROUP"
            name = item["GROUP"]
            
            if name == "_":
                name = req_name + "_" + str(l)
                l+=1
            else:
                name = name

            tmp_map["name"] = name

            req_list.append(tmp_map)
           
        #REQ
        elif "REQ" in item:
            
            tmp_map = {}
            tmp_map["type"] = "REQ"
            name = item["REQ"]
            
            if name == "_":
                name = req_name + "_" + str(l)
                l+=1
            else:
                name = name

            tmp_map["name"] = name
            tmp_map["course"] = str(item["course"])

            # check if there is a rule
            # These will be rules binded to agents
            if "rules" in item:
                tmp_map["rules"] = item["rules"]
        
            req_list.append(tmp_map)

        #OPT
        elif "OPT" in item:

            tmp_map = {}
            tmp_map["type"] = "OPT"
            name = item["OPT"]
            
            if name == "_":
                name = req_name + "_" + str(l)
                l+=1
            else:
                name = name

            tmp_map["name"] = name
            
            # create list used to generate drop-down menu
            selection_list = []

            for o in item["options"]: 
                selection_list.append(o["option"])

            tmp_map["selections"] = selection_list
                
            option_list = []

            for o in item["options"]: 
                opt_map = {}

                opt_map["option"] = o["option"]
                opt_map["content"] = parse_req_yml_json(o["content"], name)

                option_list.append(opt_map)
            
            tmp_map["options"] = option_list

            req_list.append(tmp_map)
            
        # Rules not in REQ must be global
        # elif "RULE" in item:
            
        #     name = item["RULE"]
            
        #     #rules in <expression> mst be global
        #     #add the rule to the rule list
        #     rule_buffer.append(RuleAgent(name))

        #     html+="<div class=\"rule " + name + "\">" 
            
        #     #state="rule-global"
        #     #l = l + 1
        #     #check each key/value pair
        #     for param in item: 
                
        #         if param == "course" or param == "A" or param == "B":
        #             #Rules almost always refer to course. Find them out. 
        #             #Obtain the value of the keys
        #             line = item[param]
        #             req_list = []
        #             if isinstance(line, list):
        #                 #convert it to an object 
        #                 req_list = line
        #             elif line[0] == "$":
        #                 req_list = [line]

        #             rule_buffer[-1].ref = req_list
    
        #     html+="</div>" 
        
   
    return req_list


# def parse_req(req, l, state, req_name):

#     html=""

#     root_buffer = []
#     agent_buffer = []
#     rule_buffer = []
#     #group = []
    
#     while l < len(req):
        

    
#         line = req[l]

#         #print(line)
#         #print(state)

#         #check and consume the indentation 
#         indent = 0

#         while line[0] == "\t":
#             line=line[1:]
#             indent = indent + 1
#         #print(indent)
        
#         length = len(line)

#         if line[0] == "!":
#             break
        
#         if state == "expression":
            
#             #GROUP
#             if length > 2 and line[0] == "G" and line[1] == "R" and line[2] == "O":
#                 line = line[7:]

#                 #consume whitespace
#                 while line[0] == " " or line[0] == "\t":
#                     line = line[1:]
                
#                 name = trim_nonalpha(line)

#                 if name[0:5] == "$anon":
#                     name = name.split("?")
#                     if len(name) > 1:
#                         req_name = req_name + "." + name[1]
#                     else:
#                         req_name = req_name
#                 else:
#                     req_name = name

#                 html+="<div class=\"group " + req_name + "\">" 
#                 html+="<h3>" + req_name + "</h3>" 
#                 # Add another option 
#                 # By syntax this must be an instance of OptAgent 
#                 root_buffer.append(RootAgent(req_name))
#                 l = l + 1
#                 state = "group"

#                 continue
            
#             #REQ
#             elif length > 2 and line[0] == "R" and line[1] == "E" and line[2] == "Q":
                
#                 line = line[4:]
#                 #consume whitespace
#                 while line[0] == " " or line[0] == "\t":
#                     line = line[1:]
                
#                 name = trim_nonalpha(line)

                
#                 if name[0:5] == "$anon":
#                     name = name.split("?")
#                     if len(name) > 1:
#                         name = req_name + "." + name[1]
#                     else:
#                         name = req_name

#                 html+="<div class=\"req " + name + "\">" 
#                 html+="<h3>" + name + "</h3>" 
               

#                 #If there is already a group in the buffer, add this req to its reference list 
#                 if len(root_buffer) > 0 and root_buffer[-1].isClosed == False:
#                     root_buffer[-1].ref.append(name)
                
#                 #add this to buffer
#                 agent_buffer.append(Agent(name))

#                 state = "req"
#                 l = l + 1
#                 continue
            
#             #OPT
#             elif length > 2 and line[0] == "O" and line[1] == "P" and line[2] == "T":
                
#                 line = line[4:]
#                 #consume whitespace
#                 while line[0] == " " or line[0] == "\t":
#                     line = line[1:]
                
#                 name = trim_nonalpha(line)

#                 if name[0:5] == "$anon":
#                     name = name.split("?")
#                     if len(name) > 1:
#                         req_name = req_name + "." + name[1]
#                     else:
#                         req_name = req_name
#                 else:
#                     req_name = name

#                 html+="<div class=\"opt " + req_name + "\">" 
#                 html+="<h3>" + req_name + "</h3>" 
                

#                 #If there is already a group in the buffer, add this req to its reference list 
#                 if len(root_buffer) > 0 and root_buffer[-1].isClosed == False:
#                     root_buffer[-1].ref.append(req_name)
                
#                 #add this to buffer
#                 agent_buffer.append(OptAgent(req_name))

#                 state = "OPT"
#                 l = l + 1
#                 continue

#             #RULE
#             elif length > 2 and line[0] == "R" and line[1] == "U" and line[2] == "L":
                
#                 s = line.split()
#                 name = s[1]
                
#                 #rules in <expression> mst be global
#                 #add the rule to the rule list
#                 rule_buffer.append(RuleAgent(name))

#                 html+="<div class=\"rule " + name + "\">" 
                
#                 state="rule-global"
#                 l = l + 1
#                 continue


#             #/option
#             elif length > 2 and line[0] == "/" and line[1] == "o" and line[2] == "p":
#                 #html+="</div>"
#                 state = "opt"
#                 l = l + 1
#                 return [agent_buffer, root_buffer, rule_buffer, l, html]
            
#             elif length > 2 and line[0] == "/" and line[1] == "g" and line[2] == "r":
#                 state = "group"
#                 l = l + 1
#                 return [agent_buffer, root_buffer, rule_buffer, l, html]
            
#             else:
#                 l = l + 1
#                 continue
            
#         elif state == "req":

#             #course param
#             if length > 2 and line[0] == "c" and line[1] == "o" and line[2] == "u":
#                 line = line[7:]

#                 #consume whitespace
#                 while line[0] == " " or line[0] == "\t":
#                     line = line[1:]
    
                
#                 html+="<p>" + str(line) + "</p>" 

#                 req_list = []
#                 #if the courses are already parsed
#                 if line[0] == "[":
#                     #convert it to an object 
#                     req_list = tool.string2list(trim_nonalpha(line))
#                 elif line[0] == "%":
#                     req_list = [trim_nonalpha(line)]
#                 #otherwise, parse the list
#                 else:
#                     req_list = parser.parseReq(trim_nonalpha(line))


#                 #process req list
#                 req_list = tool.simplifyReq(req_list)

#                 agent_buffer[-1].req = req_list
#                 l = l + 1
#                 continue 
            
#             #course param
#             elif length > 2 and line[0] == "c" and line[1] == "h" and line[2] == "k":
#                 line = line[5:]
#                 agent_buffer[-1].chk = trim_nonalpha(line)
#                 l = l + 1
#                 continue
                
#             elif length > 2 and line[0] == "u" and line[1] == "p" and line[2] == "d":
#                 line = line[5:]
#                 agent_buffer[-1].upd = trim_nonalpha(line)
#                 l = l + 1
#                 continue
            
#             elif length > 2 and line[0] == "/" and line[1] == "R" and line[2] == "E":
#                 #This indicates a requirement is over
#                 html+="</div>" 
                
#                 state = "expression"
#                 l = l + 1
#                 continue
            
#             elif length > 2 and line[0] == "R" and line[1] == "U" and line[2] == "L":
            
#                     s = line.split()
#                     name = s[1]

#                     #rule in <REQ> must be local
#                     agent_buffer[-1].rules.append(RuleAgent(name))

#                     html+="<div class=\"rule " + name + "\">" 
#                     html+="<p>" + name + "</p>" 

#                     state="rule-local"
#                     l = l + 1
#                     continue
#                 #else if this rule is global
#             #TODO RULE binded to group
#             else:
#                 l = l + 1
#                 continue


#         elif state == "OPT":
#             #option
#             if length > 2 and line[0] == "o" and line[1] == "p" and line[2] == "t":

#                 line = line[7:]

#                 #consume whitespace
#                 while line[0] == " " or line[0] == "\t":
#                     line = line[1:]
                
#                 name = trim_nonalpha(line)
#                 # Add another option 
#                 # By syntax this must be an instance of OptAgent 
#                 html+="<div class=\"option " + name + "\">"
               
#                 agent_buffer[-1].options.append([name, [], [], [] ])
#                 print("ENTER OPT")
#                 #recursively parse all agents and rules in this option
#                 rec_result = parse_req(req, l+1, "expression", req_name)
#                 #record the result to the option
#                 agent_buffer[-1].options[-1][1] = rec_result[0].copy()
#                 agent_buffer[-1].options[-1][2] = rec_result[1].copy()
#                 agent_buffer[-1].options[-1][3] = rec_result[2].copy()
#                 print("EXIT OPT")
#                 state="OPT"
#                 l = rec_result[3]
#                 html+=rec_result[4]
#                 html+="</div>"
#                 continue

#             #/OPT
#             elif length > 2 and line[0] == "/" and line[1] == "O" and line[2] == "P":
                
#                 state = "expression"
#                 l = l + 1 

#                 #create dropdown memnu
#                 html+="<select onChange=\"select_opt(this, this.value)\" class=\"sel\">"
#                 for o in agent_buffer[-1].options:
#                     html+="<option value=\"" + o[0] + "\">" + o[0] + "</option>"
#                 html+="</select>"
#                 html+="</div>"
               

#                 continue
#             else:
#                 l = l + 1
#                 continue

#         elif state == "rule-local":
#             #course
#             if (length > 2 and line[0] == "c" and line[1] == "o" and line[2] == "u")  or line[0] == "A" or line[0] == "B":
#                 line = line[7:]
#                 #consume whitespace
#                 while line[0] == " " or line[0] == "\t":
#                     line = line[1:]

#                 html+="<p>" + str(line) + "</p>"

#                 req_list = []
#                 #if the courses are already parsed
#                 if line[0] == "[":
#                     #convert it to an object 
#                     req_list = tool.string2list(trim_nonalpha(line))
#                 #otherwise, parse the list
#                 else:
#                     req_list = parser.parseReq(trim_nonalpha(line))

#                 agent_buffer[-1].rules[-1].ref.append(req_list)
                
#                 l = l + 1
#                 continue
#             elif length > 2 and line[0] == "/" and line[1] == "R" and line[2] == "U":
#                 state = "req"
#                 html+="</div>" 
#                 l = l + 1
#                 continue

#         elif state == "rule-global":
#             #course
#             if length > 2 and line[0] == "c" and line[1] == "o" and line[2] == "u":
#                 line = line[7:]
#                 #consume whitespace
#                 while line[0] == " " or line[0] == "\t":
#                     line = line[1:]

#                 html+="<p>" + line + "</p>"

#                 req_list = []
#                 #if the courses are already parsed
#                 if line[0] == "[":
#                     #convert it to an object 
#                     req_list = tool.string2list(trim_nonalpha(line))
#                 #otherwise, parse the list
#                 else:
#                     req_list = parser.parseReq(trim_nonalpha(line))

#                 rule_buffer[-1].ref = req_list
#                 l = l + 1
#                 continue
            
#             elif length > 2 and line[0] == "/" and line[1] == "R" and line[2] == "U":
#                 state = "expression"
#                 html+="</div>" 
#                 l = l + 1
#                 continue
        
#         elif state == "group":
#             if length > 2 and line[0] == "u" and line[1] == "p" and line[2] == "d":
#                 line = line[5:]
#                 root_buffer[-1].upd = trim_nonalpha(line)
#                 l = l + 1
#                 continue

#             elif length > 2 and line[0] == "g" and line[1] == "r" and line[2] == "o":
#                 #recursively parse all agents and rules in this option
#                 rec_result = parse_req(req, l+1, "expression", req_name)
#                 #record the result
#                 agent_buffer = agent_buffer + rec_result[0].copy()
#                 # before updating the list of root agents, make sure to update the ref list of the 
#                 # group class for this group.
#                 for a in rec_result[0]:
#                     root_buffer[-1].ref.append(a.name)
                
#                 #TODO ensure req's are not added to closed groups
#                 root_buffer = rec_result[1].copy() + root_buffer
#                 rule_buffer = rule_buffer + rec_result[2].copy()
            
#                 state="group"
#                 l = rec_result[3]
#                 html+=rec_result[4]
#                 continue

#              #/GROUP
#             elif length > 2 and line[0] == "/" and line[1] == "G" and line[2] == "R":
#                 html+="</div>"
#                 state = "expression"
#                 l = l + 1 
#                 continue

        
#     return [agent_buffer, root_buffer, rule_buffer, l, html]


# Takes a *LIST* of items, and builds the HTML and Js executable. 

def parse_req_yml(req, req_name):

    html=""

    root_buffer = []
    agent_buffer = []
    rule_buffer = []
    #group = []
    l = 0
    
    for item in req:
        
        #GROUP
        if "GROUP" in item:
            
            name = item["GROUP"]
            
            if name == "_":
                name = req_name + "_" + str(l)
                l+=1
            else:
                name = name

            html+="<div class=\"group " + name + "\">" 
            html+="<h3>" + name + "</h3>" 
            # Add another option 
            # By syntax this must be an instance of OptAgent 
            root_buffer.append(RootAgent(name))
            root_buffer[-1].upd = item["upd"]

            #recursive
            rec_result = parse_req_yml(item["content"], name)
            agent_buffer = agent_buffer + rec_result[0].copy()

            for a in rec_result[0]:
                root_buffer[-1].ref.append(a.name)
            
            root_buffer = rec_result[1].copy() + root_buffer
            rule_buffer = rule_buffer + rec_result[2].copy()

            html+=rec_result[4]                
            html+="</div>"
        
        #REQ
        elif "REQ" in item:
            
            name = item["REQ"]

            if name == "_":
                name = req_name + "_" + str(l)
                l+=1
            else:
                name = name

            html+="<div class=\"req " + name + "\">" 
            html+="<h3>" + name + "</h3>" 
            
            #If there is already a group in the buffer, add this req to its reference list 
            #if len(root_buffer) > 0 and root_buffer[-1].isClosed == False:
            #    root_buffer[-1].ref.append(name)
            
            #add this to buffer
            agent_buffer.append(Agent(name))

            #state = "req"
            #course param
            line = item["course"] 
            #print(line)
            
            html+="<p>" + str(line) + "</p>" 

            req_list = []
            #if the courses are already parsed
            if isinstance(line, list):
                #convert it to an object 
                req_list = line
            elif line[0] == "%":
                req_list = [line]
            #otherwise, parse the list
            else:
                req_list = parser.parseReq(line)


            #process req list
            req_list = tool.simplifyReq(req_list)

            agent_buffer[-1].req = req_list
            
            
            
            agent_buffer[-1].chk = item["chk"]
                
            agent_buffer[-1].upd = item["upd"]
                
            html+="</div>" 
                
            # check if there is a rule
            # These will be rules binded to agents
            if "rules" in item:

                #check each rule
                for rule in item["rules"]:

                    name = rule["RULE"]
                    print("RULE" + name)

                    agent_buffer[-1].rules.append(RuleAgent(name))
                    html+="<div class=\"rule " + name + "\">" 
                    html+="<p>" + name + "</p>" 
                    #check each key/value pair
                    for param in rule: 

                        if param == "course" or param == "A" or param == "B":
                            #Rules almost always refer to course. Find them out. 
                            #Obtain the value of the keys
                            line = rule[param]
                            req_list = []
                            if isinstance(line, list):
                                #convert it to an object 
                                req_list = line
                            elif line[0] == "%":
                                req_list = [line]
                            # if the list is written in plaintext
                            else:
                                req_list = parser.parseReq(line)

                            agent_buffer[-1].rules[-1].ref.append(req_list)
            
                    html+="</div>" 
        
            

        #OPT
        elif "OPT" in item:
            
            name = item["OPT"]

            if name == "_":
                name = req_name + "_" + str(l)
                l+=1
            else:
                name = name

            html+="<div class=\"opt " + name + "\">" 
            html+="<h3>" + name + "</h3>" 
            

            #If there is already a group in the buffer, add this req to its reference list 
            #if len(root_buffer) > 0 and root_buffer[-1].isClosed == False:
            #    root_buffer[-1].ref.append(req_name)
            
            #add this to buffer
            agent_buffer.append(OptAgent(name))

            #option

            for o in item["options"]: 
                o_name = o["option"]
                
                html+="<div class=\"option " + o_name + "\">"
            
                agent_buffer[-1].options.append([o_name, [], [], [] ])
                
                #recursively parse all agents and rules in this option
                rec_result = parse_req_yml(o["content"], name)
                #record the result to the option
                agent_buffer[-1].options[-1][1] = rec_result[0].copy()
                agent_buffer[-1].options[-1][2] = rec_result[1].copy()
                agent_buffer[-1].options[-1][3] = rec_result[2].copy()
                
                html+=rec_result[4]
                html+="</div>"
            

        
            #create dropdown memnu
            html+="<select onChange=\"select_opt(this, this.value)\" class=\"sel\">"
            for o in agent_buffer[-1].options:
                html+="<option value=\"" + o[0] + "\">" + o[0] + "</option>"
            html+="</select>"
            html+="</div>"
            

        # RULE
        # Rules not in REQ must be global
        elif "RULE" in item:
            
            name = item["RULE"]
            
            #rules in <expression> mst be global
            #add the rule to the rule list
            rule_buffer.append(RuleAgent(name))

            html+="<div class=\"rule " + name + "\">" 
            
            #state="rule-global"
            #l = l + 1
            #check each key/value pair
            #rule_buffer[-1].ref = []
            for param in item: 
                
                if param == "course" or param == "A" or param == "B":
                    #Rules almost always refer to course. Find them out. 
                    #Obtain the value of the keys
                    line = item[param]
                   
                    req_list = item[param]
                    if isinstance(line, list):
                        #convert it to an object 
                        req_list = line
                    elif line[0] == "%":
                        req_list = [line]
                    else:
                        req_list = parser.parseReq(line)

                    rule_buffer[-1].ref.append(req_list)
    
            html+="</div>" 
        
    return [agent_buffer, root_buffer, rule_buffer, l, html]


def parse_write(output, result):

    output.write(
        """function audit_build(option){
//agents
agents= [];
//root agents
root_agents= [];
//rules
rules = [];
//global list of completed courses 
taken = []

    let a_len = 0; 
    \n\n"""
    )

    parse_write_rec(output, result, "\t")

    output.write("}")

# def parse_write_json(result):

#     json_map = {}
#     json_map["master"] = parse_write_json_rec(result)

#     return json_map

# def parse_write_json_rec(result):


def parse_write_rec(output, result, depth):

    #output the agents
    for ag in result[0]:

        if isinstance(ag, Agent):
            txt =  depth + "agents.push(new Agent(\n"
            txt += depth + "\t'" + ag.name + "',\n"
            txt += depth + "\t" + str(ag.req) + "\n"
            txt += depth + "\t)\n"
            txt += depth + ");\n\n"

            func = ""
            #handle chk function
            params = re.split("[(), ]+", ag.chk)
            if params[0] == "CHECK":
                func = "check"
            elif params[0] == "CHECK_UNIT":
                func = "check_unit"
            else:
                raise Exception("unknown function " + params[0])
            txt+=depth + "a_len = agents.length-1;\n"
            txt += depth + "agents[a_len].chk = " + func + ".bind(agents[a_len]"
            for p in params[1:]:
                txt+=", " + p
            txt+=");\n"

            #handle upd function
            params = re.split("[(), ]+", ag.upd)
            if params[0] == "FINISH":
                func = "finish"
            elif params[0] == "FINISH_UNIT":
                func = "finish_unit"
            else:
                raise Exception("unknown function " + params[0])
            txt += depth + "agents[a_len].upd = " + func + ".bind(agents[a_len]"
            for p in params[1:]:
                txt+=", " + p
            txt+=");\n\n"
            output.write(txt)
            txt=""

            #handle any rules
            for rule in ag.rules:
                rule_name = rule.name
                func = ""
                if rule_name == "NOT_USED_FOR_OTHER":
                    func = "not_used_for_other"
                elif rule_name == "SUBSET_RESTRICTION":
                    func = "subset_restriction"
                elif rule_name == "A_NOT_APPROVED_IF_B":
                    func = "a_not_if_b"
                else:
                    raise Exception("unknown rule " + rule_name) 

                txt = depth + "agents[a_len].rules.push(" + func + ".bind(agents[a_len]"
                #txt += depth + "r_len = agents[a_len].rules.length;\n" 
                #txt += depth + "agents[a_len].rules[r_len-1].bind("
                for param in rule.ref:
                    txt+= "," + str(param)
                txt+= "));\n"
                output.write(txt)
                txt=""
        else:
            # create an if statement for each option
            for opt in ag.options:
                txt = depth + "if (option['" + ag.name + "'] == " 
                txt += "'" + opt[0] + "'){\n"
                output.write(txt)
                txt=""
                parse_write_rec(output, opt[1:], depth + "\t")
                txt = depth + "}\n"
                output.write(txt)
                txt=""

    #output the groups
    for root in result[1]:
        txt =  depth + "root_agents.push(new RootAgent(\n"
        txt += depth + "\t'" + root.name + "',\n"
        txt += depth + "\t" + str(root.ref) + "\n"
        txt += depth + "\t)\n"
        txt += depth + ");\n\n"

        func = ""
        #handle upd function
        params = re.split("[(), ]+", root.upd)
        if params[0] == "FINISH":
            func = "finish_agents"
        elif params[0] == "FINISH_GRP":
            func = "finish_agent_subgrp"
        else:
            raise Exception("unknown function " + params[0])

        txt+=depth + "a_len = root_agents.length-1;\n"
        txt += depth + "root_agents[a_len].upd = " + func + ".bind(root_agents[a_len]"
        for p in params[1:]:
            txt+=", " + p
        txt+=");\n"
        output.write(txt)
        txt=""



# def parse_write_json(output, result):

#     output.write(
#         """{"""
#     )

#     parse_write_rec_json(output, result, "\t")

#     output.write("}")

def parse_write_json(output, result):

    parse_write_rec_json(output, result, "")


def parse_write_rec_json(output, result, depth):

    output.write(depth + "{\n" + depth + "\"agents\":[\n")

    #output the agents
    for i, ag in enumerate(result[0]):
        # if this is requirement
        txt = ""
        if i > 0:
            txt = ",\n"

        if isinstance(ag, Agent):

            

            txt +=  depth + "\t{\n"
            txt += depth + "\t\"type\":\"REQ\",\n"           # record that this is REQ type
            txt += depth + "\t\"name\":\"" + ag.name + "\",\n"
            txt += depth + "\t\"course\":" + str(ag.req).replace("'", "\"") + ",\n"
            

            func = ""
            #handle chk function
            params = re.split("[(), ]+", ag.chk)
            func = params[0]

            txt += depth + "\t\"chk\":\"" + func + "\",\n"
            txt += depth + "\t\"chk_param\":" + str(params[1:-1]).replace("'", "") + ",\n"
         

            #handle upd function
            params = re.split("[(), ]+", ag.upd)
            func = params[0]

            txt += depth + "\t\"upd\":\"" + func + "\",\n"
            txt += depth + "\t\"upd_param\":" + str(params[1:-1]).replace("'", "") + ",\n"
           
            txt += depth + "\t\"rules\":[\n"

            if len(ag.rules) > 0:
                rule = ag.rules[0]
                txt += depth + "\t\t{\"name\":\"" + rule.name + "\", "
                txt += "\"course\":" + str(rule.ref).replace("'", "\"")
                txt += "}" 
                for rule in ag.rules[1:]:
                    txt += ",\n" + depth + "\t\t{\"name\":\"" + rule.name + "\", "
                    txt += "\"course\":" + str(rule.ref).replace("'", "\"")
                    txt += "}\n" 
                
            txt += depth + "\t]\n"
            txt += depth + "}\n" 

            output.write(txt)
                
        # If this is an option    
        else:
            txt +=  depth + "{\n"
            txt += depth + "\"type\":\"OPT\",\n"           # record that this is REQ type
            txt += depth + "\"name\":\"" + ag.name + "\",\n"
            txt += depth + "\"options\":" + "{\n"
            # create an if statement for each option
            for j, opt in enumerate(ag.options):
                if j > 0:
                    txt+=",\n"
                txt += depth + "\t\"" + opt[0] + "\":\n"
                output.write(txt)
                txt=""
                parse_write_rec_json(output, opt[1:], depth + "\t")
                txt = "\n"
                output.write(txt)
                txt=""
            
            output.write("}}")

    output.write(depth + "],\n")
    output.write(depth + "\"directors\":[")

    #output the groups
    for i, direc in enumerate(result[1]):

        txt = ""
        if i > 0:
            txt = ",\n"

        txt +=  depth + "{\n"
        txt += depth + "\t\"type\":\"GROUP\",\n"           # record that this is REQ type
        txt += depth + "\t\"name\":\"" + direc.name + "\",\n"
        txt += depth + "\t\"agent\":" + str(direc.ref).replace("'", "\"") + ",\n"


        func = ""
        #handle chk function
        params = re.split("[(), ]+", direc.upd)
        func = params[0]

        txt += depth + "\"upd\":\"" + func + "\",\n"


        #handle upd function
        txt += depth + "\"upd_param\":" + str(params[1:-1]).replace("'", "\"")
        txt+="}\n"

        output.write(txt)
    
    output.write(depth + "],\n")
    output.write(depth + "\"rules\":[")

    for i, rule in enumerate(result[2]):
    
        txt = ""
        if i > 0:
            txt = ",\n"

        txt += "\n" + depth + "\t\t{\"name\":\"" + rule.name + "\", "
        txt += "\"course\":" + str(rule.ref).replace("'", "\"")
        txt += "}\n" 

        output.write(txt)

    output.write("]}")


def trim_nonalpha(s):
    while not s[-1].isalpha() and not s[-1].isdigit() and s[-1] != "]":
        s = s[0:-1]
    return s

if __name__ == "__main__":
    parse()