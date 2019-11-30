import math


class DecisionTree(object):

    def __init__(self, dataset):
        self.Model = dataset.Model
        self.TreeRootNode = None

    @property
    def Size(self):
        if not self.TreeRootNode:
            return 0
        else:
            return self.ComputeSizeTree(self.TreeRootNode)

    @property
    def Leaves(self):
        if not self.TreeRootNode:
            return 0
        else:
            return self.ComputeLeaves(self.TreeRootNode)

    def ComputeSizeTree(self, treeRootNode):
        if not treeRootNode.Children:
            return 0
        else:
            return max(map(lambda child: self.ComputeSizeTree(child), treeRootNode.Children))+1

    def ComputeLeaves(self, treeRootNode):
        if treeRootNode.IsLeaf:
            return 1
        else:
            return sum(map(lambda child: self.ComputeLeaves(child), treeRootNode.Children))


class DecisionTreeNode(object):

    def __init__(self):
        self.Data = []
        self.Parent = None
        self.ChildSelector = None
        self.Children = []

    @property
    def IsLeaf(self):
        return (not self.Children or len(self.Children) == 0)

    def __format__(self, ident):
        result = self.__repr__()

        if not self.IsLeaf:
            for child in range(len(self.Children)):
                if self.Children[child].Data:
                    childSelector = self.ChildSelector
                    curChild = self.Children[child]
                    result = f"{result}\n{' '*((ident+1)*3)}- {childSelector.__format__(child)} {curChild.__format__(ident+1)}"

        return result

    def __repr__(self):
        if not self.ChildSelector:
            return f"[{', '.join(map(str, self.Data))}]"
        else:
            return f"[{', '.join(map(str, self.Data))}] - {self.ChildSelector}"
