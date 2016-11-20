#!/usr/bin/env python
# -*- coding: utf-8 -*- 

# script to process notifications periodically from opentrade, parse and execute them.
# output is written to the reports directory which gets created the first time

# Phase 1 : get the mail                                      DONE
# Phase 2 : feature extraction                                DONE
# Phase 3 : execute based on some parameters                 
#          (safety margin, limit/ market, equity/future,...)
# Phase 4 : Write to audit filename


# Sample run
# =================
# $ ./fetch_trade.py 
# 2016-11-20-08:33:15: Getting 2 from server
# List:('+OK 2 messages (13426 bytes)', ['1 6713', '2 6713'], 16)
# MySubject:Fwd: Fwd: Fwd: Fwd: New trade by Ara - Opentrade
# Time:Sat, 19 Nov 2016 04:20:05 -0800
# file written to reports/output_20161120_08_33_13.txt
# Retaining mail
# offset of transaction found at 124
# [currtime, mytime, src, trade_type, tx, stock, price]
# ['2016_11_20_08_33', '02:25 PM', 'NFO', 'SOLD', 'BANKNIFTY03NOV1618900PE', '12.91']
# Saving to file : reports/zeroresult.csv

###############################################################################
# TODOs:
# add command line knobs :
#     retain, execute_nfo, execute_nse, execute_bse, execute_all
# send mail / notification whenever format goes kaput
# get subject 
# get time of mail
###############################################################################
import os
import datetime
import poplib
from email import parser
import code
import html2text
import time
import sys
import csv
import re
import linecache
import unicodedata
import logging
import errno

################################################################################

knob_reports_dir = 'reports'
tmp_mail_dump = 'output_'
knob_suffix = time.strftime("%Y%m%d_%H_%M_%S")
knob_report_file = knob_reports_dir + '/' + tmp_mail_dump + knob_suffix + '.txt'


#####################   CONFIGURATION PARMARETERS ##############################   
config_user='someuser@gmail.com'
config_password='XXX'
config_retain_mail = False
config_retain_mail = True

config_results = knob_reports_dir + '/' + 'zeroresult.csv'
# name of the report to generate

############################# UTILITY FUNCTIONS ################################

LOG_FILENAME = 'zeroaudit.log'
LOG_FULLPATH = knob_reports_dir + '/' + LOG_FILENAME

def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)

def get_list_after_uid(ll, n):
    index = 0
    popping = []
    for i in ll:
        if int(i) <= int(n):
            popping.append(index)
        else:
            break
        index += 1
    return ll[index:]

