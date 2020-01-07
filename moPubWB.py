#!/usr/bin/env python

import sys
import requests
import json
import csv
import ast
import re
import os
import getpass

VERSION = "v0.0.1"
SCRIPT_NAME = "moPubWB.py"

def login_to_mopub(username, password):
    global csrftoken, session_id, s
    s = requests.Session()
    r1 = s.get('https://app.mopub.com/login/')
    csrftoken = r1.cookies['csrftoken']
    # print(s.cookies['csrftoken'])

    header = {
        'x-csrftoken': csrftoken,
        'referer': 'https://app.mopub.com/login/',
        'cookie': 'csrftoken='+csrftoken+'; _referring_domain%22%3A%20%22app.mopub.com%22%7D',
    }
    payload = {
        'username': username,
        'password': password,
    }
    r2 = s.post('https://app.mopub.com/web-client/api/user/login', json=payload, headers=header)

    csrftoken = s.cookies['csrftoken']
    session_id = s.cookies['sessionid']
    return session_id


def create_lineitem(payload, account_id):
    combined_cookie = 'csrftoken='+csrftoken+'; sessionid='+session_id+'; mopub_account='+account_id
    header = {
        'x-csrftoken': csrftoken,
        'referer': 'https://app.mopub.com/line-item',
        'cookie': combined_cookie
    }
    print (payload)
    response = s.post('https://app.mopub.com/web-client/api/line-items/create', json=payload, headers=header)
    if (response.status_code != 200):
        print(response.text)

    try:    
        print(response.status_code, json.loads(response.text)['key']) 
    except KeyError:
        print('Cannot find any line item key in response. Line item might fail to be created.')
                            
    return response.status_code
    
def get_lineitem(id, account_id):
    combined_cookie = 'csrftoken='+csrftoken+'; sessionid='+session_id+'; mopub_account='+account_id
    header = {
        'x-csrftoken': csrftoken,
        'cookie': combined_cookie
    }
    keyvalue = {
        'key': id
    }

    response = s.get('https://app.mopub.com/web-client/api/line-items/get', params=keyvalue, headers=header)

    if response.status_code != 200:
        print ('This line item id was not fetched: '+ id)
        print ('Please note that default Marketplace Lineitem will not be fetched')
        return False

    return json.loads(response.text)

def get_order(id, account_id):
    combined_cookie = 'csrftoken='+csrftoken+'; sessionid='+session_id+'; mopub_account='+account_id
    header = {
        'x-csrftoken': csrftoken,
        'cookie': combined_cookie
    }
    keyvalue = {
        'key': id
    }
    response = s.get('https://app.mopub.com/web-client/api/orders/get', params=keyvalue, headers=header)
    print(response.status_code)
    # print(response.text)
    return json.loads(response.text, encoding='utf-8')

def get_all_lineitems_from_order(id, account_id):   
    return get_order(id, account_id)['lineItems']

def get_adunit(id, account_id):
    combined_cookie = 'csrftoken='+csrftoken+'; sessionid='+session_id+'; mopub_account='+account_id
    header = {
        'x-csrftoken': csrftoken,
        'cookie': combined_cookie
    }
    keyvalue = {
        'key': id,
        'includeAdSources': 'true'
    }
    response = s.get('https://app.mopub.com/web-client/api/ad-units/get', params=keyvalue, headers=header)
    y = json.loads(response.text)
    team = y["adSources"]
    zen = len(y["adSources"])
    num = 0
    lineitem_list = []
    while num < zen:
        x = y["adSources"][num]["key"]
        name = y["adSources"][num]["name"]
        print "Fetching LineItem: " + name + " " + x
        eachLineItem = get_lineitem(x, account_id)
        if eachLineItem != False:
            lineitem_list.append(get_lineitem(x, account_id))
        num += 1

    return lineitem_list



###### ADD code to cycle through line items (id stored in key) and run a line item get
###### //app.mopub.com/web-client/api/line-items/get?key=[thiskey]
# return json.loads(response.text, encoding='utf-8')

def get_all_lineitems_from_adunit(id, account_id):
    return get_adunit(id, account_id)

def update_lineitem(id, payload, account_id):
    combined_cookie = 'csrftoken='+csrftoken+'; sessionid='+session_id+'; mopub_account='+account_id

    header = {
        'x-csrftoken': csrftoken,
        'referer': 'https://app.mopub.com/line-item',
        'cookie': combined_cookie
    }
    response = s.post('https://app.mopub.com/web-client/api/line-items/update?key='+id, json=payload, headers=header)
    if (response.status_code != 200):
        print(response.text)
    print(response.status_code)    
    return response.status_code 

