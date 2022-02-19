################### AVAYA 1100 SERIES PHONE FACTORY RESET SCRIPT ######################
## Script to FACTORY RESET phones via SSH when provided a list of IP's and SSH credentials.
## Input CSV with at least columns: IP
## 
## Requires Python 3. For older linux versions with both, use "python3" to initiate script.
##
## USAGE: python3 ssh-reset.py [csv input file]
## EXAMPLE: python ssh-reset.py sample-csv.csv
## 
## Version: 1.0.0
## Updated: 2022-02-19
## Author: Brett Barker - brett.barker@brbtechsolutions.com 
########################################BRB####################################################


from paramiko import AutoAddPolicy, SSHClient
import logging; logging.basicConfig(); 
import time
import csv
import datetime
import sys
import re
import datetime

# Uncomment to turn on debug logging
#logging.getLogger('paramiko.transport').setLevel(logging.DEBUG) 

#GLOBAL VARIABLES
success_hosts = []
fail_hosts = []
SSH_Username = 'help'   # Default value if not changed in user prompt.
SSH_Pass = '1234'       # Default value if not changed in user prompt.

def perform_factory_reset(ip):
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
                if 'Incorrect MAC-address' in out.decode("ascii"):
                    fail_hosts.append(ip)
                else:
                    success_hosts.append(ip)
            else:
                fail_hosts.append(ip)
                
        else:
            print('Error sending reset2factory command')
            fail_hosts.append(ip)

        chan.close()  # Close Shell Channel
        client.close() # Close the client itself
    except:
        print('- Failed connecting to: ' + str(ip))
        fail_hosts.append(ip)
    return

def get_phone_info(ip_address, ssh_user, ssh_pass):
    pass


def main():
    global success_hosts
    global fail_hosts
    global SSH_Username
    global SSH_Pass

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


    ## SETUP RESULTS FILE
    results_file_name = "ssh-reset-results.txt"
    now = datetime.datetime.now()
    results_file = open(results_file_name, 'a')
    results_file.write('\n-----\n' + now.strftime('%Y-%m-%d %H:%M') + ' Starting SSH Reset Script\n')

    ## PROMPT FOR SSH CREDENTIALS
    new_ssh_user = input('Enter SSH Username: [' + SSH_Username + ']: ')
    new_ssh_pass = input('Enter SSH Password: [' + SSH_Pass + ']: ')
    if new_ssh_user:
        SSH_Username = new_ssh_user
        print('New SSH User set: ' + SSH_Username)
    if new_ssh_pass:
        SSH_Pass = new_ssh_pass
        print('New SSH Password set: ' + SSH_Pass)


    ## Check for correct header row with IP field in the input file.
    if not 'IP' in file_dict.fieldnames:
        print('Error: ' + inputfile + ' does not contain a header row with "IP"\n')
        file.close() # Close the input file before erroring out.
        return 0
    ## Change CSV dict into a set of IP addresses.
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
        perform_factory_reset(ip)


    ## Post Results to Terminal
    print('\n---------- RESULTS ----------')
    print('Avaya 11xx Factory Reset Attempts From: ' + inputfile)
    print('Total Attempted: ' + str(countIPs))
    print('Successful Factory Resets: ' + str(len(success_hosts)))
    print('Number of Failures: ' + str(len(fail_hosts)))
    print('** More details in ' + results_file_name + '**')
    print('-----------------------------\n')

    ## Write Results to Results file
    results_file.write('+++ SUCCESSFUL RESETS +++\n')
    for each in success_hosts:
        results_file.write(str(each) + '\n')
    results_file.write('--- FAILURES ---\n')
    for each in fail_hosts:
        results_file.write(str(each) + '\n')

    results_file.write('\n---------- RESULTS FROM ' + now.strftime('%Y-%m-%d %H:%M') + ' ----------\n')
    results_file.write('Avaya 11xx Factory Reset Attempts From: ' + inputfile + '\n')
    results_file.write('Total Attempted: ' + str(countIPs) + '\n')
    results_file.write('Successful Factory Resets: ' + str(len(success_hosts)) + '\n')
    results_file.write('Number of Failures: ' + str(len(fail_hosts)) + '\n')
    results_file.write('----------------------------------------------------------\n')

    results_file.close()
    file.close()
    return 0


# RUN MAIN
if __name__=="__main__":
    main()
