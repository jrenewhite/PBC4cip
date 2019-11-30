import math


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
