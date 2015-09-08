# Wsdl-Scraper


## Requires 
Mechanize
lxml
sqlalchemy

## Runnning

1. Run google_wsld_links.py to gather a list of candidate wsdl links stored in a file called WsdlDatatLinks.txt
2. Run wsdl_retrievier.py to open the file created by the previous script and fetch all the wsdls, store the results in a database file called wsdl.db and cache the rusults in the .cache directory
 
