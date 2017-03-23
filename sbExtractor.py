#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 10 19:00:14 2017

@author: joro
"""
import nltk
import json
from textblob import  TextBlob
import whiteList
import internalBoosts

class sbExtractor:

#    this is a class performing the extraction on a single article 
#    
#
#
#       data structure:
#    articleAsString - the text of the article as a string
#    entities Dictionary (as in the google response + some additional fields)
# 
#    structure of the entities dictionary
#    {"language": "en"
#    "entities": [
#    {
#      "name": "Lawrence of Arabia",
#      "type": "WORK_OF_ART",
#      "metadata": {
#        "mid": "/m/0bx0l",
#        "wikipedia_url": "http://en.wikipedia.org/wiki/Lawrence_of_Arabia_(film)"
#      },
#      "salience": 0.75222147,
#      "mentions": [
#        {
#          "text": {
#            "content": "Lawrence of Arabia",
#            "beginOffset": 1
#          },
#          "type": "PROPER"
#        },
#        {
#          "text": {
#            "content": "film biography",
#            "beginOffset": 39
#          },
#          "type": "COMMON"
#        }
#      ]
#    },
#    {
#      "name": "T.E. Lawrence",
#      "type": "PERSON",}
# ......
#    ] 
# }
  



#   sentencesDictionary (as in the google response + some additional fields)
#
#- structure of the sentence dictionary:
#   {"documentSentiment": {
#    "score": 0.2,
#    "magnitude": 3.6
#  },
#  "language": "en"
#    "sentences": [
#     {
#       "text": {
#         "content": "Four score and seven years ago our fathers brought forth
#         on this continent a new nation, conceived in liberty and dedicated to
#         the proposition that all men are created equal.",
#         "beginOffset": 0
#       },
#       "sentiment": {
#         "magnitude": 0.8,
#         "score": 0.8
#       }
#       "relevance": 1.7
#     },
#    ...]
#    
#    
#    

    def __init__(self, articleAsString, annotationsAsJsonString, useOfflineSentences=False):
        self.articleAsString = articleAsString
        self.lengthOfDocument = len(articleAsString)
        # self.annotationDict = self.__gcpAnnotation__(articleAsString) - this is the right one but the API call is not implemented yet
        tempDict = self.__gcpAnnotation__(annotationsAsJsonString) #gets the full gcp annotation dictionary
        language = "en"
        self.entitiesDict = tempDict["entitiesDict"]
        #add white list annotations
        if ("language" in tempDict):
            language = tempDict["language"]
        whiteList = self.__whiteListAnnotations__(articleAsString, language)
        self.entitiesDict["entities"] += whiteList
        
        self.sentencesDict = {}
        if (useOfflineSentences):
            self.sentencesDict = self.sentenceOffsetsAndSentimentBlob(articleAsString)
        else:
            self.sentencesDict =tempDict["sentencesDict"]
        #sort the sentences chronologically (if for some reason they are not already ...)
        self.sentencesDict["sentences"]=sorted(self.sentencesDict["sentences"], key = lambda sentenceTemp: sentenceTemp["text"]["beginOffset"])  
        self.sentenceRelevances()
    
    
    def __whiteListAnnotations__(self, articleAsString, language = "en"):
        """ annotate white list entities """
        whiteListDict = whiteList.whiteList["general"] + whiteList.whiteList[language]
        totalLength = len(articleAsString)
        annotationSet = []
        for entity in whiteListDict:
            entityAnnotation = {}
            entityAnnotation["name"]= entity["preferredLabel"]
            entityAnnotation["type"]= entity["type"]
            entityAnnotation["metadata"]={"White_List":True}
            entityAnnotation["boost"]=entity["boost"]
            entityAnnotation["mentions"] = []
            surfaceForms = entity["aliases"][:]
            surfaceForms.append(entity["preferredLabel"])
            salience = 0
            mentionsList = []
            for surfaceForm in surfaceForms:
                beginOffsets = self.findAllSubstringOffsets(articleAsString, surfaceForm)#each list has distinct elements
                mentionsList.append({"content":surfaceForm, "beginOffsets":beginOffsets})
            #clean up duplicate offsets
            for mentionsListIdx in range(len(mentionsList)-1):
                for offsetTemp in mentionsList[mentionsListIdx]["beginOffsets"]:
                    for mentionLargetIdx in range(mentionsListIdx+1, len(mentionsList)):
                        try:
                            mentionsList[mentionLargetIdx]["beginOffsets"].remove(offsetTemp)
                        except:
                            pass
                        
            cleanListOffsets = []
            for mention in mentionsList:
                for offset in mention["beginOffsets"]:
                    entityAnnotation["mentions"].append({"text": {"content": mention["content"],"beginOffset": offset},"type": entity["typeP"]})
                    cleanListOffsets.append(offset)
            
            salience += self.__calculateOffsetRelevance__(totalLength, cleanListOffsets)
            
            #print("mentions "+ entity["preferredLabel"])
            #for offset in cleanListOffsets:
            #    print(offset)
            
            entityAnnotation["salience"] = salience      
            annotationSet.append(entityAnnotation)  
        return annotationSet
            
    def __calculateOffsetRelevance__(self, totalLength, listOfOffsets):
        relevance = 0
        for offset in listOfOffsets:
            relevance += totalLength/(offset + totalLength)
        return relevance
    
    def findAllSubstringOffsets(self, articleString, entityForm):
        result = []
        k = 0
        articleLower = articleString.lower()
        entityLower = entityForm.lower()
        while k < len(articleLower):
            k = articleLower.find(entityLower, k)
            if k == -1:
                return result
            else:
                result.append(k)
                k += len(entityLower) 
        return result

    
    def __addVotabilityScores__(self):
        for entity in self.entitiesDict["entities"]:
            votability = entity["salience"]
            if (not ( ("White_List" in entity["metadata"] ) or ("wikipedia_url" in entity["metadata"] ) ) ) :
                votability = 0
            elif (  ("White_List" in entity["metadata"] ) and  ("boost" in entity ) ):
                votability *= entity["boost"]
            else:
                # TODO add boosts
                boost = 1
                if (entity["type"] in internalBoosts.boostsGeneral):
                    boost = internalBoosts.boostsGeneral[entity["type"]]
                votability *= boost
                entity["votability"] = votability
        return self.entitiesDict
                

        
    def __gcpAnnotation__(self,textAsString):
        """Call gcp with a string to get initial annotations.
        Transform data in a python dictionary"""
        
        #call ggogle nlp API
        #for now do as if textAsString is the json
        annotationsAsString = textAsString
        annotationsDict = json.loads(annotationsAsString)
        returnDict = {}
        returnDict["entitiesDict"]={}
        returnDict["sentencesDict"]={}
        if ("language" in annotationsDict):
            returnDict["entitiesDict"]["language"]=annotationsDict["language"]
            returnDict["sentencesDict"]["language"]=annotationsDict["language"]
        if ("entities" in annotationsDict):
            returnDict["entitiesDict"]["entities"]=annotationsDict["entities"]
        if ("documentSentiment" in annotationsDict):
            returnDict["sentencesDict"]["documentSentiment"]=annotationsDict["documentSentiment"]
        if ("sentences" in annotationsDict):
            returnDict["sentencesDict"]["sentences"]=annotationsDict["sentences"]
        return returnDict
    
    
        
    def __sentenceOffsetsAndSentimentNltk__(self,textAsString):
        """Call NLTK  with a string to get sentences and their relevances.
        Transform data in a python dictionary"""
        
        sentencesNltk = nltk.sent_tokenizer(textAsString)
        sentencesDict = {}
        sentencesDict['sentences'] = [] #initialize sentences as an empty list
        for sentenceItem in sentencesNltk:
            itemDictionary = {} #each sentence is a dictionary
            #fill in the fields: text, offset, sentiment
            itemDictionary["text"]={}
            itemDictionary["text"]["content"]=sentenceItem
            itemDictionary["text"]["beginOffset"] = textAsString.find(sentenceItem)
            textAsBlob = TextBlob(sentenceItem)
            itemDictionary["magnitude"]=textAsBlob.sentiment.subjectivity
            itemDictionary["score"]=textAsBlob.sentiment.polarity 
        return sentencesDict
    
    def sentenceOffsetsAndSentimentBlob(self,textAsString):
        """Call TextBlob with a string to get sentences and their relevances.
        Transform data in a python dictionary"""
        
        textAsBlob = TextBlob(textAsString)
        setOfSentences = textAsBlob.sentences
        sentencesDict = {}
        sentencesDict['sentences'] = [] #initialize sentences as an empty list
        for sentenceItem in setOfSentences:
            itemDictionary = {} #each sentence is a dictionary
            #fill in the fields: text, offset, sentiment
            itemDictionary["text"]={}
            itemDictionary["text"]["content"]=str(sentenceItem)
            itemDictionary["text"]["beginOffset"] = sentenceItem.start
            itemDictionary["magnitude"]=sentenceItem.sentiment.subjectivity
            itemDictionary["score"]=sentenceItem.sentiment.polarity 
            sentencesDict["sentences"].append(itemDictionary)
        return sentencesDict
   
    def sentenceRelevances(self):
        """Calculate sentence relevances and add data in the sentences' dictionary"""
        for sentenceIndex in range(len(self.sentencesDict["sentences"])):
            #initialize the field
            self.sentencesDict["sentences"][sentenceIndex]['relevance']=0
            #get beginning and end of sentence
            sentenceOffset = self.sentencesDict["sentences"][sentenceIndex]["text"]["beginOffset"]
            nextSentenceOffset = 0
            if (sentenceIndex < (len(self.sentencesDict["sentences"])-1)):
                nextSentenceOffset = self.sentencesDict["sentences"][sentenceIndex+1]["text"]["beginOffset"]
            else:
                nextSentenceOffset = self.lengthOfDocument + 1
            #run over all concepts    
            for concept in self.entitiesDict["entities"]:
                conceptRelevance = concept["salience"] 
                #run over all mentions
                for conceptMention in concept["mentions"]:
                    mentionOffset = conceptMention["text"]["beginOffset"]
                    if ((mentionOffset>=sentenceOffset) and (mentionOffset<nextSentenceOffset)):
                        self.sentencesDict["sentences"][sentenceIndex]["relevance"] += conceptRelevance
                        
        return self.sentencesDict

    def summaryInternal(self,nbOfSentences, sentenceList):
        """Get a summary of  nbOfSentences  sentences. returns a list of dictionaries  """
        
        if(nbOfSentences<1):
            return []
        elif (nbOfSentences>= len(sentenceList) ):
            return sentenceList
        else:
            #order by relevance to get the top n
            sortedSentences = sorted(sentenceList, key = lambda sentenceTemp: sentenceTemp["relevance"],reverse=True)    
            sortedSentences = sortedSentences[:nbOfSentences]
            #return in chronological order
            return sorted(sortedSentences, key = lambda sentenceTemp: sentenceTemp["text"]["beginOffset"])
        
    def  summary(self,nbOfSentences) :
        """Get a summary of  nbOfSentences  sentences. Returns a string """
        listOfSentences = self.summaryInternal(nbOfSentences, self.sentencesDict["sentences"][:])
        summaryAsString = listOfSentences[0]["text"]["content"]
        for sentenceIdx in range(1,len(listOfSentences)):
            summaryAsString = summaryAsString + " " + listOfSentences[sentenceIdx]["text"]["content"]
        return summaryAsString
    
    
    def conceptSummaryInternal(self,entityName, nbSentences):
        """summary wrt to a concept: internal calcs"""
        
        if(nbSentences<1):
            return []
        else:
            listOfSentences = []
            #get all sentences with a mention of the concept 
            for concept in self.entitiesDict["entities"]:
                if (concept["name"]==entityName):
                    for sentenceIdx in range(len(self.sentencesDict["sentences"])):
                        sentenceAdded = False
                        sentenceOffset = self.sentencesDict["sentences"][sentenceIdx]["text"]["beginOffset"]
                        nextSentenceOffset = 0
                        if (sentenceIdx < (len(self.sentencesDict["sentences"])-1)):
                            nextSentenceOffset = self.sentencesDict["sentences"][sentenceIdx+1]["text"]["beginOffset"]
                        else:
                            nextSentenceOffset = self.lengthOfDocument + 1 
                        for conceptMention in concept["mentions"]: 
                            mentionOffset = conceptMention["text"]["beginOffset"]
                            if ((mentionOffset>=sentenceOffset) and (mentionOffset<nextSentenceOffset)):
                                if (not sentenceAdded):
                                    listOfSentences.append(self.sentencesDict["sentences"][sentenceIdx])
                                    sentenceAdded = True
                                if (conceptMention["type"]=="PROPER"):
                                    listOfSentences[-1]["relevance"] *= internalBoosts.boostForProperMentionInSummary
        
            if(nbSentences < len(listOfSentences)):
                #sort by relevance
                listOfSentences = sorted(listOfSentences, key = lambda sentenceTemp: sentenceTemp["relevance"],reverse=True) 
                #take top n
                listOfSentences = listOfSentences[:nbSentences]
                #sort chronologically
                listOfSentences = sorted(listOfSentences, key = lambda sentenceTemp: sentenceTemp["text"]["beginOffset"])
            return  listOfSentences   
           
        
    def conceptSummary(self,entityName, nbSentences):
        """summary wrt to a concept""" 
        listOfSentences = self.conceptSummaryInternal(entityName, nbSentences)
        summaryAsString = listOfSentences[0]["text"]["content"]
        for sentenceIdx in range(1,len(listOfSentences)):
            summaryAsString = summaryAsString + " " + listOfSentences[sentenceIdx]["text"]["content"]
        return summaryAsString
                                
                           
    
    def getEntities(self):
        return self.entitiesDict
    
    def getSentences(self):
        return self.sentencesDict
    
    def getSentence(self,indexOfTheSentence):
        sentenceIndex = min(indexOfTheSentence, len(self.sentencesDict["sentences"]) )
        return self.sentencesDict["sentences"][sentenceIndex]
    
    

     


