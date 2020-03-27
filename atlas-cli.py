import argparse
import os
import boto3

import scrape
import compiler

parser = argparse.ArgumentParser(description=""" 
    CLI software to maintain atlas's database
""")

parser.add_argument('--update_dept',
                    help="Update database for departments",
                    action="store_true")

parser.add_argument('--update_courses',
                    help="Update course catalog listed under each department",
                    action="store_true")

parser.add_argument('--update_lectures',
                    help="Update lecture info for each course for a given term",
                    default=""
                    )

parser.add_argument('--set_env',
                    help="Specify the env file with credentials for the database. Default is config.env",
                    default="config.env"
                    )

# parser.add_argument('--set_env_aws',
#                     help="Specify the env file with credentials for the database. Default is config.env",
#                     default="config.env"
#                     )

parser.add_argument('--compile_req',
                    help="Takes a path to a major requirement written as YAML and converts it into JSON. Use set_env to specify database credentials",
                    default=""
                    )

parser.add_argument('--s3',
                    help="After running --compile_req, automatically stores the result in AWS S3. Be sure to specify AWS S3 in the aws cli tool",
                    action="store_true")

args = parser.parse_args()



cred = "config.env"
if args.set_env:
    cred = args.set_env

print("Using '" + cred + "' as credentials")

if args.update_dept:
    scrape.set_path(cred)
    scrape.scrape_dept()

if args.update_courses:
    scrape.set_path(cred)
    scrape.scrape_courses()

if not args.update_lectures == "":
    scrape.set_path(cred)
    scrape.scrape_lectures(args.update_lectures)

if not args.compile_req == "":
    print("Make sure to run --update_dept and --update_courses before running this command")

    path = args.compile_req
    compiler.parse(path, cred)

    if args.s3:

        s3_client = boto3.client('s3')
        name = path.split('/')[-1] 
        inst = path.split('/')[-2] 
       
        res = s3_client.upload_file(path + '/req.json', 'atlas-majors-'+inst, name+'-req.json')
        res = s3_client.upload_file(path + '/desc.json', 'atlas-majors-'+inst, name+'-desc.json')


  


