import os
import string
from math import sqrt
from math import ceil
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
from nltk.stem.porter import PorterStemmer

from collections import defaultdict

"""
    index.py can use inverted_index.py to load data into postings.txt and dictionary.txt.
    - self.postings and self.dictionary will have contents.
    
    search.py can use inverted_index.py to retrieve terms' posting lists, skip pointers.
    - Loading dictionary from memory will be done at class constructor.
    - Only self.dictionary will have contents. self.postings will be empty as we do not need to load everything from disk to mem. 
"""
class InvertedIndex:

    def __init__(self, in_dir = "", out_dict = "dictionary.txt", out_postings = "postings.txt"):
        print("Initialise Inverted Indexes...")

        self.in_dir = in_dir
        self.out_dict = out_dict
        self.out_postings = out_postings

        # Data Structures to be read for creating files
        # To be used for creating indexes
        self.postings = defaultdict(list) # key: Term, Value: List of doc_id
        self.dictionary = set() # Terms

        # line_offset list tells us the offset value for each line in the posting file
        # To be used for fulfilling search queries
        self.line_offset = []

        # Load Dictionary Terms into memory when search.py initialises inverted_index
        if in_dir == "":
            self.LoadDictionaryFromMem()

    """
        ////////////////////////////////////////
        Methods for index.py
        ////////////////////////////////////////
    """

    """
           Method to read the data file and fill up self.postings and self.dictionary.
           
           Current implementation only removes punctuations, case folding and do word stemming.
           It does not remove stop words.   
    """
    def ConstructIndex(self):
        print("Constructing Indexes...")

        stemmer = PorterStemmer()
        translator = str.maketrans('','', string.punctuation)

        for doc_id in os.listdir(self.in_dir):
            for line in self.ReadFromFile(self.in_dir + "/" + doc_id):
                # Tokenize by sentences
                for s_token in sent_tokenize(line):
                    # Tokenize by word
                    for w_token in word_tokenize(s_token):

                        # Remove Punctuation
                        w_token = w_token.translate(translator)

                        # Word Stemming & Case-Folding
                        term = stemmer.stem(w_token).lower()

                        # Remove numbers
                        if w_token.isnumeric() or len(term) == 0:
                            continue

                        if term not in self.dictionary:
                            self.dictionary.add(term)
                        if doc_id not in self.postings[term]:
                            self.postings[term].append(doc_id)

    """
           Method to write the contents of self.dictionary to file dictionary.txt
    """
    def SaveDictToMem(self):
        print("Save dictionary to dictionary.txt ...")

        result = ""
        for d in sorted(self.dictionary):
            result += d + "\n"

        self.WriteToFile(self.out_dict, result)

    """
        Method to write the contents of self.postings to file postings.txt
        
        Reference to self.dictionary is to ensure that the ordering of postings.txt and
        dictionary.txt are the same for all the terms.
    """
    def SavePostingsToMem(self):
        print("Save all postings to postings.txt in the format of [term doc_id doc_id doc_id ... ]  ...")

        result = ""
        for term in sorted(self.dictionary):
            result += term + " "
            for doc_id in sorted(self.postings[term]):
                result += doc_id + " "
            result += "\n"

        self.WriteToFile(self.out_postings, result)


    """
        Method to Write to out_file.
        Params: 
            out_file: file path
            result: Text to store in out_file
    """
    def WriteToFile(self, out_file, result):
        fw = open(out_file, 'w')
        fw.write(''.join(result))


    """
        ////////////////////////////////////////
        Methods for Search.py
        ////////////////////////////////////////
    """


    """
        Method to load the contents of dictionary.txt into self.dictionary set
        
        Called by constructor when search.py initialises inverted index class
    """
    def LoadDictionaryFromMem(self):
        if len(self.dictionary) != 0:
            return
        for term in self.ReadFromFile(self.out_dict):
            self.dictionary.add(term.rstrip('\n'))

    """
        Method to obtain the list of posting list for input term.

        Params: 
            term: term value
    
        Returns:
            A list of posting list for given term
    """
    def GetPostingListForTerm(self, term):
        print("Loading Posting List for term in memory...")

        offset = self.GetOffset(term)
        if offset == -1:
            # Term not found
            return []

        line = self.ReadFromFile(self.out_postings, offset)

        # remove first item in the line which contains term value and last value \n
        return line.split(" ")[1:-1]

    """
        Method to get offset of the term in postings.txt
        
        The terms in posting.txt and dictionary.txt have the same ordering.
        term_index: We deduce the line number that the term appears in the postings.txt
        from it's position in the sorted list of dictionary set.
        line_offset[term_index] tells us the offset value of term
        
        Params: 
            term: term value
            result: Text to store in out_file
        Returns:
            offset value of term in postings.txt
    """
    def GetOffset(self, term):

        # If self.line_offset has been constructed before, we skip this process
        if len(self.line_offset) == 0:
            offset = 0
            for line in self.ReadFromFile(self.out_postings):
                self.line_offset.append(offset)
                offset += len(line) + 1 # 1 value is for accomodating \n

        try:
            term_index = list(sorted(self.dictionary)).index(term)
            return self.line_offset[term_index]
        except:
            # Term not found
            return -1;

    """
        Method to get a list of indexes that indicates the next index to jump to from current index 
        skip_pointer[i] = next index j we can jump to at index i
        If we cannot have skip pointer at i, then value will be i by default
        Params: 
            posting_list
        Returns:
            skip_pointers_list 
    """
    def GetSkipPointers(self, posting_list):
        print("Constructing Skip Pointers...")

        skip_pointers = []
        jump = ceil(sqrt(len(posting_list)))

        for idx, posting in enumerate(posting_list):
            if idx % jump == 0 and (idx+jump) < len(posting_list):
                skip_pointers.append(idx + jump)
            else:
                skip_pointers.append(idx)

        return skip_pointers

    """
        Method to Read in the contents of in_file.
        Params: 
            in_file: file path 
            offset: Optional offset to read from file
            
        Return: 
            Returns either all the lines or a single line
    """
    def ReadFromFile(self, in_file, offset = None):
        f = open(in_file, 'r')

        if offset == None:
            return f.readlines()
        else:
            f.seek(0)
            f.seek(offset)
            return f.readline()

