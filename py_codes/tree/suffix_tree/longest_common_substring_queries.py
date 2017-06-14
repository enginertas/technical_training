#!/usr/bin/env python

import sys

sys.setrecursionlimit(20000)

class STree():
    """
    Class representing the suffix tree.
    Taken from: https://github.com/ptrus/suffix-trees
    License: Apache
    """
    def __init__(self, input, q_array):
        self.root = _SNode()
        self.root.depth = 0
        self.root.idx = 0
        self.root.parent = self.root
        self.root._add_suffix_link(self.root)

        self._prepareQueryDict(q_array)
        self.build(input)

    def _prepareQueryDict(self, q_array):
        self.interested = set()
        self.query_dict = {}
        for x, y in q_array:
            if not self.query_dict.has_key(x):
                self.query_dict[x] = {}
            self.query_dict[x][y] = 0
            self.interested.add(y)

    def build(self, x):
        self._build_generalized(x)

    def _build(self, x):
        """Builds a Suffix tree by a single string"""
        self.word = x
        self._build_McCreight(x)

    def _build_McCreight(self, x):
        """Builds a Suffix tree using McCreight O(n) algorithm.
        Algorithm based on:
        McCreight, Edward M. "A space-economical suffix tree construction algorithm." - ACM, 1976.
        Implementation based on:
        UH CS - 58093 String Processing Algorithms Lecture Notes
        """
        u = self.root
        d = 0
        for i in xrange(len(x)):
            while u.depth == d and u._has_transition(x[d+i]):
                u = u._get_transition_link(x[d+i])
                d = d + 1
                while d < u.depth and x[u.idx + d] == x[i + d]:
                    d = d + 1
            if d < u.depth:
                u = self._create_node(x, u, d)
            self._create_leaf(x, i, u, d)
            if not u._get_suffix_link():
                self._compute_slink(x, u)
            u = u._get_suffix_link()
            d = d - 1
            if d < 0:
                d = 0

    def _create_node(self, x, u, d):
        i = u.idx
        p = u.parent
        v = _SNode(idx=i, depth=d)
        v._add_transition_link(u,x[i+d])
        u.parent = v
        p._add_transition_link(v, x[i+p.depth])
        v.parent = p
        return v

    def _create_leaf(self, x, i, u, d):
        w = _SNode()
        w.idx = i
        w.depth = len(x) - i
        u._add_transition_link(w, x[i + d])
        w.parent = u
        return w

    def _compute_slink(self, x, u):
        d = u.depth
        v = u.parent._get_suffix_link()
        while v.depth < d - 1:
            v = v._get_transition_link(x[u.idx + v.depth + 1])
        if v.depth > d - 1:
            v = self._create_node(x, v, d-1)
        u._add_suffix_link(v)

    def _build_generalized(self, xs):
        """Builds a Generalized Suffix Tree (GST) from the array of strings provided.
        """
        terminal_gen = self._terminalSymbolsGenerator()

        _xs = ''.join([x + next(terminal_gen) for x in xs])

        self.word = _xs
        self._generalized_word_starts(xs)
        self._build(_xs)
        self.root._traverse(self._label_generalized)

    def _label_generalized(self, node):
        """Helper method that labels the nodes of GST with indexes of strings
        found in their descendants.
        """
        if node.is_leaf():
            index = self.word_start_index_dict[node.idx]
            if index in self.interested or index in self.query_dict:
                x = {index}
            else:
                x = {}
        else:
            x = {n for ns in node.transition_links for n in ns.generalized_idxs}
            for el in x:
                if el in self.query_dict:
                    q = self.query_dict[el]
                    for comp in q:
                        if (comp in x) and node.depth > q[comp]:
                            q[comp] = node.depth

        node.generalized_idxs = x

    def lcs_len(self, x, y):
        return self.query_dict[x][y]

    def _generalized_word_starts(self, xs):
        """Helper method returns the starting indexes of strings in GST"""
        self.word_starts = []
        i = 0
        for n in xrange(len(xs)):
            self.word_starts.append(i)
            i += len(xs[n]) + 1

        j = 1
        self.word_start_index_dict = [0] * len(self.word)
        for i in xrange(self.word_starts[-1]):
            if i == self.word_starts[j]:
                j += 1
            self.word_start_index_dict[i] = j - 1

        for i in xrange(self.word_starts[-1], len(self.word)):
            self.word_start_index_dict[i] = len(self.word_starts) - 1


    def _terminalSymbolsGenerator(self):
        """Generator of unique terminal symbols used for building the Generalized Suffix Tree.
        Unicode Private Use Area U+E000..U+F8FF is used to ensure that terminal symbols
        are not part of the input string.
        """
        UPPAs = list(list(range(0xE000,0xF8FF+1)) + list(range(0xF0000,0xFFFFD+1)) + list(range(0x100000, 0x10FFFD+1)))
        for i in UPPAs:
            yield(unichr(i))


class _SNode():
    """Class representing a Node in the Suffix tree."""
    def __init__(self, idx=-1, parentNode=None, depth=-1):
        self._suffix_link = None
        self.transition_links = []
        self.transition_dict = {}
        self.idx = idx
        self.depth = depth
        self.parent = parentNode
        self.generalized_idxs = {}

    def _add_suffix_link(self, snode):
        self._suffix_link = snode

    def _get_suffix_link(self):
        if self._suffix_link != None:
            return self._suffix_link
        else:
            return False

    def _get_transition_link_index(self, suffix):
        if self.transition_dict.has_key(suffix):
            return self.transition_dict[suffix]

        return None

    def _get_transition_link(self, suffix):
        index = self._get_transition_link_index(suffix)
        if index != None:
            return self.transition_links[index]
        else:
            return False

    def _add_transition_link(self, snode, suffix=''):
        tl = self._get_transition_link_index(suffix)
        if tl != None:
            self.transition_links[tl] = snode
        else:
            self.transition_dict[suffix] = len(self.transition_links)
            self.transition_links.append(snode)

    def _has_transition(self, suffix):
        return self.transition_dict.has_key(suffix)

    def is_leaf(self):
        return self.transition_links == []

    def _traverse(self, f):
        for node in self.transition_links:
            node._traverse(f)
        f(self)


def readInput():
    n,q = map(int, raw_input().strip().split())

    unique_dict = {}
    translate = {}
    arr = []
    for i in xrange(n):
        s = raw_input().strip()
        if s in unique_dict:
            translate[i] = unique_dict[s]
        else:
            unique_dict[s] = len(arr)
            translate[i] = len(arr)
            arr.append(s)

    queries = []
    for i in xrange(q):
        x, y = map(int, raw_input().strip().split())
        x, y = translate[x], translate[y]
        queries.append((min(x, y), max(x, y)))
       
    s_tree = STree(arr, queries)
    for x, y in queries:
        if x == y:
            print len(arr[x])
        else:
            print s_tree.lcs_len(x, y)

if __name__ == "__main__":
	readInput()

	    
