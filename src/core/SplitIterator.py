import math
from core.Helpers import FindDistribution, Substract
import operator


class SplitIterator(object):

    def __init__(self, dataset, feature):
        self.Dataset = dataset
        self.Model = self.Dataset.Model
        self.Class = self.Dataset.Class
        self.Feature = self.Dataset.GetAttribute(feature)
        self.CurrentDistribution = None

        self.__iterators = {"integer": self.NumericOnPoint,
                            "real": self.NumericCenterBetweenPoints,
                            "numeric": self.NumericCenterBetweenPoints,
                            "nominal": self.ValueAndComplement}
        self.__initialized = False
        self.__numClasses = 0
        self.__instances = 0
        self.__currentIndex = None
        self.__lastClassValue = None
        self.__sortedInstances = None
        self.__selectorFeatureValue = None
        self.__perValueDistribution = None
        self.__totalDistribution = None
        self.__valuesCount = None
        self.__existingValues = None
        self.__iteratingTwoValues = None
        self.__valueIndex = None
        self.__twoValuesIterated = None

    def Initialize(self, instances):
        if not self.Model:
            raise Exception("Model is null")
        if self.Class[1] in ['numeric', 'real', 'integer', 'string']:
            raise Exception("Cannot use this iterator on non-nominal class")
        self.__numClasses = len(self.Dataset.GetClasses())

        if self.Dataset.IsNominalFeature(self.Feature):
            self.InitializeNominal(instances)
        else:
            self.InitializeNumeric(instances)
        self.__instances = len(instances)
        self.__initialized = True

    def FindNext(self):
        if not self.__initialized:
            raise Exception("Iterator not initialized")
        if self.Dataset.IsNominalFeature(self.Feature):
            return self.FindNextNominal()
        else:
            return self.FindNextNumeric()

    def CreateCurrentChildSelector(self):
        selector = None
        if self.Dataset.IsNominalFeature(self.Feature):
            if self.__iteratingTwoValues:
                selector = SingleFeatureSelector(
                    self.Dataset, self.Feature, SingleFeatureSelector.MultipleValuesSelector)
                selector.Values = list(self.__perValueDistribution.keys())
            else:
                selector = SingleFeatureSelector(
                    self.Dataset, self.Feature, SingleFeatureSelector.ValueAndComplementSelector)
                selector.Value = self.__existingValues[self.__valueIndex]
        else:
            selector = SingleFeatureSelector(
                self.Dataset, self.Feature, SingleFeatureSelector.CutPointSelector)
            selector.CutPoint = self.__selectorFeatureValue

        return selector

    # region Numeric splitIterators
    def InitializeNumeric(self, instances):
        self.CurrentDistribution = [list()]*2

        self.__sortedInstances = list(
            filter(lambda element: not self.IsMissing(element[0]), instances))
        self.__sortedInstances.sort(
            key=lambda element: self.GetFeatureValue(element[0]))

        self.CurrentDistribution[0] = [0]*self.__numClasses
        self.CurrentDistribution[1] = FindDistribution(
            self.__sortedInstances, self.Model, self.Dataset.Class)

        if (len(self.__sortedInstances) == 0):
            return

        self.__currentIndex = -1
        self.__lastClassValue = self.FindNextClass(0)

    def FindNextNumeric(self):
        if (self.__currentIndex >= len(self.__sortedInstances) - 1):
            return False

        self.__currentIndex += 1
        while self.__currentIndex < len(self.__sortedInstances) - 1:
            instance = self.__sortedInstances[self.__currentIndex][0]
            objClass = self.GetClassValue(instance)
            self.CurrentDistribution[0][objClass] += self.__sortedInstances[self.__currentIndex][1]
            self.CurrentDistribution[1][objClass] -= self.__sortedInstances[self.__currentIndex][1]

            if self.GetFeatureValue(instance) != self.GetFeatureValue(self.__sortedInstances[self.__currentIndex+1][0]):
                nextClassValue = self.FindNextClass(self.__currentIndex + 1)
                if (self.__lastClassValue != nextClassValue) or (self.__lastClassValue == -1 and nextClassValue == -1):
                    CuttingStrategy = self.__iterators[self.Feature[1].lower()]
                    self.__selectorFeatureValue = CuttingStrategy(instance)
                    self.__lastClassValue = nextClassValue
                    return True
            self.__currentIndex += 1
        return False

    def FindNextClass(self, index):
        currentClass = self.GetClassValue(self.__sortedInstances[index][0])
        currentValue = self.GetFeatureValue(self.__sortedInstances[index][0])
        index += 1
        while index < len(self.__sortedInstances) and currentValue == self.GetFeatureValue(self.__sortedInstances[index][0]):
            if currentClass != self.GetClassValue(self.__sortedInstances[index][0]):
                return -1
            index += 1
        return currentClass

    def NumericOnPoint(self, instance):
        return instance[self.GetFeatureIdx()]

    def NumericCenterBetweenPoints(self, instance):
        return (instance[self.GetFeatureIdx()] + self.__sortedInstances[self.__currentIndex][0][self.GetFeatureIdx()]) / 2
    # endregion

    # region Nominal splitIterator

    def InitializeNominal(self, instances):
        self.__perValueDistribution = {}
        self.__totalDistribution = [0]*self.__numClasses
        self.CurrentDistribution = [list()]*2

        for instance in instances:
            if self.IsMissing(instance[0]):
                continue
            value = self.GetFeatureValue(instance[0])
            current = [0]*self.__numClasses
            if not value in self.__perValueDistribution:
                self.__perValueDistribution.update({value: current})

            classIdx = self.GetClassValue(instance[0])
            self.__perValueDistribution[value][classIdx] += instance[1]
            self.__totalDistribution[classIdx] += instance[1]

        self.CurrentDistribution = [list()]*2
        self.__valuesCount = len(self.__perValueDistribution)
        self.__existingValues = list(self.__perValueDistribution.keys())
        self.__iteratingTwoValues = (self.__valuesCount == 2)
        self.__valueIndex = -1
        self.__twoValuesIterated = False

    def FindNextNominal(self):
        if self.__valuesCount == self.__instances:
            return False
        if self.__iteratingTwoValues:
            if self.__twoValuesIterated:
                return False
            self.__twoValuesIterated = True
            self.CalculateCurrent(
                self.__perValueDistribution[self.__existingValues[0]])
            return True
        else:
            if(self.__valuesCount < 2 or self.__valueIndex >= self.__valuesCount - 1):
                return False
            self.__valueIndex += 1
            self.CalculateCurrent(
                self.__perValueDistribution[self.__existingValues[self.__valueIndex]])
            return True

    def ValueAndComplement(self, instance):
        pass

    def CalculateCurrent(self, current):
        self.CurrentDistribution[0] = current
        self.CurrentDistribution[1] = Substract(
            self.__totalDistribution, current)

    # endregion

    # region Support methods

    def GetFeatureIdx(self):
        return self.Dataset.GetFeatureIdx(self.Feature)

    def IsMissing(self, instance):
        return self.Dataset.IsMissing(self.Feature, instance)

    def GetFeatureValue(self, instance):
        return self.Dataset.GetFeatureValue(self.Feature, instance)

    def GetClassValue(self, instance):
        return self.Dataset.GetClasses().index(instance[self.Dataset.GetClassIdx()])
    # endregion


