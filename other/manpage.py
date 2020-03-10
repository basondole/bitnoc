# This code contains directives on the use of Basondole Tools
# Serves as  embeded manual in the core program

__author__ = "Paul S.I. Basondole"
__version__ = "2.0"
__maintainer__ = "Paul S.I. Basondole"
__email__ = "bassosimons@me.com"

def manpage():

    man = r'''
 +--------------------+
 | DEVELOPER MESASAGE |
 +--------------------+

 What this tool accomplishes may seem basic at first, but these are common and critical tasks within the service provider realm, meaning they hold high value in the automation arena.
 

+-----------------+
| TOOLBAR OPTIONS |
+-----------------+

 Home           Takes user to the main screen of the program where user can navigate other operations

 Devices        Provides a view of the devices the program can interact with.
                That is if the user can authenticate against the device successfully.
                The window offers options to add or remove devices from the database.
                If device is not in this list the program will not operate on it.
                Editing of device parameters in the database is no currently supported, to edit the device you have to re-add it with respective attributes
                When devices are added or removed, system must be reloaded for changes to take effect.

 Command        Provides use with a window to input arguments.
                Allows user to specify two arguments. 
                First argument is commands which can be a string or list of commands separated by ":" or text file containing commands separated by a newline
                Second argument is ip address which can be a string or a text file containing ip addresses separated by a new line
                The ip address(es) specified in this window do not need to be in the devices list from above window.

 Settings       Provides user with three tabs for settings.
                - General settings includes the authentication server and the file path to the device database. 
                  User must only specify the path of the directory that will contain the device database file, the database file itself will be created by the program with a ".bas" extension
                - Burst packages provides user with settings to specify the burst package server address and the full path to the burst client file.
                  Full path includes the file name and extension. If these settings are not specified the burst package operations will be disabled.
                - Bandwidth on Demand provides settings associated with the server for bandwidth on demand services. 
                  User must manually create two directories in the working directory path sepecified in settings. 
                  The two directories to be created in the server are "PendingTickets" and "Logs". The directory names are case sensitive.
                  If these settings are not specified the bandwidth on demand operations will be disabled.
                When settings are altered, system must be reloaded for changes to take effect.


 About          Provides user with information about the program    

 Quit           Exits the program



+---------------------+
| MAIN WINDOW OPTIONS |
+---------------------+



 Vlan operation         [OPTIONS]

                        Vlan Finder:
                            Provides user with a window where they can choose a router from the IP list and the respective interface
                            From which the program will return a list of free vlans in a separate output window. This works on a single IP address chosen.
                            User has the flexibility of specifying the range of interest by using the radio button options

                        Vlan Finder2:
                            Provides user with a window where they can choose two router from the IP list and their respective interface
                            From which the program will return a list of co-existing free vlans from the two routers in a separate output window. This works on a the two IP addresses chosen.
                            User has the flexibility of specifying the range of interest by using the radio button options.
                            Useful for layer 2 pseudowires and for identifying free vlans from two interfaces of the same router.

                        Locate vlan:
                            Provides user with a window to input the VLAN id and the program returns the list of IP addresses from the devices database in which the VLAN id has been used.
                            If the respective interface of the router has been configured with interface description, the description is also included in the output.


 Ipv4 operation         [OPTIONS]

                        Locate address: 
                            Provides user with a window to input an IP address (with prefix length) or subnet (with prefix length)
                            The program then returns the list of IP addresses from the devices database in which the IP/subnet or its subnets have been used.
                            Includes support for VRFs and logical systems for JunOS.
                            For cisco IOS and IOSXE software search sections are [access-list|interfaces|ip route|prefix-lists].
                            For juniper JunOS search hierarchies are [interfaces|static route|route-filter|prefix-lists]



 Locate service         [OPTIONS]

                        Locate vlan:
                            Provides user with a window to input the VLAN id and the program returns the list of IP addresses from the devices database in which the VLAN id has been used.
                            If the respective interface of the router has been configured with interface description, the description is also included in the output.

                        Locate address: 
                            Provides user with a window to input an IP address (with prefix length) or subnet (with prefix length)
                            The program then returns the list of IP addresses from the devices database in which the IP/subnet or its subnets have been used.
                            For cisco IOS and IOSXE software search sections are [access-list|interfaces|ip route|prefix-lists].
                            For juniper JunOS search hierarchies are [interfaces|static route|route-filter|prefix-lists]

                        Locate name:
                            Provides user with a window to input the name of service or client. This name must be part of the description of the interface assosicated with the client.
                            The program then returns the list of IP addresses from the devices database in which the name is found.
                            Supports regular expression for input however the regular expression style must be supported by the device operationg system.
                            JunOS and Cisco IOS and IOS XE do not support GNU notations for regular expressions such as \d or \s or \w as well as quantifiers in curly brackets {}
                            With JunOS the length of the pattern and command used to search for the pattern altogher can only be as long 65499 bytes about 


 Burst packages         Provides functionality to manage bandwidth change configuration for burst clients.
                        This functionality requires a server whith which to sync data. The burst server is specified in the settings tab for burst packages.
                        The burst server must exist and it must have the burstman code installed.
                        The server must be linux based. More on server setup is covered in bBurt section.

                        Dependancies:
                            burstman code
                            crontab which will schedule the running of the burstman code
                            python which is the language used to write the burstman code

                        [OPTIONS]

                        Add a client:
                            Provides user a window to add details pertaining to addition of a new client to the system.
                            This operation is done on the burst server specified on the settings tab. The server details will be shown on the top of this window.
                            If the server details and file paths have not been specified this option will be unavailable.

                        Remoce client
                            Provides user a window to specify details pertaining to removal of an existing client from the system.
                            This operation is done on the burst server specified on the settings tab. The server details will be shown on the top of this window.
                            If the server details and file paths have not been specified this option will be unavailable.

                        Move client
                            Provides user a window to modify details pertaining to an existing client to the system.
                            User is only required to specify the updated information related to the client.
                            This operation is done on the burst server specified on the settings tab. The server details will be shown on the top of this window.
                            If the server details and file paths have not been specified this option will be unavailable.

                        View clients
                            Provides user a window to view all the existing clients in the system with their respective packages.
                            The presentation format will be in a human readable easy to understand text form, each line presents a single client.
                            If the server details and file paths have not been specified this option will be unavailable.


 B on Demand            Provides functionality to manage bandwidth change configuration for clients with on demand capacity requirements.
                        This functionality requires a server whith which to sync data.
                        The server is specified in the settings tab for bandwidth on demand.
                        The bandwidth on demand server must exist and it must have the willdo code installed.
                        The server must be linux based. More on bandwidth on demand is covered in bandwodth on demand section.

                        Dependancies :
                            at which will schedule the running of the willdo code
                            sed and awk
                            willdo 
                            python which is the language used to write the burstman code

                        [OPTIONS]

                        Add a ticket:
                            Provides user a window to add details pertaining to current and the demanded bandwidth subscriptions and the required duration.
                            This information is saved on the bandwidth on demand server specified in the settings tab. The server details will be shown on the top of this window.
                            The program will generate a script to revert the bandwidth subscription and schedule the task on the specified date.
                            If the server details and file paths have not been specified this option will be unavailable.

                        Delete ticket
                            Provides user a window from which to remove a pending ticket from the system.
                            This operation is done on the bandwidth on demand server specified on the settings tab. The server details will be shown on the top of this window.
                            If the server details and file paths have not been specified this option will be unavailable.

                        Update ticket
                            Provides user a window to modify details pertaining to an existing ticket in the system.
                            User is only required to specify the updated information related to the ticket.
                            This operation is done on the bandwidth on demand server specified in the settings tab. The server details will be shown on the top of this window.
                            If the server details and file paths have not been specified this option will be unavailable.

                        View tickets
                            Provides user a window to view all the pending tickets in the system with their respective due dates.
                            The presentation format will be in a human readable text form.
                            If the server details and file paths have not been specified this option will be unavailable.




 Provision service      Provides user with a dedicate window for service provisioning.

                        [OPTIONS]

                        Internet:
                            Currently support provisioning of internet services.
                            For internet provisioning the program offers support for both ipv4 and ipv6 with auto vlan listing and bandwidth policing.
                            This wizard can also be used to partially provision layer 3 MPLS in terms of IP address assignment, traffic policing and vlan selection.
                            No support for advanced layer 3 MPLS VRFs and routing configurations.
                            After the system configures the service it will display what has been done before and after as well as the results of reachability test on the provisoned service.


                        Layer 3 MPLS:

                        Layer 2 MPLS:           
                            Provide support for player 2 MPLS pseudowires/l2circuits Martini based using targeted LDP.
                            The program auto vlan listing and bandwidth policing and auto virtual-circuit-id selection.
                            The MTU must be explicitly specified. This is to facilitate multi vendor compatibility.
                            After the system configures the service it will display what has been done before and after as well as the results of reachability test on the provisoned service.
                                        
                        Testing methodology:
                            For layer 2 MPLS the latest device to commit the configuration will have the most accurate reachability test. Despite the fact that the devices will be configured simultaneously,
                            one of the device will complete the configuration faster than the other and will ran tests while the other device is still provisioning the test. 
                            This is not an error as the processing speed of the device depends on the device hardware resources and response time with respect to this program.
                            Therefore if the output of the tests from the two devices are similar the test is conclusive.
                            If they differ the successful test is the conlusive test.

                        Note: Only devices with valid interfaces will be available in this menu. Devices which could not be contacted during program loading will be excluded.


+------------------------------------+
| BURST PACKAGE SERVER CONFIGURATION |
+------------------------------------+

 Requirement:
    - crontab
    - burstman executbale


 Installation steps on server:
 1. Create a main directory

 2. Put the device database in this main directory; the device database is a file designated as "devices.yml". You can copy the file from a windows PC running this client end application

 3. Create a burstman directory to put the burst client database

 4. Create a file "burstclients.db" in the directory above and put a test client as shown below
    pe=192.168.56.36  interface=em1   vlan=400   daybandwidth=1M   nightbandwidth=5M   starttime=1800  endtime=0800  days=weekends  sitename=test_site
    Note: the bandwidth column must contain the bandwith policer or service policy name as specified in the respective router in the pe column. This is one time setup and the process will be automated later.

 5. Put the burstman executable in the burstman directory created in step 3 above. Use the Debian version for ubuntu server or Redhat version for Centos Server if using executable binary otherwise put the burstman raw code instead.

 6. Create a "log" directory within the directory created in step 3 above

 7. Run the burstman executable with option -testip and -creddir
    Option -testip is used to test credentials against the secified IP address, use any active IP iaddress in your network
    Option -creddir is used to specify the full path to the directory you want to save your router credential for auto-retrieval and logins
    it is recommended the credential directory be the same as the directory created in step 1 above,

        user@server:~/docs/burstmanager$ burstman -testip 192.168.56.36 -creddir "/home/basondole/docs/burstmanager/"
        Username:

    You will be promted to enter username and password. This will validate your credentials and store them in the specified path in an encrypted format.
    After above you can re-run the command to verify and you should get a message "INFO: username and password auto-retrieved"

        user@server:~/docs/burstmanager$ burstman -testip 192.168.56.36 -creddir "/home/basondole/docs/burstmanager/"
        INFO: username and password auto-retrieved
        Sun Apr  7 06:09:22 2019 (user = paul) initializing connection   192.168.56.36
        Sun Apr  7 06:09:22 2019 (user = paul) authentication starting 192.168.56.36  
        Sun Apr  7 06:09:22 2019 (user = paul) passed authentication > 192.168.56.36  
        Credential saved successfully

    Use similar metodology to modify the credentials or regenerate the credential file if it gets corrupted or if you intend to change the credentials file directory.


 8. The burstman must be executed with other options in order to do the auto configurations and logging. Use below option to run burstman
    All of the below options must be specified when running burstman
        Option -creddir  specifies the credential directory path
        Option -ipdb     specifies the device ip address database path
        Option -clientdb specifies the clients database path
        Option -logdir   specifies the log directoy path
    

    eg: user@server:~/docs/burstmanager$ burstman -creddir "/home/basondole/docs/burstmanager/" -ipdb "/home/basondole/docs/burstmanager/devices.yml" -clientdb "/home/basondole/docs/burstmanager/burstclients.db" -logdir "/home/basondole/docs/Logs/"
    
    If no errors are generated. The setup is succesful. If you get error messages revisit steps 1 through 8

 9. Create a cronjob to run at desired time depeding on your packages start and end times
    For testing create a cronob to run every 5 minutes

    basondole@bigpaul:~$ crontab -l | egrep "^\*"
    */5 * * * * cd /home/basondole/doc/burstmanager && /home/basondole/docs/burstmanager/burstman -creddir "/home/basondole/docs/burstmanager/" -ipdb "/home/basondole/docs/burstmanager/device.yml" -clientdb "/home/basondole/docs/burstmanager/clients.db" -logdir "/home/basondole/docs/logs/"  1>> /home/basondole/docs/logs/cron.log 2>> /home/basondole/docs/logs/cron.err
    basondole@bigpaul:~$ 

    For reference and this cronjob will put the stdout of the executed cron job to a file cron.log and the std error to cron.err

    This cronjob runs every 5 minutes. When it runs;
    - It goes to dicrectory /home/basondole/doc/burstmanager
    - Then run /home/basondole/docs/burstmanager/burstman -creddir "/home/basondole/docs/burstmanager/" -ipdb "/home/basondole/docs/burstmanager/devices.yml" -clientdb "/home/basondole/docs/burstmanager/clients.db" -logdir "/home/basondole/docs/logs/"
    - Then save the output from cron execution to /home/basondole/docs/logs/cron.log
    - and save cron encoutered errors to /home/basondole/docs/logs/cron.err 

 10. Logging
        In addition to the stdout and std error loggin done by cron in step 9 above. burstman creates two types of log file.
        The log file will be created in the log directory specified with the -logdir option
        Type 1 log:
            192.168.56.57-cmd.log this will show the commands that have been issued by burstman to the pe ip 192.168.56.57
        Type 2 log:
            192.168.56.57-cli.log   this will show the actual interaction between burstman and the cli for the pe ip 192.168.56.57 with time stamps

 11. For client application connection authentication to this server refer CLIENT SERVER ATHENTICATION section




+----------------------------+
| BANDWIDTH on DEMAND SERVER |
+----------------------------+

 Requirement:
    - at
    - bash
    - awk
    - sed 
    - sendmail
    - willdo executabe

 Installation steps:

 1. Create a main directory

 2. Put the device database in this main directory; the device database is a file designated as "devices.yml". You can copy the file from a windows PC running this client end application

 3. Create a ondemand directory

 4. Put the willdo executable in the directory created in step 3 above

 5. In the directory created in step 3 above create two other directories named "Logs" and "PendingTickets" names are case sensitive

 6. Run willdo executable with options -commands and -ipaddress, you will be promted to enter username and password. This will validate your credentials and store them in current directory in an encrypted format. This process will save your credentials in an encrypted format and they will be used in future scheduled tasks.

    Use any command of your preference as the command option and any ip address active in the network
    
        user@server:~/docs/bOd$./willdo -commands "show system alarms" -ipaddress 192.168.56.36
        Username: fisi
        Password:
        Sat Jun 15 04:14:03 2019 (user = fisi) passed authentication > 192.168.56.36
        [192.168.56.36]
           fisi@big> show system alarms
           No alarms currently active

    After above you can re-run the command to verify and you should get a message "INFO: username and password auto-retrieved"

        user@server:~/docs/bOd$ ./willdo -commands "show system alarms" -ipaddress 192.168.56.36
        INFO: username and password auto-retrieved
        Sat Jun 15 04:19:09 2019 (user = fisi) passed authentication > 192.168.56.36

        [192.168.56.36]
           fisi@big> show system alarms
           No alarms currently active

    Use similar metodology to modify the credentials or regenerate the credential file if it gets corrupted or if you change the credentials file directory.


 7. For client application to this server authenticaton refer CLIENT SERVER ATHENTICATION section

 8. All tickets added from the client apptication go to the PendingTickets directory created in step 5

 9. Loggint of executed tasks will be saved in the Logs directory created in step 5 above

 10. If the server is configured with mail capabilities an email will be sent to the configured mail box




+------------------------------+
| CLIENT SERVER AUTHENTICATION |
+------------------------------+

 While access to devices is limited to the use of username and password. Clients will use keys to authenticate with the server in order to add, view or remove clients.
 The user of the client must create an rsa key that will be added to the authorised keys in the server.

 Creating keys in windows with OpenSSH:

 1. go to c:\windows\system32\openssh

 2. run ssh-keygen

 3. Ouput below
    c:\Windows\System32\OpenSSH>ssh-keygen.exe
    Generating public/private rsa key pair.
    Enter file in which to save the key (C:\Users\u/.ssh/id_rsa): C:\Users\u\.ssh\id_rsa
    Enter passphrase (empty for no passphrase):
    Enter same passphrase again:
    Your identification has been saved in C:\Users\u\.ssh\id_rsa.
    Your public key has been saved in C:\Users\u\.ssh\id_rsa.pub.
    The key fingerprint is:
    SHA256:BZLZjkj7OYTqMw4xQekJwgDO7PS0jgoyQUMkQIRyDeo paul@LWBS-STZ-150YNL
    The key's randomart image is:
    +---[RSA 2048]----+
    |#*oo  .+.        |
    |%+. o o...       |
    |BO.o + o  .      |
    |=++ = o ..       |
    |+E + o .S        |
    | ++   +          |
    |=o .   .         |
    |+o+              |
    |...o             |
    +----[SHA256]-----+

    c:\Windows\System32\OpenSSH>

 4. Open the location and copy the public key

 5. Open the server and edit the authorized host to add the copied key above

    basondole@bigpaul:~/.ssh$ nano authorized_keys
    ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCZG.....

 6. Open settings window of the client application and add the path to the gerated private key


 +------+
 | APIs |
 +------+

 This client application can interface with Netdot and Solarwind Orion NPM. User is required to configure the server details in settings for these operations to work.
 The usename and password used to authenitcate on those servers must be similar to the username and password used for ssh login to the router and they are input by user during application startup
     '''

    return man




if __name__=='__main__':
    print(manpage())
