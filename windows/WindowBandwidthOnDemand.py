# This module is part of the core Basondole Tools
# This class creates a GUI for input data that will be used by bonDemand

#Note: Only interfaces with descriptions are considered valid to be used in on demand services

import tkinter
import re
import ttk
import datetime
import time
from windows.WindowLoading import loading
from widget.WidgetDatepicker import Datepicker
from windows.WindowDialog import Dialog
from other.Essential import resource_path
from core.bandwidthOnDemand import Server, createJob
from core.SendCommand import SendCommand
from core.vlanSingleFinder import getUsedVlanDesc

__author__ = "Paul S.I. Basondole"
__version__ = "2.0"
__maintainer__ = "Paul S.I. Basondole"
__email__ = "bassosimons@me.com"

warning_icon = resource_path(r"warning-icon.png")
error_icon = resource_path(r"error-icon.png")
check_icon = resource_path(r"check-icon.png")


class BandwidthOnDemand(tkinter.Toplevel):

    def __init__(self,username,password,ipDict,serverdata,choice=False):

        self.username = username
        self.password = password
        self.serverlogin = serverdata['user']
        self.server = serverdata['address']
        self.scriptPath = serverdata['onserver_dir']
        self.keyPath = serverdata['key']
        self.port = serverdata['port']

        try: self.mail = serverdata['mail']
        except KeyError: self.mail = False

        self.choice = choice


        
        tkinter.Toplevel.__init__(self)

        self.withdraw() # the window to  remain hidden untill all widgets are loaded

        _bgcolor = '#d9d9d9'  # X11 color: 'gray85'
        _fgcolor = '#000000'  # X11 color: 'black'
        _compcolor = '#d9d9d9' # X11 color: 'gray85'
        _ana1color = '#d9d9d9' # X11 color: 'gray85'
        _ana2color = '#ececec' # Closest X11 color: 'gray92'
        font9 = "-family Calibri -size 15 -weight bold -slant roman "  \
            "-underline 0 -overstrike 0"
        self.style = ttk.Style()
        self.style.configure('.',background=_bgcolor)
        self.style.configure('.',foreground=_fgcolor)
        self.style.configure('.',font="TkDefaultFont")
        self.style.map('.',background=
            [('selected', _compcolor), ('active',_ana2color)])

        self.geometry("570x690+346+156")
        self.resizable(width=False,height=False)
        self.title("Bandwidth on Demand")
        self.configure(background="#d9d9d9")
        self.configure(highlightbackground="#d9d9d9")
        self.configure(highlightcolor="black")



        self.Frame1 = tkinter.Frame(self)
        self.Frame1.place(relx=0.018, rely=0.014, relheight=0.978, relwidth=0.974)
        self.Frame1.configure(borderwidth="2")
        self.Frame1.configure(background="#d9d9d9")
        self.Frame1.configure(highlightbackground="#d9d9d9")
        self.Frame1.configure(highlightcolor="black")
        self.Frame1.configure(width=555)

        self.Label1 = tkinter.Label(self.Frame1)
        self.Label1.place(relx=0.018, rely=0.015, height=43, width=289)
        self.Label1.configure(activebackground="#f9f9f9")
        self.Label1.configure(activeforeground="black")
        self.Label1.configure(background="#d9d9d9")
        self.Label1.configure(disabledforeground="#a3a3a3")
        self.Label1.configure(font=font9)
        self.Label1.configure(foreground="#000000")
        self.Label1.configure(highlightbackground="#f0f0f0f0f0f0")
        self.Label1.configure(highlightcolor="black")
        self.Label1.configure(text='''Bandwidth on demand''')


        self.Frame3 = tkinter.Frame(self.Frame1)
        self.Frame3.place(relx=0.018, rely=0.104, relheight=0.881, relwidth=0.964)
        self.Frame3.configure(borderwidth="2")
        self.Frame3.configure(background="#d9d9d9")
        self.Frame3.configure(highlightbackground="#d9d9d9")
        self.Frame3.configure(highlightcolor="black")
        self.Frame3.configure(width=535)

        self.Frame3_9 = tkinter.Frame(self.Frame3)
        self.Frame3_9.place(relx=0.037, rely=0.218, relheight=0.261, relwidth=0.925)
        self.Frame3_9.configure(relief='groove')
        self.Frame3_9.configure(borderwidth="2")
        self.Frame3_9.configure(relief='groove')
        self.Frame3_9.configure(background="#d9d9d9")
        self.Frame3_9.configure(highlightbackground="#d9d9d9")
        self.Frame3_9.configure(highlightcolor="black")
        self.Frame3_9.configure(width=495)



        def updateint(*args):
            self.usedvlans = [] # reset the vlan list when interface is changed
            self.TEntry1_12.delete(0,tkinter.END) # clear the description field

            self.TCombobox1_6.configure(textvar=self.intselect, values=ipDict[self.devselect.get()]['interfaces'])
            self.TCombobox1_6.set('Select interface')
            self.TCombobox1_7.configure(textvar=self.vlanselect, values=self.usedvlans)
            self.TCombobox1_7.set('Select')
            self.TCombobox1_10.configure(textvar=self.cirselect, values=ipDict[self.devselect.get()]['policers'])
            self.TCombobox1_10.set('Select')
            self.TCombobox1_11.configure(textvar=self.pirselect, values=ipDict[self.devselect.get()]['policers'])
            self.TCombobox1_11.set('Select')

            # Update the logical system options upone device selection
            try:
                if ipDict[self.devselect.get()]['logicalsystem']:
                    # insert a none logical system to reflect the main systen
                    self.TCombobox1_4.configure(textvariable=self.sysselect,
                                                values=['None']+list(ipDict[self.devselect.get()]['logicalsystem'].keys()))
                    self.TCombobox1_4.set('Select')

                elif ipDict[self.devselect.get()]['systemname']:
                    self.TCombobox1_4.configure(textvariable=self.sysselect,values=['None',ipDict[self.devselect.get()]['systemname']])
                    self.TCombobox1_4.set(ipDict[self.devselect.get()]['systemname'])


            except (IndexError,TypeError,KeyError):
                self.TCombobox1_4.configure(textvar=self.sysselect, values=[])
                self.TCombobox1_4.set('None')

                

        ipList = list(ipDict.keys())
        ipList.sort()

        self.devselect = tkinter.StringVar(self.Frame3_9)
        self.TCombobox1_5 = ttk.Combobox(self.Frame3_9)
        self.TCombobox1_5.place(relx=0.02, rely=0.258, relheight=0.2, relwidth=0.448)
        self.TCombobox1_5.configure(takefocus="")
        self.TCombobox1_5.configure(textvariable=self.devselect, values=ipList)
        self.TCombobox1_5.bind("<<ComboboxSelected>>", updateint)



        def updatepol(*args):
            ''' Update the policer options once a device is selected
            '''
            if self.TCombobox1_4.get().lower() == 'none' or not self.TCombobox1_4.get():
                # when there is no logical system use the main system
                self.TCombobox1_11.configure(textvar=self.pirselect, values=ipDict[self.TCombobox1_5.get()]['policers'])
                self.TCombobox1_10.configure(textvar=self.cirselect, values=ipDict[self.TCombobox1_5.get()]['policers'])

            else:
                try:
                    # when a virtual system ip is selected directly
                    ipDict[self.devselect.get()]['systemname']
                    ls_ip = self.devselect.get()
                except KeyError:
                    # otherwise get the virtual system ip from the main system
                    ls_ip = ipDict[self.devselect.get()]['logicalsystem'][self.TCombobox1_4.get()]
                self.TCombobox1_11.configure(textvar=self.pirselect, values=ipDict[ls_ip]['policers'])
                self.TCombobox1_10.configure(textvar=self.cirselect, values=ipDict[ls_ip]['policers'])         

            self.TCombobox1_10.set('Select')
            self.TCombobox1_11.set('Select')



        self.sysselect = tkinter.StringVar(self.Frame3_9)
        self.TCombobox1_4 = ttk.Combobox(self.Frame3_9)
        self.TCombobox1_4.place(relx=0.505, rely=0.258, relheight=0.2, relwidth=0.448)
        self.TCombobox1_4.configure(takefocus="")
        self.TCombobox1_4.bind("<<ComboboxSelected>>", updatepol)


        def updatevlan(*args):

            self.usedvlans = []
            self.TEntry1_12.delete(0,tkinter.END)

            if self.TCombobox1_6.get() == 'Null':
                self.TCombobox1_7.configure(textvar=self.vlanselect, values=self.usedvlans)
                return

            self.loading = loading(self.Frame3_9,self,pbar=[0.505,0.71,0.2,0.448],words='Loading vlans')
            self.update_idletasks()

            self.vlanDict = getUsedVlanDesc(self.TCombobox1_5.get(),ipDict,self.TCombobox1_6.get(),self.username,self.password)
            self.usedvlans = list(self.vlanDict.keys())
            self.usedvlans.sort()

            self.TCombobox1_7.configure(textvar=self.vlanselect, values=self.usedvlans)
            self.TCombobox1_7.set('Select')

            self.config(cursor='')
            self.update()
            self.loading.stop(self)


        self.intselect = tkinter.StringVar(self.Frame3_9)
        self.TCombobox1_6 = ttk.Combobox(self.Frame3_9)
        self.TCombobox1_6.place(relx=0.02, rely=0.71, relheight=0.2, relwidth=0.448)
        self.TCombobox1_6.configure(takefocus="")
        self.TCombobox1_6.bind("<<ComboboxSelected>>", updatevlan)


        def updatedesc(*args):
            self.TEntry1_12.delete(0,tkinter.END)
            self.TEntry1_12.insert(0,self.vlanDict[self.vlanselect.get()])


        self.vlanselect = tkinter.StringVar(self.Frame3_9)
        self.TCombobox1_7 = ttk.Combobox(self.Frame3_9)
        self.TCombobox1_7.place(relx=0.505, rely=0.71, relheight=0.2, relwidth=0.448)
        self.TCombobox1_7.configure(takefocus="")
        self.TCombobox1_7.bind("<<ComboboxSelected>>", updatedesc)

        self.TLabel1_7 = ttk.Label(self.Frame3_9)
        self.TLabel1_7.place(relx=0.02, rely=0.06, height=29, width=150)
        self.TLabel1_7.configure(background="#d9d9d9")
        self.TLabel1_7.configure(foreground="#000000")
        self.TLabel1_7.configure(font="TkDefaultFont")
        self.TLabel1_7.configure(relief='flat')
        self.TLabel1_7.configure(text='''Edge router''')

        self.TLabel1_6 = ttk.Label(self.Frame3_9)
        self.TLabel1_6.place(relx=0.505, rely=0.06, height=29, width=150)
        self.TLabel1_6.configure(background="#d9d9d9")
        self.TLabel1_6.configure(foreground="#000000")
        self.TLabel1_6.configure(font="TkDefaultFont")
        self.TLabel1_6.configure(relief='flat')
        self.TLabel1_6.configure(text='''Logical system''')

        self.TLabel1_8 = ttk.Label(self.Frame3_9)
        self.TLabel1_8.place(relx=0.02, rely=0.516, height=29, width=100)
        self.TLabel1_8.configure(background="#d9d9d9")
        self.TLabel1_8.configure(foreground="#000000")
        self.TLabel1_8.configure(font="TkDefaultFont")
        self.TLabel1_8.configure(relief='flat')
        self.TLabel1_8.configure(text='''Interface''')

        self.TLabel1_9 = ttk.Label(self.Frame3_9)
        self.TLabel1_9.place(relx=0.505, rely=0.516, height=29, width=100)
        self.TLabel1_9.configure(background="#d9d9d9")
        self.TLabel1_9.configure(foreground="#000000")
        self.TLabel1_9.configure(font="TkDefaultFont")
        self.TLabel1_9.configure(relief='flat')
        self.TLabel1_9.configure(text='''VLAN''')

        self.Frame3_10 = tkinter.Frame(self.Frame3)
        self.Frame3_10.place(relx=0.037, rely=0.034, relheight=0.16, relwidth=0.925)
        self.Frame3_10.configure(relief='groove')
        self.Frame3_10.configure(borderwidth="2")
        self.Frame3_10.configure(relief='groove')
        self.Frame3_10.configure(background="#d9d9d9")
        self.Frame3_10.configure(highlightbackground="#d9d9d9")
        self.Frame3_10.configure(highlightcolor="black")
        self.Frame3_10.configure(width=495)

        # Service ticket
        self.TLabel1_11 = ttk.Label(self.Frame3_10)
        self.TLabel1_11.place(relx=0.02, rely=0.02, height=29, width=130)
        self.TLabel1_11.configure(background="#d9d9d9")
        self.TLabel1_11.configure(foreground="#000000")
        self.TLabel1_11.configure(font="TkDefaultFont")
        self.TLabel1_11.configure(relief='flat')
        self.TLabel1_11.configure(text='''Service ticket''')
        self.TLabel1_11.configure(width=130)


        self.TCombobox1_8 = ttk.Combobox(self.Frame3_10)
        self.TCombobox1_8.place(relx=0.02, rely=0.35, relheight=0.326, relwidth=0.448)
        self.TCombobox1_8.configure(takefocus="")


        if choice:

            def updateothers(*args):
                self.TCombobox1_5.set(self.bigdict[self.tickets.get()]['host'])
                self.TCombobox1_6.set(self.bigdict[self.tickets.get()]['interface'])
                self.TCombobox1_7.set(self.bigdict[self.tickets.get()]['vlan'])

                self.pick = Datepicker(self.Frame3_10,datevar=self.revdatevar,entrystate= 'readonly',
                                        dateformat="%d-%m-%Y",assign=self.bigdict[self.tickets.get()][5])

                self.TCombobox1_10.configure(textvar=self.cirselect, values=ipDict[self.devselect.get()]['policers'])
                self.TCombobox1_10.set(self.bigdict[self.tickets.get()]['cir'])

                self.TCombobox1_11.configure(textvar=self.pirselect, values=ipDict[self.devselect.get()]['policers'])
                self.TCombobox1_11.set('Select')

            serv = Server(self.serverlogin,self.server,self.scriptPath,'*',self.keyPath,parent=self,port=self.port)

            if serv.up:
                self.bigdict = serv.retrieveRemoteFile(bigdict=True) #dictionary containing info about ticket
                self.tickets = tkinter.StringVar(self.Frame3_10)
                self.TCombobox1_8.configure(state='readonly')
                self.TCombobox1_8.configure(textvar=self.tickets,values=list(self.bigdict.keys()))
                self.TCombobox1_8.bind("<<ComboboxSelected>>", updateothers)
            else:
                self.destroy()
                return


        # revert date

        def revertdate(clear_calendar=False):
            ''' Provides pop up calendar option for date selection
            '''
            if clear_calendar:
                try: self.pick.destroy()
                except Exception: pass

            if self.TCombobox1_08.get() == 'Enter number of days':
                self.TCombobox1_08.set('')
            elif self.TCombobox1_08.get() == 'Calendar':
                self.pick = Datepicker(self.Frame3_10,datevar=self.revdatevar,entrystate= 'readonly',
                                       dateformat="%d-%m-%Y",assign='Click to choose date')
                self.pick.place(relx=0.505, rely=0.35, relheight=0.326, relwidth=0.448)                


        self.revdatevar = tkinter.StringVar()
        self.TCombobox1_08 = ttk.Combobox(self.Frame3_10)
        self.TCombobox1_08.configure(textvar=self.revdatevar,values=['Enter number of days','Calendar'])
        self.TCombobox1_08.place(relx=0.505, rely=0.35, relheight=0.326, relwidth=0.448)
        self.TCombobox1_08.set('Select')
        self.TCombobox1_08.bind("<<ComboboxSelected>>", revertdate)



        self.TLabel1_12 = ttk.Label(self.Frame3_10)
        self.TLabel1_12.place(relx=0.505, rely=0.02, height=29, width=180)
        self.TLabel1_12.configure(background="#d9d9d9")
        self.TLabel1_12.configure(foreground="#000000")
        self.TLabel1_12.configure(font="TkDefaultFont")
        self.TLabel1_12.configure(relief='flat')
        self.TLabel1_12.configure(text='''Revert date''')



        self.TLabel1_13 = ttk.Label(self.Frame3_10)
        self.TLabel1_13.place(relx=0.50, rely=0.70, height=20, width=240)
        self.TLabel1_13.configure(justify='left')
        font14 = "-family {Segoe UI} -size 7 -weight normal -slant "  \
             "italic -underline 0 -overstrike 0"
        self.TLabel1_13.configure(font=font14,anchor='w')
        self.TLabel1_13.configure(text='eg: June 1 2019 or 10 days')
        self.TLabel1_13.bind("<Button-1>", revertdate) # left click to remove calendar


        self.Frame3_11 = tkinter.Frame(self.Frame3)
        self.Frame3_11.place(relx=0.037, rely=0.504, relheight=0.261
                , relwidth=0.925)
        self.Frame3_11.configure(relief='groove')
        self.Frame3_11.configure(borderwidth="2")
        self.Frame3_11.configure(relief='groove')
        self.Frame3_11.configure(background="#d9d9d9")
        self.Frame3_11.configure(highlightbackground="#d9d9d9")
        self.Frame3_11.configure(highlightcolor="black")
        self.Frame3_11.configure(width=495)

        self.cirselect = tkinter.StringVar(self.Frame3_11)
        self.TCombobox1_10 = ttk.Combobox(self.Frame3_11)
        self.TCombobox1_10.place(relx=0.02, rely=0.258, relheight=0.2
                , relwidth=0.448)
        self.TCombobox1_10.configure(takefocus="")

        self.pirselect = tkinter.StringVar(self.Frame3_11)
        self.TCombobox1_11 = ttk.Combobox(self.Frame3_11)
        self.TCombobox1_11.place(relx=0.505, rely=0.258, relheight=0.2
                , relwidth=0.448)
        self.TCombobox1_11.configure(takefocus="")

        self.TLabel1_11 = ttk.Label(self.Frame3_11)
        self.TLabel1_11.place(relx=0.02, rely=0.516, height=29, width=190)
        self.TLabel1_11.configure(background="#d9d9d9")
        self.TLabel1_11.configure(foreground="#000000")
        self.TLabel1_11.configure(font="TkDefaultFont")
        self.TLabel1_11.configure(relief='flat')
        self.TLabel1_11.configure(text='''Client name (optional)''')
        self.TLabel1_11.configure(width=190)

        self.TLabel1_12 = ttk.Label(self.Frame3_11)
        self.TLabel1_12.place(relx=0.02, rely=0.06, height=29, width=180)
        self.TLabel1_12.configure(background="#d9d9d9")
        self.TLabel1_12.configure(foreground="#000000")
        self.TLabel1_12.configure(font="TkDefaultFont")
        self.TLabel1_12.configure(relief='flat')
        self.TLabel1_12.configure(text='''Standard subscription''')
        self.TLabel1_12.configure(width=180)

        self.TLabel1_13 = ttk.Label(self.Frame3_11)
        self.TLabel1_13.place(relx=0.505, rely=0.06, height=29, width=210)
        self.TLabel1_13.configure(background="#d9d9d9")
        self.TLabel1_13.configure(foreground="#000000")
        self.TLabel1_13.configure(font="TkDefaultFont")
        self.TLabel1_13.configure(relief='flat')
        self.TLabel1_13.configure(text='''On-demand subscription''')
        self.TLabel1_13.configure(width=210)


        self.TEntry1_12 = ttk.Entry(self.Frame3_11)
        self.TEntry1_12.place(relx=0.02, rely=0.71, relheight=0.2
                , relwidth=0.94)
        self.TEntry1_12.configure(takefocus="")
        self.TEntry1_12.configure(cursor="ibeam")


        def pickdate():
          self.TCheckbutton1.configure(text='''Start at a later time''')
          if self.checkbox.get():
              self.datepicker = tkinter.Toplevel()
              self.datepicker.geometry("290x256+460+356")
              self.datepicker.resizable(width=False,height=False)

              self.attributes('-disabled', True)


              self.setdatevar = tkinter.StringVar()
              self.pick = Datepicker(self.datepicker,datevar=self.setdatevar,entrystate= 'readonly',
                                justify='center',dateformat="%d-%m-%Y",updatebutton=self.TCheckbutton1,show=True)
              self.pick.pack()

              def close():
                    self.attributes('-disabled', False)
                    self.datepicker.destroy()
                    if not self.setdatevar.get(): self.TCheckbutton1.deselect()

              self.datepicker.protocol('WM_DELETE_WINDOW', lambda: close())

          else: self.datepicker.destroy()

        self.checkbox = tkinter.IntVar(self.Frame3)
        self.TCheckbutton1 = tkinter.Checkbutton(self.Frame3)
        self.TCheckbutton1.place(relx=0.034, rely=0.78, relwidth=0.55
                , relheight=0.0, height=31)
        self.TCheckbutton1.configure(variable=self.checkbox)
        self.TCheckbutton1.configure(takefocus="")
        self.TCheckbutton1.configure(text='''Start at a later time''')
        self.TCheckbutton1.configure(width=233,anchor="w")
        self.TCheckbutton1.configure(command=lambda: pickdate())



        self.Button1 = tkinter.Button(self.Frame3)
        self.Button1.place(relx=0.093, rely=0.877, height=42, width=158)
        self.Button1.configure(pady="0")
        self.Button1.configure(text='''Submit''')
        self.Button1.configure(command= lambda: CONF(self,ipDict,mail=self.mail))


        self.Button1_13 = tkinter.Button(self.Frame3)
        self.Button1_13.place(relx=0.579, rely=0.877, height=42, width=158)
        self.Button1_13.configure(pady="0")
        self.Button1_13.configure(text='''Clear''')
        self.Button1_13.configure(command= lambda: self.clear())


        self.deiconify() # display the window with all loaded widgets

        try: open(self.keyPath)
        except FileNotFoundError:
            Dialog(self,prompt="SSH private login key not found\n confirm file location in settings\n",icon = error_icon)
            self.destroy()
            return


    def clear(self,confirmed=False):
       if not confirmed:
           d = Dialog(self,prompt="Are you sure? \n",icon = warning_icon)

       if confirmed or d.ans == 'ok':
           comboboxes = [self.TCombobox1_4,self.TCombobox1_5,self.TCombobox1_6,self.TCombobox1_08,
                         self.TCombobox1_7,self.TCombobox1_8,self.TCombobox1_10,self.TCombobox1_11]

           for cbox in comboboxes: cbox.set('')
           try: self.pick.destroy()
           except: pass
           self.TEntry1_12.delete(0,tkinter.END)
           self.TCheckbutton1.deselect()
           self.TCheckbutton1.configure(text='''Start at a later time''')
        
       else: return




