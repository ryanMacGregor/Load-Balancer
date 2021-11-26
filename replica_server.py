import socket
import sys
#For argument parsing
import argparse
#For packet creation
import struct
#For logging
import logging
#For downloading the webpage
import urllib.request
#For handinling multiple connections
import threading

#TESTING USING: python3 replica_server.py -p 3279 -l slog.txt -w https://tntech-ngin.github.io/csc4200/programming3/index.html

def main(argv):
    passed_arguments = parse_console_args()
    server_host_port = passed_arguments['p']
    server_log_file_location = passed_arguments['l']
    server_page_to_download = passed_arguments['w']
    logging.basicConfig(filename=server_log_file_location, level=logging.INFO, filemode='w')
    logging.info('\n\nServer port: %s', server_host_port)
    logging.info('Server log file location: %s',  server_log_file_location)
    logging.info('Page to download: %s',  server_page_to_download)

    #Create + bind to socket
    host_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)

    site = urllib.request.urlretrieve(server_page_to_download, "webpage_to_send.txt")

    host_socket.bind((hostname, server_host_port))
    print(IPAddr)

    #MAIN LOOP
    while 1:
        #Listen for connections
        host_socket.listen(5)
        #Accept connection
        connection_object, address = host_socket.accept()
        #TODO: gracefully process incorrect port number and exit with a non-zero error code
        received_packet = connection_object.recv(514)
        finBit, reqBit, payload = unpack(received_packet)
        #open the file we wrote the webpage to
        web_data = open("webpage_to_send.txt", "rb")
        #get first chunk from the file for the payload
        data = web_data.read(512)
        #set timer for the timeout
        #host_socket.settimeout(0.5)
        finBit = '0' #the server starts sending - it is not yet finished
        reqBit = '0' #the server will not request anything
        while data:
            if finBit == '1':
                #host_socket.settimeout(0)
                break
            if(len(data) < 512):
                finBit = '1'.encode("UTF-8")
                reqBit = '0'.encode("UTF-8")
            else:
                finBit = '0'.encode("UTF-8")
                reqBit = '0'.encode("UTF-8")
            #make packet
            kwargs = {"payload": data, "finBit": finBit, "reqBit": reqBit}
            primary_conent_packet = create_packet(**kwargs)
            #log and print to screen
            print("\nSEND: " + "[fin:" + finBit.decode("UTF-8") + "] [req:" + reqBit.decode("UTF-8") + "]\n")
            log_data(1, finBit.decode("UTF-8"), reqBit.decode("UTF-8"))
            #send packet
            connection_object.sendto(primary_conent_packet, address)
            #read data
            data = web_data.read(512)

def parse_console_args():
    #Set up argument parser
    console_parser = argparse.ArgumentParser(description="Start anonserver for program 3.")
    #Add arguments for parser to recognize
    console_parser.add_argument('-p', type=int)
    console_parser.add_argument('-l')
    console_parser.add_argument('-w', type=str)
    #Retrieve passed arguments
    passed_arguments = vars(console_parser.parse_args())
    return passed_arguments

def create_packet(**kwargs):
    packet = struct.pack("!c", kwargs.get("finBit"))  # pack the FIN
    packet += struct.pack("!c", kwargs.get("reqBit"))
    packet += struct.pack("!512s", kwargs.get("payload"))
    return packet

def unpack(packet):

    #unpack packet
    finBit, reqBit, payload = struct.unpack("!2c512s", packet)

    #decode characters and strings
    finBit = finBit.decode("UTF-8")
    reqBit = reqBit.decode("UTF-8")
    payload = payload.decode("UTF-8")

    #print to screen
    print("\nRECV: " + "[fin:" + finBit + "] [req:" + reqBit + "]\n")
    log_data(0, finBit, reqBit)

    #return the unpacked values
    return finBit, reqBit, payload

def log_data(identifier, finBit, reqBit):
    #0 indicates receiving, 1 indicates sending
    #This is completely arbitrary and there was/is no reason for this choice.
    if(identifier == 0):
        logging.info("\nRECV: " + "[fin:" + finBit + "] [req:" + reqBit + "]\n") 
    elif(identifier == 1): 
        logging.info("\nSEND: " + "[fin:" + finBit + "] [req:" + reqBit + "]\n")

#MAIN
if __name__ == "__main__":
   main(sys.argv[1:])
