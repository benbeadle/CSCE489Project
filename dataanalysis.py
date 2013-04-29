from lxml import etree
import os, os.path, time, codecs, csv, json, unicodedata, re, urllib2, csv
from collections import defaultdict, Counter

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

#Find word frequencies in the common names
def word_counter():
    import_data()
    
    common_index = [index for index,h in enumerate(headers) if h.lower()=="common names (eng)"][0]
    
    result_dict = defaultdict(int)
    
    print "Aggregating"
    for row in rows:
        if row[common_index].strip() != "":
            name = str(row[common_index]).strip().lower()
            name_spl = set(re.split(" |,|-", name))
            for n_s in name_spl:
                if n_s.strip() != "":
                    result_dict[n_s.strip()] += 1
    
    
    c = Counter(result_dict)
    f = open("common_word_count.txt", "w")
    f.write("\n".join([t[0]+": "+str(t[1]) for t in c.most_common()]))
    f.close()
    print "Done working on {0} rows!".format(len(rows))

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
    return text(el[0], False)#.encode("UTF-8")
    
def data_work_major_threats(specie, page):
    el = page.xpath(DATA_XPATH["major threat(s)"])
    if len(el) != 1:
        print "(majorthreats) id: {0}, len: {1}".format(specie, len(el))
        exit()
    return text(el[0], False)

def data_work_population(specie, page):
    el = page.xpath(DATA_XPATH["population"])
    if len(el) != 1:
        print "(population) id: {0}, len: {1}".format(specie, len(el))
        exit()
    return text(el[0], False)

def data_work_systems(specie, page):
    el = page.xpath(DATA_XPATH["systems"])
    if len(el) != 1:
        print "(systems) id: {0}, len: {1}".format(specie, len(el))
        exit()
    return text(el[0], False).encode("UTF-8")
    
def data_work_habitat_ecology(specie, page):
    el = page.xpath(DATA_XPATH["habitat and ecology"])
    if len(el) != 1:
        return ""
    return text(el[0], False).encode("UTF-8")

def add_to_csv():
    import_data()
    global headers, rows
    #Add what I'm currently working on to the headers
    header_name = "Habitat and Ecology"
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
                
                # data = data_work_systems(id, page)
                # if data == "":
                    # found = False
                    # break
                # data = data.split(";")
                # data = map(str.strip, data)
                # row.append(json.dumps(data))
                
                #data = data_work_major_threats(id, page).encode("utf-8")
                
                #data = data_work_population(id, page).encode("utf-8")
                
                data = unicodedata.normalize('NFD', unicode(data_work_habitat_ecology(id, page),errors="ignore")).encode('ascii', 'ignore')
                
                
                row.append(data.replace("\n", "  "))
                
                break
            #Endif
        if not found:
            row.append(json.dumps(""))
    
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

#Change some of the columns initially provided in the export
def fix_data():
    import_data()
    global headers, rows
    #Add what I'm currently working on to the headers
    syns_index = [index for index,h in enumerate(headers) if h.lower()=="synonyms"][0]
    #Add the data to each row
    for index,row in enumerate(rows):
        if index % 1000 == 0:
            print "Species " + str(index)
        id = int(row[0])
        
        syns = ""
        
        try:
            syns = row[syns_index].encode("UTF-8")
        except:
            syns = row[syns_index]
        
        if syns.strip() == "":
            row[syns_index] = json.dumps([])
            continue
        
        syns = map(str.strip, syns.split("|"))
        row[syns_index] = json.dumps(syns)
    
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
     
 
 
 
def data_get_contents():
    f = open("data.csv")
    reader = csv.reader(f)
    rows = []
    for row in reader:
        t = []
        for r in row:
            try:
                t.append(r.decode("UTF-8"))
            except:
                t.append(r)
        rows.append(t)
    f.close()
    return rows
def iso_get_contents():
    f = open("ISOtoCountry.xls")
    reader = csv.reader(f)
    rows = [row for row in reader if row is not None]
    f.close()
    return rows
