import string

import nltk

from inverted_index import InvertedIndex

stemmer = nltk.PorterStemmer()
translator = str.maketrans('', '', string.punctuation)


# TODO: Add NOT functionality
# TODO: Optimise queries (skip pointers, size of postings, AND NOT) - done skip pointers and size of posting
# TODO: Create test data set to check correctness - partially done...

class Query:
    def __init__(self):
        self.is_flipped = False
        self.is_primitive = False
        pass

    def toDNF(self):
        return Query()

    def evaluate(self, inverted_index):
        """
        Return a list of documents that satisfies the query
        """
        raise NotImplementedError("evaluate not implemented")

    def get_size(self, inverted_index):
        raise NotImplementedError("getSize not implemented")

    def __str__(self):
        return "Query"


class QueryTerm(Query):
    def __init__(self, term=""):
        super().__init__()
        self.is_primitive = True
        self.term = stemmer.stem(term.strip().translate(translator).lower())

    def evaluate(self, inverted_index):
        # TODO maybe make this an iterator
        docs = inverted_index.get_posting_list_for_term(self.term)
        return docs

    def get_size(self, inverted_index):
        return inverted_index.get_size_for_term(self.term)

    def __str__(self):
        return self.term


class QueryOr(Query):
    def __init__(self, ops):
        super().__init__()
        self.ops = ops
        self.union = None
        self.size = None

    def evaluate(self, inverted_index):
        if self.union == None:
            # Don't evaluate more than once
            self.size, self.union = self._evaluate(inverted_index)

        return self.union

    def _evaluate(self, inverted_index):
        # TODO: is there a better way?
        # Convert evaluate output to set
        # then compute union and convert back to sorted list
        union = set(self.ops[0].evaluate(inverted_index))
        # if not self.operand1.is_flipped and not self.operand2.is_flipped:
        for op in self.ops:
            curr_list = set(op.evaluate(inverted_index))
            union.update(curr_list)

        return len(union), sorted(list(union))

    def get_size(self, inverted_index):
        if self.size == None:
            # Don't evaluate more than once
            self.size, self.union = self._evaluate(inverted_index)
        return self.size

    def __str__(self):
        return "∨".join([op.__str__() for op in self.ops])


class QueryAnd(Query):
    def __init__(self, ops):
        super().__init__()
        self.ops = ops
        self.ops_size = {}  # Dictionary to hold [op: size]
        self.total_size = None

    def evaluate(self, inverted_index):
        if len(self.ops) == 0:
            return []

        if len(self.ops_size) == 0:
            # While computing the size, the func fills up self.ops_size dict
            self.get_size(inverted_index)

        # Sort ops by size, evaluate from small to large
        sorted_ops = sorted(self.ops_size.items(), key=lambda x: x[1])
        lists = [list(op[0].evaluate(inverted_index)) for op in sorted_ops]
        merged_list = lists[0]
        for each_list in lists:
            merged_list = self.merge_two_lists(inverted_index, merged_list, each_list)

        self.total_size = len(merged_list)
        return merged_list

    def merge_two_lists(self, invertedIndex, list1, list2):
        # list1_skips = invertedIndex.get_skip_pointers(list1)
        # list2_skips = invertedIndex.get_skip_pointers(list2)
        # list1_skips = []
        # list2_skips = []

        merged_list = []
        i = 0
        j = 0
        a, b = len(list1), len(list2)  # cache list sizes to save on repeated invocations of len(list)
        while i < a and j < b:
            if list1[i] == list2[j]:
                merged_list.append(list1[i])
                i += 1
                j += 1
            elif list1[i] < list2[j]:
                # next_i = list1_skips[i]
                # if next_i != i and list1[next_i] < list2[j]:
                #     i = next_i
                # else:
                i += 1
            else:
                # next_j = list2_skips[j]
                # if next_j != j and list2[next_j] < list1[i]:
                #     j = next_j
                # else:
                j += 1

        return merged_list

    # TODO: Double check this total_size
    def get_size(self, inverted_index):
        self.total_size = 0
        for op in self.ops:
            curr_size = op.get_size(inverted_index)
            self.ops_size[op] = curr_size
            self.total_size += curr_size

        # Return self.total_size when this particular QueryAND has been evaluated and this getSize method
        # is called by another Query obj.
        # Otherwise, it means getSize was called by the current QueryAnd obj and we return self.total_size which evaluates
        # to None. In this case, the total_size val is not used and we aare actually only concerned with populating self.ops_size.
        return self.total_size

    def __str__(self):
        return "∧".join([op.__str__() for op in self.ops])


