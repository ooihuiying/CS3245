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

    query = QueryParser.Parse("a")
    assert query.__str__() == 'a'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [0]

    query = QueryParser.Parse("(a)")
    assert query.__str__() == 'a'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [0]

def TestAndQueries(inverted_index_class):

    # Single AND
    query = QueryParser.Parse("a AND b")
    assert query.__str__() == 'a∧b'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [0]

    # Test Stemming of query
    query = QueryParser.Parse("(A AND r)")
    assert query.__str__() == 'a∧r'
    posting_list = query.Evaluate(inverted_index_class)
    assert len(posting_list) == 0

    # Test longer AND query
    query = QueryParser.Parse("(a AND c) AND (x AND y)")
    assert query.__str__() == 'a∧c∧x∧y'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [0]

    # Test longer AND query
    query = QueryParser.Parse("(x AND y) AND (v AND z) AND (u AND z)")
    assert query.__str__() == 'x∧y∧v∧z∧u∧z'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [0, 1]

    # Test query for non-existing terms
    query = QueryParser.Parse("(abc AND r)")
    assert query.__str__() == 'abc∧r'
    posting_list = query.Evaluate(inverted_index_class)
    assert len(posting_list) == 0

def TestOrQueries(inverted_index_class):
    # Single OR
    query = QueryParser.Parse("a OR z")
    assert query.__str__() == 'a∨z'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [0, 1, 2]

    # Test Stemming of query
    query = QueryParser.Parse("(A OR r)")
    assert query.__str__() == 'a∨r'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [0, 1]

    # Test longer OR query
    query = QueryParser.Parse("(a OR b) OR (r OR a)")
    assert query.__str__() == 'a∨b∨r∨a'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [0, 1]

    # Test longer OR query
    query = QueryParser.Parse("(a OR b) OR (r OR a) OR (b OR z)")
    assert query.__str__() == 'a∨b∨r∨a∨b∨z'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [0, 1, 2]

    # Test query for non-existing terms
    query = QueryParser.Parse("(abc OR r)")
    assert query.__str__() == 'abc∨r'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [1]

def TestNotQueries(inverted_index_class):
    # Single NOT
    query = QueryParser.Parse("NOT z")
    assert query.__str__() == '¬z'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [3]

    # Single And Not
    query = QueryParser.Parse("a AND NOT z")
    assert query.__str__() == 'a∧¬z'
    posting_list = query.Evaluate(inverted_index_class)
    assert len(posting_list) == 0

    # Longer And Not
    query = QueryParser.Parse("(y AND z) AND NOT (a OR r)")
    assert query.__str__() == 'y∧z∧¬a∨r'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [2]

    # And Not with Term and with Query
    query = QueryParser.Parse("(y AND NOT z) AND NOT (a OR r)")
    assert query.__str__() == 'y∧¬z∧¬a∨r'
    posting_list = query.Evaluate(inverted_index_class)
    assert len(posting_list) == 0

    query = QueryParser.Parse("(y AND NOT a) AND NOT (b)")
    assert query.__str__() == 'y∧¬a∧¬b'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [1, 2]

    query = QueryParser.Parse("NOT (y AND NOT a) AND NOT (r)")
    assert query.__str__() == '¬y∧¬a∧¬r'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [0, 3]

    # Not in front of And Not
    # TODO: Double check the expected result for this
    query = QueryParser.Parse("NOT s AND NOT a")
    assert query.__str__() == '¬s∧¬a'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [2, 3]

    query = QueryParser.Parse("NOT (s AND NOT a)")
    assert query.__str__() == '¬s∧¬a'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [0, 2, 3]

    # And Not in front of Not
    query = QueryParser.Parse("z AND NOT NOT bb")
    assert query.__str__() == 'z∧¬¬bb'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [2]

    # NOT VALID QUERY BELOW
    # query = QueryParser.Parse("a NOT AND NOT z")
    # assert query.__str__() == 'a¬∧¬z'
    # posting_list = query.Evaluate(inverted_index_class)
    # assert len(posting_list) == 0

def TestMixQueries(inverted_index_class):

    query = QueryParser.Parse("(a OR r) AND (r AND z)")
    assert query.__str__() == 'a∨r∧r∧z'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [1]

    query = QueryParser.Parse("(a AND r) OR (p AND q) OR (n AND x)")
    assert query.__str__() == 'a∧r∨p∧q∨n∧x'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [0,1]

    query = QueryParser.Parse("(a) OR (aa AND z) AND (n AND x)")
    assert query.__str__() == 'a∨aa∧z∧n∧x'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [0]

    query = QueryParser.Parse("(a) OR (aa AND x) AND (bb AND y)")
    assert query.__str__() == 'a∨aa∧x∧bb∧y'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [0, 2]

    query = QueryParser.Parse("aa AND dd AND ee OR b")
    assert query.__str__() == 'aa∧dd∧ee∨b'
    posting_list = query.Evaluate(inverted_index_class)
    assert posting_list == [0, 3]

def run_test(dict_file, postings_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """

    print('Running test...')
    # Create index
    inverted_index_class = InvertedIndex("Tests", dict_file, postings_file)
    inverted_index_class.ConstructIndex()

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
        dictionary_file  = a
    elif o == '-p':
        postings_file = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None:
    usage()
    sys.exit(2)

run_test(dictionary_file, postings_file)
