from lxml import etree
import os, os.path, time, codecs, csv, json, unicodedata
from collections import defaultdict

DATA = "data.csv"
FOLDER = "pages/"
FILE = FOLDER + "{0}.html"
DATA_XPATH = {
    "labels":"//td[@class='label']",
    #"taxonomyths":"//table[@class='tab_data'][1]/tr/th", #Already in csv file
    #"taxonomytds":"//table[@class='tab_data'][1]/tr/td", #Already in csv file
    #"red list category & criteria":"//strong[.='Red List Category & Criteria:']/../../td[2]", #Already in csv file
    "systems":"//strong[.='Systems:']/../../td[2]",
    "scientific name":"//strong[.='Scientific Name:']/../../td[2]",
    "countries":"//strong[.='Countries:']/../../td[2]",
    #"common name/s":"//strong[.='Common Name/s:']/../table/tr", #Already in csv file
    #"population trend":"//strong[.='Population Trend:']/../../td[2]/span", #Already in csv file
    "justification":"//strong[.='Justification:']/..", #Need to remote "Justification:" from text
    "population":"//strong[.='Population:']/../../td[2]",
    "taxonomic notes":"//strong[.='Taxonomic Notes:']/../../td[2]",
    "conservation actions":"//strong[.='Conservation Actions:']/../../td[2]",
    "major threat(s)":"//strong[.='Major Threat(s):']/../../td[2]",
    "habitat and ecology":"//strong[.='Habitat and Ecology:']/../../td[2]",
    #"synonym/s":"//strong[.='Synonym/s:']/../../td[2]" #Already in csv file
}

#Checks if a value is an integer
def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
#Returns the text inside a DOM element using etree.tostring
def text(item, lower=True):
    ret = etree.tostring(item, method="text", encoding=unicode).strip()
    if lower:
        ret = ret.lower()
    return ret
#Helps keep track of execution time
#If you don't pass in a value, it rturns the time
#Else it returns the execution time between now and the parameter
def timer(start=None):
  t = time.time()
  if start != None:
    return t - start
  return t
headers = []
rows = []
#Import the data from the DATA (csv) file
#Must decode when necessary
def import_data():
    #Import the data from the exported file
    global headers, rows
    f = open(DATA)
    reader = csv.reader(f)
    for row in reader:
        t = []
        for r in row:
            try:
                t.append(r.decode("UTF-8"))
            except:
                t.append(r)
        rows.append(t)
    f.close()
    headers = rows.pop(0)
#Find out how many pages have what data
def counts():
    species = [int(name.replace(".html", "")) for name in os.listdir(FOLDER) if is_int(name.replace(".html", ""))]
    total = len(species)
    
    label_dict = defaultdict(float)
    
    for index,specie in enumerate(species):
        if index % 1000 == 0:
            print "On species {0}".format(index)
        page = etree.HTML(open(FILE.format(specie)).read())
        
        labels = page.xpath(DATA_XPATH["labels"])
        for label in labels:
            l = text(label).replace(":", "")
            if l == "":
                continue
            label_dict[l] += 1.0
        
    sorted_labels = sorted(label_dict, key=label_dict.get, reverse=True)
    
    f = open("label_counts.txt", "w")
    for sorted_l in sorted_labels:
        out = "{0}: {1} ({2}%)\n".format(sorted_l.encode("UTF-8"), int(label_dict[sorted_l]), round((label_dict[sorted_l] / total) * 100.0, 2))
        f.write(out)
        #f.write("{0}:{1}\n".format(sorted_l, int(label_dict[sorted_l])))
    f.close()

