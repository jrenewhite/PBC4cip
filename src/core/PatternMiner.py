import random
import math
import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool, freeze_support, cpu_count
from functools import partial
from core.SupervisedClassifier import DecisionTreeClassifier
from core.RandomSampler import SampleWithoutRepetition
from core.EmergingPatterns import EmergingPatternCreator, EmergingPatternComparer, EmergingPatternSimplifier
from core.Item import ItemComparer
from core.FilteredCollection import FilteredCollection


class PatternMiner:

    def __init__(self, dataset, treeCount=None, featureCount=None, minePatternsWhileBuildingTree=None):
        self.Dataset = dataset
        self.Patterns = list()
        self.DecisionTreeBuilder = None
        self.EPTester = None
        self.FilterRelation = None

        self.__emergingPatternCreator = None
        self.__emergingPatternComparer = None
        self.__emergingPatternSimplifier = None
        self.__minimal = None

        if not featureCount:
            self.FeatureCount = -1
        else:
            self.FeatureCount = featureCount

        if not treeCount:
            self.TreeCount = 100
        else:
            self.TreeCount = treeCount

        if not minePatternsWhileBuildingTree:
            self.MinePatternsWhileBuildingTree = False
        else:
            self.MinePatternsWhileBuildingTree = minePatternsWhileBuildingTree

    # region Pattern extraction

    def Mine(self):
        self.Patterns = list()
        self.__emergingPatternCreator = EmergingPatternCreator(self.Dataset)
        self.__emergingPatternComparer = EmergingPatternComparer(
            ItemComparer().Compare)
        self.__emergingPatternSimplifier = EmergingPatternSimplifier(
            ItemComparer().Compare)
        self.__minimal = FilteredCollection(
            self.__emergingPatternComparer.Compare, self.FilterRelation)
        self.Patterns = self.DoMine(
            self.__emergingPatternCreator, self.PatternFound)
        return self.Patterns

    def DoMine(self, emergingPatternCreator, action):
        freeze_support()  # for Windows support
        featureCount = 0
        if self.FeatureCount != -1:
            featureCount = self.FeatureCount
        else:
            featureCount = int(math.log(len(self.Dataset.Attributes), 2) + 1)

        self.DecisionTreeBuilder.FeatureCount = featureCount
        self.DecisionTreeBuilder.OnSelectingFeaturesToConsider = SampleWithoutRepetition

        for i in tqdm(range(self.TreeCount), unit="tree", desc="Building trees and extracting patterns", leave=False):
            tree = self.DecisionTreeBuilder.Build()
            treeClassifier = DecisionTreeClassifier(tree)
            emergingPatternCreator.ExtractPatterns(treeClassifier, action)

        return self.__minimal.GetItems()

    # endregion

    def CreateTreeAndExtractpatterns(self, emergingPatternCreator, action, iterable):
        tree = self.DecisionTreeBuilder.Build()
        treeClassifier = DecisionTreeClassifier(tree)
        emergingPatternCreator.ExtractPatterns(treeClassifier, action)

    def PatternFound(self, pattern):
        if self.EPTester(pattern.Counts, self.Dataset.Model, self.Dataset.Class):

            self.__minimal.Add(
                self.__emergingPatternSimplifier.Simplify(pattern))
