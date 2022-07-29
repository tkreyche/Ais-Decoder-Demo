
import sys
from pyais import decode
import json
import socket
import pyodbc
import logging

# set up error logging
logging.basicConfig(filename='/temp/ais.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)

# set up UDP connection
UDP_IP = "192.168.0.55"
UDP_PORT = 5006
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# set up SQL Server connection


#cnxn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER=myserver;DATABASE=AIS;UID=admin;PWD=mypassword;ENCRYPT=No;')

# test SQL Server connection
"""
cursor = cnxn.cursor()
cursor.execute("SELECT @@version;") 
row = cursor.fetchone() 

while row: 
    print(row[0])
    row = cursor.fetchone()
cnxn.close()
"""

# runs in permanent loop
while True:

    # get UDP data
    data, addr = sock.recvfrom(4096)

    # parse incoming json
    try:
        j = json.loads(data)
    except Exception as e:
        print ('Exception: '+ str(e))
        logger.error(e)
        continue

    # extract nmea element from json
    try:
        n = (j["NMEA"])
    except Exception as e:
        print ('Exception: '+ str(e))
        logger.error(e)
        continue

    # get the channel value, not handled in pyais decoder
    try:
        channel = n[0].split(',')[4]
    except Exception as e:
        print ('Exception: '+ str(e))
        logger.error(e)
        continue 


    # decode to dictionary with pyais
    try:
        d = decode(*n).asdict()
    except Exception as e:
        print ('Exception: '+ str(e))
        logger.error(e)
        continue





    # process data, when data extraction ok
    # this is just a demo of a porttion of the data

    if "shipname" in d:
        print(d["shipname"])

    if "name" in d:
        print(d["name"])

    print(d["mmsi"], d["msg_type"], j["signalpower"], j["ppm"], channel )
    print("----------------")
    
    # just using fixed stations for now, save in sql server using sproc
    if d["msg_type"] == 21 or d["msg_type"] == 4:

        virtual = False
        if "virtual_aid" in d:
            print ("Virtual: " + str(d["virtual_aid"]))
            virtual = d["virtual_aid"]


        try:
            crsr = cnxn.cursor()

            sproc = "exec [dbo].[insertFixedRecords2] @mmsi = ?, @msgType = ?, @pwr = ?, @ppm = ?, @channel = ?, @virtual = ?, @lat = ?, @lng = ?"
            params = d["mmsi"], d["msg_type"], j["signalpower"], j["ppm"], channel, virtual, d["lat"], d["lon"]
            crsr.execute( sproc, params) 
            crsr.commit()
            crsr.close()
        except Exception as e:
            print ('Exception: '+ str(e))
            logger.error(e)
            continue