#Parse the pages to see what distinct data each label has
def data_parse():
    times = defaultdict(float)
    times["file"] = timer()
    species = [int(name.replace(".html", "")) for name in os.listdir(FOLDER) if is_int(name.replace(".html", ""))]
    total = len(species)
    times["file"] = timer(times["file"])
    
    data = defaultdict(list)
    ignored_data = set()
    
    times["loop"] = timer()
    for index, specie in enumerate(species):
        if index % 1000 == 0:
            print "On species {0}".format(index)
        
        page = etree.HTML(open(FILE.format(specie)).read())
        
        #Now find all the other data which is in wrapped in strong elements
        strongs = page.xpath(DATA_XPATH["labels"])
        for strong in strongs:
            item = text(strong).replace(":", "")
            #If it's not there, then we most likely don't care about this data
            if item not in DATA_XPATH:
                ignored_data.add(item)
                continue
            el = page.xpath(DATA_XPATH[item])
            if len(el) == 0:
                continue
            data[item].append(text(el[0]))
    times["loop"] = timer(times["loop"])
    
    #Now get the counts outputted from counts()
    f = open("label_counts.txt")
    contents = f.read().split("\n")
    f.close()
    label_counts = dict([(key.split(":")[0],key.split(":")[1]) for key in contents])
    
    #Write the data to files
    times["write"] = timer()
    print "Writing data to /label_data"
    out = []
    for item in data:
        if item not in label_counts:
            s = ">{0} not in label_counts!".format(item)
            print s
            out.append(s)
        if len(data[item]) != int(label_counts[item]):
            s = ">>{0} ({1} != {2})".format(item, len(data[item]), label_counts[item])
            print s
            out.append(s)
        
        f = codecs.open("label_data/{0}.txt".format(item.replace("/", "")), "w", "utf-8")
        for item in data[item]:
            try:
                f.write(item+ "\n\n")
            except Exception as e:
                print "Exception: {0}".format(e)
                print item[63].encode("ascii", errors="ignore")
                exit()
        f.close()
    times["write"] = timer(times["write"])
    
    s = "Ignored {0} labels".format(len(ignored_data))
    print s
    out.append(s)
    
    for item in ignored_data:
        s = ">>>Ignored: " + item
        print s
        out.append(s)
    
    f = open("data_parse_out.txt", "w")
    f.write("\n".join(out))
    f.close()
    print "Output written to data_parse_out.txt"
    
    for t in times:
        print "{0} time: {1}s, {2}m".format(t, round(times[t], 4), round(times[t]/60.0, 4))

def data_work_scientific_name(specie, page):
    el = page.xpath(DATA_XPATH["scientific name"])
    if len(el) != 1:
        print "(scientific name) id: {0}, len: {1}".format(specie, len(el))
        exit()
    return text(el[0], False)
def data_work_countries(specie, page):
    el = page.xpath(DATA_XPATH["countries"])
    if len(el) != 1:
        print "(countries) id: {0}, len: {1}".format(specie, len(el))
        exit()
    return text(el[0], False)#.encode("ascii")
    
def data_work_major_threats(specie, page):
    el = page.xpath(DATA_XPATH["major threat(s)"])
    if len(el) != 1:
        print "(countries) id: {0}, len: {1}".format(specie, len(el))
        exit()
    print text(el[0], False)#.encode("ascii")
    exit()

def data_work_systems(specie, page):
    el = page.xpath(DATA_XPATH["systems"])
    if len(el) != 1:
        print "(countries) id: {0}, len: {1}".format(specie, len(el))
        exit()
    return text(el[0], False).encode("ascii")

def add__to_csv():
    import_data()
    global headers, rows
    #Add what I'm currently working on to the headers
    header_name = "Systems"
    if header_name in headers:
        print header_name + " already in headers!"
        exit()
    headers.append(header_name)
    #Add the data to each row
    for index,row in enumerate(rows):
        if index % 1000 == 0:
            print "Species " + str(index)
        id = int(row[0])
        page = etree.HTML(open(FILE.format(id)).read())
        
        strongs = page.xpath(DATA_XPATH["labels"])
        found = False
        for strong in strongs:
            item = text(strong).replace(":", "")
            if item == header_name.lower():
                found = True
                #row.append(data_work_scientific_name(id, page))
                
                #data = data_work_countries(id, page)
                #types = data.split("\n\n")
                #statusdict = {}
                #for type in types:
                #    spl = type.split(":")
                #    status = spl[0]
                #    statusdict[status] = [unicodedata.normalize('NFD', c.strip()).encode('ascii', 'ignore') for c in spl[1].split(";")]
                #row.append(json.dumps(statusdict))
                
                data = data_work_systems(id, page)
                if data == "":
                    found = False
                    break
                data = data.split(";")
                data = map(str.strip, data)
                row.append(json.dumps(data))
                
                break
            #Endif
        if not found:
            row.append(json.dumps([]))
    
    print "Writing to file"
    f = open(DATA.replace(".csv","")+"_out.csv", 'wb')
    csvw = csv.writer(f, delimiter=',')
    csvw.writerow(headers)
    for row in rows:
        t = []
        for r in row:   
            if isinstance(r, str):
                t.append(r)
            else:
                t.append(r.encode("UTF-8"))
        csvw.writerow(t)
    f.close()
    print "The output has been written to " + DATA.replace(".csv","")+"_out.csv"
    
