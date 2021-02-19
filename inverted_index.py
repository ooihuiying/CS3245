import os
import shutil
import string
from queue_item import QueueItem
from queue import PriorityQueue
from math import sqrt
from math import ceil
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
from nltk.stem.porter import PorterStemmer

from collections import defaultdict

# For this assignment, you can set an artificial threshold (e.g., after a certain number of pairs
# have been processed) so that your system process those pairs as a block.

class InvertedIndex:
    """
        index.py can use inverted_index.py to load data into postings.txt and dictionary.txt.
        - We will write out a subset of the posting list to block files under /block folder using SPIMI-Invert method.
        - Once all those block files have been filled, we will then process all these block files together
        - and append to posting.txt using the BISC k-way merge
        - self.postings and self.dictionary will have contents.

        search.py can use inverted_index.py to retrieve terms' posting lists, skip pointers.
        - Loading dictionary from memory will be done at class constructor.
        - Only self.dictionary will have contents. self.postings will be empty as we do not need to load everything from disk to mem.
    """

    BLOCK_SIZE_LIMIT = 100000

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

    def ConstructIndex(self):
        """
                   Method to read the data file and fill up self.postings and self.dictionary.

                   Current implementation only removes punctuations, case folding and do word stemming.
                   It does not remove stop words.
        """
        print("Constructing Indexes...")

        stemmer = PorterStemmer()
        translator = str.maketrans('','', string.punctuation)

        block_index = 0
        curr_block_size = 0

        self.ResetFiles()

        # Get all the file names in reuters
        all_files = []
        for doc_id in os.listdir(self.in_dir):
            all_files.append(int(doc_id))

        # Read in ascending order of their file names
        for doc_id in sorted(all_files):
            for line in self.ReadFromFile(self.in_dir + "/" + str(doc_id)):
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
                        if str(doc_id) not in self.postings[term]:
                            self.postings[term].append(str(doc_id))

                        curr_block_size += 1

                        # Write the previous items to new block
                        if curr_block_size == self.BLOCK_SIZE_LIMIT:
                            self.WriteBlockToDisk(block_index)
                            curr_block_size = 0
                            block_index += 1

        # Write last block
        self.WriteBlockToDisk(block_index)
        self.MergeBlocks(block_index)

    def ResetFiles(self):
        """
                   Method to create /blocks folder to keep all the intermediate block files
                   Method to remove all existing /block folders and posting.txt and dictionary.txt files
        """

        block_dir = "blocks"
        if os.path.exists(block_dir):
            # Delete block folder
            shutil.rmtree(block_dir)
        os.makedirs(block_dir)

        if os.path.exists(self.out_postings):
            os.remove(self.out_postings)

        if os.path.exists(self.out_dict):
            os.remove(self.out_dict)

    def WriteBlockToDisk(self, block_index):
        """
                    Method to write the contents of posting lists (stored as self.postings in memory) to a new block file
                    SPIMI-Invert
                    Params:
                        - block_index: Gives us the file name
        """
        print("create new block ... " + str(block_index))

        result = ""
        # Sort Dictionary Terms. Line 11 of SPIMI - INVERT
        for term in sorted(self.dictionary):
            result += term + " "
            # No need to sort postings because they are already in sorted form when we processed
            # the docs in ascending order previously
            for doc_id in self.postings[term]:
                result += doc_id + " "
            result += "\n"

        self.WriteToFile("blocks/"+str(block_index), result)

        # Clear Postings and Dictionary from memory
        self.postings = defaultdict(list)
        self.dictionary = set()


    def MergeBlocks(self, total_num_blocks):
        """
                    Method to read all the block files inside /Blocks and append them into Posting.txt
                    using BSBI Merging -> (total_num_blocks) K-Way Merge
                    Params:
                        - total_num_blocks: Total number of block files that we want to merge
        """
        print("Merge all blocks ...")

        # blocks_offset[i] stores the offset value for reading from file of block i
        blocks_offset = [0] * total_num_blocks

        q = PriorityQueue()

        # Add the first line of each block to priority queue
        for block_num in range(0, total_num_blocks):
            line = self.ReadFromFile("blocks/"+str(block_num), blocks_offset[block_num])
            blocks_offset[block_num] = blocks_offset[block_num] + len(line) + 1 # 1 for \n
            q.put(QueueItem(line, block_num))

        # K-Way
        term_to_write = ''
        doc_ids_to_write = []

        while not q.empty():

            # Process current Item in the queue
            curr_item = q.get()
            curr_term = curr_item.GetTerm()
            curr_posting_list = curr_item.GetLine().split(" ")[1:-1]
            curr_block = curr_item.GetBlockNum()

            # Encountering new term -> need to append previous term and it's doc_ids to posting.txt
            # TODO: Should not write out to memory each time we encounter a new term
            if curr_term != term_to_write and term_to_write != '':
                content = term_to_write + " " + str(len(doc_ids_to_write)) + " " + " ".join(doc_ids_to_write)
                self.WriteToFile(self.out_postings, content + "\n", True)
                self.WriteToFile(self.out_dict, term_to_write + "\n", True)

                # Reset
                doc_ids_to_write = []

            term_to_write = curr_term

            for doc_id in curr_posting_list:
                if len(doc_ids_to_write) == 0 or int(doc_id) != int(doc_ids_to_write[-1]):
                    doc_ids_to_write.append(doc_id)

            # Check if can add next line in the block to queue
            line = self.ReadFromFile("blocks/" + str(curr_block), blocks_offset[curr_block])
            # End of File
            if line == '':
                continue

            # Add next line in current block to queue
            queue_item = QueueItem(line, curr_block)
            blocks_offset[curr_block] = blocks_offset[curr_block] + len(line) + 1 # 1 for \n
            q.put(queue_item)


        # For the last term - posting lists
        content = term_to_write + " " + str(len(doc_ids_to_write)) + " " + " ".join(doc_ids_to_write)
        self.WriteToFile(self.out_postings, content + "\n", True)
        self.WriteToFile(self.out_dict, term_to_write + "\n", True)


    def WriteToFile(self, out_file, result, append = False):
        """
                Method to Write to out_file.
                Params:
                    out_file: file path
                    result: Text to store in out_file
        """

        if not append:
            fw = open(out_file, 'w+')
            fw.write(''.join(result))
        else:
            # Append to the end of the file
            fw = open(out_file, 'a')
            fw.write(''.join(result))


    """
        ////////////////////////////////////////
        Methods for Search.py
        ////////////////////////////////////////
    """

    def LoadDictionaryFromMem(self):
        """
                Method to load the contents of dictionary.txt into self.dictionary set

                Called by constructor when search.py initialises inverted index class
        """
        if len(self.dictionary) != 0:
            return

        unsorted_dict = set()
        for term in self.ReadFromFile(self.out_dict):
            unsorted_dict.add(term.rstrip('\n'))

        self.dictionary = sorted(unsorted_dict)

    def GetPostingListForTerm(self, term):
        """
                Method to obtain the list of posting list for input term.

                Params:
                    term: term value

                Returns:
                    A tuple containing the (len of posting list, the list of posting list for given term)
        """

        print("Loading Posting List for term in memory...")

        offset = self.GetOffset(term)
        if offset == -1:
            # Term not found
            return 0, []

        line = self.ReadFromFile(self.out_postings, offset)
        split_line = line.strip().split(" ")

        # remove first 2 items in the line which contains term value & size
        return split_line[1], split_line[2:]

    def GetOffset(self, term):
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

        # If self.line_offset has been constructed before, we skip this process
        if len(self.line_offset) == 0:
            offset = 0
            for line in self.ReadFromFile(self.out_postings):
                self.line_offset.append(offset)
                offset += len(line) + 1 # 1 value is for accomodating \n

        try:
            term_index = list(self.dictionary).index(term)
            return self.line_offset[term_index]
        except:
            # Term not found
            return -1;

    def GetSkipPointers(self, posting_list):
        """
                Method to get a list of indexes that indicates the next index to jump to from current index
                skip_pointer[i] = next index j we can jump to at index i
                If we cannot have skip pointer at i, then value will be i by default
                Params:
                    posting_list
                Returns:
                    skip_pointers_list
        """
        print("Constructing Skip Pointers...")

        skip_pointers = []
        jump = ceil(sqrt(len(posting_list)))

        for idx, posting in enumerate(posting_list):
            if idx % jump == 0 and (idx+jump) < len(posting_list):
                skip_pointers.append(idx + jump)
            else:
                skip_pointers.append(idx)

        return skip_pointers

    def ReadFromFile(self, in_file, offset = None):
        """
                Method to Read in the contents of in_file.
                Params:
                    in_file: file path
                    offset: Optional offset to read from file

                Return:
                    Returns either all the lines or a single line
        """
        f = open(in_file, 'r')

        if offset == None:
            return f.readlines()
        else:
            f.seek(0)
            f.seek(offset)
            return f.readline()