def create_animal_list():
    print "create_animal_list"
    #Import the data
    rows = data_get_contents()
    headers = rows.pop(0)
    #Stands for header index
    def hi(s):
        res = [index for index,h in enumerate(headers) if h.lower()==s.lower()]
        if len(res) == 0:
            return -2
        return res[0]
    
    #Loop through the rows and get the data
    country_index = hi("countries")
    
    kingdom_index = hi("kingdom")
    phylum_index = hi("phylum")
    class_index = hi("class")
    order_index = hi("order")
    family_index = hi("family")
    genus_index = hi("genus")
    species_index = hi("species")
    
    synonyms_index = hi("synonyms")
    common_name_index = hi("Common names (Eng)")
    scientific_name_index = hi("Scientific Name")
    
    country_list = set()
    
    names = {
        "kingdom": set(),
        "phylum": set(),
        "class": set(),
        "order": set(),
        "family": set(),
        "genus": set(),
        "species": set(),
        "synonym": set(),
        "common": set(),
        "Animal": set(),
        "scientific": set()
    }
    
    for row in rows:
        #Work on country data
        if row[country_index] == "N/A":
            continue
        countries = json.loads(row[country_index])
        for status in countries:
            #Some countries have their specific states. We don't care about that here
            country_list.update(set([country.split(" (")[0] for country in countries[status]]))
        
        names["kingdom"].add(row[kingdom_index].lower())
        names["phylum"].add(row[phylum_index].lower())
        names["class"].add(row[class_index].lower())
        names["order"].add(row[order_index].lower())
        names["family"].add(row[family_index].lower())
        names["genus"].add(row[genus_index].lower())
        names["species"].add(row[species_index].lower())
        names["scientific"].add(row[scientific_name_index].lower())
        if row[synonyms_index].strip() != "":
            names["synonym"].update([res.strip() for res in row[synonyms_index].split("|") if res is not None and res.strip() != ""])
        names["common"].update(set(re.split(",|-",row[common_name_index].lower())))
        
    country_list = list(country_list)
    
    iso_rows = iso_get_contents()
    
    code_dict = defaultdict(str)
    for row in iso_rows:
        #For countries that have commas, the row is split into more than just [country, code]
        if len(row) == 2:
            code_dict[row[0].lower()] = row[1]
        else:
            code = row.pop()
            code_dict[",".join(row).lower()] = code
    
    def rang(input):
        letter = input[0].lower()
        if letter in ["a", "b", "c", "d"]:
            return "a-d"
        elif letter in ["e", "f", "g", "h"]:
            return "e-h"
        elif letter in ["i", "j", "k", "l"]:
            return "i-l"
        elif letter in ["m", "n", "o", "p"]:
            return "m-p"
        elif letter in ["q", "r", "s", "t"]:
            return "q-t"
        elif letter in ["u", "v", "w", "x", "y", "z"]:
            return "u-z"
    
    animal_list = {}
    for type in names:
        for name in names[type]:
            if name == "":
                continue
            if isinstance(name, str):
                name = unicodedata.normalize('NFKD', unicode(name,errors="ignore"))#.decode('ascii', 'ignore')
            else:
                name = unicodedata.normalize('NFKD', name).encode('ascii', errors='ignore')
            if name == "":
                continue
            r = rang(name)
            if r not in animal_list:
                animal_list[r] = {}
            if type not in animal_list[r]:
                animal_list[r][type] = []
            if name not in animal_list[r][type]:
                animal_list[r][type].append(name)
    
    print "Writing to animal_list.json"
    f = open("animal_list.json", "w")
    f.write(json.dumps(animal_list))
    f.close()
    print "Complete."

def e(s):
    if isinstance(s, str):
        return unicodedata.normalize('NFKD', unicode(s,errors="ignore"))#.decode('ascii', 'ignore')
    else:
        return unicodedata.normalize('NFKD', s).encode('ascii', errors='ignore')
