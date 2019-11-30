from core.SplitIterator import SplitIterator, SingleFeatureSelector

Unknown = -1
EqualThan = 0
DifferentThan = 1
LessOrEqualThan = 2
GreatherThan = 3


class SubsetRelation(object):
    Unknown = 0
    Unrelated = 1
    Equal = 2
    Subset = 3
    Superset = 4
    Different = 5


class SingleValueItem(object):

    def __init__(self, dataset, feature, itemType, value):
        self.Dataset = dataset
        self.Feature = feature
        self.Model = self.Dataset.Model
        self.Value = value
        self.ItemType = itemType

    def IsMatch(self, instance):
        if self.Dataset.IsMissing(self.Feature, instance):
            return False

        value = self.GetValue(instance)

        if self.ItemType == EqualThan:
            return value == self.Value
        elif self.ItemType == DifferentThan:
            return value != self.Value
        elif self.ItemType == LessOrEqualThan:
            return value <= self.Value
        elif self.ItemType == GreatherThan:
            return value > self.Value
        else:
            return False

    def CompareTo(self, other):
        if not other or not isinstance(other, SingleValueItem):
            return SubsetRelation.Unknown

        if self.ItemType == EqualThan:
            return self.CompareEqualsThan(other)
        elif self.ItemType == DifferentThan:
            return self.CompareDifferentThan(other)
        elif self.ItemType == LessOrEqualThan:
            return self.CompareLessOrEqualThan(other)
        elif self.ItemType == GreatherThan:
            return self.CompareGreaterThan(other)
        else:
            return SubsetRelation.Unknown

    # region Comparison methods
    def CompareEqualsThan(self, other):
        if other.ItemType == EqualThan:
            if self.Value == other.Value:
                return SubsetRelation.Equal
            else:
                return SubsetRelation.Unrelated
        elif other.ItemType == DifferentThan:
            if self.Value == other.Value:
                return SubsetRelation.Unrelated
            if self.Dataset.IsNominalFeature(self.Feature):
                numberOfValues = len(self.Feature[1])
                if self.Value != other.Value:
                    if numberOfValues == 2:
                        return SubsetRelation.Equal
                    else:
                        return SubsetRelation.Subset

        return SubsetRelation.Unrelated

    def CompareDifferentThan(self, other):
        if other.ItemType == DifferentThan:
            if self.Value == other.Value:
                return SubsetRelation.Equal
            else:
                return SubsetRelation.Unrelated
        elif other.ItemType == EqualThan:
            if self.Value == other.Value:
                return SubsetRelation.Unrelated
            if self.Dataset.IsNominalFeature(self.Feature):
                numberOfValues = len(self.Feature[1])
                if self.Value != other.Value:
                    if numberOfValues == 2:
                        return SubsetRelation.Equal
                    else:
                        return SubsetRelation.Superset

        return SubsetRelation.Unrelated

    def CompareLessOrEqualThan(self, other):
        if other.ItemType == LessOrEqualThan:
            if self.Value == other.Value:
                return SubsetRelation.Equal
            if self.Value > other.Value:
                return SubsetRelation.Superset
            else:
                return SubsetRelation.Subset

        return SubsetRelation.Unrelated

    def CompareGreaterThan(self, other):
        if other.ItemType == GreatherThan:
            if self.Value == other.Value:
                return SubsetRelation.Equal
            if self.Value > other.Value:
                return SubsetRelation.Subset
            else:
                return SubsetRelation.Superset

        return SubsetRelation.Unrelated
    # endregion

    def __repr__(self):
        if self.ItemType == EqualThan:
            return f"{self.Feature[0]} = {self.GetValueRepresentation()}"
        elif self.ItemType == DifferentThan:
            return f"{self.Feature[0]} != {self.GetValueRepresentation()}"
        elif self.ItemType == LessOrEqualThan:
            return f"{self.Feature[0]} <= {self.GetValueRepresentation()}"
        elif self.ItemType == GreatherThan:
            return f"{self.Feature[0]} > {self.GetValueRepresentation()}"
        else:
            return super().__repr__()

    def GetValue(self, instance):
        return self.Dataset.GetFeatureValue(self.Feature, instance)

    def GetValueRepresentation(self):
        if self.Dataset.IsNominalFeature(self.Feature):
            return self.Feature[1][self.Value]
        else:
            return self.Value


class ItemBuilder(object):
    def GetItem(self, generalSelector, index):
        if generalSelector.Selector == SingleFeatureSelector.CutPointSelector:
            if index == 0:
                return SingleValueItem(generalSelector.Dataset, generalSelector.Feature, LessOrEqualThan, generalSelector.CutPoint)
            elif index == 1:
                return SingleValueItem(generalSelector.Dataset, generalSelector.Feature, GreatherThan, generalSelector.CutPoint)
            else:
                raise Exception("Invalid index value for CutPointSelector")
        elif generalSelector.Selector == SingleFeatureSelector.ValueAndComplementSelector:
            if index == 0:
                return SingleValueItem(generalSelector.Dataset, generalSelector.Feature, EqualThan, generalSelector.Value)
            elif index == 1:
                return SingleValueItem(generalSelector.Dataset, generalSelector.Feature, DifferentThan, generalSelector.Value)
            else:
                raise Exception(
                    "Invalid index value for ValueAndComplementSelector")
        elif generalSelector.Selector == SingleFeatureSelector.MultipleValuesSelector:
            if index < 0 or index >= len(generalSelector.Values):
                raise Exception(
                    "Invalid index value for MultipleValuesSelector")
            return SingleValueItem(generalSelector.Dataset, generalSelector.Feature, EqualThan, generalSelector.Values[index])
        else:
            raise Exception(
                "Unknown selector")


def CompareSingleValueItems(left, right):
    if left.Feature == right.Feature:
        return left.CompareTo(right)
    return SubsetRelation.Unrelated
