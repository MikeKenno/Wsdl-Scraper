# lxml is a complete library for parsing xml and html files.  http://codespeak.net/lxml/
# The interface is not totally intuitive, but it is very effective to use, 
# especially with cssselect.

import mechanize
import codecs
import lxml.etree
import lxml.html
import re

import wsdlchecks
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from wsdlchecks import WSDLCheck
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

#set filename
outfilename = 'wsdl data links.txt'
count=0
urlnum=0

engine = create_engine('sqlite:///wsdl.db', echo=True)
wsdl_table = WSDLCheck.__table__
metadata = wsdlchecks.Base.metadata
metadata.create_all(engine)

##########################################################################
#
# Main function
#
##########################################################################
def main():
    global urlnum
    filehandler('WsdlDataLinks.txt')
    
    inf=open(outfilename,'r')
    for line in inf:
        url=line.split(',')
        print url[0],url[1],url[2]
        urlnum = url[0]
        parseurl(url[2])
    inf.close()
        
    print "Finished"
    
def parseurl(url):
    global urlnum
    section =0.1
    print "get the wsdladdresses from "+url
    r = re.compile('.*/services/')
    m=r.search(url)
    if m:
        phost =[url,url[m.start():m.end()],url[m.start():m.end()]+'listServices']
        #print 'axis2 link: '+urlnum
        for p in phost:
            getpage(p)
    else:
        #print 'asmx link: '+urlnum
        getpage(url)
        
def filehandler(filename):
    global count
    inf=open(filename,'r')
    #open the file, in unicode format for appending
    outf=open(outfilename,'a')
    outf.write('Count,Host,Wsdl address\n')
    for line in inf:
        hosts =line.split(',')
        r = re.compile('//.*?/')
        try:
            m=r.search(hosts[2])
            hosturl= hosts[2][m.start()+2:m.end()-1]
            if re.search(r'.*\?.*',hosts[2]):
                host=hosts[2].split('?')
                outf.write(str(count)+','+hosturl+','+host[0]+'\n')
            else:
                outf.write(str(count)+','+hosturl+','+hosts[2])
                print count,hosts[2]
        except IndexError:
            print count,"Unable to get the hosts[2] element"
        count+=1
            
    inf.close()
    outf.close()
################################################################################
#
#Retrieve function - given a url it will attempt to open the url and retrieve
#                   the data that was returned
#
################################################################################
def retrieve(url):
    check = False
    try:
        html=mechanize.Browser()
        html.set_handle_robots(False)
        html.addheaders = [('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.517.44 Safari/534.7')]
        data=html.open(url)
        check=True
    except:
        print "unable to retrieve page"
    if check:
        return data
    else:
        return check
##########################################################################
#
# getpage function - get the links for all the search results
#
##########################################################################
def getpage(url):
    
    returl = retrieve(url)
    #print returl
    if returl:
        root = lxml.html.parse(returl).getroot()
        #print(lxml.etree.tostring(root, pretty_print=True))
        #create a list of urls based on the css
        #get the href from the css element 'a'
        if root:
            urls = [a.get('href') for a in root.cssselect('a')if re.match(r".*\?[wW][sS][dD][lL]", lxml.etree.tostring(a))]
            for i,u in enumerate(urls):
                if re.search(r"^http://", u):
                    #print 'full string: '+u
                    storewsdl(u)
                else:
                    #print 'only relative link: '+url+u
                    relativeurl=url.replace('\n','?WSDL')
                    #print relativeurl
                    storewsdl(relativeurl)
    else:
        print "unable to get the links"

##########################################################################
#
# storewsdladdress function - get the addresses of the found wsdls and
#                           and store them in the file
#
##########################################################################
def storewsdl(url):
    '''
    global urlnum
    returl = retrieve(url)
    wsdl=url.replace('/','-').replace(':','').replace('?','.')
    wsdlfile='Numbered Wsdls/'+str(urlnum)+wsdl#+'.wsdl'
    if returl:
        try:
            #open the address passed in
            root = lxml.etree.parse(returl)
            #  print (lxml.etree.tostring(root, pretty_print=True))
            #open the file, in unicode format for appending
            f=codecs.open(wsdlfile,encoding='utf-8',mode='a')
            f.write('<?xml version="1.0" encoding="utf-8"?>\n')
            f.write(lxml.etree.tostring(root, pretty_print=True))
            #close the file
            f.close()
        except:
            print 'Unable to parse wsdl correctly'
    else:
        print 'no wsdl data returned'
    '''
    
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        wsdl = WSDLCheck(url)
        session.add(wsdl)
        session.new
        session.commit()
    except:
        pass
    
    
        
if __name__ == "__main__":
    main()
