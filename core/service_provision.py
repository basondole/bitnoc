# This module is part of the core Basondole Tools
# This code provides GUI for user to provison IP service and Martini layer 2 circuits
# Can work with most shell with ssh support but it is further optimized for JunOS, Cisco IOS and IOS XE and Debian


import ipaddr
import ipaddress
from core.NetdotOrion import NetdotOrionServers
from core.send_command import send_command


__author__ = "Paul S.I. Basondole"
__version__ = "2.0"
__maintainer__ = "Paul S.I. Basondole"
__email__ = "bassosimons@me.com"




def provision_ipv4(user,passwd, ipDict, res_block, netdotURL):
    ''' Assign ip address
    '''
    try:
        solardot = NetdotOrionServers(user,passwd)

        if netdotURL:

            assigned_ipv4 = solardot.getFromNetdot(netdotURL,res_block )

            if not assigned_ipv4: # getFromNetdot returns false when it cant find ip
                raise KeyError

            if type(assigned_ipv4) != ipaddress.IPv4Network:
                raise assigned_ipv4

        else: raise AttributeError
        
        # split the /30 to four /32 to easily get the host addresses and
        # get the second /32 (list index 1) the first is the network address
        address_on_pe = (ipaddr.IPNetwork(assigned_ipv4).subnet(new_prefix=32))[1]

        address_on_pe = str(address_on_pe).replace('/32','/30') # change the mask from /32 to /30

        return address_on_pe

    except KeyError:
        # keyerror when pe ip is not valid
        prompt = '''Error during auto provisioning of ipv4 address:
Sytem cannot fix this so please specify the address manually
Could not load data... possible reasons:
- Device not in database
- Resident block is not defined
- Resident block(s) is(are) exhausted'''

        print(prompt)


    except (AttributeError,IndexError):
        # attribute error/index error is when couldnt login netdot
        prompt = f'''Error during auto provisioning of ipv4 address:
Sytem cannot fix this so please specify the address manually
Server: {netdotURL}
Suggetionss
- Verify addess or name of server
- Verify network reachability
- Verify login credentials'''

        print(prompt)


    return False






