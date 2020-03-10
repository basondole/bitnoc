# This module is part of the core Basondole Tools
# This code accepts a dictionary with host ip as key and commands to be sent to the host as values for input
# The code then sends the commands (dictionary values) to the host (dictionary key) via ssh then displays the output
# Can work with different shells but it is further optimised for JunoS, Cisco IOS and IOS XE and Debian
# A commit in junos results to a wait of 30 seconds to make sure the command is completed. 30 seconds is an arbitrary value

import paramiko
import threading
import socket
import time
import re
import queue

__author__ = "Paul S.I. Basondole"
__version__ = "Code 2.0 Python 3.7"
__maintainer__ = "Paul S.I. Basondole"
__email__ = "bassosimons@me.com"



class SendCommand:


    def execute(self,confDict,user,key, context_output, extra=None): # extra is used to cary string from ondemand

        context_output['_out_'] = ''
        context_output['_command_errors_'] = ''
        context_output['_errors_'] = ''
        context_output['_global_total_cmds_'] = 0
        context_output['_global_xcutd_cmds_'] = 0
        errors = False

        username,password = user,key
        threads = []
        lock = threading.Lock()

        start_time = time.time()

        ipList = list(confDict.keys())


        for ipaddress in ipList:

           t = threading.Thread(target=self.kazi, args=(username,password,ipaddress,confDict,lock,context_output))
           t.start()
           threads.append(t)

        for t in threads: t.join()

        run_time = round(time.time()-start_time)



        if context_output['_errors_']: errors = [ error.strip() for error in context_output['_errors_'].split('\n') if error.strip()]
        else: errors = []
        if context_output['_out_']:
          summary_output  = context_output['_out_'].strip()
          context_output['_out_'] = ''
        else:
          summary_output = ''

        context_output['_out_']+= '\n PERFORMED ACTIONS:'
        context_output['_out_']+= '\n ------------------'
        context_output['_out_']+= '\n '
        context_output['_out_']+= summary_output
        context_output['_out_']+= '\n'

        if extra:
           context_output['_out_']+= '\n Scheduled operation:'
           context_output['_out_']+= '\n --------------------'
           context_output['_out_']+= '\n ' + str(extra)

        context_output['_out_']+='\n Summary:'
        context_output['_out_']+='\n --------\n'
        context_output['_out_']+=' [{}/{}] command(s) executed on [{}/{}] accessed device(s)'.format(
                       context_output['_global_xcutd_cmds_'],context_output['_global_total_cmds_'],len(confDict.keys())-len(errors),len(confDict.keys()))
        
        context_output['_out_']+='\n '+ '[Finished in %s seconds]'%str(run_time)
        context_output['_out_']+='\n'

        if context_output['_errors_'] or context_output['_command_errors_']:
           errors = True # used to raise a popup window highlighting the errors
           context_output['_out_']+= '\n'
           context_output['_out_']+= '\n <span class="token function">Errors:'
           context_output['_out_']+= '\n -------'

        if context_output['_command_errors_']:
           context_output['_out_']+= context_output['_command_errors_']

        if context_output['_errors_']:
           context_output['_out_']+= '\n'
           context_output['_out_']+= '\n'+context_output['_errors_']

        if context_output['_errors_'] or context_output['_command_errors_']:
           context_output['_out_']+= '</span>'

        return errors, context_output['_out_']




    def kazi(self,username,password,ipaddress,confDict,lock, context_output):

      context_output['_global_total_cmds_'] += len(confDict[ipaddress]['commands'])

      sshClient = paramiko.SSHClient()
      sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())

      try:
         sshClient.connect(ipaddress, username=username, password=password, timeout=10,allow_agent=False,look_for_keys=False)
         authenticated = True

      except (socket.error, paramiko.AuthenticationException):
         authenticated = False
         with lock: 
          context_output['_errors_']+= '\n '+(time.ctime()+" (user = "+username+") failed authentication > "+ipaddress.ljust(15))

      if authenticated==True:
         console_output = ''
         secureCli = sshClient.invoke_shell()


         if confDict[ipaddress]['software'] == 'junos':
             secureCli.send('set cli screen-length 0\n')
             secureCli.send('set cli screen-width 0\n')
             time.sleep(2)
             pre_output = secureCli.recv(65535).decode()
             cliprompt = pre_output.split('\n')[-1].strip()
             del pre_output # delete unneeded variable

             try: commit_index = confDict[ipaddress]['commands'].index('commit and-quit') # find position of the commit command in the list
             except: commit_index = 1+len(confDict[ipaddress]['commands']) # give the index a high value that cant be matched in the following loop

             for index, line in enumerate(confDict[ipaddress]['commands']):
                time.sleep(.5)
                secureCli.send(line)
                secureCli.send('\n')
                time.sleep(.5)
                context_output['_global_xcutd_cmds_']+=1 # count the excuted commands


                if index == commit_index: # if commit is issued check if there were errors on commit

                   time.sleep(30) # wait for all output to be put on the device clie

                   tmp_output = secureCli.recv(65535).decode() # collect output after commit command

                   console_output += tmp_output # save the the output to the device output variable

                   edit_prompt = tmp_output.split('\n')[-1] # edit mode prompt

                   # if there is an error with the config it will be flagged on 
                   # first word of line 4 from last this is the sytanx in junos
                   if 'error:' == console_output .split('\n')[-4].split()[0].lower():

                      console_output, temp_command_errors = SendCommand.junos_commit_error_check(self,tmp_output,console_output,
                                                                                index,ipaddress,confDict,secureCli)
                      context_output['_command_errors_'] += '\n'
                      context_output['_command_errors_'] += temp_command_errors

                      break # stop sending the remaining commands
                    

                   elif 'error:' == tmp_output.split('\n')[-6].split()[0].lower(): # if database is locked error will be on line 6

                      for x in range(1,4): # try for 30 seconds
                        console_output +='\n'
                        console_output +='\n'
                        console_output +='INFO: Configuration locked waited for {} seconds to retry'.format(x*10)
                        console_output +='\n'
                        console_output +='\n'+ edit_prompt
                        secureCli.send('commit and-quit\n')
                        time.sleep(10)
                        _tmp_output = secureCli.recv(65535).decode()

                        console_output += _tmp_output
                        if 'error:' != _tmp_output.split('\n')[-6].split()[0].lower(): break


                      if 'error:' == _tmp_output.split('\n')[-6].split()[0].lower():
                          console_output +='\n'
                          console_output +='\n'
                          console_output +='INFO: Configuration database is still locked discarding operation'
                          console_output +='\n'
                          console_output +='\n'+ edit_prompt

                          console_output, temp_command_errors = SendCommand.junos_commit_error_check(self,console_output,console_output,index,ipaddress,confDict,secureCli)
                          context_output['_command_errors_'] += '\n'
                          context_output['_command_errors_'] += temp_command_errors

                          break # stop sending remaining command
                      


                      elif 'error:' == _tmp_output.split('\n')[-4].split()[0].lower(): #after config database unlock check if there are no config errors

                          console_output,context_output['_command_errors_'] = SendCommand.junos_commit_error_check(self,console_output,console_output,
                                                                                                                    index,ipaddress,confDict,secureCli)
                          context_output['_command_errors_'] += '\n'
                          context_output['_command_errors_'] += temp_command_errors

                          break # stop sending the remaining commands


                      else: pass



         elif confDict[ipaddress]['software'] == 'ios':
             secureCli.send('terminal length 0\n')
             secureCli.send('terminal width 0\n')
             time.sleep(2)
             pre_output = secureCli.recv(65535).decode()
             cliprompt = pre_output.split('\n')[-1].strip()
             del pre_output # delete unneeded variable

             try: wr_index = confDict[ipaddress]['commands'].index('write memory\n') # find position of the commit command in the list
             except: wr_index = 1+len(confDict[ipaddress]['commands']) # give the index a high value that cant be matched in the following loop



             for index,line in enumerate(confDict[ipaddress]['commands']):

                if index == wr_index: # if write memory is issued check if there were errors on precceding commands before saving config
                   
                   time.sleep(5) # wait for all output to be put on the device cli
                   tmp_output = secureCli.recv(65535).decode() # collect output before wr command
                   console_output += tmp_output # save the the output to the device output variable
                   cmd_prompt = tmp_output.split('\n')[-1] # device prompt
                   no_of_errors = SendCommand.ios_error_check(self,console_output,index,ipaddress,confDict,secureCli,checkonly=True)
                   
                   if no_of_errors != 0:
                       console_output +='\n'
                       console_output +='\n'
                       console_output +='INFO: There was an error in the config. The startup-config will not be updated'
                       console_output +='\n'
                       console_output +='\n'+ cmd_prompt

                       index-=1 # do not count this command

                       break # stop saving the config


                time.sleep(.5)
                secureCli.send(line)
                secureCli.send('\n')
                time.sleep(.5)
                context_output['_global_xcutd_cmds_']+=1 # count the excuted commands

                # if the sub-interface does not exist ios will throw an error
                # below is to discard that error 
                if 'show running-config interface' in line:
                  time.sleep(1)
                  tmp_output = secureCli.recv(65535).decode()
                  tmp_output_list = tmp_output.split('\n')
                  for tmp_output_line in tmp_output_list:
                    if re.search(r'^%',tmp_output_line): tmp_output_list.remove(tmp_output_line)

                  console_output += '\n'.join(tmp_output_list)




             # for ping to complete in cisco and take the next command sleep for 5 seconds (5 ping)
             # plus 1 second to avoid buffer waiting forever due to exit command issued below being droped
             time.sleep(6)



         time.sleep(5)
         secureCli.close()

         while True:
            output = secureCli.recv(65535).decode()
            if not output: break
            for line in output:
               console_output+=str(line)
         
         sshClient.close()

         console_output = cliprompt + console_output # reinsert the prompt

         if confDict[ipaddress]['software'] == 'ios':
           # check for errors in the output
           temp_command_errors, no_of_errors = SendCommand.ios_error_check(self,console_output,index,ipaddress,confDict,secureCli,context_output)
           if temp_command_errors:
             context_output['_command_errors_'] += '\n'
             context_output['_command_errors_'] += '\n'+temp_command_errors
           

         if confDict[ipaddress]['software'] == 'junos':
           # check for errors in the output
           temp_command_errors, no_of_errors = SendCommand.junos_error_check(self,console_output,ipaddress,confDict,secureCli,context_output)
           if temp_command_errors:
              context_output['_command_errors_'] += '\n'
              context_output['_command_errors_'] += '\n'+temp_command_errors


         
         output_lines = console_output.split('\n')
         output_lines[0] = cliprompt+str(output_lines[0]) # add the prompt to the first line since its not there

         if cliprompt == output_lines[-1].strip():
            output_lines.pop(-1) # remove the last line of output if it is the prompt

         for _index,line in enumerate(output_lines):
            line = line.rstrip()
            output_lines[_index] = line # strip trailing spaces

            if re.search(r'^'+cliprompt,line):
               line = line.split(cliprompt)
               line = ' '.join(line) # remove the prompt from the command

               head = '\n'
               head += line.strip() +'\n'+ ''.join(['-' for x in range(len(line.strip()))]) # underline the command
               output_lines[_index] = head # replace the command with underlined command


         output_lines = '\n'.join(output_lines) # rejoin all lines
         output_lines = output_lines.split('\n') # split all the new lines including newly added from loop above

         # print(ipaddress,output_lines)

         with lock:
             context_output['_out_'] += '\n'+ ('['+ipaddress+']')
             context_output['_out_'] += '\n'
             context_output['_out_'] += '\n  [{}/{}] command(s) executed'.format(index+1-no_of_errors,len(confDict[ipaddress]['commands'])) # +1 since index starts from 0
             context_output['_out_'] += '\n'
             for line in output_lines: context_output['_out_'] += '\n' + '   '+line
             context_output['_out_'] += '\n'
             context_output['_out_'] += '\n'





    @staticmethod
    def junos_commit_error_check(self,tmp_output,console_output,index,ipaddress,confDict,secureCli):
        # index is the number of commands executed thus far
        for line in tmp_output.split('\n'): 
          # if 'show | compare' in line: 
          if 'commit and-quit' in line:
             show_comp_index = tmp_output.split('\n').index(line) # find the index of show | compare from device cli output
             break

        show_comp_output = tmp_output.split('\n')[show_comp_index:-1] # collect the text from show compare to the end of commit
        show_comp_output = '\n  '.join(line.strip() for line in show_comp_output) # collect the text from show compare to the end of commit
        
        command_errors = '\n '
        command_errors+= '<span class="token function">[{} commit Error]'.format(ipaddress)
        command_errors+= ' [{}/{}] command(s) executed'.format(index+1,len(confDict[ipaddress]['commands'])) # +1 because index starts at 0
        command_errors+= '\n'
        command_errors+= '\n  '+ show_comp_output # record the above output as device errors
        command_errors+= '</span>\n'
        
        

        try:
           secureCli.send('quit\n')
           # below to ignore uncomitted changes in junos if there were errors
           secureCli.send('\n') # enter key to discard changes and exit config mode
           time.sleep(2)
           discard_output = secureCli.recv(65535).decode()
           console_output += discard_output
        except socket.error: pass # session is already Closed there were no uncommited changes

        return console_output, command_errors



    @staticmethod
    def ios_error_check(self,console_output,lastcommand_index,ipaddress,confDict,secureCli,context_output,checkonly=False):
        # checkonly keyword is for counting the numbers of errors only without updating other counters

        command_errors, errors = '',[]

        console_output_list = console_output.split('\n')

        errors = [(index, line) for index,line in enumerate(console_output_list) if re.findall(r'^%',line)]

        if checkonly: return len(errors)

        show_comp_output = ''
        for index,error in errors:
           show_comp_output += '\n  '
           show_comp_output += '\n  '.join(console_output_list[index-3:index+1]) # collect the text from 3 lines before line with error to the next
           show_comp_output += '\n'
           context_output['_global_xcutd_cmds_']-=1 # for each error lower command xcuted count


        if show_comp_output:
           command_errors = '\n'
           command_errors+= '<span class="token function">[{} Error]'.format(ipaddress)
           command_errors+= ' [{}/{}] command(s) executed'.format(lastcommand_index+1-len(errors),len(confDict[ipaddress]['commands'])) # +1 because index starts at 0
           command_errors+= '\n'
           command_errors+= '\n  '+ show_comp_output # record the above output as device errors
           command_errors+= '</span>\n'
          

        return command_errors, len(errors)



    @staticmethod
    def junos_error_check(self,console_output,ipaddress,confDict,secureCli, context_output):

        command_errors, errors = '',[]

        console_output_list = console_output.split('\n')
        errors = [(index, line) for index,line in enumerate(console_output_list) if re.findall(r'^syntax error',line)]

        show_comp_output = ''
        for index,error in errors:
           show_comp_output += '\n  '
           show_comp_output += '\n  '.join(console_output_list[index-3:index+1]) # collect the text from 3 lines before line with error to the next
           show_comp_output += '\n'
           context_output['_global_xcutd_cmds_']-=1 # for each error lower command xcuted count

        # below is to consolidate the error and avoid duplicate count of same syntax error
        for index,line in enumerate(console_output_list):
          if re.findall(r'^syntax error',line):
             if console_output_list[index-2].split('   ')[0] in console_output_list[index+1]:
                errors.pop(0)
                context_output['_global_xcutd_cmds_']+=1


        if show_comp_output:
          command_errors = '\n'
          command_errors+= '<span class="token function">[{} Error]'.format(ipaddress)
          command_errors+= ' [{}/{}] command(s) executed'.format(len(confDict[ipaddress]['commands'])-len(errors),len(confDict[ipaddress]['commands'])) # +1 because index starts at 0
          command_errors+= '\n'
          command_errors+= '\n  '+ show_comp_output # record the above output as device errors
          command_errors+= '</span>\n'


        return command_errors, len(errors)







def send_command(confDict,username,password,context_output):

          start_time = time.time()

          kazi = SendCommand()
          error, result = kazi.execute(confDict,username,password,context_output)
 
          if error:
              prompt = {'message': 'There was an error in configuration that the sytem could not fix. \
                        Please review output provided in errors section as a base to analyse \
                        the scope of error and perhaps configure the device manually',
                        'status': 'warning'}
              # print(prompt)
              
          else:
             prompt = {'message': 'Configuration completed successfully',
                       'status': 'success'}
             # print(prompt)

          return result, prompt
