import re
import os
import sys
import base64
import random
from cryptography.fernet import Fernet
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random


__author__ = "Paul S.I. Basondole"
__credits__ = "Paul S.I. Basondole"
__version__ = "2.0"
__maintainer__ = "Paul S.I. Basondole"
__email__ = "bassosimons@me.com"


class credo:

  def changanya(username,password):
      ukey,username,key = encrypt(username.encode())
      pkey,password,key = encrypt(password.encode())
      encrypted_data = f'{key.decode()}\tux?/{username.decode()}\r\
      kx!#{password.decode()}\n9$x!{ukey.decode()}\rZ@%*{pkey.decode()}'
      return encrypted_data

  def read_from_file(encrypted_data):
      for line in encrypted_data.split('encrypted_data'):
          username = re.findall(r'ux\?/(\S+)',line)[0].encode()
          password = re.findall(r'kx\!\#(\S+)',line)[0].encode()
          ukey = re.findall(r'9\$x\!(\S+)',line)[0].encode()
          pkey= re.findall(r'Z\@\%\*(\S+)',line)[0].encode()
      return ukey,username,pkey,password

  def fungua(encrypted_data):
      ukey,username,pkey,password = credo.read_from_file(encrypted_data)
      username = decrypt(ukey,username)
      password = decrypt(pkey,password)
      return username, password

  def siri(encrypted_data):
      siri = credo.fungua(encrypted_data)[1].decode()
      return siri



def encrypt(data):
   key = 'eeCCJ-A1Kazl55rohV4V1q0xC0xl1dOewxhHBaXo4DY='
   cipher_suite = Fernet(key)
   base = cipher_suite.encrypt(data)
   key = random.choice("0123456789abcde")+random.choice('*()^%$')+random.choice('ABCDEFGH')
   key = key.encode()
   return key,base64.b64encode(base64.b64encode(
          f'{data}{key}'.encode())+key)+key,base


def decrypt(key,data):
   try: base64.b64decode(base64.b64decode(data.split(key)[0]).split(key)[0]).split(key)[0]
   except TypeError:
      print('INFO: Auto-retrieved login could not be decrypted, \
            the login file has been tempered with')
   return base64.b64decode(base64.b64decode(
          data.split(key)[0]).split(key)[0]).split(key)[0]