class  CONF():

    def __init__(self,parent,ipDict,choice=None,mail=False):

            confDict = {}
            self.error = error_icon
            self.warning = warning_icon

            ls = parent.TCombobox1_4.get()
            if ls.lower() == 'none' or ls.lower()=='select' or ls.lower()=='select system': ls=False

            pe = parent.TCombobox1_5.get()
            if not pe in list(ipDict.keys()):
                Dialog(parent,prompt="Edge router unknown\n",icon = self.error)
                return

            iface = parent.TCombobox1_6.get()
            if not iface in ipDict[pe]['interfaces'] or iface.lower()=='null':
                Dialog(parent,prompt="Interface unknown\n",icon = self.error)
                return

            vlan = parent.TCombobox1_7.get()
            try:
                if int(vlan) not in range(0,4095):
                    Dialog(parent,prompt="VLAN not in correct range\n",icon = self.error)
                    return
            except ValueError:
                Dialog(parent,prompt="VLAN not in correct range\n",icon = self.error)
                return

            cir = parent.TCombobox1_10.get()
            if not cir in ipDict[pe]['policers']:
                Dialog(parent,prompt="Standard subscription is not defined\n",icon = self.error)
                return

            pir = parent.TCombobox1_11.get()
            if not pir in ipDict[pe]['policers']:
                Dialog(parent,prompt="onDemand subscription is not defined\n",icon = self.error)
                return

            st = parent.TCombobox1_8.get()
            try: int(st)
            except ValueError:
                if parent.choice: pass
                else:
                    Dialog(parent,prompt="Service ticket must be in numbers\n",icon = self.error)
                    return

            revdate = parent.revdatevar.get()
            try:
                revdate = datetime.datetime.strptime(revdate, '%d-%m-%Y') #create a datetime object
                revdate = datetime.datetime.strftime(revdate, '%Y-%m-%d') #change the time format to be used with "at"
            except ValueError:
                try:
                    datetime.datetime.strptime(revdate, '%B %d %Y')
                except ValueError:
                    if re.findall(r'^[1-9][0-9]*\ ?(min|hour|hours|day|days|week|weeks|month|months)$',revdate):
                        revdate = 'now+'+revdate
                    else:
                        Dialog(parent,prompt="Revert date has wrong format\n",icon = self.error)
                        return


            ds = parent.TEntry1_12.get()


            if parent.choice:
               ticket = st
               jobid = parent.bigdict[ticket]['job']
               serv = Server(parent.serverlogin,parent.server,parent.scriptPath,ticket+'.sh',parent.keyPath,parent=parent, port=parent.port)
               if serv.up:
                   success = check_icon
                   serv.deleteFromRemoteFile(ticket,jobid)
                   time.sleep(1)
                   if type(choice) != bool:
                       if 'update' not in parent.choice.lower(): # if the choice is not update  below message will pop
                           Dialog(parent,prompt='Ticket '+ticket+' deleted successfully \n',icon=success)
               # convert the ST back to an integer without 'ST' and 'byuser'
               st = str(int(re.findall(r'\d+',ticket.split('by')[0])[0]))

            # call the loading class
            parent.loading = loading(parent.Frame3,parent,pbar=[0.093,0.877,0.08,0.300],words='Loading')
            parent.update_idletasks()


            d = createConfig()


            ''' create a job to revert on server '''

            if ipDict[pe]['software'] == 'junos' :
                 commandList = d.junos(pe,ls,iface,vlan,cir)
            elif ipDict[pe]['software'] == 'ios' :
                 commandList = d.cisco(pe,ls,iface,vlan,cir)

            

            data = {'pe':pe,'ticket':st,'date':revdate,'commands':commandList}

            serverlogin = parent.serverlogin
            server = parent.server
            directory = parent.scriptPath
            keyPath = parent.keyPath
            port = parent.port
            mail = parent.mail

            revert_job_created = False
            if commandList:
                revert_job_created = createJob(parent,serverlogin,server,directory,keyPath,data,mail=mail,port=port)



            if parent.checkbox.get():
                    ''' create a job to configure bandwidth on router at a later time '''

                    setdate = parent.setdatevar.get() #assign the sheduled time
                    try: setdate = datetime.datetime.strptime(setdate, '%d-%m-%Y') #create a datetime object
                    except ValueError:
                        Dialog(parent,prompt="Later date has wrong format\n",icon = self.error)
                        return
                    setdate = datetime.datetime.strftime(setdate, '%Y-%m-%d') #change the time format to be used with "at"

                    st = st.zfill(6)+'_0' #change the st name to be different form the one on revert job

                    if ipDict[pe]['software'] == 'junos' :
                         commandList = d.junos(pe,ls,iface,vlan,pir)
                    elif ipDict[pe]['software'] == 'ios' :
                         commandList = d.cisco(pe,ls,iface,vlan,pir)


                    data = {'pe':pe,'ticket':st,'date':setdate,'commands':commandList}


                    set_job_created = False # later scheduled task
                    if commandList:
                        set_job_created = createJob(parent,serverlogin,server,directory,keyPath,data,commandList,mail=mail,port=port)
                        parent.config(cursor='')
                        parent.update()
                        parent.loading.stop(parent)
                        if revert_job_created and set_job_created:
                            Dialog(parent,prompt='Ticket '+str(st)+' updated successfully \n',icon=check_icon)


            else:
                ''' configure the on demand bandwidth on router right away'''

                if ipDict[pe]['software'] == 'junos' :
                     commandList = d.junos(pe,ls,iface,vlan,pir)
                elif ipDict[pe]['software'] == 'ios' :
                     commandList = d.cisco(pe,ls,iface,vlan,pir)

                confDict[pe] = {'software':ipDict[pe]['software'],
                                'hostname': ipDict[pe]['hostname'],
                                'commands': commandList}

                self.c = SendCommand()
                error = False
                if revert_job_created:
                    error = self.c.execute(parent,confDict,parent.username, parent.password,extra=revert_job_created)

                parent.config(cursor='')
                parent.update()
                parent.loading.stop(parent)
                if revert_job_created:
                    if error:
                        Dialog(parent,prompt='There was an error in configuration of '+pe+
                                             ' \nHowever a revert task has been added on server '+server+
                                             ' \nPlease configure the device manually, revert will be automated\n',
                               icon = self.warning)
                    else: Dialog(parent,prompt='Ticket '+ticket+' updated successfully \n',icon=success)


            if revert_job_created:
                parent.clear(confirmed=True)





