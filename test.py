#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 20 23:27:15 2017

@author: joro
"""
import nltk
import json
from textblob import  TextBlob
import whiteList
import internalBoosts
import sbExtractor

textOfArticle = """'Lawrence of Arabia' is a highly rated film biography about \
                British Lieutenant T. E. Lawrence. Peter O'Toole plays \
                Lawrence in the film."""

jsonOfEntitiesAsString = """ {
  "entities": [
    {
      "name": "Lawrence of Arabia",
      "type": "WORK_OF_ART",
      "metadata": {
        "mid": "/m/0bx0l",
        "wikipedia_url": "http://en.wikipedia.org/wiki/Lawrence_of_Arabia_(film)"
      },
      "salience": 0.75222147,
      "mentions": [
        {
          "text": {
            "content": "Lawrence of Arabia",
            "beginOffset": 1
          },
          "type": "PROPER"
        },
        {
          "text": {
            "content": "film biography",
            "beginOffset": 39
          },
          "type": "COMMON"
        }
      ]
    },
    {
      "name": "T.E. Lawrence",
      "type": "PERSON",
      "metadata": {
        "mid": "/m/0bx5v",
        "wikipedia_url": "http://en.wikipedia.org/wiki/T._E._Lawrence"
      },
      "salience": 0.12430617,
      "mentions": [
        {
          "text": {
            "content": "T. E. Lawrence",
            "beginOffset": 94
          },
          "type": "PROPER"
        },
        {
          "text": {
            "content": "Lieutenant",
            "beginOffset": 83
          },
          "type": "COMMON"
        },
        {
          "text": {
            "content": "Lawrence",
            "beginOffset": 145
          },
          "type": "PROPER"
        }
      ]
    },
    {
      "name": "British",
      "type": "LOCATION",
      "metadata": {
        "mid": "/m/07ssc",
        "wikipedia_url": "http://en.wikipedia.org/wiki/United_Kingdom"
      },
      "salience": 0.078094982,
      "mentions": [
        {
          "text": {
            "content": "British",
            "beginOffset": 75
          },
          "type": "PROPER"
        }
      ]
    },
    {
      "name": "film",
      "type": "WORK_OF_ART",
      "metadata": {},
      "salience": 0.033808723,
      "mentions": [
        {
          "text": {
            "content": "film",
            "beginOffset": 161
          },
          "type": "COMMON"
        }
      ]
    },
    {
      "name": "Peter O'Toole",
      "type": "PERSON",
      "metadata": {
        "mid": "/m/0h0jz",
        "wikipedia_url": "http://en.wikipedia.org/wiki/Peter_O'Toole"
      },
      "salience": 0.011568651,
      "mentions": [
        {
          "text": {
            "content": "Peter O'Toole",
            "beginOffset": 110
          },
          "type": "PROPER"
        }
      ]
    }
  ],
  "language": "en"
}  """ 
      
def sentenceOffsetsAndSentimentBlob(textAsString):
        """Call TextBlob with a string to get sentences and their relevances.
        Transform data in a python dictionary"""
        
        textAsBlob = TextBlob(textAsString)
        setOfSentences = textAsBlob.sentences
        sentencesDict = {}
        sentencesDict["sentences"] = [] #initialize sentences as an empty list
        for sentenceItem in setOfSentences:
            itemDictionary = {} #each sentence is a dictionary
            #fill in the fields: text, offset, sentiment
            itemDictionary["text"]=str(sentenceItem)
            itemDictionary["beginOffset"] = sentenceItem.start
            itemDictionary["magnitude"]=sentenceItem.sentiment.subjectivity
            itemDictionary["score"]=sentenceItem.sentiment.polarity 
            sentencesDict["sentences"].append(itemDictionary)
        return sentencesDict