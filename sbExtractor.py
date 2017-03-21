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
#    data structure:
#    articleAsString - the text of the article as a string
#    sentencesDictionary - 
#    {
#   "documentSentiment": {
#     "score": 0.2,
#     "magnitude": 3.6
#   },
#   "language": "en",
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
#     },
#    ...
#   }
#    annotationList - a list of the annotations: follows the googleAPI format
    
    #see here https://cloud.google.com/natural-language/docs/basics
#"{entities": [
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
#      "type": "PERSON",
# ......
#    ],
#"language":en}
    #boosts: a dictionary of the form {annotationType: boost}
    
    
    
    def __init__(self, articleAsString, entitiesAsJson, boostsAsJson = "use_internal"):
        self.lengthOfDocument = len(articleAsString)
        self.annotationDict = self.__gcpAnnotation__(entitiesAsJson)
        self.articleAsString = articleAsString
        #self.sentencesDict = self.__sentenceOffsetsAndSentimentGcp__(articleAsString)
        self.sentencesDict = self.sentenceOffsetsAndSentimentBlob(articleAsString)
        self.sentenceRelevances()
    
    def __gcpAnnotation__(self,textAsString):
        """Call gcp with a string to get initial annotations.
        Transform data in a python dictionary"""
        
        #call ggogle nlp API
        #for now do as if textAsString is the json
        annotationsAsString = textAsString
        annotationsDict = json.loads(annotationsAsString)
        return annotationsDict
    
    def __sentenceOffsetsAndSentimentGcp__(self,textAsString):
        """Call gcp with a string to get sentences and their relevances.
        Transform data in a python dictionary"""
        
        #call google sentiment api and get a json
        #for now do as if textAsString is the json
        extractedJsonAsString = textAsString
        sentencesDict = json.loads(extractedJsonAsString)
        return sentencesDict
        
        
        
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
            for concept in self.annotationDict["entities"]:
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
            sortedSentences = sorted(sentenceList, key = lambda sentenceTemp: sentenceTemp["relevance"])    
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
    
    def getEntities(self):
        return self.annotationDict
    
    def getSentences(self):
        return self.sentencesDict
    
    

     


