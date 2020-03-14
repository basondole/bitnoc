# This module is part of the core Basondole Tools
# This code provides a GUI to manage devices invetory in Basondole Tools

import yaml
import ipaddress
from other.Essential import dotted


__author__ = "Paul S.I. Basondole"
__version__ = "2.0"
__maintainer__ = "Paul S.I. Basondole"
__email__ = "bassosimons@me.com"


class Devices():



    def addDevice(ip_dict, taarifa, path):

        software = taarifa['software']
        hostname = taarifa['hostname'].replace(" ","_")
        ipaddr = taarifa['ipv4']
        blocks = taarifa['blocks']
        systems = taarifa['systems']

        try: ipaddress.IPv4Address(ipaddr)
        except Exception as e:
            prompt = "IPv4 Error: "+str(e)
            return prompt

        if not software or not hostname:
            prompt = 'Enter hostname and software'
            return prompt

        #initialize a device record
        ip_dict[ipaddr] = {}
        ip_dict = dotted(ip_dict)
        ip_dict[ipaddr].software = software
        ip_dict[ipaddr].hostname = hostname
        ip_dict[ipaddr].synced = False
        ip_dict[ipaddr].logicalsystem = {}

        
        try:
            blocksvar, sysvar = done(blocks, systems)
        except ValueError: # if a string message is returned
            return done(blocks, systems)

        if type(sysvar) == dict:
            ip_dict[ipaddr].logicalsystem = sysvar

        if type(blocksvar):

            ip_dict[ipaddr].residentblock = [] # main system blocks

            for block in list(set(blocksvar)): # initialize resident block holder for logical system
               if ':' in block:
                   name = block.split(':')[0]
                   ip_dict[ipaddr].logicalsystem[name].update({'residentblock': []})

            for block in list(set(blocksvar)):
               if ':' in block:
                   name = block.split(':')[0]
                   resb = block.split(':')[1]
                   ip_dict[ipaddr].logicalsystem[name]['residentblock'].append(resb)
               else:
                   ip_dict[ipaddr].residentblock.append(block)


        
        Devices.save_to_file(ip_dict, path)

        return True





    def removeDevice(ip_dict, ipaddr, path="./"):
        try:
            ip_dict.pop(ipaddr)
        except KeyError:
           msg = f"Device with address { ipaddr } not found"
           return msg
        Devices.save_to_file(ip_dict, path)
        return True

    def save_to_file(ip_dict, path):

        ip_dict = dotted(ip_dict)
        keylist = list(ip_dict.keys())
        keylist.sort()

        with open(path+'devices.yml','w') as f:
            # initialize the yaml device file
            f.write('---\n')

            # write the dict in yaml format
            for key in keylist:
                f.write(key+':\n')
                for x in range(4): f.write(' ')
                f.write('software: '+ip_dict[key].software.lower()+'\n')

                for x in range(4): f.write(' ')
                f.write('hostname: '+ip_dict[key].hostname.lower()+'\n')

                for x in range(4): f.write(' ')
                f.write('logicalsystem:\n')
                try:
                    for systemname in ip_dict[key].logicalsystem.keys():
                        for x in range(8): f.write(' ')
                        f.write(systemname+':\n')
                        for x in range(12): f.write(' ')
                        f.write('ip: '+ip_dict[key].logicalsystem[systemname]['ip']+'\n')
                        for x in range(12): f.write(' ')
                        f.write('residentblock:\n')
                        try:
                            for block in ip_dict[key].logicalsystem[systemname]['residentblock']:
                                for x in range(16): f.write(' ')
                                f.write('- '+block+'\n')
                        except Exception as e: # when the above optional attributes are not set
                            pass

                except (KeyError,TypeError,AttributeError):pass

                for x in range(4): f.write(' ')
                f.write('residentblock:\n')
                try:
                    for block in ip_dict[key].residentblock:
                        for x in range(8): f.write(' ')
                        f.write('- '+block+'\n')
                except Exception as e: # when the above optional attributes are not set
                    pass

                f.write('\n')

        return True





