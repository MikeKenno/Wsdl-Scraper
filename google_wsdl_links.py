#!/usr/bin/env python

# lxml is a complete library for parsing xml and html files.  http://codespeak.net/lxml/
# The interface is not totally intuitive, but it is very effective to use, 
# especially with cssselect.

import mechanize
import codecs
import lxml.etree
import lxml.html
import re

#set filename
filename = 'WsdlDataLinks.txt'

googlebase='http://www.google.co.uk'
nextlinkcount=0
wsdllinks=0
##########################################################################
#
# Main function
#
##########################################################################
def main():

    # urls to crawl
    targets =['/search?hl=en&noj=1&q=inurl:"/axis2/services/"&btnG=Search&aq=f&aqi=&aql=&oq=&gs_rfai=',
            '/search?q="Service+EPR"&oq="Service+EPR"&ie=UTF-8#q=%22Service+EPR%22+inurl%3Alistservices',
            '/search?q=filetype:asmx&btnG=Search&hl=en&noj=1&sa=2']
    
    # To load directly from a url, use
    #root = lxml.html.parse(base+starturl).getroot()
    #print(lxml.etree.tostring(root, pretty_print=True))
    for search in targets:
        getallresultsgoogle(googlebase+search)    
    print "Finished"

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
# getallresults function - get the links for all the search results
#
##########################################################################
def getallresultsgoogle(url):
    global nextlinkcount

    storewsdladdressesgoogle(url)
    print "get the wsdladdresses from "+url
    returl = retrieve(url)
    if returl:
        root = lxml.html.parse(returl).getroot()
        #print(lxml.etree.tostring(root, pretty_print=True))
        #create a list of urls based on the css
        #get the href from the css element 'table#nav td.b a'
        urls = [a.get('href') for a in root.cssselect('table#nav td.b a')if re.search(r"next", lxml.etree.tostring(a))]
        for i,url in enumerate(urls):
            print nextlinkcount,i,url
            nextlinkcount+=1
            getallresultsgoogle(googlebase+url)
    else:
        print "unable to get the links"

##########################################################################
#
# storewsdladdress function - get the addresses of the found wsdls and
#                           and store them in the file
#
##########################################################################
def storewsdladdressesgoogle(url):
    global wsdllinks
    returl = retrieve(url)
    if returl:
        root = lxml.html.parse(returl).getroot()

        f=codecs.open(filename,encoding='utf-8',mode='a')

        #create a list of urls based on the css
        #get the href from the css element 'div.rc h3.r a'
        #we're only interested in the ones that are likely to be actual imlementations not posting or messages about axis2
        urls = [a.get('href') for a in root.cssselect('div.srg div.g div.rc h3.r a') if re.search(
            r"\.asmx", lxml.etree.tostring(a)) or re.search(r"services", lxml.etree.tostring(a))] #search for those lines that match .asmx or for those lines that match /axis2/services

        #loop through the urls and number them
        for i,url in enumerate(urls):
            #write them to the file
            print wsdllinks,url
            f.write(str(wsdllinks)+','+str(i)+','+url+'\n')
            wsdllinks+=1
            #close the file
        f.close()
    else:
        print 'no wsdl data returned'

if __name__ == "__main__":
    main()
