# This module contains different essential functions
__author__ = "Paul S.I. Basondole"
__version__ = "2.0"
__maintainer__ = "Paul S.I. Basondole"
__email__ = "bassosimons@me.com"

class dotted(dict):
    ''' Convert ordinary dictionary to support dot nottation
    '''
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self,dictionary):
        for key, value in dictionary.items():
            if hasattr(value, 'keys'):
                value = dotted(value)
            self[key] = value



def resource_path(relative_path):
    ''' Get absolute path to resource, works for dev and for PyInstaller
    '''
    import sys
    import os
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def close(current,parent=False):
    ''' Restore focus on a parent tkinter window and closes the current window
    '''
    if parent: parent.attributes('-disabled', False)
    current.destroy()




def delEmptyLine(file):
   ''' Sort and remove empty line from a text file
   '''

   list = file.split('\n')
   list.sort()
   cleanFile = [item.strip() for item in list if item]
   cleanFile = '\n'.join(cleanFile)
   return cleanFile.strip()





def location(master,frame,relx=0.24, rely=0.3):
    ''' Estimate position for a pop up window with respect to parent window
    '''
    widget = frame
    if master.winfo_ismapped():
        m_width = master.winfo_width()
        m_height = master.winfo_height()
        m_x = master.winfo_rootx()
        m_y = master.winfo_rooty()
    else:
        m_width = master.winfo_screenwidth()
        m_height = master.winfo_screenheight()
        m_x = m_y = 0
    w_width = widget.winfo_reqwidth()
    w_height = widget.winfo_reqheight()
    x = m_x + (m_width - w_width) * relx
    y = m_y + (m_height - w_height) * rely
    if x+w_width > master.winfo_screenwidth():
        x = master.winfo_screenwidth() - w_width
    elif x < 0:
        x = 0
    if y+w_height > master.winfo_screenheight():
        y = master.winfo_screenheight() - w_height
    elif y < 0:
        y = 0

    return x,y



def update_loading_screen(popup,label='',value=''):

   if value == 100:
      try: popup['window'].destroy()
      except Exception: pass
      return

   try:
       popup['value'].set(value)
       popup['label'].config(text = label)
       popup['window'].update()

   except Exception: pass
