#!/usr/bin/python3
import re
import string

import nltk
import sys
import getopt

from inverted_index import InvertedIndex
from query import QueryParser


def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")

def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    """
    single query search
    query parsing 
    multi query search
    optimise 
    test
    """

    print('running search on the queries...')

    # This is an empty method
    # Pls implement your code in below


    ############################################
    # Example code below to demonstrate how search.py may use InvertedIndex class to retrieve posting lists for term etc.....

    inverted_index_class = InvertedIndex(out_dict=dict_file, out_postings=postings_file)


    f = open(queries_file, 'r')
    for query in f.readlines():


        print(query)
        posting_list = QueryParser.parse(query).evaluate(inverted_index_class)
        print(" ".join(posting_list), end=" ")
        print("\n")


    # Get the corresponding posting List for Term -> "brake"
    # query = "brake"
    # size, posting_list = inverted_index_class.GetPostingListForTerm(query)
    # for p in posting_list:
    #     print(p, end = " ")
    # print("\n")

    # AND
    # term1 AND term2
    # OR
    # term1 OR term2

    # NOT
    # NOT term1

    # NOT term1 AND term2
    # NOT term1 AND NOT term2

    # NOT term1 OR  term2
    # NOT term1 OR NOT term2

    # term1 AND (term2 OR term3)
    # (term1 AND term2) OR term3

    # NOT term1 AND (term2 OR term3)
    # term1 AND (NOT term2 OR term3)
    # NOT (term1 AND term2) OR term3

    # (term1 AND term2) OR term3

    # A OR B OR (C AND D) OR
    # A + B + CD + ...

    # A AND B AND C AND (D OR E)
    # A AND B AND C AND D OR A AND B AND C AND E
    # ABCD + ABCE # DNF (this one better)
    # ABC (D + E) # CNF

    # Obtain the skip list for current postingList
    # skip_list = inverted_index_class.GetSkipPointers(posting_list)
    # for s in skip_list:
    #     print(s, end = " ")

    ############################################

dictionary_file = postings_file = file_of_queries = output_file_of_results = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file  = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None :
    usage()
    sys.exit(2)

run_search(dictionary_file, postings_file, file_of_queries, file_of_output)