def bulk_update_lineitem(payload, account_id):
    combined_cookie = 'csrftoken='+csrftoken+'; sessionid='+session_id+'; mopub_account='+account_id

    header = {
        'x-csrftoken': csrftoken,
        'referer': 'https://app.mopub.com/line-item',
        'cookie': combined_cookie
    }
    response = s.post('https://app.mopub.com//web-client/api/line-items/bulk-update', json=payload, headers=header)
    if (response.status_code != 200):
        print(response.text)
    print(response.status_code)
    return response.status_code 

def bulk_update_lineitems_from_csv(inputFilename, account_id):
    csv_input_file = open(inputFilename, 'r')
    csvreader = csv.DictReader(csv_input_file)
    payload_dict_dict = {}
    for row in csvreader:
        status = ''
        for key, value in row.items():
            if key == "status":
                status = value 
                if value not in ["archived", "unarchived"]:
                    break   
                if value not in payload_dict_dict:    
                    payload_dict_dict[value] = {"status": value, "keys":[]}
            if key == "key":
                payload_dict_dict[status]["keys"].append(value)

    for k, v in payload_dict_dict.items():
        bulk_update_lineitem(v, account_id)
    csv_input_file.close()


def get_all_lineitems_from_adunit_to_csv(id, account_id, filename):
    exportJSONtoCSV(get_all_lineitems_from_adunit(id, account_id), filename)

def get_all_lineitems_from_order_to_csv(id, account_id, filename):  
    exportJSONtoCSV(get_all_lineitems_from_order(id, account_id), filename)

def exportJSONtoCSV(lineitems, filename):
    csv_file = open(filename, 'w')
    csvwriter = csv.writer(csv_file)
    count = 0
    for lineitem_obj in lineitems:
        if count == 0:
            header = lineitem_obj.keys()
            csvwriter.writerow(header)
            count += 1
        csvwriter.writerow([ byteify(value) for value in lineitem_obj.values()])
    csv_file.close()


def csv_row_parser(row, action):
    payload_dict = {}
    for key, value in row.items():
        if key in [
                "key", 
                "orderName",
                "network",
                "advertiser",
                "filterLevel",
                "categoryBlocklist",
                "attributeBlocklist",
                "advanceBiddingEnabled",
                "status",
                "started",
                "creatives",
                "pmpDealFields",
                "active",
                "targetOther",
                "bidStrategy",
                "autoCpm",
                "visible"
            ]:
            # print "Skip: " + key + " " + value
            continue

        elif key in ["enablePrivateKeywords"]:
            # print "Deprecate: " + key + " " + value
            continue
        
        if (action == "update"):
            if key in [
                    "orderKey", 
                    "type", 
                    "networkType", 
                    "disabled", 
                    "disallowAutoCpm"
                ]:    
                continue

        if value in [""]:
            continue

        elif re.search(r'^\[.*\]$',value):
            payload_dict[key] = ast.literal_eval(value)
        elif re.search(r'^\{.*\}$',value):
            if key in ["overrideFields"]: 
                payload_dict[key] = {}
                try:
                    if payload_dict["enableOverrides"] is not True:
                       # Make sure to remove "overrideFields", "enableOverrides" field to not to update on non-network Lineitems. Otherwise API returns error.
                       payload_dict.pop("overrideFields", None) 
                       payload_dict.pop("enableOverrides", None)
                       continue
                except KeyError:
                    print('enableOverrides is not defined. Please also move the enableOverrides before overrideFields.')
                    continue        

                for k in ["network_account_id","network_adunit_id","network_app_id","app_signature","location","video_enabled","custom_event_class_name","custom_event_class_data"]:
                    try:
                        if (ast.literal_eval(value)[k] != ''):
                            payload_dict[key][k] = ast.literal_eval(value)[k]
                    
                    except KeyError:
                        # print('KeyError to find '+k)
                        continue
            else:
                payload_dict[key] = ast.literal_eval(value)

        elif key in ["minIosVersion"]:
            payload_dict[key] = '{:02.1f}'.format(float(value))
        elif key in ["allocationPercentage"]:
            payload_dict[key] = round(float(value))

        else:
            payload_dict[key] = str_to_bool(value)

    return payload_dict

def create_lineitems_from_csv(inputFilename, account_id):
    csv_file = open(inputFilename, 'r')
    csvreader = csv.DictReader(csv_file)
    rowcount = 1
    for row in csvreader:
        rowcount += 1
        print("Creating Row: " + str(rowcount))
        create_lineitem(csv_row_parser(row, "create"), account_id)
    csv_file.close()

