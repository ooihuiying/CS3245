#!/usr/bin/python3
import re
import nltk
import sys
import getopt

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



    # car AND cat
    i = postings['car'].__iter()__
    j = postings['cat'].__iter()__

    a = i.__next()__
    b = j.__next()__
    if a == b:
        # add a to search results
    elif a < b:
        a = i.__next__()
    else:



    index1 = 0
    index2 = 0


    for ...
        if index1 % sqrt(len(postings['cat']))
            index1 += ...

        if index2 % sqrt(len(postings['car']))
            index1 += ...

        if a == b:
        # add a to search results
        elif a < b:
            a = postings['cat'][index1]
        else:

    print('running search on the queries...')
    # This is an empty method
    # Pls implement your code in below

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