def create_data_json():
    print "create_data_json"
    #"""
    #Import the data
    rows = data_get_contents()
    headers = rows.pop(0)
    the_species = []
    #Stands for header index
    def hi(s):
        res = [index for index,h in enumerate(headers) if h.lower()==s.lower()]
        if len(res) == 0:
            return -2
        return res[0]
    
    #Loop through the rows and get the data
    country_index = hi("countries")
    
    kingdom_index = hi("kingdom")
    phylum_index = hi("phylum")
    class_index = hi("class")
    order_index = hi("order")
    family_index = hi("family")
    genus_index = hi("genus")
    species_index = hi("species")
    
    synonyms_index = hi("synonyms")
    common_name_index = hi("Common names (Eng)")
    scientific_name_index = hi("Scientific Name")
    
    for row in rows:
        species = {}
        #Work on country data
        if row[country_index] == "N/A":
            continue
        species["id"] = row[0]
        countries = json.loads(row[country_index])
        species["countries"] = []
        for status in countries:
            #Some countries have their specific states. We don't care about that here
            for c in [country.split(" (")[0] for country in countries[status]]:
                species["countries"].append((status, c,))
        
        species["names"] = [("kingdom",row[kingdom_index].lower(),)]
        species["names"].append(("phylum",row[phylum_index].lower(),))
        species["names"].append(("class",row[class_index].lower(),))
        species["names"].append(("order",row[order_index].lower(),))
        species["names"].append(("family",row[family_index].lower(),))
        species["names"].append(("genus",row[genus_index].lower(),))
        species["names"].append(("species",e(row[species_index]).lower(),))
        species["names"].append(("scientific",row[scientific_name_index].lower(),))
        if row[synonyms_index].strip() != "":
            species["names"] += [("synonym",res.strip(),) for res in e(row[synonyms_index]).split("|") if res is not None and res.strip() != ""]
        for n in set(re.split(",|-",e(row[common_name_index]).lower())):
            species["names"].append(("common",n,))
        
        species["names"] = [n for n in species["names"] if n[1] != ""]
        species["scientific_name"] = e(row[scientific_name_index].lower())
        
        species["major_threats"] = row[hi("Major Threat(s)")] if row[hi("Major Threat(s)")] != "" and row[hi("Major Threat(s)")] != "[]" else ""
        species["population"] = row[hi("Population")] if row[hi("Population")] != "" and row[hi("Population")] != "[]" else ""
        species["red_list"] = row[hi("Red List status")] if row[hi("Red List status")] != "" and row[hi("Red List status")] != "[]" else ""
        species["systems"] = row[hi("Systems")] if row[hi("Systems")] != "" and row[hi("Systems")] != "[]" else []
        species["habitat_ecology"] = row[hi("Habitat and Ecology")] if row[hi("Habitat and Ecology")] != "" and row[hi("Habitat and Ecology")] != "[]" else ""
        the_species.append(species)
    #"""
    """
    print "writing"
    filespecies = open('species.csv', 'wb')
    filecountries = open('countries.csv', 'wb')
    filenames = open('names.csv', 'wb')
    csvspecies = csv.writer(filespecies, delimiter=',')
    csvscountries = csv.writer(filecountries, delimiter=',')
    csvsnames = csv.writer(filenames, delimiter=',')
    
    csvspecies.writerow(["id", "scientfic_name", "red_list", "major_threats"])
    csvscountries.writerow(["id", "country"])
    csvsnames.writerow(["id", "type", "name"])
    print len(the_species)
    for row in the_species:
        csvspecies.writerow([row["id"], row["scientific_name"].lower(),row["red_list"], e(row["major_threats"])])
        for country in row["countries"]:
            csvscountries.writerow([row["id"], country[0], e(country[1])])
        for name in row["names"]:
                csvsnames.writerow([row["id"], name[0], e(name[1])])
    filespecies.close()
    filecountries.close()
    filenames.close()
    """
    print "converting"
    def weight(rls):
        if rls == "LC" or rls == "LR/cd" or rls == "LR/lc":
            return 1
        elif rls == "NT" or rls == "LR/nt":
            return 2
        elif rls == "VU":
            return 3
        elif rls == "EN":
            return 4
        elif rls == "CR":
            return 5
        elif rls == "EW":
            return 6
        elif rls == "EX":
            return 7
        return 0
    sqlstats = open('stats.sql', 'wb')
    sqlstats.write('USE its;\n')
    sqlstats.write('CREATE TABLE Stat (\nid CHAR(10),\nscientific_name CHAR(25),\nctype CHAR(25),\ncname CHAR(25),\nntype CHAR(25),\nnname CHAR(25), red_list CHAR(5),\nred_val TINYINT);\n')
    count = 0
    for row in the_species:
        for country in row["countries"]:
            #csvscountries.writerow([row["id"], country[0], e(country[1])])
            for name in row["names"]:
                sqlstats.write('INSERT INTO Stat (id, scientific_name, ctype, cname, ntype, nname, red_list, red_val) VALUES ("{0}","{1}","{2}","{3}","{4}","{5}", "{6}", {7});\n'.format(row["id"], e(row["scientific_name"]), e(country[0]), e(country[1]), e(name[0]), e(name[1]), row["red_list"], weight(row["red_list"])))
                count += 1
        #print count
    sqlstats.close()
    exit()
    return
    #file_name = "species"
    #create_sql = 'CREATE TABLE Specie (\nid CHAR(10),\nscientific_name CHAR(10),\nred_list CHAR(5),\nmajor_threats TEXT);\n'
    #insert_sql = 'id, scientific_name, red_list, major_threats'
    #file_name = "countries"
    #create_sql = 'CREATE TABLE Country (\nid CHAR(10),\nctype CHAR(25),\nname CHAR(25));\n'
    #insert_sql = 'id, ctype, name'
    file_name = "names"
    create_sql = 'CREATE TABLE Name (\nid CHAR(10),\nntype CHAR(25),\nname CHAR(25));\n'
    insert_sql = 'id, ntype, name'
    
    sqlfile = open(file_name + ".sql", "w")
    speciesf = open(file_name + ".csv")
    csvreader = csv.reader(speciesf)
    #speciessql.write('CREATE DATABASE its;\n')
    sqlfile.write('USE its;\n')
    for index,row in enumerate(csvreader):
        if index == 0:
            sqlfile.write(create_sql)
            continue
        sqlfile.write('INSERT INTO Name (' + insert_sql + ') VALUES ("' + '","'.join([r.replace('"','\\"') for r in row]) + '");\n')
    sqlfile.close()
    #    exit()
    print "Done"
    return
    #"""
    f = open("species.json", "w")
    f.write(json.dumps(the_species))
    f.close()
    return
    s = []
    index = 0
    while len(the_species) > 0:
        s.append(the_species.pop())
        if len(s) >= 5000:
            f = open("species_" + str(index) + ".json", "w")
            f.write(json.dumps(s))
            f.close()
            s = []
            index += 1
    f = open("species_" + str(index) + ".json", "w")
    f.write(json.dumps(s))
    f.close()
    print "wrote to " + str(index+1) + " files."
    