def done(blocks, systems): 

    blocksvar = []
    sysvar = {}

    for item in blocks:
        item = item.strip()
        if item :
            try : 
                if ':' in item:
                    ipaddr4 =item.split(':')[0]+':'+str(ipaddress.IPv4Network(item.split(':')[1]))
                else:
                    ipaddr4 = ipaddress.IPv4Network(item,strict=True)
            except Exception as e:
                msg ="Error: "+str(e)
                print(f'\nERROR: Devices.py via function done says: resident block error: {msg}\n')
                return msg
            blocksvar.append(str(ipaddr4))


    for item in systems:
        item = item.strip()
        if item :
            if len(item.split(':')) !=2:
                msg = "Specify with valid format for "+ item
                print(f'logical systems error: {msg}')
                return msg
            try:
                ipaddress.IPv4Address(item.split(':')[1])
            except Exception as e:
                msg = str(e)
                print(f'logical systems error: {msg}')
                return msg
        
            sysvar[item.split(':')[0]] = {'ip': item.split(':')[1],'residentblock':[]}

    return blocksvar, sysvar



def group_devices(ip_dict,option=None):
   ipList = list(ip_dict.keys())
   ipList.sort()

   cisco_devices = ''
   juniper_devices = ''
   other_devices = ''

   for line in ipList:
        try:
           if 'junos' in ip_dict[line]['software']:
               if not ip_dict[line]['synced'] :
                 juniper_devices += ip_dict[line]['ip'].ljust(15)+' ['+ip_dict[line]['hostname']+\
                                                    ' synced: NO ]\n'

               else:
                   juniper_devices += ip_dict[line]['ip'].ljust(15)+' ['+ip_dict[line]['hostname']+\
                                      ' VRFs: '+str(len(ip_dict[line]['instances']))+']\n'

           elif 'ios' in ip_dict[line]['software']:
               if not ip_dict[line]['synced'] :
                  cisco_devices += ip_dict[line]['ip'].ljust(15)+' ['+ip_dict[line]['hostname']+\
                                                    ' synced: NO ]\n'
               else:
                  cisco_devices += ip_dict[line]['ip'].ljust(15)+' ['+ip_dict[line]['hostname']+\
                                    ' VRFs: '+str(len(ip_dict[line]['instances']))+']\n'

           else:
               other_devices += ip_dict[line]['ip'].ljust(15)+' ['+ip_dict[line]['software'].ljust(10)+\
                                ' '+ip_dict[line]['hostname']+']\n'
        except Exception as e: 
            try:
                other_devices += ip_dict[line]['ip'].ljust(15)+' ['+ip_dict[line]['software']+' Error:'+str(e)+' '+str(ip_dict[line]['errors'])+' ]\n'
            except Exception as e: print(line,e)

   all_devices = f'''
   <div class="table table-active">
       <label style="margin-left: 5px;">Cisco</label>
   </div>
   <pre>{cisco_devices}</pre>
   <br/><br/>
   <div class="table table-active">
       <label style="margin-left: 5px;">Juniper</label>
   </div>
   <pre>{juniper_devices}</pre>
   <br/><br/>
   <div class="table table-active">
       <label style="margin-left: 5px;">Others</label>
   </div>
   <pre>{other_devices}</pre>
   <br/>
   '''

   if option == 'juniper':return juniper_devices
   elif option == 'cisco' : return cisco_devices

   else: return all_devices



def raw(ip_dict):
    ''' Given dictionary or dotted dictionary return yaml formatted string
    '''

    keylist = list(ip_dict.keys())
    keylist.sort()
    raw_output = ''

    for key in keylist:
        # skip logical systems
        try:
            if ip_dict[key]['systemname']:
                continue
        except: pass

        raw_output+=(ip_dict[key]['ip']+'\n')

        for x in range(4): raw_output+=(' ')
        raw_output+=('ip: '+ip_dict[key]['ip'].lower()+'\n')

        for x in range(4): raw_output+=(' ')
        raw_output+=('software: '+ip_dict[key]['software'].lower()+'\n')

        for x in range(4): raw_output+=(' ')
        raw_output+=('logicalsystem:\n')
        try:
            for systemname in ip_dict[key]['logicalsystem'].keys():
                for x in range(8): raw_output+=(' ')
                raw_output+=(systemname+':\n')
                for x in range(12): raw_output+=(' ')
                raw_output+=('ip: '+ip_dict[key]['logicalsystem'][systemname]['ip']+'\n')
                for x in range(12): raw_output+=(' ')
                raw_output+=('residentblock:\n')
                try:
                    for block in ip_dict[key]['logicalsystem'][systemname]['residentblock']:
                        for x in range(16): raw_output+=(' ')
                        raw_output+=('- '+block+'\n')
                except: pass

        except: pass

        for x in range(4): raw_output+=(' ')
        raw_output+=('residentblock:\n')
        try:
            for block in ip_dict[key]['residentblock']:
                for x in range(8): raw_output+=(' ')
                raw_output+=('- '+block+'\n')
        except: pass


        raw_output+=('\n')


    return raw_output




