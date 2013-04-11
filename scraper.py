import csv, os, os.path, random
from lxml import etree
import urllib2
from time import sleep

DATA = "export-39385.csv"
FOLDER = "pages/"
FILE = FOLDER + "{0}.html"
URL = "http://www.iucnredlist.org/details/full/{0}/0"
DELAY = 1.0

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
def save_file(loc, content):
    f = open(loc, "w")
    f.write(content)
    f.close()

headers = []
rows = []
def import_data():
    #Import the data from the exported file
    global headers, rows
    f = open(DATA)
    reader = csv.reader(f)
    rows = [row for row in reader]
    f.close()
    
    headers = rows.pop(0)
def text(item, lower=True):
    ret = etree.tostring(item, method="text", encoding=unicode).strip()
    if lower:
        ret = ret.lower()
    return ret

def main():
    #print "Importing"
    import_data()
    
    print "Thinking"
    #Figure out what's left to do
    completed = [int(name.replace(".html", "")) for name in os.listdir(FOLDER) if is_int(name.replace(".html", ""))]
    all = [int(row[0]) for row in rows]
    remaining = list(set(all) - set(completed))
    len_remaining = len(remaining)
    
    #all = []
    #f = open("remaining.txt")
    #remaining = f.read().split("\n")
    #f.close()
    #len_remaining = len(remaining)
    
    print "Out of {0} species, there are {1} remaining.".format(len(all), len(remaining))
    
    #Go through the remaining to download the species' information
    for index, item in enumerate(remaining):
        if os.path.exists(FILE.format(item)):
            print "species {0} already exists.".format(item)
            continue
        print "Downloading species ({0}) {1} of {2}, {3} left.".format(item, index+1, len_remaining, len_remaining - (index+1))
        page = etree.HTML(urllib2.urlopen(URL.format(item)).read())
        el = page.xpath("//div[@id='data_factsheet']")
        #Make sure the element we want is there
        if len(el) != 1:
            print "For species {0}, len(el) == {1}".format(item, len(el))
            exit()
        
        #Print out the scientific name so I know it's changing
        sci = el[0].xpath("//strong[.='Scientific Name:']/../../td[2]")
        if len(sci) != 1:
            print "For species {0}, len(sci) == {1}".format(item, len(el))
            exit()
        print "Scientific name (" + str(item) + "): " + text(sci[0], False).encode("ascii", errors="ignore")
        #exit()
        #Save the information to the file
        content = etree.tostring(el[0])
        
        save_file(FILE.format(item), content)
        
        rand_del = round(random.random()*DELAY, 2)
        sleep(rand_del)
    
    
if __name__ == '__main__':
    main()