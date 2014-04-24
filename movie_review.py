#!/usr/bin/python

from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from nltk.chunk import RegexpParser
from sentiwordnet import SentiWordNetCorpusReader, SentiSynset
import re, string

#constants used for passing values in evaluation
NP = 0
VP = 1
NN = 2
VB = 3
ADV = 4
ADJ = 5
PRD = 6
CLS = 7

#gets a tree of NP and returns is as a tuple with <[ADJ] [NN]>
# Sample tree : Tree('NP', [('It', 'PRP')])
def getNP(tree):
    adj = []
    nn = []

       #iterates over the tree and add the words to respective arrays
    for t in tree:
        try:
            if t[1] == "JJ" or t[1]=="JJR" or t[1]=="JJS":
                adj.append(t[0])
            elif t[1] == "NN" or t[1] == "NNP":
                nn.append(t[0])
            elif t[1] == "NNS" or t[1]=="NNPS":
                nn.append(t[0])
            elif t[1]=="PRP" or t[1] == "PRPS":
                nn.append(t[0])
        except:
            continue

    return (adj , nn)

#gets a tree of NP and returns is as a tuple with <[ADV] [VB]>
# Sample tree : Tree('V', [('was', 'VBD')])
def getVP(tree):
    adv = []
    vb = []

       #iterates over the tree and add the words to respective arrays   
    for t in tree:
        try:
            if t[1] == "RB":
                adv.append(t[0])
        except:
            if t.node == "V":
                vb.append(t[0][0])
    return (adv , vb)


def getPred(tree):
    tmp = (getNP(tree[0]), getVP(tree[1]))
    return tmp

def getClause1(tree):
    tmp = (getNP(tree[0]), getPred(tree[1]))
    return tmp

def getClause2(tree):
    tmp = (getNP(tree[1]), getPred(tree[0]))
    return tmp

#find the score to be given to each word
def getWordScore(word, dType):
      #using the sentiwordnet file to get the score for each word
    swn_filename = 'SentiWordNet_3.0.0_20130122.txt'
    swn = SentiWordNetCorpusReader(swn_filename)
    word = re.sub('[%s]' % re.escape(string.punctuation), ' ', word) #removes all the punctuations and replace with a space
    word = word.lower()
    wS = 0
    
    for w in word.split():
		#gets the synsets of each word
        if dType == NN:
            test = swn.senti_synsets(w, 'n') 
        elif dType == ADJ:
            test = swn.senti_synsets(w, 'a')
        elif dType == VB:
            test = swn.senti_synsets(w, 'v')
        elif dType == ADV:
            test = swn.senti_synsets(w, 'r')
        try:
            p_score = test[0].pos_score
            n_score = test[0].neg_score
            wS += p_score - n_score #gets the summation of all scores
            
        except:
            continue
        print w,"\n Positive Score : ",test[0].pos_score,"\n Negative Score : ",test[0].neg_score

    if len(word.split()) == 0:
        return 0
    else:
        return wS/len(word.split()) #returns average score for in a sentence



def getScoreNP(tmpNP):		#tmpNP = [(<[ADJ] [NN]>) , ...]
    scoreAdj = 0
    scoreNn = 0
    totalScore = 0
    normcount = 0

    for temp in tmpNP:

        scoreAdj = 0
        scoreNn = 0

        for t1 in temp[0]:
            wordscore = getWordScore(t1, ADJ)
            if wordscore==0:
                normcount+=1
            scoreAdj +=  wordscore

        for t1 in temp[1]:
            wordscore = getWordScore(t1, NN)
            if wordscore==0:
                normcount+=1
            scoreNn +=  wordscore

        if len(temp[0]) != 0 and len(temp[1]) != 0:
            totalScore += (scoreAdj/len(temp[0]) + scoreNn/len(temp[1]))/2
            
        elif len(temp[0]) == 0 and len(temp[1]) != 0:
            totalScore += (scoreNn/len(temp[1]))

        elif len(temp[0]) != 0 and len(temp[1]) == 0:
            totalScore += (scoreAdj/len(temp[0]))

        else:
            totalScore += 0

    if len(tmpNP) != 0 and len(tmpNP)!= normcount:
        return totalScore/(len(tmpNP)-normcount)
    else:
        return 0


def getScoreVP(tmpVP):
    scoreAdv = 0
    scoreVb = 0
    totalScore = 0
   
    for temp in tmpVP:
        scoreAdv = 0
        scoreVb = 0
        for t1 in temp[0]:
            scoreAdv +=  getWordScore(t1, ADV)
        for t1 in temp[1]:
            scoreVb +=  getWordScore(t1, VB)

        if len(temp[0]) != 0 and len(temp[1]) != 0:
            totalScore += (scoreAdv/len(temp[0]) + scoreVb/len(temp[1]))/2

        elif len(temp[0]) == 0 and len(temp[1]) != 0:
            totalScore += (scoreVb/len(temp[1]))

        elif len(temp[0]) != 0 and len(temp[1]) == 0:
            totalScore += (scoreAdv/len(temp[0]))
        else:
            totalScore += 0

    if len(tmpVP) != 0:
        return totalScore/len(tmpVP)
    else:
        return 0

