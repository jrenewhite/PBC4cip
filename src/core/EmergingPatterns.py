from copy import copy
from core.Item import SubsetRelation
from core.FilteredCollection import FilteredCollection
from core.DecisionTreeBuilder import SelectorContext
from core.Item import ItemBuilder
from itertools import chain
from collections import OrderedDict


class EmergingPattern(object):
    def __init__(self, dataset, items=None):
        self.Dataset = dataset
        self.Model = self.Dataset.Model
        self.Items = None
        if not items:
            self.Items = list()
        else:
            self.Items = items
        self.Counts = []
        self.Supports = []

    def IsMatch(self, instance):
        for item in self.Items:
            if not item.IsMatch(instance):
                return False
        return True

    def UpdateCountsAndSupport(self, instances):
        matchesCount = [0]*len(self.Dataset.Class[1])

        for instance in instances:
            if(self.IsMatch(instance)):
                matchesCount[instance[self.Dataset.GetClassIdx()]] += 1
        self.Counts = matchesCount
        self.Supports = CalculateSupports(matchesCount)

    def CalculateSupports(self, data):
        classInfo = self.Dataset.ClassInformation
        result = copy(data)
        for i in range(len(result)):
            if classInfo.Distribution[i] != 0:
                result[i] /= classInfo.Distribution[i]
            else:
                result[i] = 0
        return result

    def Clone(self):
        result = EmergingPattern(self.Dataset, self.Items)
        result.Counts = copy(self.Counts)
        result.Supports = copy(self.Supports)
        return result

    def __repr__(self):
        return self.BaseRepresentation() + " " + self.SupportInfo()

    def BaseRepresentation(self):
        return ' AND '.join(map(lambda item: item.__repr__(), self.Items))

    def SupportInfo(self):
        return ' '.join(map(lambda count, support: f"{str(count)} [{str(round(support,2))}]", self.Counts, self.Supports))

    def ToDictionary(self):
        dictOfPatterns = {"Pattern": self.BaseRepresentation()}

        dictOfClasses = {self.Dataset.Class[1][i]+" Count": self.Counts[i]
                         for i in range(0, len(self.Dataset.Class[1]))}

        dictOfClasses.update({self.Dataset.Class[1][i]+" Support": self.Supports[i]
                              for i in range(0, len(self.Dataset.Class[1]))})

        for key in sorted(dictOfClasses.keys()):
            dictOfPatterns.update({key: dictOfClasses[key]})

        return dictOfPatterns


class EmergingPatternCreator(object):
    def __init__(self, dataset):
        self.Dataset = dataset

    def Create(self, contexts):
        pattern = EmergingPattern(self.Dataset)
        for context in contexts:
            childSelector = context.Selector
            builder = ItemBuilder()
            item = builder.GetItem(childSelector, context.Index)
            pattern.Items.append(item)
        return pattern

    def ExtractPatterns(self, treeClassifier, action):
        context = list()
        self.DoExtractPatterns(
            treeClassifier.DecisionTree.TreeRootNode, context, action)

    def DoExtractPatterns(self, node, contexts, action):
        if node.IsLeaf:
            newPattern = self.Create(contexts)
            newPattern.Counts = node.Data
            newPattern.Supports = newPattern.CalculateSupports(node.Data)
            if action:
                action(newPattern)
        else:
            for index in range(len(node.Children)):
                context = SelectorContext()
                context.Index = index
                context.Selector = node.ChildSelector

                contexts.append(context)
                self.DoExtractPatterns(node.Children[index], contexts, action)
                contexts.remove(context)


class EmergingPatternComparer(object):
    def __init__(self, itemComparer):
        self.Comparer = itemComparer

    def Compare(self, leftPattern, rightPattern):
        directSubset = self.IsSubset(leftPattern, rightPattern)
        inverseSubset = self.IsSubset(rightPattern, leftPattern)
        if (directSubset and inverseSubset):
            return SubsetRelation.Equal
        elif (directSubset):
            return SubsetRelation.Subset
        elif (inverseSubset):
            return SubsetRelation.Superset
        else:
            return SubsetRelation.Unrelated

    def IsSubset(self, leftPattern, rightPattern):
        leftItems = rightPattern.Items
        rightItems = leftPattern.Items
        relations = list(map(lambda leftItem, rightItem: self.Comparer(
            leftItem, rightItem), leftItems, rightItems))
        subsetRelations = list(filter(lambda relation: relation == SubsetRelation.Equal or relation == SubsetRelation.Subset,
                                      relations))
        return len(subsetRelations) > 0


class EmergingPatternSimplifier(object):
    def __init__(self, itemComparer):
        self.__comparer = itemComparer
        self.__collection = FilteredCollection(
            self.__comparer, SubsetRelation.Subset)

    def Simplify(self, pattern):
        resultPattern = pattern.Clone()
        self.__collection.SetResultCollection(resultPattern.Items)
        self.__collection.AddRange(pattern.Items)
        return resultPattern