class SingleFeatureSelector(object):

    CutPointSelector = 1
    ValueAndComplementSelector = 2
    MultipleValuesSelector = 3

    def __init__(self, dataset, feature, selector):
        self.ChildrenCount = 2
        self.Dataset = dataset
        self.Model = dataset.Model
        self.Feature = feature
        self.Selector = selector
        self.CutPoint = math.nan
        self.Values = []
        self.Value = math.nan

    def Select(self, instance):
        if self.Dataset.IsMissing(self.Feature, instance):
            return None
        if self.Selector == SingleFeatureSelector.CutPointSelector:
            return self.SelectCutPoint(instance)
        elif self.Selector == SingleFeatureSelector.MultipleValuesSelector:
            return self.SelectMultipleValues(instance)
        elif self.Selector == SingleFeatureSelector.ValueAndComplementSelector:
            return self.SelectValueAndComplement(instance)
        else:
            return None

    def SelectCutPoint(self, instance):
        if self.Dataset.IsNominalFeature(self.Feature):
            raise Exception("Cannot use cutpoint on nominal data")
        if self.Dataset.GetFeatureValue(self.Feature, instance) <= self.CutPoint:
            return [1, 0]
        else:
            return [0, 1]

    def SelectMultipleValues(self, instance):
        if not self.Dataset.IsNominalFeature(self.Feature):
            raise Exception("Cannot use multiple values on non-nominal data")
        value = self.Dataset.GetFeatureValue(self.Feature, instance)
        index = self.Values.index(value)
        if index == -1:
            return None
        result = [0]*self.ChildrenCount
        result[index] = 1
        return result

    def SelectValueAndComplement(self, instance):
        if not self.Dataset.IsNominalFeature(self.Feature):
            raise Exception("Cannot use multiple values on non-nominal data")
        if self.Dataset.GetFeatureValue(self.Feature, instance) == self.Value:
            return [1, 0]
        else:
            return [0, 1]

    def ToString(self, index):
        if self.Selector == SingleFeatureSelector.CutPointSelector:
            if index == 0:
                return f"{self.Feature[0]}<={self.CutPoint}"
            else:
                return f"{self.Feature[0]}>{self.CutPoint}"
        elif self.Selector == SingleFeatureSelector.MultipleValuesSelector:
            return f"{self.Feature[0]}={self.Dataset.GetValueOfIndex(self.Feature,index)}"
        elif self.Selector == SingleFeatureSelector.ValueAndComplementSelector:
            if index == 0:
                return f"{self.Feature[0]}={self.Dataset.GetValueOfIndex(self.Feature,self.Value)}"
            else:
                return f"{self.Feature[0]}<>{self.Dataset.GetValueOfIndex(self.Feature,self.Value)}"
        else:
            return "???"

    def __format__(self, index):
        if self.Selector == SingleFeatureSelector.CutPointSelector:
            if index == 0:
                return f"{self.Feature[0]}<={self.CutPoint}"
            else:
                return f"{self.Feature[0]}>{self.CutPoint}"
        elif self.Selector == SingleFeatureSelector.MultipleValuesSelector:
            return f"{self.Feature[0]}={self.Dataset.GetValueOfIndex(self.Feature[0],index)}"
        elif self.Selector == SingleFeatureSelector.ValueAndComplementSelector:
            if index == 0:
                return f"{self.Feature[0]}={self.Dataset.GetValueOfIndex(self.Feature[0],self.Value)}"
            else:
                return f"{self.Feature[0]}<>{self.Dataset.GetValueOfIndex(self.Feature[0],self.Value)}"
        else:
            return super().__str__()

    def __repr__(self):
        if self.Selector == SingleFeatureSelector.CutPointSelector:
            return f"{self.Feature[0]}<={self.CutPoint}"
        elif self.Selector == SingleFeatureSelector.MultipleValuesSelector:
            return f"{self.Feature[0]}in[{', '.join(map(lambda value: self.Dataset.GetValueOfIndex(self.Feature[0],value),self.Values))}]"
        elif self.Selector == SingleFeatureSelector.ValueAndComplementSelector:
            return f"{self.Feature[0]}={self.Dataset.GetValueOfIndex(self.Feature[0],self.Value)}"
        else:
            return "???"
