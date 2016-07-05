import random
from itertools import combinations

help_moneys = {"4": 5000, "5": 6000, "6": 4000, "7": 3000}
apply_moneys = {"1": 10000, "2": 2000, "3": 3000, "4": 5000}


def fenpei(apply_moneys, help_moneys):
    for uid, money in apply_moneys.items():
        a = list(combinations(help_moneys.keys(), 3))
        for i in a:
            if help_moneys[i[0]] + help_moneys[i[1]] + help_moneys[i[2]] == money:
                del apply_moneys[uid]
                print "uid:{0},money:{1};uid:{2},money:{3};;uid:{4},money:{5};".format(i[0], help_moneys[i[0]], i[1],
                                                                                       help_moneys[i[1]], i[2],
                                                                                       help_moneys[i[2]])
    for uid, money in apply_moneys.items():
        a = list(combinations(help_moneys.keys(), 2))
        for i in a:
            if help_moneys[i[0]] + help_moneys[i[1]] == money:
                del apply_moneys[uid]
                print "uid:{0},money:{1};uid:{2},money:{3};".format(i[0], help_moneys[i[0]], i[1], help_moneys[i[1]])
    for uid, money in apply_moneys.items():
        a = list(combinations(help_moneys.keys(), 1))
        for i in a:
            if help_moneys[i[0]] == money:
                del apply_moneys[uid]
                print "uid:{0},money:{1}".format(uid, money)

    print apply_moneys


if __name__ == "__main__":
    fenpei(apply_moneys, help_moneys)
