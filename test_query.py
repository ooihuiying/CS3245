#!/usr/bin/python3
import re
import string

import nltk
import sys
import getopt

from inverted_index import InvertedIndex
from query import QueryParser


# Program Arguments:
# -d test-dictionary.txt -p test-postings.txt

def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file")


def TestSingleQuery(inverted_index_class):
    query = QueryParser.parse("a")
    assert query.__str__() == 'a'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [0]

    query = QueryParser.parse("(a)")
    assert query.__str__() == 'a'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [0]


def TestAndQueries(inverted_index_class):

    # Single AND
    query = QueryParser.parse("a AND b")
    assert query.__str__() == 'b∧a'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [0]

    # Test Stemming of query
    query = QueryParser.parse("(A AND r)")
    assert query.__str__() == 'r∧a'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert len(posting_list) == 0


    # Test longer AND query
    query = QueryParser.parse("(a AND c) AND (x AND y)")
    assert query.__str__() == 'y∧x∧c∧a'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [0]


    # Test longer AND query
    query = QueryParser.parse("(x AND y) AND (v AND z) AND (u AND z)")
    assert query.__str__() == 'z∧u∧z∧v∧y∧x'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [0, 1]

    # Test query for non-existing terms
    query = QueryParser.parse("(abc AND r)")
    assert query.__str__() == 'r∧abc'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert len(posting_list) == 0


def TestOrQueries(inverted_index_class):
    # Single OR
    query = QueryParser.parse("a OR z")
    assert query.__str__() == 'z∨a'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [0, 1, 2]

    # Test Stemming of query
    query = QueryParser.parse("(A OR r)")
    assert query.__str__() == 'r∨a'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [0, 1]

    # Test longer OR query
    query = QueryParser.parse("(a OR b) OR (r OR a)")
    assert query.__str__() == 'a∨r∨b∨a'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [0, 1]

    # Test longer OR query
    query = QueryParser.parse("(a OR b) OR (r OR a) OR (b OR z)")
    assert query.__str__() == 'z∨b∨a∨r∨b∨a'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [0, 1, 2]

    # Test query for non-existing terms
    query = QueryParser.parse("(abc OR r)")
    assert query.__str__() == 'r∨abc'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [1]


def TestNotQueries(inverted_index_class):
    # Single NOT
    query = QueryParser.parse("NOT z")
    assert query.__str__() == '¬z'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [3]

    # Single And Not
    query = QueryParser.parse("a AND NOT z")
    assert query.__str__() == '¬z∧a'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert len(posting_list) == 0

    # Longer And Not
    query = QueryParser.parse("(y AND z) AND NOT (a OR r)")
    assert query.__str__() == '¬r∨a∧z∧y'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [2]

    # And Not with Term and with Query
    query = QueryParser.parse("(y AND NOT z) AND NOT (a OR r)")
    assert query.__str__() == '¬r∨a∧¬z∧y'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert len(posting_list) == 0

    query = QueryParser.parse("(y AND NOT a) AND NOT (b)")
    assert query.__str__() == '¬b∧¬a∧y'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [1, 2]

    query = QueryParser.parse("NOT (y AND NOT a) AND NOT (r)")
    assert query.__str__() == '¬r∧¬¬a∧y'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [0, 3]

    # Not in front of And Not
    query = QueryParser.parse("NOT s AND NOT a")
    assert query.__str__() == '¬a∧¬s'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [2, 3]

    query = QueryParser.parse("NOT (s AND NOT a)")
    assert query.__str__() == '¬¬a∧s'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [0, 2, 3]

    # And Not in front of Not
    query = QueryParser.parse("z AND NOT NOT bb")
    assert query.__str__() == 'bb∧z'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [2]
    return False

    query = QueryParser.parse("z AND NOT (NOT bb)")
    assert query.__str__() == '¬¬bb∧z'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [2]
    return False

def TestMixQueries(inverted_index_class):
    query = QueryParser.parse("(a OR r) AND (r AND z)")
    assert query.__str__() == 'z∧r∧r∨a'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [1]

    query = QueryParser.parse("(a AND r) OR (p AND q) OR (n AND x)")
    assert query.__str__() == 'x∧n∨q∧p∨r∧a'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [0, 1]

    query = QueryParser.parse("(a) OR (aa AND z) AND (n AND x)")
    assert query.__str__() == 'x∧n∧z∧aa∨a'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [0]

    query = QueryParser.parse("(a) OR (aa AND x) AND (bb AND y)")
    assert query.__str__() == 'y∧bb∧x∧aa∨a'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [0, 2]

    query = QueryParser.parse("aa AND dd AND ee OR b")
    assert query.__str__() == 'b∨ee∧dd∧aa'
    posting_list = query.evaluate(inverted_index_class, forced=True)
    assert posting_list == [0, 3]


def run_test(dict_file, postings_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """

    print('Running test...')
    # Create index
    inverted_index_class = InvertedIndex("Tests/data", dict_file, postings_file)
    inverted_index_class.construct_index()

    # Query index
    inverted_index_class_done = InvertedIndex("", dict_file, postings_file)

    TestSingleQuery(inverted_index_class_done)

    TestAndQueries(inverted_index_class_done)

    TestOrQueries(inverted_index_class_done)

    TestNotQueries(inverted_index_class_done)

    TestMixQueries(inverted_index_class_done)

    # Maybe can test for invalid queries


dictionary_file = postings_file = file_of_queries = output_file_of_results = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file = a
    elif o == '-p':
        postings_file = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None:
    usage()
    sys.exit(2)

run_test(dictionary_file, postings_file)