class CONFIGURE():
    ''' Methods to verify the input data and sends commands to device for configuration
    '''

    def __init__(self,user,key,ipDict, context_output, netdotURL=None, orion_server=None,engine_id=None):


        self.user = user
        self.key = key
        self.netdotURL = netdotURL
        self.orion_server = orion_server
        self.engine_id = engine_id
        self.netWind = NetdotOrionServers('noc','snet123')
        self.confDict = {}
        self.context_output = context_output



    def internet(self, ipDict, data):

        # Collect the input

        PE = data['PE']
        LS = data['LS']
        IF = data['IF']
        VL = data['VL']
        P4 = data['P4']
        P6 = data['P6']
        BW = data['BW']      
        DS = data['DS']
        ND = data['ND']
        SO = data['SO']


        # Validate the input data

        if not IF in ipDict[PE]['interfaces'] or IF.lower()=='null':
            Dialog(parent,prompt="Interface [%s] unknown\n"%IF,icon=self.error)
            return



        if P6:
             try: ipaddress.ip_network(P6,strict=False)
             except Exception as e:
                Dialog(parent,prompt=str(e)+'\n',icon=self.error)
                return



        # Make internet configuration

        if ipDict[PE]['software'] == 'junos':
            commandList = InetConfigPrep.junos(system=LS,iface=IF.strip(),vlan=VL.strip(),ipaddr4=P4.strip(),
                                                   ipaddr6=P6.strip(),cap=BW.strip(),alias=DS.strip())


        elif ipDict[PE]['software'] == 'ios':
            commandList = InetConfigPrep.cisco(system=LS,iface=IF.strip(),vlan=VL.strip(),ipaddr4=P4.strip(),
                                                   ipaddr6=P6.strip(),cap=BW.strip(),alias=DS.strip())


        # Make a configuration dictionary

        self.confDict[PE] = {'software': ipDict[PE]['software'],
                             'hostname': ipDict[PE]['hostname'],
                             'commands': commandList}



        # updating netdot and orion servers 

        assignedIPNet = ipaddress.ip_network(P4,strict=False)
        # get the second /32 from the assigned /30
        # counting from 0 the first is the network, second is provider edge
        try: address_on_ce = (ipaddr.IPNetwork(assignedIPNet).subnet(new_prefix=32))[2]
        except IndexError: address_on_ce = assignedIPNet # if the assigned net is a /32 and not /30
        # remove the prefix length from the client ip
        address_on_ce = str( address_on_ce ).strip('/32')



        if ND or SO:

            info = " Information:\n"
            info += " "+"-"*len(info)
            info += "\n"

        if ND:
            
            if self.netdotURL:
                # save subnet to netdot
                saved_status = self.netWind.saveToNetdot(self.netdotURL,assignedIPNet,service_description=DS)

                if saved_status == True:
                    info += f'  Netdot has been updated [{self.netdotURL}]'

                elif saved_status == False:
                    info += f'  <span style="color: orange">Could not connect to [{self.netdotURL}]</span>'

                elif saved_status == AttributeError:
                    info += f'  <span style="color: orange">Could not connect to [{self.netdotURL}] Verify credentials and server reachability</span>'

                else:
                    info += f'  <span style="color: orange">Could not connect to [{self.netdotURL}] Error [{saved_status}]</span>'

                info += "\n"


        if SO:
            
            if self.orion_server:
                # print(orion_server)
                orion_node = self.netWind.addNodeToOrion(self.orion_server,address_on_ce,service_description=DS,engine_id=self.engine_id)
                # print(orion_node)

                if orion_node == True:
                    info += f'  Orion has been updated [{self.orion_server}]'
                elif orion_node == ConnectionError:
                    info += f'  <span style="color: orange">Could not connect to [{self.orion_server}] Verify server reachability</span>'
                elif orion_node == AttributeError:
                    info += f'  <span style="color: orange">Could not connect to [{self.orion_server}] Verify server login credentials</span>'
                else:
                    info += f'  <span style="color: orange">Could not connect to [{self.orion_server}] Error [{orion_node}]</span>'



        # Send commands to device

        result, prompt = send_command(self.confDict,self.user,self.key, self.context_output)
        result += f'\n{info}'

        return { 'result': result, 'prompt': prompt }





    def l3mpls(self,ipDict, data):

        PE = data['PE']
        LS = data['LS']
        IF = data['IF']
        VL = data['VL']
        VF = data['VF']
        P4 = data['P4']
        P6 = data['P6']
        BW = data['BW']
        DS = data['DS']
        ND = data['ND']
        SO = data['SO']


        # Validate the input data

        if P4:
            try: ipaddress.ip_network(P4,strict=False)
            except Exception as e:
                Dialog(parent,prompt=str(e)+'\n',icon=self.error)
                return


        if P6:
             try: ipaddress.ip_network(P6,strict=False)
             except Exception as e:
                Dialog(parent,prompt=str(e)+'\n',icon=self.error)
                return

        # Make internet configuration

        if ipDict[PE]['software'] == 'junos':
            commandList = L3ConfigPrep.junos(system=LS,iface=IF.strip(),vlan=VL.strip(),vrf=VF.strip(),
                                             ipaddr4=P4.strip(), ipaddr6=P6.strip(),cap=BW.strip(),alias=DS.strip())


        elif ipDict[PE]['software'] == 'ios':
            commandList = L3ConfigPrep.cisco(system=LS,iface=IF.strip(),vlan=VL.strip(),vrf=VF.strip(),
                                             ipaddr4=P4.strip(), ipaddr6=P6.strip(),cap=BW.strip(),alias=DS.strip())



        # Make a configuration dictionary

        self.confDict[PE] = {'software': ipDict[PE]['software'],
                             'hostname': ipDict[PE]['hostname'],
                             'commands': commandList}



        # updating netdot and orion servers 


        assignedIPNet = ipaddress.ip_network(P4,strict=False)
        # get the second /32 from the assigned /30
        # counting from 0 the first is the network, second is provider edge
        try: address_on_ce = (ipaddr.IPNetwork(assignedIPNet).subnet(new_prefix=32))[2]
        except IndexError: address_on_ce = assignedIPNet # if the assigned net is a /32 and not /30
        # remove the prefix length from the client ip
        address_on_ce = str( address_on_ce ).strip('/32')



        if ND or SO:

            info = "Information:\n"
            info += "-"*len(info)
            info += "\n"

        if ND:
            
            if self.netdotURL:
                # save subnet to netdot
                saved_status = self.netWind.saveToNetdot(self.netdotURL,assignedIPNet,service_description=DS)

                if saved_status == True:
                    info += f'Netdot has been updated [{self.netdotURL}]'

                elif saved_status == False:
                    info += f'Could not connect to [{self.netdotURL}]'

                elif saved_status == AttributeError:
                    info += f'Could not connect to [{self.netdotURL}] Verify credentials and server reachability'

                else:
                    info += f'Could not connect to [{self.netdotURL}] Error: [{saved_status}]'

                info += "\n"


        if SO:
            
            if self.orion_server:
                # print(orion_server)
                orion_node = self.netWind.addNodeToOrion(self.orion_server,address_on_ce,service_description=DS,engine_id=self.engine_id)
                # print(orion_node)

                if orion_node == True:
                    info += f'Orion has been updated [{self.orion_server}]'

                elif orion_node == ConnectionError:
                    info += f'Could not connect to [{self.orion_server}] Verify server reachability'

                elif orion_node == AttributeError:
                    info += f'Could not connect to [{self.orion_server}] Verify server login credentials'

                else:
                    info += f'Could not connect to [{self.orion_server}] Error: [{orion_node}]'



        # Send commadas to device

        result, prompt = send_command(self.confDict,self.user,self.key,self.context_output)

        return { 'result': result, 'prompt': prompt }





    def l2mpls(self,ipDict, data):
        

        PE1 = data['PE']
        LS1 = data['LS']
        IF1 = data['IF']
        BW1 = data['BW']

        PE2 = data['PE2']
        LS2 = data['LS2']
        IF2 = data['IF2']
        BW2 = data['BW2']

        MTU = "1500"         

        VL = data['VL']
        VC = data['VL']
        DS = data['DS']
        CW = 'No'

        if CW == 'Yes':
            CW = True
        elif CW == 'No':
            CW = False

        # Make l2mpls configuration


        l2dict = {}

        l2dict[PE1] = [LS1,IF1,VL,BW1,DS,PE2,VC,MTU,CW]
        l2dict[PE2] = [LS2,IF2,VL,BW2,DS,PE1,VC,MTU,CW]

        for pe in l2dict.keys():

            if ipDict[pe]['software'] == 'junos':

                commandList = L2ConfigPrep.junos(system=l2dict[pe][0],iface=l2dict[pe][1],vlan=l2dict[pe][2],
                                                 cap=l2dict[pe][3],alias=l2dict[pe][4],neighbor=l2dict[pe][5],
                                                 vc=l2dict[pe][6],mtu=l2dict[pe][7],cw=l2dict[pe][8])

            elif ipDict[pe]['software'] == 'ios':
                commandList = L2ConfigPrep.cisco(system=l2dict[pe][0],iface=l2dict[pe][1],vlan=l2dict[pe][2],
                                                 cap=l2dict[pe][3],alias=l2dict[pe][4],neighbor=l2dict[pe][5],
                                                 vc=l2dict[pe][6],mtu=l2dict[pe][7],cw=l2dict[pe][8])

            # Update a configuration dictionary

            self.confDict[pe] = {'software': ipDict[pe]['software'],
                                 'hostname': ipDict[pe]['hostname'],
                                 'commands': commandList}



        # Send commadas to device

        result, prompt = send_command(self.confDict,self.user,self.key,self.context_output)

        return { 'result': result, 'prompt': prompt }



