import socket
import sys
#For argument parsing
import argparse
#For packet creation
import struct
#For logging
import logging
import os 
from _thread import *
from scapy.all import *
import re


#TESTING USING: sudo python3 replica_redirector.py -s [SERVER IP LIST] -p [SERVER PORT] -l rlog.txt
#TODO: put in readme testing using sudo
#TODO: put in readme smth abt installing scapy

def main(argv):
    passed_arguments = parse_console_args()
    replica_server_IP_list = passed_arguments['s']
    redirector_port = passed_arguments['p']
    redirector_log_file_location = passed_arguments['l']

    logging.basicConfig(filename=redirector_log_file_location, level=logging.INFO, filemode='w')
    logging.info('\n\nFile Containing List of Replica Server IPs: %s', replica_server_IP_list) 
    logging.info('Server port to listen on: %s', redirector_port)
    logging.info('Client log file location: %s',  redirector_log_file_location)

    redirector_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)
    print(IPAddr)
    #Bind to socket so cient can connect
    redirector_socket.bind((hostname, redirector_port))

    redirector_socket.listen(5)
    while 1:
        #get connection from client
        client, client_address = redirector_socket.accept()
        #TODO: log connection
        #Ping servers
        loss_percentage = 0
        delay = 0
        with open(replica_server_IP_list) as ip_file:
            entire_file = ip_file.read()
            target_server_port = ip_file.readline()
        print(target_server_port)
        #ASSUME EACH IP IS IN A.B.C.D FORMAT AND EACH ON DIFFERENT LINE
        try:
            regex_IP = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", entire_file)
        except Exception as annoying_error:
            print("\nError occured while reading in IPs from file.")
            print(annoying_error)
            print("\n")
        timeList = []
        #Arbitrarily large number to ensure that there's something smaller than it
        #And if there isn't a response time lower than this then I think we have other problems
        bestTime = 100000
        ping_count = 3
        for x in range(len(regex_IP)):
            try:
                target = regex_IP[x]
            except IndexError as index_error:
                print("\nIndex error occured. Possibly no valid IPs read in.")
                print(annoying_error)
                print("\n")
            try:
                total_time, unanswered = ping_replica_server(target, ping_count, target_server_port, redirector_socket)
                avg_time = total_time/ping_count
                if(len(unanswered) != 0):
                    loss_percentage = ping_count/len(unanswered)
                else:
                    loss_percentage = ping_count
                weight = (0.75 * loss_percentage) + (0.25 * avg_time)
                timeList.insert(int(weight), x)
                print("weight: " + str(weight))
            except Exception as probably_ping_error:
                print("\nError occured, probably while trying to ping replica servers..")
                print(probably_ping_error)
                print("\n")
        for i in timeList:
            if timeList[i] < bestTime:
                bestTime = timeList[i]
        best_replica = regex_IP[bestTime]
        ip_file.close()
        #Generate arguments for a new client connection thread
        thread_arguments = ((redirector_socket, client, client_address, best_replica))
        #Start new thread
        start_new_thread(threaded_connection, thread_arguments)


def ping_replica_server(target, count, target_server_port, redirector_socket):
    #TODO: this function
    t = 0.0
    for x in range(count):
        packet = Ether()/IP(dst=target)/ICMP()
        ans, unans = srp(packet, filter='icmp', verbose=0)
        rx = ans[0][1]
        tx = ans[0][0]
        delta = rx.time-tx.sent_time
        print("Ping:", delta)
        t += delta
    return t, unans

def threaded_connection(redirector_socket, client, client_address, best_replica):
    #Receive initial packet
    received_packet = client.recv(514)
    finBit, reqBit, payload = unpack(received_packet)
    #if received_packet is initialization packet
    if reqBit == '1':
        #Create and send packet back
        reqBit = '0'
        kwargs = {"payload": str(best_replica).encode("UTF-8"), "finBit": finBit.encode("UTF-8"), "reqBit": reqBit.encode("UTF-8")}
        packet_to_send = create_packet(**kwargs)
        client.send(packet_to_send)
        #print to screen + log
        print("\nSEND: " + "[fin:" + finBit + "] [req:" + reqBit + "]\n")
        log_data(1, finBit, reqBit)

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

    #print to screen + log
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
