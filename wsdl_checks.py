#Wsdl Parsing class
import re,socket,mechanize,time
import sys, os,codecs
import lxml.etree
import lxml.html
try:
    from hashlib import sha1 as _sha, md5 as _md5
except ImportError:
    import sha
    import md5
    _sha = sha.new
    _md5 = md5.new

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.ext.declarative import declarative_base


#Globals
USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
SCRAPING_DOMAINS = {}
SCRAPING_DOMAIN_RE = re.compile("\w+:/*(?P<domain>[a-zA-Z0-9.]*)/")
SCRAPING_CACHE_FOR = 60 * 15 # cache for 15 minutes
SCRAPING_REQUEST_STAGGER = 1100 # in milliseconds
URI = re.compile(r"^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?")

Base = declarative_base()
class WSDLCheck(Base):
    __tablename__ = 'WSDL'
    id = Column(Integer, primary_key=True)
    wsdlLocation = Column(String)
    authority = Column(String)
    ip = Column(String)
    ipr = Column(String)
    wsdlservicelocation = Column(String)
    #wsdltext = Column(String)
    
    def __init__(self,uri):
        """Initialise the WSDLCheck class to store the items in a dictionary
        """
        self.wsdlLocation= uri
        (self.scheme,self.authority,self.path,self.query,self.fragment)=parse_uri(uri)
        if self.authority!=None:
            (self.ip,self.ipr)=self.dnsLookup(self.authority)
        self.remote = self.loc()
        self.loadWsdl()

    def __repr__(self):
        return '<WSDL(%s)>'%self
        

    def displayData(self):
        print ('WsdlLocation = %s Wsdl File Location = %s\nAuthority = %s IP = %s Reversed IP = %s'%( self.wsdlLocation,self.wsdlfilelocation,self.authority,self.ip,self.ipr))

    def loc(self):
        if self.authority==None:  #and self.data['scheme'] !='http':
            return False
            #debug string
            #print 'Local file %s'%(self.data['wsdlLocation'])        
        elif self.authority !=None:
            return True
            #debug string
            #print 'Remote file %s'%(self.data['wsdlLocation'])
        
    def dnsLookup(self,serv):
        ip='0'
        rserv=['0','0']
        if re_semi.search(serv):
            serv= re_semi.sub('',serv)
        try:
            ip = socket.gethostbyname(serv)
            rserv=socket.gethostbyaddr(ip)
        except:
            pass
        return ip, rserv[0]
            
    def loadWsdl(self):
        if self.remote:
            data=self.fetch(self.wsdlLocation)
            self.storeWsdl(data)
        else:
            wsdlfile=open(self.wsdlLocation,'r')
            root = lxml.etree.parse(wsdlfile)
            data=(lxml.etree.tostring(root, pretty_print=True))
            wsdlfile.close()
        self.wsdltext = data

    def fetch(self,url,robots=False,cache=True):
        scrape=True         #whether to scrape or not
        key=(url,robots)    #create a key based on the url
        now=time.time()     #get the current time
        (scheme, authority, request_uri, defrag_uri)=urlnorm(url)
        if cache:           #check if a cache is used, default true
            cache = FileCache('.cache') #create the folder
        try: 
            if SCRAPING_DOMAINS.has_key(authority):        #if the domain has been scraped
                last_scraped = SCRAPING_DOMAINS[authority] #check the last time it was scraped
                elapsed = now - last_scraped            #calculate the elapsed time
                if elapsed < SCRAPING_REQUEST_STAGGER:  #check if enough time has passed since previous request to the domain
                    wait_period = (SCRAPING_REQUEST_STAGGER - elapsed) / 1000 
                    time.sleep(wait_period)             #create a wait period and pause until it's elapsed
            SCRAPING_DOMAINS[authority] = time.time()      #update the time in the domains dictionary
            if cache:
                cached_value= None
                cachekey=defrag_uri
                cached_value,cache_file=cache.get(cachekey)
                if cached_value:
                    cachedat=(os.path.getctime(cache_file))
                    change = now-cachedat
                    change /= 60 #convert from seconds to minutes
                    print change,SCRAPING_CACHE_FOR, change > SCRAPING_CACHE_FOR
                    if change > SCRAPING_CACHE_FOR:
                        scrape=True
                        cache.delete(cachekey)
                        print 'retrieving new page'
                    else:
                        scrape=False
                        print 'retrieving page from cache'
                else:
                    scrape=True
                    print 'retrieving new page'
            if scrape:
                br=mechanize.Browser()                      #create a mechanize browser object
                br.set_handle_robots(robots)                #set robots.txt handling
                br.addheaders = [('User-agent', USER_AGENT)]#set user agent string
                br.open(url)                                #get the data
                data=br.response().get_data()
                if cache:
                    cache.set(cachekey,data)
            else:
                data = cached_value
                
            return data
        except:
            print "unable to retrieve page"
            return False

    def storeWsdl(self,data,wsdldir='Wsdls/'):
        if not os.path.exists(wsdldir):
            os.makedirs(wsdldir)
        wsdl=self.wsdlLocation.replace('/','-').replace(':','').replace('?','.')
        wsdlfile=wsdldir+wsdl
        root = lxml.etree.fromstring(data)
        f=codecs.open(wsdlfile,encoding='utf-8',mode='a')
        f.write('<?xml version="1.0" encoding="utf-8"?>\n')
        f.write(lxml.etree.tostring(root, pretty_print=True))
        #close the file
        f.close()
        wsdl=[]
        self.wsdlservicelocation ="" 
        for element in root.iter("*"):
            if element.get('location') is not None:
                wsdl.append(element.get('location'))
        wsdlset=set(wsdl)
        for e in wsdlset:
            self.wsdlservicelocation +=e+" "
        self.wsdlfilelocation=os.path.abspath(wsdlfile)
            
