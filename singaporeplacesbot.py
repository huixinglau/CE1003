# CE1003 SingaporePlacesBot

import sys
import telepot
from telepot.loop import MessageLoop
import time
import requests
import xml.etree.ElementTree as ET
from fastkml import kml
from shapely import geometry
from shapely.geometry import Point, shape, Polygon
import re
import json
import urllib
from urllib.request import urlopen
import json
import urllib.request
import re
import os
from pprint import pprint


bot = telepot.Bot("463338689:AAEoVE1MnKlXtvRLz7ZlD9YA6H9jVEIJak8")
mapPath = "Planning Area Boundary (Web).kml"

# This is the list of abbreviations used by NEA
weatherAbbrev = ["BR", "CL", "DR", "FA", "FG", "FN", "FW", "HG",
                 "HR", "HS", "HT", "HZ", "LH", "LR", "LS", "OC",
                 "PC", "PN", "PS", "RA", "SH", "SK", "SN", "SR",
                 "SS", "SU", "SW", "TL", "WC", "WD", "WF", "WR", "WS"]
weatherInterpret = ["Mist", "Cloudy", "Drizzle", "Fair (Day)", "Fog",
                    "Fair (Night)", "Fair & Warm",
                    "Heavy Thundery Showers with Gusty Winds", "Heavy Rain",
                    "Heavy Showers", "Heavy Thundery Showers", "Hazy",
                    "Slightly Hazy", "Light Rain", "Light Showers", "Overcast",
                    "Partly Cloudy (Day)", "Partly Cloudy (Night)",
                    "Passing Showers", "Moderate Rain", "Showers",
                    "Strong Winds, Showers", "Snow", "Strong Winds, Rain",
                    "Snow Showers", "Sunny", "Strong Winds","Thundery Showers",
                    "Windy, Cloudy","Windy","Windy, Fair","Windy, Rain","Windy, Showers"]

# Areas not part of the New Town scheme are allocated places nearest to it
neaTownList = ['BISHAN', 'BUKIT BATOK', 'BUKIT MERAH', 'BUKIT PANJANG', 'BUKIT TIMAH',
               'CENTRAL WATER CATCHMENT', 'CHANGI', 'CHANGI', 'CHOA CHU KANG',
               'CLEMENTI', 'GEYLANG', 'NOVENA', 'PASIR RIS', 'PAYA LEBAR', 'SELETAR',
               'SEMBAWANG', 'BEDOK', 'BOON LAY', 'SENGKANG', 'SERANGOON', 'ANG MO KIO',
               'TENGAH', 'TOA PAYOH', 'WESTERN WATER CATCHMENT', 'YISHUN', 'CITY',
               'CITY', 'NOVENA', 'TANGLIN', 'WOODLANDS', 'CITY', 'CITY',
               'HOUGANG', 'JURONG EAST', 'LIM CHU KANG', 'MANDAI', 'MARINE PARADE',
               'PULAU UBIN', 'PIONEER', 'PUNGGOL', 'QUEENSTOWN',
               'SOUTHERN ISLANDS', 'TUAS', 'JURONG WEST', 'KALLANG', 'YISHUN',
               'SUNGEI KADUT', 'TAMPINES', 'WESTERN ISLANDS', 'TANGLIN', 'CITY',
               'TANGLIN', 'CITY', 'CITY', 'CITY']

# Create polygons of new towns
mapTree = ET.parse(mapPath)

# Find all Polygon elements anywhere in the doc
elems = mapTree.findall('.//{http://www.opengis.net/kml/2.2}Placemark')

# Create a dictionary of coordinates
dict = {}
locationNameList = []

for placemark in elems:
    
    for nameDescrip in placemark:
        
        if nameDescrip.tag == "{http://www.opengis.net/kml/2.2}name":
            locationName = nameDescrip.text
            #print (locationName)
            locationNameList = locationNameList + [locationName]
            
        for outerBound in nameDescrip:
            
            for linearRing in outerBound:
                
                if (outerBound.tag == "{http://www.opengis.net/kml/2.2}outerBoundaryIs" or linearRing.tag == "{http://www.opengis.net/kml/2.2}outerBoundaryIs"):

                # Account for those with MultiGeometry
                    if linearRing.tag == "{http://www.opengis.net/kml/2.2}outerBoundaryIs":

                        for linearRingII in linearRing:

                            for teselCoord in linearRingII:

                                if teselCoord.tag == "{http://www.opengis.net/kml/2.2}coordinates":
                                    dict [locationName] = ((teselCoord.text.replace(" ","")).replace("\n",","))

                    else:    
                        for teselCoord in linearRing:

                            # Make the polygons
                            if teselCoord.tag == "{http://www.opengis.net/kml/2.2}coordinates":
                                
                                dict [locationName] = ((teselCoord.text.replace(" ","")).replace("\n",","))
                                 #print ((teselCoord.text))

# Create list of polygons
polygonList = []

