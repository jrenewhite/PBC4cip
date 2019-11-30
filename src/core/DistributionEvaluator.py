import math
import sys


def Hellinger(parent, children):
    # region Preconditions
    if len(children) != 2:
        raise Exception(
            "Hellinger Distance need only two child nodes (binary split)")

    if sum(parent) == max(parent):
        return 0
    # endregion

    s1p = math.sqrt(children[0][0] / parent[0])
    s1n = math.sqrt(children[0][1] / parent[1])

    s2p = math.sqrt(children[1][0] / parent[0])
    s2n = math.sqrt(children[1][1] / parent[1])

    result = math.sqrt(math.pow(s1p - s1n, 2) + math.pow(s2p - s2n, 2))

    return result


def MultiClassHellinger(parent, children):
    # region Preconditions
    if len(children) != 2:
        raise Exception(
            "Hellinger Distance need only two child nodes (binary split)")

    if sum(parent) == max(parent):
        return 0
    # endregion

    hellinger = sys.float_info.min

    try:
        for i in range(len(parent)):
            tn = SumDifferent(parent, i)

            s1p = math.sqrt(children[0][i] / parent[i])
            s1n = math.sqrt(SumDifferent(children[0], i) / tn)
            s2p = math.sqrt(children[1][i] / parent[i])
            s2n = math.sqrt(SumDifferent(children[1], i) / tn)

            currentValue = math.pow(s1p - s1n, 2) + math.pow(s2p - s2n, 2)
            if currentValue > hellinger:
                hellinger = currentValue
    except ZeroDivisionError:
        return sys.float_info.max

    return math.sqrt(hellinger)


def SumDifferent(vector, index):
    sumValue = 0
    for i in range(len(vector)):
        if index != i:
            sumValue += vector[i]
    return sumValue
