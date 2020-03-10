# This module is part of the core Basondole Tools
# This class provided GUI for input data to be used with bBurst


import tkinter
import ttk
from core.burstServiceEditor import burst_actions, kazi
from core.vlanSingleFinder import getUsedVlanDesc
from other.Essential import resource_path
from windows.WindowDialog import Dialog
from windows.WindowLoading import loading


__author__ = "Paul S.I. Basondole"
__version__ = "2.0"
__maintainer__ = "Paul S.I. Basondole"
__email__ = "bassosimons@me.com"

warning_icon = resource_path(r"warning-icon.png")


class BurstPackages(tkinter.Toplevel):

    def __init__(self,username,password,ipDict,serverdata,action=None):

        self.user = username
        self.key = password

        serverlogin = serverdata['user']
        server = serverdata['address']
        FQP = serverdata['onserver_file']
        keypath = serverdata['private_key']
        port = serverdata['port']

        if not action: title = 'Burst Packages'

        tkinter.Toplevel.__init__(self)

        self.withdraw() # remain hidden untill all widgets are loaded

        _bgcolor = '#d9d9d9'  # X11 color: 'gray85'
        _fgcolor = '#000000'  # X11 color: 'black'
        _compcolor = '#d9d9d9' # X11 color: 'gray85'
        _ana1color = '#d9d9d9' # X11 color: 'gray85'
        _ana2color = '#ececec' # Closest X11 color: 'gray92'
        font11 = "-family Calibri -size 15 -weight bold -slant roman "  \
            "-underline 0 -overstrike 0"
        self.style = ttk.Style()
        self.style.configure('.',background=_bgcolor)
        self.style.configure('.',foreground=_fgcolor)
        self.style.configure('.',font="TkDefaultFont")
        self.style.map('.',background=
            [('selected', _compcolor), ('active',_ana2color)])

        self.geometry("570x690+346+156")
        self.resizable(width=False, height=False)
        self.title(action)
        self.configure(background="#d9d9d9")

        try: open(keypath)
        except FileNotFoundError:
            Dialog(self,prompt="SSH private login key not found\n confirm file location in settings\n",icon = warning_icon)
            self.destroy()
            return

        self.Frame1 = tkinter.Frame(self)
        self.Frame1.place(relx=0.013, rely=0.014, relheight=0.978, relwidth=0.974)
        self.Frame1.configure(borderwidth="2")
        self.Frame1.configure(background="#d9d9d9")
        self.Frame1.configure(width=555)

        self.Label1 = tkinter.Label(self.Frame1)
        self.Label1.place(relx=0.013, rely=0.015, height=43, width=193)
        self.Label1.configure(background="#d9d9d9")
        self.Label1.configure(disabledforeground="#a3a3a3")
        self.Label1.configure(font=font11)
        self.Label1.configure(foreground="#000000")
        self.Label1.configure(highlightbackground="#f0f0f0f0f0f0")
        self.Label1.configure(text='''Burst Packages''')


        self.Frame3 = tkinter.Frame(self.Frame1)
        self.Frame3.place(relx=0.013, rely=0.104, relheight=0.881, relwidth=0.964)


        self.Frame3.configure(background="#d9d9d9")
        self.Frame3.configure(highlightbackground="#d9d9d9")
        self.Frame3.configure(highlightcolor="black")
        self.Frame3.configure(width=535)

        self.Frame3_9 = tkinter.Frame(self.Frame3)
        self.Frame3_9.place(relx=0.037, rely=0.034, relheight=0.261, relwidth=0.925)
        self.Frame3_9.configure(relief='groove')
        self.Frame3_9.configure(borderwidth="2")
        self.Frame3_9.configure(relief='groove')
        self.Frame3_9.configure(background="#d9d9d9")
        self.Frame3_9.configure(highlightbackground="#d9d9d9")
        self.Frame3_9.configure(highlightcolor="black")
        self.Frame3_9.configure(width=495)


        def updateint(*args):
            comboboxes = [self.TCombobox1_5,self.TCombobox1_6,self.TCombobox1_7,
                          self.TCombobox1_8,self.TCombobox1_9,self.TCombobox1_10,self.TCombobox1_11]
            for cbox in comboboxes: cbox.set('') # clear the comboboxes

            self.usedvlans = []
            self.TEntry1_12.delete(0,tkinter.END)
            self.TCombobox1_6.configure(textvar=self.vlanselect, values=self.usedvlans)
            self.TCombobox1_6.set('')
            if action.lower() == 'remove' or action.lower() == 'update':
                self.TCombobox1_5.configure(textvar=self.intselect, values=list(ipDict[self.devselect.get()]['interfaces'].keys()))
                self.TCombobox1_5.set('Select interface')
                return
            self.TCombobox1_5.configure(textvar=self.intselect, values=ipDict[self.devselect.get()]['interfaces'])
            self.TCombobox1_5.set('Select interface')
            self.TCombobox1_10.configure(textvar=self.cirselect, values=ipDict[self.devselect.get()]['policers'])
            self.TCombobox1_10.set('Select CIR')
            self.TCombobox1_11.configure(textvar=self.pirselect, values=ipDict[self.devselect.get()]['policers'])
            self.TCombobox1_11.set('Select PIR')

        

        if action.lower() == 'remove' or action.lower() == 'update':

            self.view = kazi(server,serverlogin,FQP,keypath,parent=self,port=port)
            if self.view.status.up:
                clientsdata = self.view.view(self,get=True)
                _dic = ipDict # holds the actual dictionary values
                ipDict = clientsdata   # create a custom ipdict from existing client database
                try:
                    for key in ipDict.keys(): ipDict[key]['policers']= _dic[key]['policers'] #add policers to the new custom dict
                except KeyError: ipDict[key]['policers'] = ['Null']
            else:
                self.destroy()
                return

        ipList = list(ipDict.keys())
        ipList.sort()

        self.devselect = tkinter.StringVar(self.Frame3_9)
        self.TCombobox1_4 = ttk.Combobox(self.Frame3_9)
        self.TCombobox1_4.place(relx=0.02, rely=0.258, relheight=0.2, relwidth=0.448)
        self.TCombobox1_4.configure(textvariable=self.devselect, values=ipList)
        self.TCombobox1_4.configure(takefocus="")
        self.TCombobox1_4.configure(state='readonly')
        self.TCombobox1_4.bind("<<ComboboxSelected>>", updateint)



        def updatevlan(*args):
            self.TEntry1_12.delete(0,tkinter.END)
            if action.lower() == 'remove' or action.lower() == 'update':
                existingvlans = list(ipDict[self.TCombobox1_4.get()]['interfaces'][self.TCombobox1_5.get()].keys())
                existingvlans.sort()
                self.TCombobox1_6.configure(textvar=self.vlanselect, values=existingvlans)
                self.TCombobox1_6.set('Select')
                return
            if self.TCombobox1_5.get() == 'Null':
                self.usedvlans = []
                self.TCombobox1_6.configure(textvar=self.vlanselect, values=self.usedvlans)
                return
            self.loading = loading(self.Frame3_9,self,pbar=[0.505,0.71,0.2,0.448],words='Loading vlans')
            self.update_idletasks()
            self.vlanDict = getUsedVlanDesc(self.TCombobox1_4.get(),ipDict,self.TCombobox1_5.get(),self.user,self.key)
            self.usedvlans = list(self.vlanDict.keys())
            self.usedvlans.sort()
            self.TCombobox1_6.configure(textvar=self.vlanselect, values=self.usedvlans)
            self.TCombobox1_6.set('Select')
            self.config(cursor='')
            self.update()
            self.loading.stop(self)

        self.intselect = tkinter.StringVar(self.Frame3_9)
        self.TCombobox1_5 = ttk.Combobox(self.Frame3_9)
        self.TCombobox1_5.place(relx=0.02, rely=0.71, relheight=0.2
                , relwidth=0.448)
        self.TCombobox1_5.configure(takefocus="")
        self.TCombobox1_5.bind("<<ComboboxSelected>>", updatevlan)


        def updatedesc(*args):
            if action.lower() == 'remove' or action.lower() == 'update':
                
                self.TEntry1_12.delete(0,tkinter.END)
                self.TEntry1_12.insert(0, ipDict[self.TCombobox1_4.get()]['interfaces'][self.TCombobox1_5.get()][self.TCombobox1_6.get()]['name'])
                
                self.TCombobox1_10.configure(textvar=self.cirselect, values=ipDict[self.TCombobox1_4.get()]['policers'])
                self.TCombobox1_10.set(ipDict[self.TCombobox1_4.get()]['interfaces'][self.TCombobox1_5.get()][self.TCombobox1_6.get()]['daybandwidth'])
                
                self.TCombobox1_11.configure(textvar=self.pirselect, values=ipDict[self.TCombobox1_4.get()]['policers'])
                self.TCombobox1_11.set(ipDict[self.TCombobox1_4.get()]['interfaces'][self.TCombobox1_5.get()][self.TCombobox1_6.get()]['nightbandwidth'])
                
                self.TCombobox1_7.set(ipDict[self.TCombobox1_4.get()]['interfaces'][self.TCombobox1_5.get()][self.TCombobox1_6.get()]['days'])
                self.TCombobox1_8.set(ipDict[self.TCombobox1_4.get()]['interfaces'][self.TCombobox1_5.get()][self.TCombobox1_6.get()]['starttime'])
                self.TCombobox1_9.set(ipDict[self.TCombobox1_4.get()]['interfaces'][self.TCombobox1_5.get()][self.TCombobox1_6.get()]['endtime'])
                
                return               
            
            self.TEntry1_12.delete(0,tkinter.END)
            self.TEntry1_12.insert(0,self.vlanDict[self.vlanselect.get()])


        self.vlanselect = tkinter.StringVar(self.Frame3_9)
        self.TCombobox1_6 = ttk.Combobox(self.Frame3_9)
        self.TCombobox1_6.place(relx=0.505, rely=0.71, relheight=0.2, relwidth=0.448)
        self.TCombobox1_6.configure(takefocus="")
        self.TCombobox1_6.bind("<<ComboboxSelected>>", updatedesc)

        self.TLabel1_6 = ttk.Label(self.Frame3_9)
        self.TLabel1_6.place(relx=0.02, rely=0.065, height=29, width=150)
        self.TLabel1_6.configure(background="#d9d9d9")
        self.TLabel1_6.configure(foreground="#000000")
        self.TLabel1_6.configure(font="TkDefaultFont")
        self.TLabel1_6.configure(relief='flat')
        self.TLabel1_6.configure(text='''Edge router''')

        self.TLabel1_7 = ttk.Label(self.Frame3_9)
        self.TLabel1_7.place(relx=0.02, rely=0.516, height=29, width=100)
        self.TLabel1_7.configure(background="#d9d9d9")
        self.TLabel1_7.configure(foreground="#000000")
        self.TLabel1_7.configure(font="TkDefaultFont")
        self.TLabel1_7.configure(relief='flat')
        self.TLabel1_7.configure(text='''Interface''')

        self.TLabel1_8 = ttk.Label(self.Frame3_9)
        self.TLabel1_8.place(relx=0.505, rely=0.516, height=29, width=100)
        self.TLabel1_8.configure(background="#d9d9d9")
        self.TLabel1_8.configure(foreground="#000000")
        self.TLabel1_8.configure(font="TkDefaultFont")
        self.TLabel1_8.configure(relief='flat')
        self.TLabel1_8.configure(text='''VLAN''')

        self.Frame3_10 = tkinter.Frame(self.Frame3)
        self.Frame3_10.place(relx=0.037, rely=0.319, relheight=0.261, relwidth=0.925)
        self.Frame3_10.configure(relief='groove')
        self.Frame3_10.configure(borderwidth="2")
        self.Frame3_10.configure(relief='groove')
        self.Frame3_10.configure(background="#d9d9d9")
        self.Frame3_10.configure(highlightbackground="#d9d9d9")
        self.Frame3_10.configure(highlightcolor="black")
        self.Frame3_10.configure(width=495)

        self.dayselect = tkinter.StringVar(self.Frame3_10)
        self.TCombobox1_7 = ttk.Combobox(self.Frame3_10)
        self.TCombobox1_7.place(relx=0.02, rely=0.258, relheight=0.2, relwidth=0.448)
        self.TCombobox1_7.configure(textvariable=self.dayselect, values=['everyday','weekdays','weekends'])
        self.TCombobox1_7.configure(takefocus="")
        self.TCombobox1_7.configure(state='readonly')

        time = [str(x).zfill(2)+'00' for x in range(0,24)]
        self.starttime = tkinter.StringVar(self.Frame3_10)
        self.TCombobox1_8 = ttk.Combobox(self.Frame3_10)
        self.TCombobox1_8.place(relx=0.02, rely=0.71, relheight=0.2, relwidth=0.448)
        self.TCombobox1_8.configure(textvariable=self.starttime, values=time)
        self.TCombobox1_8.configure(takefocus="")
        self.TCombobox1_8.configure(state='readonly')

        self.endtime = tkinter.StringVar(self.Frame3_10)
        self.TCombobox1_9 = ttk.Combobox(self.Frame3_10)
        self.TCombobox1_9.place(relx=0.505, rely=0.71, relheight=0.2, relwidth=0.448)
        self.TCombobox1_9.configure(textvariable=self.endtime, values=time)
        self.TCombobox1_9.configure(takefocus="")
        self.TCombobox1_9.configure(state='readonly')

        self.TLabel1_9 = ttk.Label(self.Frame3_10)
        self.TLabel1_9.place(relx=0.02, rely=0.065, height=29, width=150)
        self.TLabel1_9.configure(background="#d9d9d9")
        self.TLabel1_9.configure(foreground="#000000")
        self.TLabel1_9.configure(font="TkDefaultFont")
        self.TLabel1_9.configure(relief='flat')
        self.TLabel1_9.configure(text='''Days applicable''')

        self.TLabel1_10 = ttk.Label(self.Frame3_10)
        self.TLabel1_10.place(relx=0.02, rely=0.516, height=29, width=100)
        self.TLabel1_10.configure(background="#d9d9d9")
        self.TLabel1_10.configure(foreground="#000000")
        self.TLabel1_10.configure(font="TkDefaultFont")
        self.TLabel1_10.configure(relief='flat')
        self.TLabel1_10.configure(text='''Start time''')

        self.TLabel1_11 = ttk.Label(self.Frame3_10)
        self.TLabel1_11.place(relx=0.505, rely=0.516, height=29, width=100)
        self.TLabel1_11.configure(background="#d9d9d9")
        self.TLabel1_11.configure(foreground="#000000")
        self.TLabel1_11.configure(font="TkDefaultFont")
        self.TLabel1_11.configure(relief='flat')
        self.TLabel1_11.configure(text='''End time''')

        self.Frame3_11 = tkinter.Frame(self.Frame3)
        self.Frame3_11.place(relx=0.037, rely=0.604, relheight=0.261, relwidth=0.925)
        self.Frame3_11.configure(relief='groove')
        self.Frame3_11.configure(borderwidth="2")
        self.Frame3_11.configure(relief='groove')
        self.Frame3_11.configure(background="#d9d9d9")
        self.Frame3_11.configure(highlightbackground="#d9d9d9")
        self.Frame3_11.configure(highlightcolor="black")
        self.Frame3_11.configure(width=495)


        self.cirselect = tkinter.StringVar(self.Frame3_11)
        self.TCombobox1_10 = ttk.Combobox(self.Frame3_11)
        self.TCombobox1_10.place(relx=0.02, rely=0.258, relheight=0.2, relwidth=0.448)
        self.TCombobox1_10.configure(takefocus="")


        self.pirselect = tkinter.StringVar(self.Frame3_11)
        self.TCombobox1_11 = ttk.Combobox(self.Frame3_11)
        self.TCombobox1_11.place(relx=0.505, rely=0.258, relheight=0.2, relwidth=0.448)
        self.TCombobox1_11.configure(takefocus="")

        self.TLabel1_10 = ttk.Label(self.Frame3_11)
        self.TLabel1_10.place(relx=0.02, rely=0.516, height=29, width=150)
        self.TLabel1_10.configure(background="#d9d9d9")
        self.TLabel1_10.configure(foreground="#000000")
        self.TLabel1_10.configure(font="TkDefaultFont")
        self.TLabel1_10.configure(relief='flat')
        self.TLabel1_10.configure(text='''Client name''')

        self.TLabel1_11 = ttk.Label(self.Frame3_11)
        self.TLabel1_11.place(relx=0.02, rely=0.065, height=29, width=160)
        self.TLabel1_11.configure(background="#d9d9d9")
        self.TLabel1_11.configure(foreground="#000000")
        self.TLabel1_11.configure(font="TkDefaultFont")
        self.TLabel1_11.configure(relief='flat')
        self.TLabel1_11.configure(text='''Subscription (CIR)''')

        self.TLabel1_12 = ttk.Label(self.Frame3_11)
        self.TLabel1_12.place(relx=0.505, rely=0.065, height=29, width=100)
        self.TLabel1_12.configure(background="#d9d9d9")
        self.TLabel1_12.configure(foreground="#000000")
        self.TLabel1_12.configure(font="TkDefaultFont")
        self.TLabel1_12.configure(relief='flat')
        self.TLabel1_12.configure(text='''Burst (PIR)''')

        self.TEntry1_12 = ttk.Entry(self.Frame3_11)
        self.TEntry1_12.place(relx=0.02, rely=0.71, relheight=0.2, relwidth=0.933)
        self.TEntry1_12.configure(takefocus="")
        self.TEntry1_12.configure(cursor="ibeam")

        self.Button1 = tkinter.Button(self.Frame3)
        self.Button1.place(relx=0.093, rely=0.900, height=42, width=158)
        self.Button1.configure(pady="0")
        self.Button1.configure(text='''Save''')
        self.Button1.configure(command= lambda: conf(self,ipDict,serverdata,action))

        self.Button1_13 = tkinter.Button(self.Frame3)
        self.Button1_13.place(relx=0.550, rely=0.900, height=42, width=158)
        self.Button1_13.configure(pady="0")
        self.Button1_13.configure(text='''Clear''')
        self.Button1_13.configure(command= lambda: self.clear())

        if action.lower() == 'remove':

            self.geometry("570x600")
            self.Label1.place(relx=0.013, rely=0.01, height=43, width=193)
            self.Frame3_9.place(relx=0.037, rely=0.05, relheight=0.34, relwidth=0.925)
            self.Frame3_11.place(relx=0.037, rely=0.404, relheight=0.34 , relwidth=0.925)
            self.Button1.configure(text='''Remove''')          
            self.Button1.place(relx=0.093, rely=0.850, height=42, width=158)
            self.Button1_13.place(relx=0.550, rely=0.850, height=42, width=158)
            self.Frame3_10.place_forget()
            

        if action.lower() == 'update': self.Button1.configure(text='''Update''')

        self.deiconify() #show the window after all widgets are loadded


    def clear(self):
       comboboxes = [self.TCombobox1_4,self.TCombobox1_5,self.TCombobox1_6,
                     self.TCombobox1_7,self.TCombobox1_8,self.TCombobox1_9,
                     self.TCombobox1_10,self.TCombobox1_11]

       for cbox in comboboxes: cbox.set('')
       self.TEntry1_12.delete(0,tkinter.END)



