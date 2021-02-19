#!/usr/bin/python3
import re
import nltk
import sys
import getopt

from inverted_index import InvertedIndex

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

    inverted_index_class = InvertedIndex()

    # Get the corresponding posting List for Term -> "brake"
    query = "brake"
    size, posting_list = inverted_index_class.GetPostingListForTerm(query)
    for p in posting_list:
        print(p, end = " ")
    print("\n")

    # Obtain the skip list for current postingList
    skip_list = inverted_index_class.GetSkipPointers(posting_list)
    for s in skip_list:
        print(s, end = " ")

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