def parse_uri(uri):
    """Parses a URI using the regex given in Appendix B of RFC 3986.

        (scheme, authority, path, query, fragment) = parse_uri(uri)
    """
    groups = URI.match(uri).groups()
    return (groups[1], groups[3], groups[4], groups[6], groups[8])

def urlnorm(uri):
    (scheme, authority, path, query, fragment) = parse_uri(uri)
    if not scheme or not authority:
        raise RelativeURIError("Only absolute URIs are allowed. uri = %s" % uri)
    authority = authority.lower()
    scheme = scheme.lower()
    if not path:
        path = "/"
    # Could do syntax based normalization of the URI before
    # computing the digest. See Section 6.2.2 of Std 66.
    request_uri = query and "?".join([path, query]) or path
    scheme = scheme.lower()
    defrag_uri = scheme + "://" + authority + request_uri
    return scheme, authority, request_uri, defrag_uri

# Cache filename construction (original borrowed from Venus http://intertwingly.net/code/venus/)
re_url_scheme    = re.compile(r'^\w+://')
re_slash         = re.compile(r'[?/:|]+')
re_semi          = re.compile(r'[?\:|].*')

def safename(filename):
    """Return a filename suitable for the cache.

    Strips dangerous and common characters to create a filename we
    can use to store the cache in.
    """
    try:
        if re_url_scheme.match(filename):
            if isinstance(filename,str):
                filename = filename.decode('utf-8')
                filename = filename.encode('idna')
            else:
                filename = filename.encode('idna')
    except UnicodeError:
        pass
    if isinstance(filename,unicode):
        filename=filename.encode('utf-8')
    filemd5 = _md5(filename).hexdigest()
    filename = re_url_scheme.sub("", filename)
    filename = re_slash.sub(",", filename)

    # limit length of filename
    if len(filename)>200:
        filename=filename[:200]
    return ",".join((filename, filemd5))


class FileCache(object):
    """Uses a local directory as a store for cached files.
    Not really safe to use if multiple threads or processes are going to
    be running on the same cache.
    """
    def __init__(self, cache, safe=safename): # use safe=lambda x: md5.new(x).hexdigest() for the old behavior
        self.cache = cache
        self.safe = safe
        if not os.path.exists(cache):
            os.makedirs(self.cache)

    def get(self, key):
        retval = None
        cacheFullPath = os.path.join(self.cache, self.safe(key))
        #print cacheFullPath
        try:
            f = file(cacheFullPath, "rb")
            retval = f.read()
            f.close()
        except IOError:
            pass
            
        return retval,cacheFullPath

    def set(self, key, value):
        cacheFullPath = os.path.join(self.cache, self.safe(key))
        f = file(cacheFullPath, "wb")
        f.write(value)
        f.close()

    def delete(self, key):
        cacheFullPath = os.path.join(self.cache, self.safe(key))
        if os.path.exists(cacheFullPath):
            os.remove(cacheFullPath)
    
            
            
        
