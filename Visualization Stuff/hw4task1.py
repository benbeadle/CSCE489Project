import csv
import sys
from itertools import chain, combinations

# With help from http://webdocs.cs.ualberta.ca/~zaiane/courses/cmput499/slides/Lect10/sld052.htm and https://github.com/asaini/Apriori/blob/master/apriori.py

'''
 Attribute Information:
   1. Class Name: 2 (democrat, republican)
   2. handicapped-infants: 2 (y,n)
   3. water-project-cost-sharing: 2 (y,n)
   4. adoption-of-the-budget-resolution: 2 (y,n)
   5. physician-fee-freeze: 2 (y,n)
   6. el-salvador-aid: 2 (y,n)
   7. religious-groups-in-schools: 2 (y,n)
   8. anti-satellite-test-ban: 2 (y,n)
   9. aid-to-nicaraguan-contras: 2 (y,n)
  10. mx-missile: 2 (y,n)
  11. immigration: 2 (y,n)
  12. synfuels-corporation-cutback: 2 (y,n)
  13. education-spending: 2 (y,n)
  14. superfund-right-to-sue: 2 (y,n)
  15. crime: 2 (y,n)
  16. duty-free-exports: 2 (y,n)
  17. export-administration-act-south-africa: 2 (y,n) 
'''

# List used to transform data so it isn't just yes or no anymore.
oneAFileTransforms = ['dem', 'rep', 'class?', 'hiy', 'hin', 'hi?', 'wpcsy', 'wpcsn', 'wpcs?', 'abry', 'abrn', 'abr?', 'pffy', 'pffn', 'pff?', 'esay', 'esan', 'esa?', 'rgsy', 'rgsn', 'rgs?', 'astby', 'astbn', 'astb?', 'ancy', 'ancn', 'anc?', 'mmy', 'mmn', 'mm?', 'iy', 'in', 'i?', 'sccy', 'sccn', 'scc?', 'esy', 'esn', 'es?', 'srsy', 'srsn', 'srs?', 'cy', 'cn', 'c?', 'dfey', 'dfen', 'dfe?', 'eadsy', 'eadsn', 'eads?']

currentTransactionData = []
totalCountDic = {}

# Read in file and make new better one
def transformOneAData():
		
	fileName = open('untransformed1aData.txt', 'r')
	f = open('1aData.txt', 'w')
	reader = csv.reader(fileName)
	for row in reader:
		i = 0
		newRow = ""
		for attribute in row:
			if (attribute == "democrat"):
				newRow = newRow + oneAFileTransforms[i] + ", "
			elif (attribute == "republican"):
				newRow = newRow + oneAFileTransforms[i + 1] + ", "
			elif (attribute == "y"):
				newRow = newRow + oneAFileTransforms[i] + ", "
			elif (attribute == "n"):
				newRow = newRow + oneAFileTransforms[i + 1] + ", "
			else: 
				newRow = newRow + oneAFileTransforms[i + 2] + ", "
			i += 3
		newRow = newRow[:-2]
		f.write(newRow)
		f.write('\n')
		
def transformOneBData():
	fileName = open('untransformed1bData.txt', 'r')
	f = open('1bData.txt', 'w')
	reader = csv.reader(fileName)
	for row in reader:
		i = 0
		newRow = ""
		for attribute in row:
			if i == 2 or i == 4 or i == 12 or i == 10 or i == 11:
				newRow = newRow
			else:
				newRow = newRow + attribute + ", "
			i += 1
		newRow = newRow[:-2]
		f.write(newRow)
		f.write('\n')

# Read in given file		
def readInfile(filename):
	currentItemSet = set()
	fileName = open(filename, 'r')
	reader = csv.reader(fileName)
	for row in reader:
		rowData = []
		for attribute in row:
			data = attribute.replace(" ", "")
			rowData.append(data)
			#f.write(data)
			#f.write('\n')
			currentItemSet.add(frozenset([data]))
		currentTransactionData.append(frozenset(rowData))
	return currentItemSet
	
# Counts frequency of a given list
def count(countSet):
	global totalCountDic
	countDic = {}
	for element in countSet:
		for cart in currentTransactionData:
			if(element.issubset(cart)):
				if element not in countDic:
					countDic[element] = 1
					totalCountDic[element] = 1
				else:
					countDic[element] += 1
					totalCountDic[element] += 1
	return countDic
		
# Reduce by support
def supportReduction(minSupport, countDic):
	setOfFrequentElements = set()
	for element in countDic:
		support = float(countDic[element])/len(currentTransactionData)
		if  support >= minSupport:
			setOfFrequentElements.add(element)
	return setOfFrequentElements

# Does the unioning of sets that met support value
def joinSet(itemSet,length):
	"""Join a set with itself and returns the n-element itemsets"""
	listnew = []
	for i in itemSet:
		for j in itemSet:
			if len(i.union(j)) == length:
				listnew.append(i.union(j))
	return set(listnew)

# Source: http://stackoverflow.com/questions/7988695/getting-the-subsets-of-a-set-in-python
def powerset(iterable):
	"powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
	s = list(iterable)
	powerSet = chain.from_iterable(combinations(s, r) for r in range(len(s)+1))
	listOfSets = map(set, powerSet)
	listOfSets.remove(set([]))
	return listOfSets
	
# Get support for subset in Rule function
def getSupport(setList):
	global totalCountDic
	#print str(totalCountDic[frozenset(setList)])
	support = float(totalCountDic[frozenset(setList)])/len(currentTransactionData)
	return support
		
# Find rules with Confidence 
def findRules(itemSet, minConfidence):
	global totalCountDic
	rules = []
	for item in itemSet:
		listOfSubsets = powerset(item)
		for element in listOfSubsets:
			remain = item.difference(element)
			if len(remain)>0:
				confidence = getSupport(item)/getSupport(element)
				if confidence >= minConfidence:
					print "rule: " + str(element) + " -> " + str(remain)
					print "confidence = " + str(confidence) + " = "
					print "support of " + str(set(item)) + " = " + str(totalCountDic[frozenset(item)]) + "/" + str(len(currentTransactionData)) + " *100 = " + str(getSupport(item)) + " / " + "support of " + str(set(element)) + " = " + str(totalCountDic[frozenset(element)]) + "/" + str(len(currentTransactionData)) + "*100 = " + str(getSupport(element))
					print 
					rules.append(((tuple(element), tuple(remain)), confidence))
	return rules
	
			
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Main
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

	
def main():
	#transformOneAData() # Called once to make prettier file
	#transformOneBData() # Called once to make prettier file
	
	currentItemSet = readInfile(sys.argv[1])
	
	listOfResults = []
	
	countResults = count(currentItemSet)
	
	commonSet = supportReduction(float(sys.argv[2]), countResults)
	listOfResults.append(commonSet)
	
	i = 2
	while len(commonSet) != 0:
		join = joinSet(commonSet, i)
		countResults = count(join)
		commonSet = supportReduction(float(sys.argv[2]), countResults)
		if len(commonSet) != 0:
			listOfResults.append(commonSet)
		i+=1
		
	results = []
	for result in listOfResults:
		results += findRules(result, float(sys.argv[3])) 

if __name__=="__main__":
	main()