def save_to_datastore():
    r = range(0, 10)
    for index in r:
        #print len(json.loads(open("interactivethreatenedspecies/species_" + str(index) + ".json").read()))
        #continue
        print "Index: " + str(index)
        req = urllib2.Request("http://localhost:12084/queue/cacher?index={0}".format(index))
        try:
            urllib2.urlopen(req).read()
        except URLError as e:
            print e.reason
            exit()
        
        
def search_data_api():
    
    name_lower = "lizard".lower()
    
    rows = data_get_contents()
    headers = rows.pop(0)
    #Stands for header index
    def hi(s):
        res = [index for index,h in enumerate(headers) if h.lower()==s.lower()]
        if len(res) == 0:
            return -2
        return res[0]
    
    def weight(rls):
        if rls == "LC" or rls == "LR/cd" or rls == "LR/lc":
            return 1
        elif rls == "NT" or rls == "LR/nt":
            return 2
        elif rls == "VU":
            return 3
        elif rls == "EN":
            return 4
        elif rls == "CR":
            return 5
        elif rls == "EW":
            return 6
        elif rls == "EX":
            return 7
        return 0
    counts = Counter()
    hic = hi("countries")
    hir = hi("Red List Status")
    while len(rows) > 0:
        row = rows.pop(0)
        
        countries = json.loads(row[hic])
        rls = row[hir]
        rls_weight = weight(rls)
        #If it's 0, then it's not one of the valid statuses (AKA DD - data deficient)
        if rls_weight == 0:
            continue
        for type in countries:
            for country in countries[type]:
                counts[country] += rls_weight
    print counts.most_common(10)
    
def main():
    #counts()
    #data_parse()
    #data_distinct()
    #add_to_csv()
    #analyze_countries()
    #analyze_red_list()
    #analyze_major_threats()
    #fix_data()
    #word_counter()
    #create_animal_list()
    #search_data_api()
    create_data_json()
    #save_to_datastore()
    exit()
    f = open("interactivethreatenedspecies/species_0.json")
    contents = json.loads(f.read())
    for i,c in enumerate(contents):
        if i >= 80:
            print str(i) + ": " + str(c["systems"])
        if i == 90:
            exit()

if __name__ == '__main__':
    main()