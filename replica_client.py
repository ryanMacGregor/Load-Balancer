from http import client
import socket
import sys
#For argument parsing
import argparse
#For packet creation
import struct
#For logging
import logging


#TESTING USING: python3 replica_client.py -s [REDIRECTOR IP] -p [REDIRECTOR PORT] -l clog.txt


def main(argv):
    passed_arguments = parse_console_args()
    #Assign to variables
    redirector_server_IP = passed_arguments['s']
    redirector_server_port = passed_arguments['p']
    client_log_file_location = passed_arguments['l']

    logging.basicConfig(filename=client_log_file_location, level=logging.INFO, filemode='w')
    logging.info('\n\nTarget server IP: %s', redirector_server_IP)
    logging.info('Target server port: %s', redirector_server_port)
    logging.info('Client log file location: %s',  client_log_file_location)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    #connect to redirector
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try: #gracefully process incorrect port number and exit with a non-zero error code
        client_socket.connect((redirector_server_IP, redirector_server_port))
    except Exception as someError:
        print("\ncan't connect, check the IP and port")
        print(someError)
        print("\n")
    
    #create + send packet to redirector, indicate request for best proxy IP
    payload = "".encode("UTF-8")
    finBit = '1'.encode("UTF-8")
    reqBit = '1'.encode("UTF-8")
    kwargs = {"payload": payload, "finBit": finBit, "reqBit": reqBit}
    initPacket = create_packet(**kwargs)
    client_socket.sendall(initPacket)
    #log and print to screen
    print("\nSEND: " + "[fin:" + finBit.decode("UTF-8") + "] [req:" + reqBit.decode("UTF-8") + "]\n")
    log_data(1, finBit.decode("UTF-8"), reqBit.decode("UTF-8"))

    #wait for server IP and Port to be given
    recvData = client_socket.recv(514)
    finBit, reqBit, ReplicaIP = unpack(recvData)

    #close connection with redirector
    client_socket.close()

    #connect to designated server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cleaned_IP = ReplicaIP.replace('\00' , '')
    print("Connecting to " + cleaned_IP + ":" + str(redirector_server_port))

    try: #gracefully process incorrect port number and exit with a non-zero error code
        client_socket.connect((cleaned_IP, redirector_server_port))
    except Exception as someError:
        print("\ncan't connect, check the IP and port")
        print(someError)
        print("\n")

    

    #send packet requesting data
    payload = "".encode("UTF-8")
    finBit = '1'.encode("UTF-8") #this is the end of what the client will send
    reqBit = '1'.encode("UTF-8") #the client is requesting data
    kwargs = {"payload": payload, "finBit": finBit, "reqBit": reqBit}
    initPacket = create_packet(**kwargs)
    client_socket.sendall(initPacket)
    #log and print to screen
    print("\nSEND: " + "[fin:" + finBit.decode("UTF-8") + "] [req:" + reqBit.decode("UTF-8") + "]\n")
    log_data(1, finBit.decode("UTF-8"), reqBit.decode("UTF-8"))

    #receive data
    writeData = ""
    webData = ""
    while True:
        recvData = client_socket.recv(514)
        finBit, reqBit, webData = unpack(recvData)
        writeData += webData
        if(finBit == '1'):
            break
        
    #close connection to server
    client_socket.close()
    output = open("received.html", "w")
    output.write(writeData)


def parse_console_args():
    #Set up argument parser
    console_parser = argparse.ArgumentParser(description="Start anonclient for program 2.")
    #Add arguments for parser to recognize
    console_parser.add_argument('-s')
    console_parser.add_argument('-p', type=int)
    console_parser.add_argument('-l')
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