class QueryNot(Query):
    def __init__(self, op: Query):
        super().__init__()
        self.is_primitive = op.is_primitive
        self.op = op
        self.is_flipped = not op.is_flipped

    def evaluate(self, inverted_index: InvertedIndex):
        # TODO remove temporary naive implementation
        matches = self.op.evaluate(inverted_index)
        return inverted_index.all_files.difference(matches)

    def get_size(self, inverted_index):
        return self.op.get_size(inverted_index)

    def __str__(self):
        return "¬{}".format(self.op)


class Token:
    AND = 1
    OR = 2
    NOT = 3
    LB = 4
    RB = 5


class QueryParser:
    @classmethod
    def tokenize(cls, query_string: str):
        tokens = []
        for chunk in query_string.split(" "):
            chunk = chunk.strip()
            if chunk == "":
                continue
            elif chunk == "AND":
                tokens.append(Token.AND)
            elif chunk == "OR":
                tokens.append(Token.OR)
            elif chunk == "NOT":
                tokens.append(Token.NOT)
            elif chunk[0] == "(":
                tokens.append(Token.LB)
                rb = chunk.find(")")
                remaining = chunk[1:].strip()
                if rb != -1:
                    remaining = chunk[1:rb].strip()
                    tokens.append(remaining)
                    tokens.append(Token.RB)
                elif len(remaining) > 0:
                    tokens.append(remaining)
            elif chunk[-1] == ")":
                remaining = chunk[:-1].strip()
                if len(remaining) > 0:
                    tokens.append(remaining)
                tokens.append(Token.RB)
            else:
                tokens.append(chunk)
        return tokens

    # Z AND A OR (B AND C) OR (D OR E)
    @classmethod
    def parse(cls, query_string: str, use_sh: bool = False):
        tokens = cls.tokenize(query_string)
        if use_sh:
            return cls._parse_sh(tokens)
        return cls._parse(tokens)

    @classmethod
    def _get_op(cls, op_token):
        if op_token == Token.NOT:
            return QueryNot
        elif op_token == Token.AND:
            return QueryAnd
        elif op_token == Token.OR:
            return QueryOr
        else:
            raise ValueError("No such op")

    @classmethod
    def _get_precedence(self, op_token):
        if op_token == Token.AND:
            return 1
        if op_token == Token.OR:
            return 2
        return -1

    @classmethod
    def _parse_sh(cls, tokens):
        ops = []
        opr = []
        in_bracket = False
        bracket_current = []
        negate_next = False

        for token in tokens:
            if in_bracket and token == Token.RB:
                subquery = cls._parse_sh(bracket_current)
                if negate_next:
                    subquery = QueryNot(subquery)
                    negate_next = False
                opr.append(subquery)
                bracket_current = []
                in_bracket = False
            elif token == Token.LB:
                in_bracket = True
            elif in_bracket:
                bracket_current.append(token)
            elif token == Token.NOT:
                negate_next = not negate_next
            elif token == Token.AND or token == Token.OR:
                # ops.append(token)
                if len(ops) > 0 and cls._get_precedence(token) >= cls._get_precedence(ops[-1]):
                    operands = [opr.pop(), opr.pop()]
                    op = cls._get_op(ops.pop())(operands)
                    opr.append(op)
                ops.append(token)
            else:  # query term
                query = QueryTerm(token)
                if negate_next:
                    query = QueryNot(query)
                    negate_next = False
                opr.append(query)

        while len(ops) > 0:
            operands = [opr.pop(), opr.pop()]
            op = cls._get_op(ops.pop())(operands)
            opr.append(op)
        return opr.pop()

    @classmethod
    def _parse(cls, tokens):
        in_bracket = False
        current = []
        current_op = Token.AND
        root = []  # a list of Queries in DNF
        bracket_current = []
        negate_next = False

        for token in tokens:
            if in_bracket and token == Token.RB:
                subquery = cls._parse(bracket_current)
                if negate_next:
                    subquery = QueryNot(subquery)
                    negate_next = False
                current.append(subquery)  # TODO fix this
                bracket_current = []
                in_bracket = False
            elif token == Token.LB:
                in_bracket = True
            elif in_bracket:
                bracket_current.append(token)
            elif token == Token.AND:
                current_op = Token.AND
            elif token == Token.OR:
                if len(current) > 1:
                    root.append(QueryAnd(current))
                elif len(current) == 1:
                    root.append(current[0])
                current = []
                current_op = Token.OR
            elif token == Token.NOT:
                negate_next = not negate_next
            else:  # query term
                query = QueryTerm(token)
                if negate_next:
                    query = QueryNot(query)
                    negate_next = False
                current.append(query)

        if len(current) > 1:
            root.append(QueryAnd(current))
        elif len(current) == 1:
            root.append(current[0])

        if len(root) == 1:
            return root[0]
        return QueryOr(root)
