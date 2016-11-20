#!/usr/bin/env python
# get realtime quotes using icicidirect
# sample usage : gi  'KEWKIR'
# ./gi 'KEWKIR'
# {
#     "bse": "1775.00", 
#     "nse": "1775.25"
# }

import BeautifulSoup
import requests
import sys
import json

def get_quote(st_code):
    turl = 'http://getquote.icicidirect.com/trading_stock_quote.aspx?Symbol='
    url = turl + st_code
    r = requests.get(url)
    tables  = get_tables(r.text)
    ll = makelist(tables[0])
    np = ll[4][1]
    bp = ll[4][2]
    np = np.replace(',', '')
    bp = bp.replace(',', '')
    d = {'nse':np, 'bse':bp}
    return d
    

def get_tables(htmldoc):
    soup = BeautifulSoup.BeautifulSoup(htmldoc)
    return soup.findAll('table')

def makelist(table):
  result = []
  allrows = table.findAll('tr')
  for row in allrows:
    result.append([])
    allcols = row.findAll('td')
    for col in allcols:
      #thestrings = [unicode(s) for s in col.findAll(text=True)]
      thestrings = [(s) for s in col.findAll(text=True)]
      thetext = ''.join(thestrings)
      result[-1].append(thetext)
  return result

if len(sys.argv) != 2:
	print 'Usage: ' + sys.argv[0] + ' ' + '<stock_code>'
	sys.exit(1)

#data = get_quote('KEWKIR')
data = get_quote(sys.argv[1])
j = json.dumps(data, indent=4)
print(str(j))
#print(str(data))