class createConfig:

    @staticmethod
    def junos(pe,ls,iface,vlan,bw,ds=None,inet6=None):
        commandList = []
        if ls: commandList.append('show configuration logical-systems '+ls+' interface '+iface+'.'+vlan)
        else: commandList.append('show configuration interface '+iface+'.'+vlan)
        commandList.append('configure private')
        if ls: commandList.append('edit logical-systems '+ls)
        commandList.append('edit interface '+iface+'.'+vlan)

        if bw.lower() != 'unlimited':
            commandList.append('set family inet policer input '+bw)
            commandList.append('set family inet policer output '+bw)

        if inet6:
            if bw:
                commandList.append('set family inet6 policer input '+bw)
                commandList.append('set family inet6 policer output '+bw)

        commandList.append('top')
        commandList.append('show | compare')
        commandList.append('commit and-quit')
        if ls: commandList.append('show configuration logical-systems '+ls+' interface '+iface+'.'+vlan)
        else: commandList.append('show configuration interface '+iface+'.'+vlan)

        return commandList



    @staticmethod
    def cisco(pe,ls,iface,vlan,bw,ds=None,inet6=None):
        commandList = []
        ls = False
        if int(vlan) !=0:
            commandList.append('show running-config interface '+iface+'.'+vlan)
        else: commandList.append('show running-config interface '+iface)
        commandList.append('configure terminal')
        if int(vlan) !=0:
            commandList.append('interface '+iface+'.'+vlan)
        else: commandList.append('interface '+iface)

        if bw.lower() != 'unlimited':
            commandList.append('service-policy input '+bw)
            commandList.append('service-policy output '+bw)

        commandList.append('end')
        commandList.append('write memory')
        if int(vlan) !=0:
            commandList.append('show running-config interface '+iface+'.'+vlan)
        else: commandList.append('show running-config interface '+iface)

        return commandList