class  conf():
    def __init__(self,parent,ipDict,serverdata,action):

            pe = parent.TCombobox1_4.get()
            if not pe in list(ipDict.keys()):
                Dialog(parent,prompt="Edge router unknown\n",
                       icon= warning_icon)
                return


            iface = parent.TCombobox1_5.get()
            if not iface in ipDict[pe]['interfaces'] or iface.lower()=='null':
                Dialog(parent,prompt="Interface unknown\n",icon= warning_icon)
                return

            vlan = parent.TCombobox1_6.get()
            try:
                if int(vlan) not in range(0,4095):
                    Dialog(parent,prompt="VLAN not in correct range\n",icon= warning_icon)
                    return
            except ValueError:
                Dialog(parent,prompt="VLAN not in correct range\n",icon= warning_icon)
                return

            if action.lower() != 'remove':
                days = parent.TCombobox1_7.get()
                if not days:
                    Dialog(parent,prompt="Specify applicable days\n",icon= warning_icon)
                    return

                st = parent.TCombobox1_8.get()
                if not st:
                    Dialog(parent,prompt="Specify start time\n",icon= warning_icon)
                    return

                et = parent.TCombobox1_9.get()
                if not et:
                    Dialog(parent,prompt="Specify end time\n",icon= warning_icon)
                    return

                cir = parent.TCombobox1_10.get()
                if not cir in ipDict[pe]['policers']:
                    Dialog(parent,prompt="CIR is not defined\n",icon= warning_icon)
                    return

                pir = parent.TCombobox1_11.get()
                if not pir in ipDict[pe]['policers']:
                    Dialog(parent,prompt="PIR is not defined\n",icon= warning_icon)
                    return

                ds = parent.TEntry1_12.get()
                if not ds:
                    Dialog(parent,prompt="Client name is not defined\n",icon= warning_icon)
                    return
                ds = ds.replace(' ','-')

                data = {'ip':pe, 'interface':iface,'vlan':vlan,
                        'cir': cir, 'pir': pir, 'start':st,
                        'end':et,'days':days,'name':ds}


            else: data = {'ip':pe,'interface':iface,'vlan':vlan}


            serverlogin = serverdata['user']
            server = serverdata['address']
            FQP = serverdata['onserver_file']
            keypath = serverdata['private_key']
            port = serverdata['port']


            ''' confirm before proceeding '''

            proceed = Dialog(parent,prompt='Click ok to proceed \nor cancel to review \n',
                          icon=warning_icon)
            if not proceed.ans == 'ok': return


            if action.lower() == 'remove': parent.loading = loading(parent.Frame3,parent,pbar=[0.093,0.85,0.08,0.300],words='Loading')
            else: parent.loading = loading(parent.Frame3,parent,pbar=[0.093,0.9,0.08,0.300],words='Loading')
            parent.update_idletasks()

            burst_actions(parent,serverlogin,server,FQP,keypath,action,data,port=port)

            parent.config(cursor='')
            parent.update()
            parent.loading.stop(parent)

            parent.clear()

