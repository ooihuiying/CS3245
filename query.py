import string
from math import ceil, sqrt
import nltk

from inverted_index import InvertedIndex

stemmer = nltk.PorterStemmer()
translator = str.maketrans('', '', string.punctuation)

class Query:
    def __init__(self):
        self.is_flipped = False
        self.is_primitive = False
        pass

    def evaluate(self, inverted_index, forced=False):
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

    def evaluate(self, inverted_index, forced=False):
        """
        Returns a list of integers
        """
        docs = [int(op.split(";")[0]) for op in inverted_index.get_posting_list_for_term(self.term)]
        return docs

    def _evaluate(self, inverted_index):
        """
        Returns a list of tuples (curr, next) where curr is the doc_id and next is the value of the next skip val if exist.
        Otherwise, next will be -1 if no skip is allowed for that doc.
        """
        docs = []
        for op in inverted_index.get_posting_list_for_term(self.term):
            split_op = op.split(";")
            curr = split_op[0]
            next = -1
            if len(split_op) == 2:
                next = split_op[1]
            docs.append((int(curr), int(next)))
        return docs

    def get_size(self, inverted_index):
        return inverted_index.get_size_for_term(self.term)

    def __str__(self):
        return self.term


class QueryOr(Query):
    def __init__(self, ops):
        super().__init__()
        self.ops = ops
        self.ops = self._flatten_ops()
        self.size = None

    def _flatten_ops(self):
        ops = []
        for op in self.ops:
            if isinstance(op, QueryOr):
                for _op in op._flatten_ops():
                    ops.append(_op)
            else:
                ops.append(op)

        return ops

    def evaluate(self, inverted_index, forced=False):
        ops = [set(op.evaluate(inverted_index, forced=True)) for op in self.ops]
        union = ops[0]
        for op in ops[1:]:
            union.update(op)

        union = sorted(list(union))
        self.size = len(union)

        return union

    def get_size(self, inverted_index):
        return self.size

    def __str__(self):
        return "∨".join([op.__str__() for op in self.ops])

class QueryAnd(Query):
    def __init__(self, ops):
        super().__init__()
        self.size = None
        self.ops = ops
        self.ops = self._flatten_ops()

    def _flatten_ops(self):
        ops = []
        for op in self.ops:
            if isinstance(op, QueryAnd):
                for _op in op._flatten_ops():
                    ops.append(_op)
            else:
                ops.append(op)

        return ops

    def evaluate(self, inverted_index, **kwargs):

        add_ops = [] # Format of each list item:(curr, next)
        for op in self.ops:
            if not op.is_flipped:
                if op.is_primitive:
                    #isinstance(op, QueryTerm)
                    add_ops.append((op._evaluate(inverted_index), op.get_size(inverted_index)))
                else:
                    list_ops = [(x, -1) for x in op.evaluate(inverted_index)]
                    add_ops.append((list_ops, op.get_size(inverted_index)))

        negate_ops = [set(op.evaluate(inverted_index)) for op in self.ops if op.is_flipped]

        # case 1, all negate
        if len(add_ops) == 0:
            merged = negate_ops[0]
            for op in negate_ops[1:]:
                merged.update(op)
            all_negate = list(sorted(inverted_index.all_files.difference(merged)))
            self.size = len(all_negate)
            return all_negate  # todo can still be improved
        else:
            # Sort by evaluated op size
            add_ops = sorted(add_ops, key=lambda x: x[1])

            if len(add_ops) > 1:
                # We have to merge more than 1 list
                merged_ops = add_ops[0][0]
                merged_list_size = add_ops[0][1]
                for each_list in add_ops[1:]:
                    merged_ops = self.merge_two_lists(merged_ops, each_list[0], merged_list_size, each_list[1])
                    merged_list_size = 0 # The merged list will have no skip pointers, hence 0 jumps
                merged = [x[0] for x in merged_ops]
            else:
                # Case where we only have 1 list in add_ops
                merged = [x[0] for x in add_ops[0][0]]

            # case 2, all add
            if len(negate_ops) == 0:
                self.size = len(merged)
                return merged

            # case 3, some add, some negate
            merged = set(merged)
            for op in negate_ops:
                merged = merged - op
            diff = list(sorted(merged))
            self.size = len(diff)
            return diff

    def merge_two_lists(self, list1, list2, list1_size, list2_size):
        """
            Takes in 2 lists.
            Each list contains items of the format : (curr_doc_id, next_doc_id) where next_doc_id is the next skip
            The output is a single list of the same format
        """
        jump_1 = ceil(sqrt(list1_size))
        jump_2 = ceil(sqrt(list2_size))

        if list1_size == 0:
            list1_size = len(list1)

        merged_list = []
        i = 0
        j = 0

        while i < list1_size and j < list2_size:
            item_1 = list1[i]
            item_2 = list2[j]
            if item_1[0] == item_2[0]:
                merged_list.append(item_1)
                i += 1
                j += 1
            elif item_1[0] < item_2[0]:
                # Has skip pointer
                if item_1[1] != -1 and item_1[1] < item_2[0]:
                    i += jump_1
                else:
                    i += 1
            else:
                # Has skip pointer
                if item_2[1] != -1 and item_2[1] < item_1[0]:
                    j += jump_2
                else:
                    j += 1

        return merged_list

    def get_size(self, inverted_index):
        return self.size

    def __str__(self):
        return "∧".join([op.__str__() for op in self.ops])

class QueryNot(Query):
    def __init__(self, op: Query):
        super().__init__()
        self.is_primitive = op.is_primitive
        self.op = op
        self.is_flipped = not op.is_flipped
        self.size = None

    def evaluate(self, inverted_index: InvertedIndex, forced=False):
        matches = self.op.evaluate(inverted_index)
        if forced:
            diff = list(inverted_index.all_files.difference(matches))
            self.size = len(diff)
            return diff
        else:
            self.size = len(matches)
            return matches

    def get_size(self, inverted_index):
        return self.size

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
        lb = query_string.find("(")
        if lb != -1:
            rb = query_string.find(")")
            if rb == -1:
                raise Exception("Missing closing bracket in chunk {}".format(query_string))
            return cls.tokenize(query_string[:lb]) + [Token.LB] + cls.tokenize(query_string[lb+1:rb]) + [Token.RB] + cls.tokenize(query_string[rb+1:])

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
            else:
                tokens.append(chunk)
        return tokens

    # Z AND A OR (B AND C) OR (D OR E)
    @classmethod
    def parse(cls, query_string: str, use_sh: bool = False):
        tokens = cls.tokenize(query_string)
        # if use_sh:
        #     return cls._parse_sh(tokens)
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
    def _parse(cls, tokens):
        ops = []
        opr = []
        in_bracket = False
        bracket_current = []
        negate_next = False

        for token in tokens:
            if in_bracket and token == Token.RB:
                subquery = cls._parse(bracket_current)
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
