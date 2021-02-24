import string

import nltk

stemmer = nltk.PorterStemmer()
translator = str.maketrans('', '', string.punctuation)

# TODO: Add NOT functionality
# TODO: Optimise queries (skip pointers, size of postings, AND NOT)
# TODO: Create test data set to check correctness
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

    def __str__(self):
        return "Query"


class QueryTerm(Query):
    def __init__(self, term=""):
        super().__init__()
        self.term = stemmer.stem(term.strip().translate(translator).lower())

    def evaluate(self, inverted_index):
        # TODO maybe make this an iterator
        _, docs = inverted_index.GetPostingListForTerm(self.term)
        return set(docs)

    def __str__(self):
        return self.term


class QueryOr(Query):
    def __init__(self, ops):
        super().__init__()
        self.ops = ops

    def evaluate(self, inverted_index):
        union = self.ops[0].evaluate(inverted_index)
        # if not self.operand1.is_flipped and not self.operand2.is_flipped:
        for op in self.ops:
            union.update(op.evaluate(inverted_index))
        # compute intersection
        return union

    def __str__(self):
        return "∨".join([op.__str__() for op in self.ops])


class QueryAnd(Query):
    def __init__(self, ops):
        super().__init__()
        self.ops = ops

    def evaluate(self, inverted_index):
        if len(self.ops) == 0:
            return set()
        # TODO: sort ops by size, evaluate from small to large
        sets = [set(op.evaluate(inverted_index)) for op in self.ops]
        intersection = sets[0]
        for i in sets:
            intersection.intersection_update(i)
        return intersection

    def __str__(self):
        return "∧".join([op.__str__() for op in self.ops])


class QueryNot(Query):
    def __init__(self, op1:Query):
        super().__init__()
        self.operand1 = op1
        self.is_flipped = not op1.is_flipped
        # new_op = op1.copy()
        # new_op.is_flipped = not new_op.is_flipped
        # return new_op

    def evaluate(self, inverted_index):
        return self.operand1.evaluate(inverted_index)

    def __str__(self):
        return "¬{}".format(self.operand1)


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
        return QueryOr(root)