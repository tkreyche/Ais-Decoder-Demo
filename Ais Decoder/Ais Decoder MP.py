# SuperFastPython.com
#https://superfastpython.com/multiprocessing-queue-in-python/
# example of using the queue with processes


import sys
from pyais import decode
import json
import socket
import pyodbc
import logging


from time import sleep
import random
from random import randrange
from multiprocessing import Process
from multiprocessing import Queue


# set up error logging
logging.basicConfig(filename='/temp/ais.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)


# get data from UDP connection
def producer(queue):

    print('Producer: Running', flush=True)


    # set up UDP connection
    try:
        UDP_IP = "192.168.0.55"
        UDP_PORT = 5006
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((UDP_IP, UDP_PORT))
    except Exception as e:
        logger.error(e)
    
    try:
        while True:
            data, addr = sock.recvfrom(4096)
            queue.put(data)
    except Exception as e:
        logger.error(e)

# process data
def consumer(queue):
    print('Consumer: Running', flush=True)

    #cnxn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER=MIRAGE-CHEETAH-\SQLEXPRESS;DATABASE=AIS;UID=admin;PWD=xxxxxxxx;ENCRYPT=No;')


    while True:

        qsize = queue.qsize()
        print("Q Size " + str(qsize), flush=True)

        if qsize == 0:
            sleep(1)
            continue


        data = queue.get()
        #print(f'{item}', flush=True)


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
                #print ("Virtual: " + str(d["virtual_aid"]))
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




 
# entry point
if __name__ == '__main__':
    # create the shared queue
    queue = Queue()
    # start the consumer
    consumer_process = Process(target=consumer, args=(queue,))
    consumer_process.start()
    # start the producer
    producer_process = Process(target=producer, args=(queue,))
    producer_process.start()
    # wait for all processes to finish
    producer_process.join()
    consumer_process.join()
