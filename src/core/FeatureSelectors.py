import math

# region Single feature selectors


class SingleFeatureSelector(object):
    def __init__(self, dataset, feature):
        self.ChildrenCount = 2
        self.Dataset = dataset
        self.Model = dataset.Model
        self.Feature = feature

    def Select(self, instance):
        if self.Dataset.IsMissing(self.Feature, instance):
            return None

    def __format__(self, index):
        return self.__repr__()

    def __repr__(self):
        return f"¿[{self.Feature[0]}]?"


class CutPointSelector(SingleFeatureSelector):
    def __init__(self, dataset, feature):
        super().__init__(dataset, feature)
        self.CutPoint = math.nan

    def Select(self, instance):
        super().Select(instance)
        if self.Dataset.IsNominalFeature(self.Feature):
            raise Exception("Cannot use cutpoint on nominal data")
        if self.Dataset.GetFeatureValue(self.Feature, instance) <= self.CutPoint:
            return [1, 0]
        else:
            return [0, 1]

    def __format__(self, index):
        if index == 0:
            return f"{self.Feature[0]}<={self.CutPoint}"
        else:
            return f"{self.Feature[0]}>{self.CutPoint}"

    def __repr__(self):
        return f"{self.Feature[0]}<={self.CutPoint}"


class MultipleValuesSelector(SingleFeatureSelector):
    def __init__(self, dataset, feature):
        super().__init__(dataset, feature)
        self.Values = []

    def Select(self, instance):
        super().Select(instance)
        if not self.Dataset.IsNominalFeature(self.Feature):
            raise Exception("Cannot use multiple values on non-nominal data")
        value = self.Dataset.GetFeatureValue(self.Feature, instance)
        index = self.Values.index(value)
        if index == -1:
            return None
        result = [0]*self.ChildrenCount
        result[index] = 1
        return result

    def __format__(self, index):
        return f"{self.Feature[0]}={self.Dataset.GetValueOfIndex(self.Feature[0],index)}"

    def __repr__(self):
        return f"{self.Feature[0]}in[{', '.join(map(lambda value: self.Dataset.GetValueOfIndex(self.Feature[0],value),self.Values))}]"


class ValueAndComplementSelector(SingleFeatureSelector):
    def __init__(self, dataset, feature):
        super().__init__(dataset, feature)
        self.Value = math.nan

    def Select(self, instance):
        super().Select(instance)
        if not self.Dataset.IsNominalFeature(self.Feature):
            raise Exception("Cannot use multiple values on non-nominal data")
        if self.Dataset.GetFeatureValue(self.Feature, instance) == self.Value:
            return [1, 0]
        else:
            return [0, 1]

    def __format__(self, index):
        if index == 0:
            return f"{self.Feature[0]}={self.Dataset.GetValueOfIndex(self.Feature[0],self.Value)}"
        else:
            return f"{self.Feature[0]}<>{self.Dataset.GetValueOfIndex(self.Feature[0],self.Value)}"

    def __repr__(self):
        return f"{self.Feature[0]}={self.Dataset.GetValueOfIndex(self.Feature[0],self.Value)}"

# endregion


# region Multiple feature selectors


class MultipleFeaturesSelector(object):
    def __init__(self, dataset, features):
        self.ChildrenCount = 2
        self.Dataset = dataset
        self.Model = dataset.Model
        self.Features = features

    def Select(self, instance):
        if any(self.Dataset.IsMissing(feature, instance) for feature in self.Features):
            return None

    def __format__(self, index):
        return self.__repr__()

    def __repr__(self):
        linearCombination = ' + '.join(
            map(lambda feature: "1.0 * " + feature[0], self.Features))
        return f"¿[{linearCombination}]?"


class MultivariateCutPointSelector(MultipleFeaturesSelector):
    def __init__(self, dataset, feature):
        super().__init__(dataset, feature)
        self.CutPoint = math.nan
        self.Weights = None

    def Select(self, instance):
        super().Select(instance)
        if any(self.Dataset.IsNominalFeature(feature) for feature in self.Features):
            raise Exception("Cannot use cutpoint on nominal data")
        if self.Dataset.ScalarProjection(
                instance, self.Features, self.Weights) <= self.CutPoint:
            return [1, 0]
        else:
            return [0, 1]

    def __format__(self, index):
        linearCombination = ' + '.join(
            map(lambda weight: str(self.Weights[weight]) + " * " + weight[0], self.Weights))
        if index == 0:
            return f"{linearCombination}<={self.CutPoint}"
        else:
            return f"{linearCombination}>{self.CutPoint}"

    def __repr__(self):
        linearCombination = ' + '.join(
            map(lambda weight: str(self.Weights[weight]) + " * " + weight[0], self.Weights))
        return f"{linearCombination}<={self.CutPoint}"

# endregion
