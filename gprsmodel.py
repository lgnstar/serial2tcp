
#!/usr/bin/env python3
#coding=utf-8

import sys
import serial
import platform
import time
import datetime
import threading
from socket import *

myserial = None
global stopevt


def serialName():
  if platform.system() == "Linux":
    return '/dev/ttyUSB0'
  if platform.system() == "Windows":
    return 'COM1'


def serialOpen():
  global myserial
  try:
    if myserial != None and myserial.isOpen():
      myserial.close()
    myserial = serial.Serial(serialName(), 115200)
    myserial.flush()
  except :
    pass

def serialReadline():
  global myserial
  try:
    return myserial.readline()
  except :
    serialOpen()
    return None

def serialWrite(data):
  global myserial
  try:
    myserial.write(data)
  except :
    serialOpen()



class tcpThread(threading.Thread):
  def __init__(self, stopevt = None, addr = None, name = 'tcpThread'):
    threading.Thread.__init__(self)
    self.stopevt = stopevt
    self.name = name
    self.addr = addr
    self.running = False
    self.connect = False
    try:
      self.client = socket(AF_INET,SOCK_STREAM)
      self.client.settimeout(1)
      self.client.connect(addr)
      self.connect = True
      print(datetime.datetime.strftime(datetime.datetime.now(),'%H:%M:%S') + '=> ' + 'socket connect OK!')
    except:
      print(datetime.datetime.strftime(datetime.datetime.now(),'%H:%M:%S') + '=> ' + 'socket connect error!')

  def isRunning(self):
    return self.running

  def isConnect(self):
    return self.connect

  def Close(self):
    self.client.close()

  def SendData(self, dat):
    if self.connect:
      try:
        self.client.sendall(dat)
      except:
        print('socket sendall error!')

  def run(self):
    global myser
    self.running = True
    print(datetime.datetime.strftime(datetime.datetime.now(),'%H:%M:%S') + '=> ' + 'tcpThread start!')
    while not self.stopevt.isSet():
      #time.sleep(0.1)
      try:
        data=''
        total_data=[]
        data=self.client.recv(1024)
        if not data:
          break
        data = ''.join(format(x, '02x') for x in data)
        if len(data) > 0:
          #dat = ''.join(format(x, '02x') for x in data)
          resp = 'OK\r\n%%IPDATA:%d,"%s"'%(len(data)/2, data.upper())
          serialWrite(resp.encode())
          print(resp)
      except:
        pass
    self.running = False
    self.connect = False
    print(datetime.datetime.strftime(datetime.datetime.now(),'%H:%M:%S') + '=> ' + 'tcpThread stop!')

stopevt = threading.Event()

def main():
  i = 0
  global myserial
  global stopevt
  tcpthread = None
  stopevt.clear()
  serialOpen()
  print(myserial)
  while 1:
    try:
      line = serialReadline()
      if line != None:
        print(datetime.datetime.strftime(datetime.datetime.now(),'%H:%M:%S') + '=> ' + line.decode())
        if line.startswith(b'AT+CSQ'):
          serialWrite(b'+CSQ: 6,99\r\nOK\r\n')

        elif line.startswith(b'AT%IPOPEN'):
          if tcpthread != None:
            print(datetime.datetime.strftime(datetime.datetime.now(),'%H:%M:%S') + '=> ' + 'stopevt.set()')
            tcpthread.Close()
            stopevt.set()
            tcpthread.join()
          str = line.decode().split(',')
          stopevt.clear()
          #tcpthread = tcpThread(stopevt, (str[1], str[2]))
          #tcpthread = tcpThread(stopevt, ('192.168.1.9', 7777))
          tcpthread = tcpThread(stopevt, ('192.168.3.67', 7777))
          #tcpthread.setDaemon(Ture)
          print(tcpthread.client)
          if tcpthread.isConnect():
            tcpthread.start()
            serialWrite(b'CONNECT\r\nOK\r\n')
            print(datetime.datetime.strftime(datetime.datetime.now(),'%H:%M:%S') + '=> ' + 'tcpthread.start()')
          else:
            serialWrite(b'ERROR\r\n')

        elif line.startswith(b'AT%IPSEND'):
          str = line.decode().split('"')
          code = bytes().fromhex(str[1])
          if tcpthread != None and tcpthread.isConnect():
            tcpthread.SendData(code)

        else :
          serialWrite(b'OK\r\n')
    except:
      print('line=serialReadline() error!!!')
      time.sleep(0.5)
      pass

if __name__ == '__main__':
  main()
