import os
import shutil
import string
from queue_item import QueueItem
from queue import PriorityQueue
from math import sqrt
from math import ceil, floor
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
from nltk.stem.porter import PorterStemmer

from collections import defaultdict

class InvertedIndex:
    """
        index.py can use inverted_index.py to load data into postings.txt and dictionary.txt.
        - We will write out a subset of the posting list to block files under /block folder using SPIMI-Invert method.
        - Once all those block files have been filled, we will then process all these block files together
        - and append to posting.txt using the BISC k-way merge

        search.py can use inverted_index.py to retrieve terms' posting lists, skip pointers.
        - Loading dictionary from memory will be done at class constructor.
        - Only self.dictionary will have contents.
    """

    MAX_LINES_TO_HOLD_IN_MEM = 100000

    def __init__(self, in_dir = "", out_dict = "dictionary.txt", out_postings = "postings.txt"):
        print("Initialise Inverted Indexes...")

        self.in_dir = in_dir
        self.out_dict = out_dict
        self.out_postings = out_postings

        # self.dictionary set is a dictionary where the key is the term name
        # and the value is a tuple of (size of posting list, offset from top line of posting.txt)
        self.dictionary = {}
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
        curr_lines_in_mem = 0 # Number of term-posting list pair

        self.ResetFiles()

        # Get all the file names in reuters
        all_files = []
        for doc_id in os.listdir(self.in_dir):
            all_files.append(int(doc_id))

        postings = defaultdict(list)  # key: Term, Value: List of doc_id
        dictionary = set()  # Terms

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

                        curr_lines_in_mem += 1
                        if term not in dictionary:
                            dictionary.add(term)

                        if str(doc_id) not in postings[term]:
                            postings[term].append(str(doc_id))

                        # Write the previous items to new block
                        if curr_lines_in_mem == self.MAX_LINES_TO_HOLD_IN_MEM:
                            self.WriteBlockToDisk(block_index, postings, dictionary)
                            # Reset
                            curr_lines_in_mem = 0
                            postings = defaultdict(list)
                            dictionary = set()
                            block_index += 1

        # Write last block if exists
        if curr_lines_in_mem > 0:
            self.WriteBlockToDisk(block_index, postings, dictionary)
            self.MergeBlocks(block_index + 1)
        else :
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

    def WriteBlockToDisk(self, block_index, postings, dictionary):
        """
                    Method to write the contents of posting lists to a new block file
                    SPIMI-Invert
                    Params:
                        - block_index: Gives us the file name
                        - postings: List of all the posting lists
                        - dictionary: List of all the terms
        """

        print("Create new block ... " + str(block_index))

        result = ""
        # Sort Dictionary Terms. Line 11 of SPIMI - INVERT
        for term in sorted(dictionary):
            result += term + " "
            # No need to sort postings because they are already in sorted form when we processed
            # the docs in ascending order previously
            result += " ".join(postings[term])
            result += "\n"

        self.WriteToFile("blocks/"+str(block_index), result)


    def MergeBlocks(self, total_num_blocks):
        """
                    Method to read all the block files inside /Blocks and append them into Posting.txt
                    using BSBI Merging -> (total_num_blocks) K-Way Merge
                    Params:
                        - total_num_blocks: Total number of block files that we want to merge
        """
        print("Merge all " + str(total_num_blocks) + " blocks ...")

        # (1) INITIALISE VARIABLES
        # blocks_offset[i] stores the offset value for reading from file of block i
        blocks_offset = [0] * total_num_blocks

        read_file_pointers = [0] * total_num_blocks
        for block_num in range(0, total_num_blocks):
            read_file_pointers[block_num] = open("blocks/" + str(block_num), 'r')

        write_posting_file_pointer = open(self.out_postings, 'a')
        write_dict_file_pointer = open(self.out_dict, 'a')

        term_to_write = ''
        doc_ids_to_write = []
        result_doc_ids_to_write = []
        result_term_to_write = []
        curr_lines_in_mem = 0
        posting_file_line_offset = 0

        lines_to_read_per_block = floor(self.MAX_LINES_TO_HOLD_IN_MEM / total_num_blocks)
        if lines_to_read_per_block == 0:
            # If the block size limit is smaller than the total num of blocks
            lines_to_read_per_block = 1

        q = PriorityQueue()

        lines_per_block_mem = [0] * total_num_blocks
        # (2) INITIAL STEP OF K WAY MERGE: Read in a batch of lines from each block file
        for block_num in range(0, total_num_blocks):
            for li in range(0, lines_to_read_per_block):
                line = self.ReadFromFile("blocks/" + str(block_num), blocks_offset[block_num], read_file_pointers[block_num])
                blocks_offset[block_num] = blocks_offset[block_num] + len(line) + 1 # 1 for \n
                q.put(QueueItem(line, block_num))
                lines_per_block_mem[block_num] += 1

        # K_WAY
        while not q.empty():

            # Process current Item in the queue
            curr_item = q.get()
            curr_term = curr_item.GetTerm()
            curr_posting_list = curr_item.GetPostingList()
            curr_block = curr_item.GetBlockNum()

            lines_per_block_mem[curr_block] -= 1

            # Encountering new term, End of prev term
            if curr_term != term_to_write and term_to_write != '':

                content = term_to_write + " " + " ".join(doc_ids_to_write) + "\n"
                result_doc_ids_to_write.append(content)
                result_term_to_write.append(term_to_write + " " + str(len(doc_ids_to_write)) + " " + str(posting_file_line_offset) + "\n") # Term Size Offset
                posting_file_line_offset += len(content) + 1

                # Complete posting list of prev term, hence increment to indicate new line in posting.txt
                curr_lines_in_mem += 1

                # Reset for new term
                doc_ids_to_write = []

            if curr_lines_in_mem == self.MAX_LINES_TO_HOLD_IN_MEM:
                self.WriteToFile(self.out_postings, "".join(result_doc_ids_to_write), True, write_posting_file_pointer)
                self.WriteToFile(self.out_dict, "".join(result_term_to_write), True, write_dict_file_pointer)

                curr_lines_in_mem = 0
                result_doc_ids_to_write = []
                result_term_to_write = []

            term_to_write = curr_term

            for doc_id in curr_posting_list:
                if len(doc_ids_to_write) == 0 or int(doc_id) != int(doc_ids_to_write[-1]):
                    doc_ids_to_write.append(doc_id)

            # When all the lines from curr_block has been processed, we add in the next batch of
            # lines from the block
            if lines_per_block_mem[curr_block] == 0:
                for li in range(0, lines_to_read_per_block):
                    line = self.ReadFromFile("blocks/" + str(curr_block), blocks_offset[curr_block], read_file_pointers[curr_block])
                    # End of File
                    if line == '':
                        break
                    blocks_offset[curr_block] = blocks_offset[curr_block] + len(line) + 1  # 1 for \n
                    q.put(QueueItem(line, curr_block))
                    lines_per_block_mem[curr_block] += 1



        # Add last Term and its' posting lists to result
        if len(doc_ids_to_write) > 0:
            content = term_to_write + " " + " ".join(doc_ids_to_write) + "\n"
            result_doc_ids_to_write.append(content)
            result_term_to_write.append(term_to_write + " " + str(len(doc_ids_to_write)) + " " + str(posting_file_line_offset + 1) + "\n")  # Term Size Offset
        # Write result in mem to file
        self.WriteToFile(self.out_postings, "".join(result_doc_ids_to_write), True, write_posting_file_pointer)
        self.WriteToFile(self.out_dict, "".join(result_term_to_write), True, write_dict_file_pointer)


    def WriteToFile(self, out_file, result, append = False, fw = None):
        """
                Method to Write to out_file.
                Params:
                    out_file: file path
                    result: Text to store in out_file
        """

        if not append and fw == None:
            fw = open(out_file, 'w+')
        elif append and fw == None:
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

        for term in self.ReadFromFile(self.out_dict): # dictionary.txt is already sorted
            term = term.rstrip('\n').strip().split(" ")
            term_name = term[0]
            term_posting_len = term[1]
            offset = term[2]
            self.dictionary[term_name] = (term_posting_len, offset)

    def GetPostingListForTerm(self, term):
        """
                Method to obtain the list of posting list for input term.

                Params:
                    term: term value

                Returns:
                    Returns a tuple of (len of posting list, the list of posting list for given term)
        """

        print("Loading Posting List for term in memory...")
        try:
            size_of_posting_list, offset = self.dictionary[term]
            line = self.ReadFromFile(self.out_postings, int(offset))
            split_line = line.rstrip('\n').split(" ")
            return size_of_posting_list, split_line[1:]  # remove first item in the line which contains term value
        except:
            # Term not found
            return 0, []

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

    def ReadFromFile(self, in_file, offset = None, f = None):
        """
                Method to Read in the contents of in_file.
                Params:
                    in_file: file path
                    offset: Optional offset to read from file
                    f: File Opener to in_file
                Return:
                    Returns either all the lines or a single line
        """

        if f == None:
            f = open(in_file, 'r')

        if offset == None:
            return f.readlines()
        else:
            f.seek(0)
            f.seek(offset)
            return f.readline()


