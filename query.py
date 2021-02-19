import string

import nltk

stemmer = nltk.PorterStemmer()
translator = str.maketrans('', '', string.punctuation)


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
        return


class QueryTerm(Query):
    def __init__(self, term=""):
        super().__init__()
        self.term = stemmer.stem(term.strip().translate(translator).lower())

    def evaluate(self, inverted_index):
        _, docs = inverted_index.GetPostingListForTerm(self.term)
        return docs


class QueryOr(Query):
    def __init__(self, op1, op2):
        super().__init__()
        self.operand1 = op1
        self.operand2 = op2

    def evaluate(self, inverted_index):
        union = set()
        if not self.operand1.is_flipped and not self.operand2.is_flipped:
            union.add(self.operand1.evaluate())
            union.add(self.operand2.evaluate())
            # compute intersection
            return union


class QueryAnd(Query):
    def __init__(self, ops):
        super().__init__()
        self.ops = ops

    def evaluate(self, inverted_index):
        if len(self.ops) == 0:
            return []
        # TODO: sort ops by size, evaluate from small to large
        sets = [set(op.evaluate(inverted_index)) for op in self.ops]
        intersection = sets[0]
        for i in sets:
            intersection = intersection.intersection(i)
        return intersection


class QueryNot(Query):
    def __init__(self, op1):
        super().__init__()
        self.operand1 = op1
        self.is_flipped = not op1.is_flipped


# NOT brake

class QueryParser:
    @classmethod
    def parse(cls, query_string):
        # assuming no parentheses, TODO
        terms = query_string.split("AND")
        query_terms = []
        for term in terms:
            term = term.strip()
            query_terms.append(QueryTerm(term))
        return QueryAnd(query_terms)