class InetConfigPrep:

    @staticmethod
    def junos(system,iface,vlan,ipaddr4,ipaddr6,cap,alias):
        ''' Create  junos config  
        '''

        commandList = []
        if system:
            commandList.append('show configuration logical-systems {} interface {}.{}'.format(system,iface,vlan))
        else:
            commandList.append('show configuration interface {}.{}'.format(iface,vlan))

        commandList.append('configure private')

        if system:
            commandList.append('edit logical-systems %s'%system)

        commandList.append('edit interface {}.{}'.format(iface,vlan))

        if int(vlan) != 0: commandList.append('set vlan-id %s'%vlan)

        if ipaddr4:
            commandList.append('set family inet address %s'%ipaddr4)
            if cap.lower() != 'unlimited':
                commandList.append('set family inet policer input %s'%cap)
                commandList.append('set family inet policer output %s'%cap)

        if ipaddr6:
            commandList.append('set family inet6 address %s'%ipaddr6)
            if cap.lower() != 'unlimited':
                commandList.append('set family inet6 policer input %s'%cap)
                commandList.append('set family inet6 policer output %s'%cap)

        commandList.append('set description "%s"'%alias)
        commandList.append('top')
        commandList.append('show | compare')
        commandList.append('commit and-quit')

        if system: commandList.append('show configuration logical-systems {} interface {}.{}'.format(system,iface,vlan))
        else: commandList.append('show configuration interface {}.{}'.format(iface,vlan))

        commandList.append('show interfaces '+iface+'.'+vlan)

        if ipaddr4:
            if system:
                commandList.append('ping rapid {} logical-system {}'.format(ipaddr4.split('/')[0],system))
                commandList.append('ping rapid 8.8.8.8 source {} logical-system {}'.format(ipaddr4.split('/')[0],system))
            else:
                commandList.append('ping rapid %s'%(ipaddr4.split('/')[0]))
                commandList.append('ping rapid 8.8.8.8 source %s'%(ipaddr4.split('/')[0]))

        if ipaddr6:
            if system:
                commandList.append('ping rapid {} logical-system {}'.format(ipaddr6.split('/')[0],system))
                commandList.append('ping rapid 2001:4860:4860::8888 source {} logical-system {}'.format(ipaddr6.split('/')[0],system))
            else:
                commandList.append('ping rapid %s'%(ipaddr6.split('/')[0]))
                commandList.append('ping rapid 2001:4860:4860::8888 source %s'%(ipaddr6.split('/')[0]))
        return commandList


    @staticmethod
    def cisco(system,iface,vlan,ipaddr4,ipaddr6,cap,alias):
        ''' Creates cisco ios internet config
        '''

        ipaddr4 = (ipaddr.IPv4Network(ipaddr4).with_netmask).replace('/',' ') # convert subnetmask to dotted decimal
        commandList = []
        system = False

        if int(vlan) !=0:
            commandList.append('show running-config interface {}.{}'.format(iface,vlan))
        else: commandList.append('show running-config interface %s'%iface)

        commandList.append('configure terminal')

        if int(vlan) !=0:
            commandList.append('interface {}.{}'.format(iface,vlan))
            commandList.append('encapsulation dot1q %s'%vlan)
        else: commandList.append('interface %s'%iface)

        if ipaddr4:
            commandList.append('ip address %s'%ipaddr4)
            if cap.lower() != 'unlimited':
                commandList.append('service-policy input %s'%cap)
                commandList.append('service-policy output %s'%cap)

        if ipaddr6:
            commandList.append('ipv6 address %s'%ipaddr6)
            if cap.lower() != 'unlimited':
                commandList.append('service-policy input %s'%cap)
                commandList.append('service-policy output %s'%cap)

        commandList.append('description %s'%alias)
        commandList.append('end')
        commandList.append('write memory\n') # add newline character to confirm if it prompts for confirmation


        if int(vlan) !=0:
            commandList.append('show running-config interface {}.{}'.format(iface,vlan))
            commandList.append('show interfaces '+iface+'.'+vlan)
        else:
            commandList.append('show running-config interface %s'%iface)
            commandList.append('show interfaces '+iface)


        if ipaddr4:
            commandList.append('ping {} timeout 0'.format(ipaddr4.split()[0]))
            commandList.append('ping 8.8.8.8 source {} timeout 0'.format(ipaddr4.split()[0]))

        if ipaddr6:
            commandList.append('ping %s timeout 0'%(ipaddr6.split('/')[0]))
            commandList.append('ping 2001:4860:4860::8888 source %s timeout 0'%(ipaddr6.split('/')[0]))

        return commandList