def detail(ip_dict):
    ''' Given dictionary or dotted dictionary return yaml formatted string
    '''

    keylist = list(ip_dict.keys())
    keylist.sort()
    raw_output = ''

    for key in keylist:

        if '--' in key:
            raw_output+=f'''
                <div class="table table-warning">
                    <label style="margin-left: 5px;">{key}</label>
                </div>
                <pre>'''
        else:
            raw_output+=f'''
                <div class="table table-active">
                    <label style="margin-left: 5px;">{key}</label>
                </div>
                <pre>'''

        raw_output+=(' ')*4
        raw_output+=('ip: '+str(ip_dict[key]['ip'])+'\n')

        try:
            raw_output+=(' ')*4
            raw_output+=('synchronised: '+str(ip_dict[key]['synced'])+'\n')
        except KeyError:
            raw_output = raw_output[:-4] # remove the spaces
            pass

        # try:
        raw_output+=(' ')*4
        raw_output+=('location: '+ip_dict[key]['hostname'].lower()+'\n')
        # except KeyError: pass

        try:
            raw_output+=(' ')*4
            raw_output+=('hostname: '+ip_dict[key]['hostid']+'\n')
        except KeyError:
            raw_output = raw_output[:-4] # remove the spaces
            pass

        # try:
        raw_output+=(' ')*4
        raw_output+=('software: '+ip_dict[key]['software'].lower()+'\n')
        # except KeyError: pass

        try:
            raw_output+=(' ')*4
            raw_output+=('version: '+ip_dict[key]['version']+'\n')
        except KeyError:
            raw_output = raw_output[:-4] # remove the spaces
            pass

        try:
            raw_output+=(' ')*4
            raw_output+=('serial: '+ip_dict[key]['serialnumber']+'\n')
        except KeyError:
            raw_output = raw_output[:-4] # remove the spaces
            pass

        try:
            raw_output+=(' ')*4
            raw_output+=('model: '+ip_dict[key]['model']+'\n')
        except KeyError:
            raw_output = raw_output[:-4] # remove the spaces
            pass

        vrf_count = 0
        up_xco_count = 0
        dn_xco_count = 0

        if ip_dict[key]['logicalsystem']:
            raw_output+=(' ')*4
            raw_output+=('logicalsystem:\n')
            try:        
                for systemname in ip_dict[key]['logicalsystem'].keys():
                    raw_output+=(' ')*8
                    systemip = ip_dict[key]['logicalsystem'][systemname]['ip']
                    raw_output+=(systemname+': '+systemip+'\n')
                    try:
                        vrf_count += len(ip_dict[systemip]['instances'])
                        up_xco_count += ip_dict[systemip]['xconnects'][0][1]
                        dn_xco_count += ip_dict[systemip]['xconnects'][1][1]
                    except KeyError:
                        continue # no info about the logical system when main system aint synced
            except AttributeError:
                continue # 'str' object has no attribute 'keys' if the ip_dict[key]['logicalsystem'] is not dict

        raw_output+=(' ')*4
        vrf_count += len(ip_dict[key]['instances'])
        raw_output+=('vrf: '+str(vrf_count)+'\n')

        raw_output+=(' ')*4
        up_xco_count += ip_dict[key]['xconnects'][0][1]
        dn_xco_count += ip_dict[key]['xconnects'][1][1]
        raw_output+=('xconnects: up: %d down: %d total: %d\n'%(up_xco_count,dn_xco_count,up_xco_count+dn_xco_count))


        for x in range(4): raw_output+=(' ')
        raw_output+=('Errors:\n')
        try:
            for errortype in ip_dict[key]['errors']:
                for x in range(8): raw_output+=(' ')
                raw_output+=(errortype+':\n')
                for x in range(12): raw_output+=(' ')
                raw_output+=('- '+ip_dict[key]['errors'][errortype]+'  \n')
        except: pass


        raw_output+='</pre>'


    return raw_output
