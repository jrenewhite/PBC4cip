import random

def SampleWithoutRepetition(poulation, sampleSize):
    return random.sample(set(
        map(lambda attribute: attribute, poulation)), sampleSize)