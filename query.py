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
        pass

    def toDNF(self):
        return Query()

    def evaluate(self, inverted_index):
        """
        Return a list of documents that satisfies the query
        """
        raise NotImplementedError("evaluate not implemented")

    def getSize(self, inverted_index):
        raise NotImplementedError("getSize not implemented")

    def __str__(self):
        return "Query"


class QueryTerm(Query):
    def __init__(self, term=""):
        super().__init__()
        self.term = stemmer.stem(term.strip().translate(translator).lower())

    def evaluate(self, inverted_index):
        # TODO maybe make this an iterator
        docs = inverted_index.GetPostingListForTerm(self.term)
        return docs

    def getSize(self, inverted_index):
        return inverted_index.GetSizeForTerm(self.term)

    def __str__(self):
        return self.term


class QueryOr(Query):
    def __init__(self, ops):
        super().__init__()
        self.ops = ops
        self.size = None

    def evaluate(self, inverted_index):
        union = set(self.ops[0].evaluate(inverted_index))
        # if not self.operand1.is_flipped and not self.operand2.is_flipped:
        for op in self.ops:
            curr_list = set(op.evaluate(inverted_index))
            union.update(curr_list)

        union = sorted(list(union))
        self.size = len(union)
        return union

    # Note: self.total_size of a Query obj can only be called after it's evaluate() has been called.
    def getSize(self, inverted_index):
        return self.size

    def __str__(self):
        return "∨".join([op.__str__() for op in self.ops])


class QueryAnd(Query):
    def __init__(self, ops):
        super().__init__()
        self.ops = ops
        self.total_size = None
        self.merged_list = None

    def evaluate(self, inverted_index):
        if len(self.ops) == 0:
            return []

        # Evaluate op first then call getSize()
        evaluated_op_list = [(op.evaluate(inverted_index), op.getSize(inverted_index)) for op in self.ops]
        # Sort by evaluated op size
        sorted_evaluated_op_list = sorted(evaluated_op_list, key=lambda x: x[1])

        # Only want to keep the evaluated operation list results
        # Discard op.getSize() value
        sorted_lists = [op[0] for op in sorted_evaluated_op_list]

        merged_list = sorted_lists[0]
        for each_list in sorted_lists:
            merged_list = self._mergeTwoLists(inverted_index, merged_list, each_list)

        self.total_size = len(merged_list)

        return merged_list

    def _mergeTwoLists(self, inverted_index, list1, list2):

        list1_skips = inverted_index.GetSkipPointers(list1)
        list2_skips = inverted_index.GetSkipPointers(list2)

        merged_list = []
        i = 0
        j = 0
        while i < len(list1) and j < len(list2):
            if list1[i] == list2[j]:
                merged_list.append(list1[i])
                i += 1
                j += 1
            elif list1[i] < list2[j]:
                next_i = list1_skips[i]
                if next_i != i and list1[next_i] < list2[j]:
                    i = next_i
                else:
                    i += 1
            else:
                next_j = list2_skips[j]
                if next_j != j and list2[next_j] < list1[i]:
                    j = next_j
                else:
                    j += 1

        return merged_list

    # Note: self.total_size of a Query obj can only be called after it's evaluate() has been called.
    def getSize(self, inverted_index):
        return self.total_size

    def __str__(self):
        return "∧".join([op.__str__() for op in self.ops])

class QueryAndNot(Query):
    def __init__(self, operand1, operand2):
        super().__init__()
        self.operand1 = operand1
        self.operand2 = operand2
        self.total_size = None
        self.merged_list = None

    def evaluate(self, inverted_index):
        if self.operand1 == None or self.operand2 == None:
            return []

        op1_list = self.operand1.evaluate(inverted_index)
        op2_list = self.operand2.evaluate(inverted_index)

        merged_list = sorted(set(op1_list).difference(set(op2_list)))
        self.total_size = len(merged_list)

        return merged_list

    def _mergeTwoLists(self, inverted_index, list1, list2):

        list1_skips = inverted_index.GetSkipPointers(list1)
        list2_skips = inverted_index.GetSkipPointers(list2)

        merged_list = []
        i = 0
        j = 0
        while i < len(list1) and j < len(list2):
            if list1[i] != list2[j]:
                merged_list.append(list1[i])

            if list1[i] < list2[j]:
                next_i = list1_skips[i]
                if next_i != i and list1[next_i] < list2[j]:
                    i = next_i
                else:
                    i += 1
            else:
                next_j = list2_skips[j]
                if next_j != j and list2[next_j] < list1[i]:
                    j = next_j
                else:
                    j += 1

        return merged_list

    # Note: self.total_size of a Query obj can only be called after it's evaluate() has been called.
    def getSize(self, inverted_index):
        return self.total_size

    def __str__(self):
        return "{}∧¬{}".format(self.operand1, self.operand2)

class QueryNot(Query):
    def __init__(self, op1:Query):
        super().__init__()
        self.operand1 = op1
        self.is_flipped = not op1.is_flipped
        self.size = None
        # new_op = op1.copy()
        # new_op.is_flipped = not new_op.is_flipped
        # return new_op

    def evaluate(self, inverted_index:InvertedIndex):
        # TODO remove temporary naive implementation
        matches = self.operand1.evaluate(inverted_index)
        diff = sorted(list(inverted_index.all_files.difference(matches)))
        self.size = sorted(list(inverted_index.all_files.difference(matches)))
        return diff

    def getSize(self, inverted_index):
        return self.size

    def __str__(self):
        return "¬{}".format(self.operand1)


class Token:
    AND_NOT = 0
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
                # Check if it is following AND
                if len(tokens)>0 and tokens[-1] == Token.AND:
                    tokens.pop() # Remove previous AND
                    tokens.append(Token.AND_NOT)
                else:
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
    def parse(cls, query_string: str):
        tokens = cls.tokenize(query_string)
        return cls._parse(tokens)

    @classmethod
    def _get_op(cls, op_token):
        if op_token == Token.NOT:
            return QueryNot
        elif op_token == Token.AND:
            return QueryAnd
        elif op_token == Token.OR:
            return QueryOr
        elif op_token == Token.AND_NOT:
            return QueryAndNot
        else:
            raise ValueError("No such op")


    @classmethod
    def _parse(cls, tokens):
        in_bracket = False
        current = []
        current_op = Token.AND
        root = [] # a list of Queries in DNF
        bracket_current = []
        negate_next = False

        for token in tokens:
            if in_bracket and token == Token.RB:
                subquery = cls._parse(bracket_current)

                if negate_next:
                    subquery = QueryNot(subquery)
                    negate_next = False

                if current_op == Token.AND_NOT:
                    prev = current.pop()
                    subquery = QueryAndNot(prev, subquery)
                    current_op = Token.AND

                current.append(subquery) # TODO fix this
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
            elif token == Token.AND_NOT:
                current_op = Token.AND_NOT
            else:  # query term
                query = QueryTerm(token)
                if negate_next:
                    query = QueryNot(query)
                    negate_next = False

                if current_op == Token.AND_NOT:
                    prev = current.pop()
                    query = QueryAndNot(prev, query)
                    current_op = Token.AND

                current.append(query)


        if len(current) > 1:
            root.append(QueryAnd(current))
        elif len(current) == 1:
            root.append(current[0])

        if len(root) == 1:
            return root[0]
        return QueryOr(root)