def update_lineitems_from_csv(inputFilename, account_id):
    csv_input_file = open(inputFilename, 'r')
    csvreader = csv.DictReader(csv_input_file)
    # csv_output_file = open(outputFilename, 'wb')
    # writer = csv.writer(file2)
    # writer.writerows(new_rows_list)
    # file2.close()
    rowcount = 1
    for row in csvreader:
        rowcount += 1
        print("Updating Row: " + str(rowcount) + " Lineitem Key: " + row["key"])
        update_lineitem(row["key"], csv_row_parser(row, "update"), account_id)
    csv_input_file.close()   
    


def byteify(input, encoding='utf-8'):
    if isinstance(input, dict):
        # return {byteify(key): byteify(value) for key, value in input.iteritems()}
        return {byteify(key): byteify(value) for key, value in input.items()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    else:
        try:
            unicode
        except NameError:
            if isinstance(input, str):
                return input   
        else: 
            if isinstance(input, unicode):
                return input.encode(encoding)

        return input

    
def str_to_bool(s):
    if s.lower() == 'true':
        return True
    elif s.lower() == 'false':
        return False
    elif s.lower() in ['', 'none']:
        return None
    else:
        return s

# def verify_user_input(argv):
#     if (len(argv) < 4):
#         print("ERROR: You are missing input arguments.")
#         print("Proper syntax: 'python run_lineitem_api.py [USER NAME] [ACCOUNT ID] [ACTION] [Input CSV file]")
#         print("For example: 'python run_lineitem_api.py abc@mopub.com 12345678 70052 update getAllLineitemsFromOrder.csv")
#         sys.exit("Exiting now")

#     path = argv[3]
#     # Path validation
#     if not os.path.isfile(path):
#         print("ERROR: Invalid file path.")
#         sys.exit("Exiting now")

#     if argv[2] == 'get':
#         if (len(argv) < 5):
#             print("ERROR: You are missing input arguments in 'Get' command")
#             print("Proper syntax: 'python run_lineitem_api.py [USER NAME] [ACCOUNT ID] [ACTION] [Output CSV file] [ORDER ID]")
#             print("For example: 'python run_lineitem_api.py abc@mopub.com 12345678 70052 get getAllLineitemsFromOrder.csv c401f2d3e8e94ca092685e9e80ca66e4")
#             sys.exit("Exiting now")

#     if argv[2] not in ["update", "create", "get", "statusupdate"]:
#         print('ERROR: You are putting a wrong action command. Please use "update", "create", "get", "statusupdate" ')
#         print("Proper syntax: 'python run_lineitem_api.py [USER NAME] [ACCOUNT ID] [ACTION] [Output CSV file] [ORDER ID]")
#         print("For example: 'python run_lineitem_api.py abc@mopub.com 12345678 70052 create createLineitems.csv")
#         sys.exit("Exiting now")


def main(argv):

    if len(sys.argv) != 4:
        print "Usage: python " + SCRIPT_NAME + " [USER_NAME] [ACCOUNT_ID] [FILE_NAME]"
        print "     USER_NAME              MoPub dashboard account (email address)."
        print "     ACCOUNT_ID             MoPub account Id. Please contact your account manager to acquire."
        print "     FILE_NAME              CSV file that can be your input/output file."
        print ""
        print "Version: " + VERSION
        return

    accountid = argv[1]
    filename = argv[2]

    print("Please enter your MoPub dashboard password")
    login_to_mopub(argv[0], getpass.getpass())

    while True:
        action = raw_input("Enter command [create, getAdunit, getOrder, update, statusupdate, quit]: ")
        
        if action == 'create':
            create_lineitems_from_csv(filename, accountid)
        elif action == 'getAdunit':
            input_id = raw_input("Enter Adunit id: ")
            print("Adunit ID: " + input_id)
            get_all_lineitems_from_adunit_to_csv(input_id, accountid, filename)
        elif action == 'getOrder':
            input_id = raw_input("Enter Order id: ")
            print("Order ID: " + input_id)
            get_all_lineitems_from_order_to_csv(input_id, accountid, filename)
        elif action == 'update':
            update_lineitems_from_csv(filename, accountid)
        elif action == 'statusupdate':
            bulk_update_lineitems_from_csv(filename, accountid)
        elif action == 'quit':
            print("Bye")
            break
        else:
            print("Please enter valid command. Commands are case-sensitive. [create, getAdunit, getOrder, update, statusupdate, quit]")
            continue

if __name__ == "__main__":
    main(sys.argv[1:])
    
