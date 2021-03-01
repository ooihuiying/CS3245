#!/usr/bin/python3
import re
import string
import time

import nltk
import sys
import getopt

from inverted_index import InvertedIndex
from query import QueryParser


def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")

use_sh = False
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

    start_time = time.perf_counter()
    n = 0
    out = []
    with open(queries_file, 'r') as f:
        with open(results_file, 'w') as fw:
            for query in f:
                query = query.strip()
                if query == "":
                    continue
                n += 1
                query = QueryParser.parse(query, use_sh)
                # print(query.__str__())
                posting_list = query.evaluate(inverted_index_class, forced=True)
                print("Query #{}: {} --> {} results".format(n, query, len(posting_list)))

                out.append(" ".join([str(i) for i in posting_list]) + "\n")
                # fw.write(" ".join([str(i) for i in posting_list]) + "\n")

            fw.writelines(out)

    print("{} queries completed in {:.2f}s".format(n, time.perf_counter() - start_time))

dictionary_file = postings_file = file_of_queries = output_file_of_results = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:s')
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
    elif o == '-s':
        use_sh = True
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None :
    usage()
    sys.exit(2)

run_search(dictionary_file, postings_file, file_of_queries, file_of_output)