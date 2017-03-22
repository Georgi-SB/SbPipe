#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 19 19:04:49 2017

@author: joro
"""

boostsGeneral = {"PERSON":4,"ORGANIZATION":4, "LOCATION":2, "WORK_OF_ART":2}
boosts = {"politics":{"person":4,"organization":4, "location":2, "WORK_OF_ART":2}, 
                               "sports": {"person":4,"organization":4, "location":2, "WORK_OF_ART":2}}
boostForPropper = 10

boostForProperMentionInSummary = 1.5