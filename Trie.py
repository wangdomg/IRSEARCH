#!Python3
# -*- coding: utf-8 -*-
class TrieNode:
    def __init__(self):
        self.is_key = False  # 这个节点是否是变形的最后一个字符，只有当这个值为True的时候，下面的self.origin才不是None
        self.orgin = None  # 这个节点所存的变形的原形
        self.child = {}  # 这个节点的所有的孩子

class Trie:
    def __init__(self):
        self.root = TrieNode()

    # 输入是(变形, 原形)
    def addWord(self,word,origin):
        node =self.root
        for i in range(len(word)):
            if word[i] not in node.child:  # 这个前缀还没有存储
                node.child[word[i]] = TrieNode()
            node = node.child[word[i]]
        node.is_key = True  # 到达这个变形的最后一个字符了
        node.origin = origin  # 存储变形的原形

    # 返回list
    def search(self,word):
        node = self.root
        for i in range(len(word)):
            if word[i] not in node.child:
                return None
            node = node.child[word[i]]
        res=[]
        self.search_prefix(node,res)
        return res

    def search_prefix(self,root,res):
        if root.is_key:
            res.append(root.origin)  # 如果这个节点已经是某一个变形的最后一个字符，则将这个原形放进res中
        for key in root.child:  # 对于那些还没到变形的最后的一个字符的情况，则递归查找
            self.search_prefix(root.child[key],res)