def getScorePred(tmpPrd):
    totalScore = 0
    tmpNP = []
    tmpVP = []
    for temp in tmpPrd:
        tmpNP.append(temp[0])
        tmpVP.append(temp[1])
        totalScore += (getScoreNP(tmpNP) + getScoreVP(tmpVP))/2
    if len(tmpPrd) != 0:
        return totalScore/len(tmpPrd)
    else:
        return 0

def getScoreClause(tmpCls):
    totalScore = 0
    tmpNP = []
    tmpPrd = []
    for temp in tmpCls:
        tmpNP.append(temp[0])
        tmpPrd.append(temp[1])
        totalScore += (getScoreNP(tmpNP) + getScoreVP(tmpPrd))/2
    if len(tmpCls) != 0:
        return totalScore/len(tmpPrd)
    else:
        return 0
    

review = " "
punctuation = [",",";",".",":",","]

#grammar for parsing the input
grammer = '''
    NP: {<DT>? <JJ>* <NN.*|PR.*>*}
    P: {<IN>}          
    V: {<V.*>}
    PP: {<P> <NP>}    
    '''
vp = "VP: {<RB|RBR|RBS>* <V> <RB|RBR|RBS>* <NP|PP>*}\n"
prd = "PRD: {<NP> <VP>}\n"
cls1 = "CLS1: {<NP> <PRD>}\n"
cls2 = "CLS2: {<PRD> <NP>}\n"

#open the file named 'input' and read it
print "Loading input file..."
fileReview = open("input", "r")	#open 
#file to retrive movie 
#reviews
arr = fileReview.read()

while arr:				#removes all trilling white spaces and
    review += arr.strip()		#adds it to var review
    arr = fileReview.read()

fileReview.close()

print "Sentence tokenization..."
review_dict = sent_tokenize(review)	#tokenizes sentences
arr_pos = []
removed = []

print "POS tagging for words..."

for sent in review_dict:	#adding individual sentences after tagging
    arr_pos.extend([pos_tag(sent.split())].__iter__())
    


print "Loading Parser..."
print "Finished loading..."

sentCount = 1
sentScore = []          #tuple with (Subj-Obj , Verb-P , )
totalS = []

print "Processing input..."
print "Number of sentences to process: ", len(arr_pos)

for q in ["", vp + prd + cls1 + cls2]:
   print "___\n"
   grammer += q  #update grammer
   print grammer
   npc = RegexpParser(grammer) #assign npc with RegexpParser for the given grammar
   sentCount=0
   print "\n"
   for i in arr_pos:
        print "Reading sentence ", sentCount
        sentCount += 1
        t = npc.parse(i) #parsing
        print t
        tmpVP = []
        tmpNP = []
        tmpPrd = []
        tmpCls = []
        x1 = ""
   
        for x in t:
            try:
                if x.node == "VP":
                    x1 = getVP(x) #gets the tuple <[ADV] [VB]>
                    tmpVP.append(x1)

                if x.node == "NP":
                    x1 = getNP(x) #gets the tuple <[ADJ] [NN]>
                    tmpNP.append(x1)

                elif x.node == "PRD":
                    x1 = getPred(x) #gets <[ADJ] [NN] [ADV] [VB]>
                    tmpPrd.append(x1)

                elif x.node == "CLS1":
                    x1 = getClause1(x)
                    tmpCls.append(x1)

                elif x.node == "CLS2":
                    x1 = getClause2(x)
                    tmpCls.append(x1)
            except:
                continue
    
        totalS.append(1) #set 1 as the initial value in the stack
   
        tNp = getScoreNP(tmpNP) #finding score of each word
        tVp = getScoreVP(tmpVP)
        tPrd = getScorePred(tmpPrd)
        tCls = getScoreClause(tmpCls)
	#multiply the old element in the list with the new element
        if tNp != 0:
            totalS.append(totalS.pop() * tNp) 
   
        if tVp != 0:
            totalS.append(totalS.pop() * tVp)
   
        if tPrd != 0:
            totalS.append(totalS.pop() * tPrd)
   
        if tCls != 0:
            totalS.append(totalS.pop() * tCls)

netscore = 0;

print "\nSCORES\n____________"
for j in range(0,len(totalS),sentCount):
   for i in range(0,sentCount):
      netscore += totalS[j+i]
      print totalS[j+i]
   print "_____________"

print "\n\nNET SCORE : ",netscore/len(totalS)