class L3ConfigPrep:

    @staticmethod
    def junos(system,iface,vlan,vrf,ipaddr4,ipaddr6,cap,alias):

        commandList = []
        if system: commandList.append('show configuration logical-systems '+system+' interface '+iface+'.'+vlan)
        else: commandList.append('show configuration interface '+iface+'.'+vlan)
        commandList.append('configure private')
        if system: commandList.append('edit logical-systems '+system)
        commandList.append('edit interface '+iface+'.'+vlan)
        if int(vlan) != 0:
            commandList.append('set vlan-id '+vlan)
        if ipaddr4:
            commandList.append('set family inet address '+ipaddr4)
            if cap.lower() != 'unlimited':
                commandList.append('set family inet policer input '+cap)
                commandList.append('set family inet policer output '+cap)
        if ipaddr6:
            commandList.append('set family inet6 address '+ipaddr6)
            if cap.lower() != 'unlimited':
                commandList.append('set family inet6 policer input '+cap)
                commandList.append('set family inet6 policer output '+cap)
        commandList.append('set description "'+alias+'"')
        commandList.append('up 3')
        commandList.append('edit routing-instance '+vrf)
        commandList.append('set interface '+iface+'.'+vlan)
        commandList.append('top')
        commandList.append('show | compare')
        commandList.append('commit and-quit')

        if system: commandList.append('show configuration logical-systems '+system+' interface '+iface+'.'+vlan)
        else: commandList.append('show configuration interface '+iface+'.'+vlan)

        commandList.append('show interfaces '+iface+'.'+vlan)

        if ipaddr4:
            if system:
                commandList.append('ping rapid routing-instance %s %s logical-system %s'%(vrf,ipaddr4.split('/')[0],system))
            else:
                commandList.append('ping rapid routing-instance %s %s'%(vrf,ipaddr4.split('/')[0]))
        if ipaddr6:
            if system:
                commandList.append('ping rapid routing-instance %s %s logical-system %s'%(vrf,ipaddr6.split('/')[0],system))
            else:
                commandList.append('ping rapid routing-instance %s %s'%(vrf,ipaddr6.split('/')[0]))

        return commandList



    @staticmethod
    def cisco(system,iface,vlan,vrf,ipaddr4,ipaddr6,cap,alias):

        ipaddr4 = (ipaddr.IPv4Network(ipaddr4).with_netmask).replace('/',' ')
        commandList = []
        system = False

        if int(vlan) !=0:
            commandList.append('show running-config interface '+iface+'.'+vlan)
        else: commandList.append('show running-config interface '+iface)
        commandList.append('configure terminal')
        if int(vlan) !=0:
            commandList.append('interface '+iface+'.'+vlan)
            commandList.append('encapsulation dot1q '+vlan)
        else: commandList.append('interface '+iface)
        commandList.append('vrf forwarding '+vrf)
        if ipaddr4:
            commandList.append('ip address '+ipaddr4)
            if cap.lower() != 'unlimited':
                commandList.append('service-policy input '+cap)
                commandList.append('service-policy output '+cap)
        if ipaddr6:
            commandList.append('ipv6 address '+ipaddr6)
            if cap.lower() != 'unlimited':
                commandList.append('service-policy input '+cap)
                commandList.append('service-policy output '+cap)
        commandList.append('description '+alias)
        commandList.append('end')
        commandList.append('write memory\n') # add newline character to confirm if it prompts for confirmation

        if int(vlan) !=0:
            commandList.append('show running-config interface '+iface+'.'+vlan)
            commandList.append('show interfaces '+iface+'.'+vlan)
        else:
            commandList.append('show running-config interface '+iface)
            commandList.append('show interfaces '+iface)


        if ipaddr4:
            commandList.append('ping vrf %s %s timeout 0'%(vrf,ipaddr4.split()[0]))
        if ipaddr6:
            commandList.append('ping vrf %s %s timeout 0'%(vrf,ipaddr6.split()[0]))

        return commandList




