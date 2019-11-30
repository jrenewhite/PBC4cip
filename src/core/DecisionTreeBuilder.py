import math
import random
from core.DecisionTree import DecisionTree, DecisionTreeNode
from core.WinningSplitSelector import WinningSplitSelector
from core.SplitIterator import SplitIterator
from core.Helpers import CreateMembershipTuple, FindDistribution

class DecisionTreeBuilder:
    def __init__(self, dataset, pruneResult=None):
        self.MinimalInstanceMembership = 0.05
        self.MinimalSplitGain = 1e-30
        self.MinimalObjByLeaf = 2
        self.MaxDepth = -1
        self.PruneResult = False
        self.Dataset = dataset
        self.FeatureCount = 0
        self.StopCondition = None
        self.DistributionEvaluator = None
        self.OnSelectingFeaturesToConsider = None

    def Build(self):
        if self.MinimalSplitGain <= 0:
            raise Exception("MinimalSplitGain must be positive")

        currentContext = []


        objectMebership = CreateMembershipTuple(self.Dataset.Instances)
        classFeature = self.Dataset.Class

        result = DecisionTree(self.Dataset)

        filteredObjMembership = tuple(filter(lambda x: x[1] >= self.MinimalInstanceMembership, objectMebership))

        parentDistribution = FindDistribution(filteredObjMembership, self.Dataset.Model, self.Dataset.Class)

        result.TreeRootNode = DecisionTreeNode()
        result.TreeRootNode.Data = parentDistribution

        self.FillNode(result.TreeRootNode,
                                            filteredObjMembership, 0, currentContext)
        return result

    #
    def FillNode(self, node, instanceTuples, level, currentContext):
        if self.StopCondition(node.Data, self.Dataset.Model, self.Dataset.Class):
            return 
        if self.MaxDepth >= 0 and level >= self.MaxDepth - 1:
            return 
        if sum(node.Data) <= self.MinimalObjByLeaf:
            return 

        whichBetterToFind = 1
        winningSplitSelector = WinningSplitSelector(whichBetterToFind)
        currentGain = 0

        sampleFeatures = self.OnSelectingFeaturesToConsider(list(map(lambda attribute: attribute[0], self.Dataset.Model)), self.FeatureCount)
        for feature in sampleFeatures:
            if feature != self.Dataset.Class[0]:
                splitIterator = SplitIterator(self.Dataset, feature)
                splitIterator.Initialize(instanceTuples)
                while splitIterator.FindNext():
                    currentGain = self.DistributionEvaluator(node.Data, splitIterator.CurrentDistribution)
                    if currentGain >= self.MinimalSplitGain:
                        winningSplitSelector.EvaluateThis(currentGain, splitIterator, level)

        if winningSplitSelector.IsWinner():
            maxSelector = winningSplitSelector.WinningSelector
            node.ChildSelector = maxSelector
            node.Children = list()
            instancesPerChildNode = CreateChildrenInstances(instanceTuples, maxSelector, self.MinimalInstanceMembership)

            for index in range(maxSelector.ChildrenCount):
                childNode = DecisionTreeNode()
                childNode.Parent = node
                childNode.Data = winningSplitSelector.WinningDistribution[index]
                node.Children.append(childNode)

                self.FillNode(childNode, instancesPerChildNode[index], level + 1, currentContext)


        return 
   

def CreateChildrenInstances(instances, selector, threshold=None):
    if not threshold:
        threshold = 0

    result = list()
    for child in range(selector.ChildrenCount):
        result.append(list(tuple()))

    for instance in instances:
        selection = selector.Select(instance[0])
        if selection:
            for index in range(len(selection)):
                if selection[index] > 0:
                    newMembership = selection[index] * instance[1]
                    if newMembership >= threshold:
                        result[index].append(tuple((instance[0], newMembership)))

    return result


class SelectorContext(object):
    def __init__(self):
        self.Index = 0
        self.Selector = None