for x in range(0,len(locationNameList)):
    
    coordinateList = []

    # Convert to numbers
    currentPlace = dict[locationNameList[x]]
    currentNum = re.findall('\d+\.\d+',currentPlace)

    # Create polygons
    lonCount = 1
    latCount = 0

    while lonCount < len(currentNum) and latCount < len(currentNum):

        coordinateList = coordinateList + [[float(currentNum[latCount]),float(currentNum[lonCount])]]
        #print ((float(currentNum[lat])))
        latCount += 2
        lonCount += 2

    poly = Polygon (coordinateList)

    polygonList.append(poly)

# Check if the polygons are correct
#s = polygonList[48]
#print (locationNameList[48])
#x,y = s.exterior.xy
#print (x)
#import matplotlib.pyplot as pp
#pp.plot(x,y,color='#6699cc', alpha=0.7,linewidth=3, solid_capstyle='round', zorder=2)
#pp.plot(p)
#pp.show()

# Send and receive messages
def handle(msg):
    
    contentType, chatType, chatID = telepot.glance(msg)
    userMessage = msg['text']
    
    if userMessage == "/start":
        bot.sendMessage (chatID,"Please enter a place!")

    else:
        
        address = userMessage.replace(" ","_") + "_singapore"

        googleMapAPI = "AIzaSyC9mzFfToQnkL-bq0gM-MDe5M78k_wDswY"
        googleURL = "http://maps.googleapis.com/maps/api/geocode/json?address=" + address
        urlQuote = urllib.parse.quote(googleURL, ':?=/')
        googleResponse = urlopen(urlQuote).read().decode('utf-8')
        googleResponseJson = json.loads(googleResponse)
        #pprint (googleResponseJson)
        
        # If the name is incorrect
        if googleResponseJson.get('results') == []:
            bot.sendMessage (chatID, "We do not have information on this place, sorry! Try again?")
        else:
            lat = googleResponseJson.get('results')[0]['geometry']['location']['lat']
            lon = googleResponseJson.get('results')[0]['geometry']['location']['lng']
            longAddress = googleResponseJson.get('results')[0]['formatted_address']
            sendAddress = "\U0001F50E: " + longAddress

            # Find the town
            placePoint = Point (lon , lat)
            #print (placePoint)

            sendWeather = "\U00002600: We currently do not have information about the weather."

            for y in range (0, len(polygonList)): 
                if (polygonList[y].contains(placePoint)):
                
                    neaInd = y
                    #print(locationNameList[y])
                    #print(townName)

                    # Match to NEA list of towns
                    townName = neaTownList [y]
                    print (townName)
            
                    # Check the weather using NEA API
                    neaURL = "http://api.nea.gov.sg/api/WebAPI/?dataset=2hr_nowcast&keyref=781CF461BB6606ADC49D8386041BBFD2716CA91F82245FBC"
                    neaResponse = requests.get(neaURL)
                    neaTree = ET.fromstring(neaResponse.content)
                    doc = neaTree.getchildren()

                    if doc == []:
                        sendWeather = "\U00002600': We currently do not have information about the weather."

                    else:
                        for x in range (0,47):
                            
                            listName = (doc[3][4][x].attrib['name']).upper()
                            #print (listName)
                            #print (townName)
                            if (listName == townName):
                                # print (listName)
                                break
                        
                        weatherNow = doc[3][4][x].attrib['forecast']

                        # Find interpretation of weather
                        weatherInd = weatherAbbrev.index(weatherNow)
                        weatherName = weatherInterpret[weatherInd]                   

                        # Send weather to user
                        sendWeather = "\U00002600: The weather is " + weatherName + "."

            # Provide places to go to
            placesTypeList = ["cafe","gym","library","movie_theater","park","shopping_mall","restaurant"]
            placesTypeNameList = ["Cafe","Gym","Library","Movie Theater","Park","Shopping Mall", "Restaurant"]
            placesInfoList = ""

            for z in range (0, len(placesTypeList)):
                
                placesURL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location="+ str(lat) + "," + str(lon) + "&radius=500&types=" + placesTypeList[z] + "&key=" + googleMapAPI
                #print (placesURL)
                placesResponse = requests.get(placesURL)
                jsonPlacesResponse = placesResponse.json()
                #print (jsonPlacesResponse)
                
                if jsonPlacesResponse["results"] != []:
                    for b in range (0, len(jsonPlacesResponse["results"])):
                        #print (len(jsonPlacesResponse["results"]))
                        placeName = jsonPlacesResponse["results"][b]['name']
                        #print (placeName)
                        if b == 0:
                            placeStr = "\n" + placesTypeNameList[z] + ": \n1. " + placeName + "\n"
                        else:
                            placeStr = str(b+1) + ": " + placeName + "\n"
                        placesInfoList = placesInfoList + placeStr

            #print(placesInfoList)

            if placesInfoList == []:

                sendPlace = "There are no places to go to around this area, sorry!"

            else:

                sendPlace = placesInfoList

            # Return results to user
            googleAppURL = "https://www.google.com.sg/maps/place/" + address
            sendText = sendAddress + "\n\n" + sendWeather + "\n" + sendPlace + "\nLaunch Google Maps:\n" + googleAppURL
            bot.sendMessage (chatID,sendText)
        
MessageLoop(bot, handle).run_as_thread()

while True:       
    time.sleep(0.5)