def analyze_countries():
    print "Importing"
    import_data()
    global headers, rows
    
    countries_index = [index for index,h in enumerate(headers) if h.lower()=="countries"][0]
    
    result_dictionary = defaultdict(lambda: defaultdict(int))
    na_countries = []
    dist_status = set()
    
    print "Aggregating"
    for row in rows:
        if row[countries_index] == "N/A":
            na_countries.append(row[countries_index-1])
            continue
        statuses = json.loads(row[countries_index])
        for status in statuses:
            dist_status.add(status)
            for country in statuses[status]:
                #Remove states / locations in the country and if the last name is first, put it at the end
                country = country.split(" (")[0]
                if "," in country:
                    country = country.split(", ")
                    country = country[1] + " " + country[0]
                
                result_dictionary[country][status] += 1.0
    
    #f = open("country_stats.txt", "w")
    #f.write(json.dumps(result_dictionary))
    #f.close()
    print len(rows)
    print len(result_dictionary)
    print len(na_countries)
    
    for status in dist_status:
        res = [(result_dictionary[r][status],r) for r in result_dictionary if status in result_dictionary[r]]
        res_s = sorted(res, reverse=True)[:5]
        print status + ": " + str(res_s)
def analyze_red_list():
    print "Importing"
    import_data()
    global headers, rows
    
    red_list_index = [index for index,h in enumerate(headers) if h.lower()=="red list status"][0]
    countries_index = [index for index,h in enumerate(headers) if h.lower()=="countries"][0]
    
    result_dictionary = defaultdict(lambda: defaultdict(int))
    dist_status = set()
    
    print "Aggregating"
    for row in rows:
        if row[countries_index] == "N/A":
            continue
        statuses = json.loads(row[countries_index])
        red_stat = row[red_list_index]
        dist_status.add(red_stat)
        for status in statuses:
            for country in statuses[status]:
                #Remove states / locations in the country and if the last name is first, put it at the end
                country = country.split(" (")[0]
                if "," in country:
                    country = country.split(", ")
                    country = country[1] + " " + country[0]
                
                result_dictionary[country][red_stat] += 1.0
        #print statuses
        #print result_dictionary
        #exit()
    
    #status = "CR"
    #print sum([result_dictionary[r][status] for r in result_dictionary if status in result_dictionary[r]])
    #exit()
    
    print len(rows)
    print len(result_dictionary)
    
    #f = open("red_list_stats_by_country.txt", "w")
    #f.write(json.dumps(result_dictionary))
    #f.close()
    
    for status in dist_status:
        res = [(result_dictionary[r][status],r) for r in result_dictionary if status in result_dictionary[r]]
        res_s = sorted(res, reverse=True)[:5]
        print status + ": " + str(res_s)
def analyze_major_threats():
    print "Importing"
    import_data()
    global headers, rows
    
    red_list_index = [index for index,h in enumerate(headers) if h.lower()=="major threat(s)"][0]
    countries_index = [index for index,h in enumerate(headers) if h.lower()=="countries"][0]
    
    result_dictionary = defaultdict(lambda: defaultdict(int))
    dist_status = set()
    
    print "Aggregating"
    for row in rows:
        if row[countries_index] == "N/A":
            continue
        statuses = json.loads(row[countries_index])
        red_stat = row[red_list_index]
        dist_status.add(red_stat)
        for status in statuses:
            for country in statuses[status]:
                #Remove states / locations in the country and if the last name is first, put it at the end
                country = country.split(" (")[0]
                if "," in country:
                    country = country.split(", ")
                    country = country[1] + " " + country[0]
                
                result_dictionary[country][red_stat] += 1.0
        #print statuses
        #print result_dictionary
        #exit()
    
    #status = "CR"
    #print sum([result_dictionary[r][status] for r in result_dictionary if status in result_dictionary[r]])
    #exit()
    
    print len(rows)
    print len(result_dictionary)
    
    #f = open("red_list_stats_by_country.txt", "w")
    #f.write(json.dumps(result_dictionary))
    #f.close()
    
    for status in dist_status:
        res = [(result_dictionary[r][status],r) for r in result_dictionary if status in result_dictionary[r]]
        res_s = sorted(res, reverse=True)[:5]
        print status + ": " + str(res_s)
         
    
def main():
    #counts()
    #data_parse()
    #data_distinct()
    add__to_csv()
    #analyze_countries()
    #analyze_red_list()
    #analyze_major_threats()

if __name__ == '__main__':
    main()