def date_str():
    pstr = str(datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S'))
    return str(pstr)

# assumes that the time is for today, accepts input like
# crafted_date = '11:32 AM' -> epoch in seconds with todays date assumed
def get_epoch_by_transaction_time(am_pm):    
    ndt = date_str()[:10]
    #'2016-11-12 11:32 AM'
    crafted_date = ndt + ' ' + am_pm
    # convert it to a struct time object
    st = time.strptime(crafted_date, '%Y-%m-%d %I:%M %p')
    print(str(st))
    # convert time to epoch
    epoch = time.mktime(st)
    return int(epoch)

# returns date and time in the present
# eg. 2016_09_08_13
def get_date_time_human_readable():
    #return str(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M:%S'))
    return str(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M'))


# read contents of a file and return a list
def read_file_to_list(filename):
    with open('mail.txt') as f:
        lines = f.read().splitlines()
    return lines

# read contents of a file as a string
def read_filename_to_string(filename):
    with open(filename, 'r') as myfilename:
        data = myfilename.read().replace('\n', '')
    #data = data.replace('\t', '    ')    
    return data

# phase 1.5
def convert_html_to_plaintext(filename):    
    html = open(filename).read()
    # convert to text
    text_body = html2text.html2text(html.decode('utf8'))
    #print(text_body)
    return text_body

# for debug functionality : to check positional parameters
def decode_everything(lines):
    for i in range(len(lines)):
        print ('i['+ str(i) +'] = {{' + lines[i] + '}}')
        zelog.debug('i['+ str(i) +'] = {{' + lines[i] + '}}')


def isInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False
# [mytime, src, trade_type, tx, stock, price]
# ['01:11 PM', 'Ara', 'NFO', 'BUY', 'NIFTY16NOV8800CE', '6.4']

# kludgy version : needs to be Fixed
def decode_trade_details(lines):
    try:
        lines = lines.encode('utf-8')
        lines = lines.replace(' EXIT', '')
        lines = lines.replace(' PARTIAL', '')
        lines = lines.replace(' COMPLETE', '')
        #if ' COMPLETE' in lines:
        #    print 'am still incomplete ONE'
        #print('---------------------------')
        #f1=open('./testfile', 'w+')
        #print>> f1, lines
        #print('||||||||||||||||||||||||||||')

        #lines = lines.replace('EXIT ', '')
        #lines = lines.replace('PARTIAL ', '')
        #lines = lines.replace('COMPLETE ', '')
        lines = lines.replace('\n', ' ')
        lines = lines.replace('|', ' ')
        if ' COMPLETE' in lines:
            #print 'am still incomplete TWO'
            lines = lines.replace(' COMPLETE', '')
        #f1=open('./testfile2', 'w+')
        #print>> f1, lines
        #print(lines)
        ll = lines.split(' ')        
        obs = 0
        count = 0
        for element in ll:
            #if ('BOUGHT' or 'SOLD') in element:
            if 'SOLD' in element:
                print('offset of transaction found at ' + str(count))
                obs = count
                break
            if 'BOUGHT' in element:
                print('offset of transaction found at ' + str(count))
                obs = count
                break
            count += 1
        
        ll = [x.strip(' ') for x in ll]
        mytime = ' '.join(ll[obs-2:obs])
        tx = ll[obs]
        stock = ll[obs + 1]
        trade_type = ll[obs + 2]
        price = ll[obs + 4]
    except Exception: 
        print('Exception encountered')
        PrintException()
        code.interact(local=locals())

    record = [mytime, trade_type, tx, stock, price]
    #record = [x.encode('UTF8') for x in record]
    #print(str(record))        
    #code.interact(local=locals())
    return record
    
# uses a global variable tmp_mail_dump
def phase_fetchmail_to_file():
    pop_conn = poplib.POP3_SSL('pop.gmail.com')
    pop_conn.user(config_user)
    pop_conn.pass_(config_password)
    num_messages = len(pop_conn.list()[1])
    
    print(date_str() + ': Getting ' + str(num_messages) + ' from server')
#     print(date_str() + ' List: ' + str((pop_conn.list())))
#     print(date_str() + 'Stat: ' + str((pop_conn.stat())))
    
    
    #Get messages from server:
    index = 0
    
    res_list = pop_conn.list()
    print('List:' + str(res_list))
    if ' 0 messages' in res_list[0]:
        print('No mails')
        sys.exit(0)
    #code.interact(local=locals())
    
    #sys.exit(0)
    #messages = [pop_conn.retr(i) for i in range(1, len(pop_conn.list()[1]) + 1)]

#     #process 1 mail at a time
    messages = [pop_conn.retr(i) for i in range(1,2)]
    
#     # Concat message pieces:
    messages = ["\n".join(mssg[1]) for mssg in messages]
    #Parse message into an email object:
    messages = [parser.Parser().parsestr(mssg) for mssg in messages]
    if len(messages) == 0:
        print('No messages')
        sys.exit(0)
    for message in messages:
#         code.interact(local=locals())
        print ('MySubject:' + message['subject'])
        print ('Time:' + message['Date'])
        #print ('Body' + message['body'])
    
    mail_body=''
    #code.interact(local=locals())
    for i in message.walk():
        #print i.get_payload(decode=True)
        mail_body += str(i.get_payload(decode=True))
        index += 1
#     print(date_str() + ': written to ' + knob_report_file)
    
    # save to a filename
    with open(knob_report_file, "w") as text_filename:
        text_filename.write(mail_body)
    
    print('file written to ' + knob_report_file)
    #code.interact(local=locals())
    if config_retain_mail == False:
        print('Deleting mail')
        pop_conn.dele(1)
        pop_conn.quit()
        
    else:
        print('Retaining mail')
    return knob_report_file

def remove_values_from_list(the_list, val):
    while val in the_list:
        the_list.remove(val)
    return the_list

# creates a directory if it does not exist
def ensure_dir(directory):
    if not os.path.exists(directory):
        print(date_str() + ': creating directory ' + directory)
        os.makedirs(directory)
        
def make_sure_path_exists(path):
    if not os.path.exists(path):
        print(date_str() + ": creating directory '" + path + "'")
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def extract_src(line):
    regex = r".*\s(?P<src>\w+)\s+just placed.*"
    patt = re.compile(regex)
    matches = patt.match(line)
    return  matches.groupdict().get('src')

def get_list_from_lines(lines):
    pll = lines.split('\n')
    # remove empty elements
    pll = filter(None, pll)
    # remove elements with just spaces
    pll = filter(lambda name: name.strip(), pll)
    # remove other superfluous values
    pll = remove_values_from_list(pll, '__')
    pll = remove_values_from_list(pll, '](https://opentrade.in)')
    return pll

def find_between(s, start, end):
    return (s.split(start))[1].split(end)[0]

if __name__ == '__main__':
    make_sure_path_exists(knob_reports_dir)
    
    # initialise logging stuff
    logging.basicConfig(filename=LOG_FULLPATH,level=logging.DEBUG)
    zelog = logging.getLogger('ze')
    
    raw_mail_file = phase_fetchmail_to_file()
    
    lines = convert_html_to_plaintext(raw_mail_file)
    record = decode_trade_details(lines)
    
    # add current timestamp to the beginning of the record
    record.insert(0, get_date_time_human_readable())
    print('[currtime, mytime, src, trade_type, tx, stock, price]')
    print(str(record))
    zelog.debug(str(record))


    # save to a file
    print('Saving to file : ' + config_results)
    myfile = open(config_results, 'ab+')
    wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
    wr.writerow(record)
