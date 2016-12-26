'''
Python Script to parse a csv input file containing source and destination URLComponents
and convert them to akamai PAPI specific json data. This script is limited to redirect
behavior. You can find this script in 
'''
import csv
import json
import re

print("\n\nOutput JSON file will be stored in JsonOutput.json  [If everything passes well]\n")
InputFilename = input("Enter the inputfile CSV name with extension (Ex: redirect.csv): NOTE: File should be in current working directory:   ")


try:
    fileHandler = open(InputFilename,'r')
    inputFileReader = csv.reader(fileHandler)
except (RuntimeError, TypeError, NameError,FileNotFoundError):
    print("Are you sure this file exists. I couldnt find one")
    exit()

jsonList = []
outputFileHandler = open('JsonOutput.json','w')

#Function to Check for valid URL, this is the Django way to do this
def is_valid_url(url):
    regex = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url is not None and regex.search(url)

#Function to Check and populate the match criterias
def criteriaList(srcURLComponents,outputJson):
    criteria_values = []
    if srcURLComponents['Hostname'] and srcURLComponents['Hostname'] != '':
        criterias_list = [] #Initialized here to avoid multiple occurances of same list
        criteria = {}
        criteria['options'] = {}
        criteria['name'] = 'hostname'
        criteria['options']['values'] = srcURLComponents['Hostname']
        criterias_list.append(criteria)
    if srcURLComponents['Query_param'] and srcURLComponents['Query_param'] != '':
        paramString = str(srcURLComponents['Query_param'])
        paramStringPair = paramString.split('&')
        criterias_list = [] #Initialized here to avoid multiple occurances of same list
        for nameValuePair in paramStringPair:
            criteria = {}
            criteria['options'] = {}
            queryName = nameValuePair.split('=')[0]
            queryValue = nameValuePair.split('=')[1]
            criteria['name'] = 'queryStringParameter'
            criteria['options']['matchOperator'] = "matchOperator"
            criteria['options']['escapeValue'] = bool(False)
            criteria['options']['matchCaseSensitiveName'] = bool(True)
            criteria['options']['matchCaseSensitiveValue'] = bool(True)
            criteria['options']['matchOperator'] = "IS_ONE_OF"
            criteria['options']['matchWildcardName'] = bool(False)
            criteria['options']['matchWildcardValue'] = bool(False)
            criteria['options']['parameterName'] = queryName
            criteria['options']['values'] = queryValue
            criterias_list.append(criteria)
    outputJson['criteria'] = criterias_list

#Function to Check and populate the behavior values for Redirect
def determineBehaviorList(DstURLComponents,outputJson):
    behaviors_list = []
    behavior = {}
    behavior['name'] = 'redirect'
    behavior['options'] = {}
    behavior['options']['destinationProtocol'] = DstURLComponents['Protocol']
    behavior['options']['destinationHostname'] = "OTHER"
    behavior['options']['destinationHostnameOther'] = DstURLComponents['Hostname']
    behavior['options']['destinationPath'] = "OTHER"
    if DstURLComponents['Path'] and DstURLComponents['Path'] != '':
        behavior['options']['destinationPathOther'] = '/'+DstURLComponents['Path']
    else:
        behavior['options']['destinationPathOther'] = "/"
    behavior['options']['mobileDefaultChoice'] = "DEFAULT"
    behavior['options']['queryString']= "IGNORE"
    behavior['options']['responseCode'] = 301
    behaviors_list.append(behavior)
    outputJson['behaviors'] = behaviors_list

#Function to Check and populate URL componenets
def fetchURLComponents(Url):
    URLComponents = {}
    urlMatch = re.match(r"(^https?)://([a-zA-Z0-9.]*)/?([a-zA-Z0-9./-]*)\??(.*)",Url)
    if urlMatch:
        URLComponents['Protocol'] = urlMatch.group(1)
        URLComponents['Hostname'] = urlMatch.group(2)
        URLComponents['Path'] = urlMatch.group(3)
        URLComponents['Query_param'] = urlMatch.group(4)
    return(URLComponents)

#Main function to parse file and populate values
for line in inputFileReader:
    outputJson = {}
    sourceUrl = str(line[0])
    destinationUrl = str(line[1])
    s = is_valid_url(sourceUrl)
    d = is_valid_url(destinationUrl)
    if s is not None and d is not None:
        SrcURLComponents = fetchURLComponents(sourceUrl)
        DstURLComponents = fetchURLComponents(destinationUrl)
        redirectName = "Redirect" + SrcURLComponents['Hostname'] + "+" + SrcURLComponents['Path'] + SrcURLComponents['Query_param']
        outputJson['name'] = redirectName
        outputJson['children'] = []
        #Add all the behaviors applicable
        determineBehaviorList(DstURLComponents,outputJson)
        criteriaList(SrcURLComponents,outputJson)
        outputJson['criteriaMustSatisfy'] = "all"
        jsonList.append(outputJson)
    else:
        print("One or more URL is not valid in :"+ sourceUrl + "    " +destinationUrl)

jsonOutputFormat = json.dumps(jsonList)
#print(jsonOutputFormat)
outputFileHandler.write(jsonOutputFormat)
print("\n\nOutput JSON file is stored in JsonOutput.json  [Looks like everything passed well]\n")