class L2ConfigPrep:

    @staticmethod
    def junos(system,iface,vlan,cap,alias,neighbor,vc,mtu,cw=True):
        commandList = []
        if system: commandList.append('show configuration logical-systems '+system+' interface '+iface+'.'+vlan)
        else: commandList.append('show configuration interface '+iface+'.'+vlan)
        commandList.append('configure private')
        if system: commandList.append('edit logical-systems '+system)
        commandList.append('edit interface '+iface+'.'+vlan)
        if int(vlan) != 0:
            commandList.append('set vlan-id '+vlan)
        commandList.append('set encapsulation vlan-ccc')
        if cap.lower() != 'unlimited':
            commandList.append('set family ccc policer input '+cap)
            commandList.append('set family ccc policer output '+cap)
        commandList.append('set description "'+alias+'"')
        commandList.append('exit')
        commandList.append('edit protocols l2circuit')
        commandList.append('edit neighbor '+neighbor)
        commandList.append('edit interface '+iface+'.'+vlan)
        commandList.append('set description "'+alias+'"')
        commandList.append('set virtual-circuit-id '+vlan)
        if mtu: commandList.append('set mtu '+mtu)
        if not cw: commandList.append('set no-control-word')

        commandList.append('top')
        commandList.append('show | compare')
        commandList.append('commit and-quit')

        if system:
            commandList.append(f'show configuration logical-systems {system} interface {iface}.{vlan}')
        else:
            commandList.append('show configuration interface '+iface+'.'+vlan)

        commandList.append('show interfaces '+iface+'.'+vlan)

        if system:
            commandList.append('show configuration logical-systems '+system+' protocols l2circuit neighbor '
                               +neighbor+' interface '+iface+'.'+vlan)
        else:  commandList.append('show configuration protocols l2circuit neighbor '
                                   +neighbor+' interface '+iface+'.'+vlan)

        if system:
            commandList.append('show l2circuit connections interface '
                               +iface+'.'+vlan+' neighbor '+neighbor+' summary  logical-system '+system)
        else:
            commandList.append('show l2circuit connections interface '
                                   +iface+'.'+vlan+' neighbor '+neighbor+' summary')

        if system: commandList.append('ping mpls l2circuit interface '+iface+'.'+vlan+
                          ' logical-system '+system+' reply-mode application-level-control-channel')
        else: commandList.append('ping mpls l2circuit interface '+iface+'.'+vlan+
                          ' reply-mode application-level-control-channel')

        return commandList


    @staticmethod
    def cisco(system,iface,vlan,cap,alias,neighbor,vc,mtu,cw=True):

        commandList = []
        system = False
        if int(vlan) !=0:
            commandList.append('show running-config interface '+iface+'.'+vlan)
        else: commandList.append('show running-config interface '+iface)
        commandList.append('configure terminal')
        if not cw:
             commandList.append('pseudowire-class L2CIRCUIT')
             commandList.append('encapsulation mpls')
             commandList.append('no control-word')
        if int(vlan) !=0:
            commandList.append('interface '+iface+'.'+vlan)
            commandList.append('encapsulation dot1q '+vlan)
        else: commandList.append('interface '+iface)
        if cap.lower() != 'unlimited':
            commandList.append('service-policy input '+cap)
            commandList.append('service-policy output '+cap)
        commandList.append('description "'+alias+'"')
        if not cw:
            commandList.append('xconnect '+neighbor+' '+vc+' pw-class L2CIRCUIT')
        else: commandList.append('xconnect '+neighbor+' '+vc+' encapsulation mpls')
        if mtu: commandList.append('mtu '+mtu)


        commandList.append('end')
        commandList.append('write memory\n') # add newline character to confirm if it prompts for confirmation

        if int(vlan) !=0:
            commandList.append('show running-config interface '+iface+'.'+vlan)
            commandList.append('show interfaces '+iface+'.'+vlan)
        else:
            commandList.append('show running-config interface '+iface)
            commandList.append('show interfaces '+iface)


        if int(vlan) !=0:
            commandList.append('show xconnect interface '+iface+'.'+vlan)
        else: commandList.append('show xconnect interface '+iface)

        commandList.append('ping mpls pseudowire '+neighbor+' '+vc+' timeout 0')

        return commandList


