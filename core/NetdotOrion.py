# This class uses API to interact with netdot and Saolarwind Orion NPm server


import re
import requests
from orionsdk import SwisClient
import pynetdot
import ipaddress
import ipaddr


__author__ = "Paul S.I. Basondole"
__version__ = "Code 2.0 Python 3.7"
__maintainer__ = "Paul S.I. Basondole"
__email__ = "bassosimons@me.com"

class NetdotOrionServers():


    def __init__(self,username,password):

        self.username = username
        self.password = password


    def getFromNetdot(self,netdot_url,residentblocks):
        # login to netdot
        pynetdot.setup(url=netdot_url,username=self.username,password=self.password)


        # search netdot for resident block and get its used subnets
        usedSubnetList = [] # list to record used ip subnets from netdot
        try:
            for residentblock in residentblocks:
                for block in pynetdot.Ipblock.search(address=residentblock):
                    for ip in block.children:
                        usedSubnetList.append(ip.address+"/"+str(ip.prefix))

        except requests.exceptions.MissingSchema: return AttributeError # if the URL is not valid
        except AttributeError: return AttributeError # if credentials are wrong
        except requests.exceptions.ConnectionError: return AttributeError # used to raise a dialog for connection issues
        except Exception as e: return e

        #create a list of all /30 from the resident blocks
        allSlash30List = [ip for residentblock in residentblocks for ip in ipaddr.IPNetwork(residentblock).subnet(new_prefix=30)]

        #convert list elements to ip network objects
        usedSubnetList = [ipaddress.ip_network(item) for item in usedSubnetList]
        allSlash30List = [ipaddress.ip_network(item) for item in allSlash30List]


        # iterate through allSlash30List to check if an item in allSlash30List
        # is a subnet of any item in usedSubnetList
        # if not, the item becomes the assigned ip 

        for proposedIPNet in allSlash30List:
            for usedIPNet in usedSubnetList:
                if proposedIPNet.subnet_of(usedIPNet):
                    # move to the next proposed_net
                    break
                else:
                    if str(usedIPNet) != str(usedSubnetList[-1]):
                        # skip the used_net until the last used_net, makes sure we have scanned the proposed_net against all used_net
                        continue
                    else:
                        return proposedIPNet

        return False # no ip address found from netdot





    def saveToNetdot(self,netdotURL,assignedIPNet,service_description=''):
        ''' Saves the assigned IP to netdot database'''

        # login to netdot
        pynetdot.setup(url=netdotURL,username=self.username,password=self.password)

        record = pynetdot.Ipblock()
        record.address = assignedIPNet
        record.description = service_description
        record.status = 5

        # status options
        # container = 0
        # container = 1
        # dicvovered = 2
        # reserved = 4
        # subnet = 5

        try:
            saved_status = record.save()

            if saved_status == True: return True

            else: return False

        except requests.exceptions.HTTPError: return AttributeError
        except requests.exceptions.MissingSchema: return AttributeError # if the URL is not valid
        except AttributeError: return AttributeError # if credentials are wrong
        except Exception as e: return str(type(e))+'\n'+str(e)




    def addNodeToOrion(self,orion_server,client_address,service_description='',engine_id=3):

        # disable SSL warnings
        requests.packages.urllib3.disable_warnings()

        # connect to orion API port=17778
        npm = SwisClient(orion_server, self.username, self.password)

        # define node properties
        # EngineID can be found in the solarwind orion database server

        props = {'IPAddress': client_address,
                 'ObjectSubType': 'ICMP',
                 'EngineID': engine_id,
                 'NodeName': service_description}

        # add the node
        try :

            record = npm.create('Orion.Nodes', **props)
            #extract the node id
            nodeid = re.findall(r'(\d+)$',record)[0]
            #enable ICMP polling
            pollers_enabled = {'N.Status.ICMP.Native': True,
                               'N.ResponseTime.ICMP.Native': True}

            # define pollers properties in a dictionary and create a list of those dicts
            pollers_props = []

            for poller in pollers_enabled:
                pollers_props.append({'PollerType': poller,
                                      'NetObject': 'N:' + nodeid,
                                      'NetObjectType': 'N',
                                      'NetObjectID': nodeid,
                                      'Enabled': pollers_enabled[poller]})

            # update the pollers in orion
            for pollers in pollers_props: npm.create('Orion.Pollers', **pollers)

            # poll the node
            npm.invoke('Orion.Nodes', 'PollNow', 'N:' + nodeid)

            return True

        except ConnectionError: return ConnectionError
        except requests.exceptions.HTTPError: return AttributeError # wrong credentials
        except Exception as e: return '%s\n%s' %(str(type(e)),str(e))




