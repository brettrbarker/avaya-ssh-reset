from paramiko import AutoAddPolicy, SSHClient
import logging; logging.basicConfig(); 
import time
import csv
import datetime
import os
import sys
import re

# Uncomment to turn on debug logging
#logging.getLogger('paramiko.transport').setLevel(logging.DEBUG) 


# SET DEFAULTS
SSH_Username = 'help'
SSH_Pass = '1234'


def main():
    ## Check for proper amount of arguments
    if len(sys.argv) < 2:
        print('Error: Missing argument. Enter CSV file as argument.')
        return  
    inputfile = sys.argv[1]
    if len(sys.argv) > 2:
        print('Error: Too many arguments. The only argument should be the CSV file.')
        return
        
    IPSet = set()
    file = open(inputfile,'r') # Open file in read only
    file_dict = csv.DictReader(file) # Read the CSV into a dictionary. Note: Header row of the CSV MUST contain MAC,Phone,
    success_hosts = []
    fail_hosts = []


    ## Check for correct header row with MAC and Phone fields in the input file.
    if not 'IP' in file_dict.fieldnames:
        print('Error: ' + inputfile + ' does not contain a header row with "IP"\n')
        file.close() # Close the input file before erroring out.
        return 0
    ## Change CSV dict into a dictionary with IP address keys and MAC values.
    for row in file_dict:
        IPSet.add(row['IP']) # Add IP to set

    # WARNING PROMPT
    countIPs = len(IPSet)
    print('##### WARNING: YOU ARE ABOUT TO ATTEMPT TO FACTORY RESET ' + str(countIPs) + ' PHONES #####')
    proceed = input('PROCEED? y/N: ')
    if not proceed.upper() == 'Y':
        print('Cancelling...')
        return 0
    print('##### FINAL WARNING: ARE YOU SURE? #####')
    proceed = input('PROCEED? y/N: ')
    if not proceed.upper() == 'Y':
        print('Cancelling...')
        return 0


    ## START LOOPING THROUGH ALL IP'S
    for ip in IPSet:
        try:
            # Set up client and connect
            client = SSHClient()
            client.set_missing_host_key_policy(AutoAddPolicy)
            client.load_host_keys('known_phones')
            client.connect(ip, username=SSH_Username, password=SSH_Pass, look_for_keys=False, allow_agent=False, banner_timeout=3, timeout=3)

            # Open Shell on Client
            #print('-----Invoking shell')
            chan = client.invoke_shell()
            out = chan.recv(9999)

            ## GET MAC ADDRESS
            #print('finding mac address')
            m = re.search('.*MAC Address = (.*)\r\nIP', out.decode("ascii"))
            phonemac = m.group(1)

            ## FACTORY RESET 
            print('+ Sending reset2factory to ' + str(ip))
            chan.send('reset2factory\n')

            while not chan.recv_ready():
                time.sleep(3)
            out = chan.recv(9999)
            if 'Reset to Default Settings... Are you sure?' in out.decode("ascii"):
                #print("Asking for Reset confirmation")
                chan.send('Y\n') # Send Y confirmation
                while not chan.recv_ready():
                    time.sleep(3)
                out = chan.recv(9999)
                if 'Enter MAC-address:' in out.decode("ascii"):
                    #print("enter mac.........")
                    chan.send(str(phonemac) + '\n')
                while not chan.recv_ready():
                    time.sleep(3)
                out = chan.recv(9999)
                print(out.decode("ascii"))

            else:
                print('Error sending reset2factory command')
            chan.close()  # Close Shell Channel
            client.close() # Close the client itself
            ## END PHONE LOOP
        except:
            print('- Failed connecting to: ' + str(ip))
            fail_hosts.append(ip)


    file.close()
    return 0


# RUN MAIN
if __name__=="__main__":
    main()
