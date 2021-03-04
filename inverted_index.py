import os
from sys import platform
import shutil
import string
import time

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

    def __init__(self, in_dir="", out_dict="dictionary.txt", out_postings="postings.txt"):
        print("Initialise Inverted Indexes...")

        self.in_dir = in_dir
        self.out_dict = out_dict
        self.out_postings = out_postings
        self.all_files = set()
        try:
            with open("document_id_list.txt") as f:
                for line in f.readlines():
                    self.all_files.update([int(i) for i in line.split(",")])
        except FileNotFoundError:
            print("Doc id list not created")

        # self.dictionary set is a dictionary where the key is the term name
        # and the value is a tuple of (size of posting list, offset from top line of posting.txt)
        self.dictionary = {}
        # Load Dictionary Terms into memory when search.py initialises inverted_index
        if in_dir == "":
            self.load_dictionary_from_mem()

        if platform == "win32":
            print("Running on Windows")
            self.new_line_offset = 1
        else:
            self.new_line_offset = 0

    """
        ////////////////////////////////////////
        Methods for index.py
        ////////////////////////////////////////
    """

    def construct_index(self):
        """
                   Method to read the data file and fill up self.postings and self.dictionary.
                   Current implementation only removes punctuations, case folding and do word stemming.
                   It does not remove stop words.
        """
        print("Constructing Indexes...")

        stemmer = PorterStemmer()
        translator = str.maketrans('', '', string.punctuation)

        block_index = 0
        curr_lines_in_mem = 0  # Number of term-posting list pair

        self.reset_files()

        # Get all the file names in reuters
        all_files = []
        for doc_id in os.listdir(self.in_dir):
            all_files.append(int(doc_id))
        all_files = sorted(all_files)

        postings = defaultdict(list)  # key: Term, Value: List of doc_id
        dictionary = set()  # Terms
        stem_dict = {}

        with open("document_id_list.txt", 'w') as f:
            f.write(",".join([str(i) for i in all_files]))

        start_time = time.perf_counter()
        # Read in ascending order of their file names
        for doc_id in all_files:
            with open(os.path.join(self.in_dir, str(doc_id))) as file:
                for line in file:
                    # Tokenize by sentences
                    for s_token in sent_tokenize(line):
                        # Tokenize by word
                        for w_token in word_tokenize(s_token):

                            # Remove Punctuation & Case-Folding
                            w_token = w_token.translate(translator).lower()

                            # Word Stemming
                            if w_token in stem_dict:
                                term = stem_dict[w_token]
                            else:
                                term = stemmer.stem(w_token)
                                stem_dict[w_token] = term

                            # Remove numbers
                            if w_token.isnumeric() or len(term) == 0:
                                continue

                            curr_lines_in_mem += 1
                            if term not in dictionary:
                                dictionary.add(term)

                            if doc_id not in postings[term]:
                                postings[term].append(doc_id)

                            # Write the previous items to new block
                            if curr_lines_in_mem == self.MAX_LINES_TO_HOLD_IN_MEM:
                                self.write_block_to_disk(block_index, postings, dictionary)
                                print("Create block {} ({:.2f}s)".format(block_index, time.perf_counter() - start_time))
                                start_time = time.perf_counter()
                                # Reset
                                curr_lines_in_mem = 0
                                postings = defaultdict(list)
                                dictionary = set()
                                block_index += 1

        # Write last block if exists
        if curr_lines_in_mem > 0:
            self.write_block_to_disk(block_index, postings, dictionary)
            self.merge_blocks(block_index + 1)
        else:
            self.merge_blocks(block_index)

    def reset_files(self):
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

    def write_block_to_disk(self, block_index, postings, dictionary):
        """
                    Method to write the contents of posting lists to a new block file
                    SPIMI-Invert
                    Params:
                        - block_index: Gives us the file name
                        - postings: List of all the posting lists
                        - dictionary: List of all the terms
        """

        result = ""
        # Sort Dictionary Terms. Line 11 of SPIMI - INVERT
        for term in sorted(dictionary):
            result += term + " "
            # No need to sort postings because they are already in sorted form when we processed
            # the docs in ascending order previously
            result += " ".join([str(i) for i in postings[term]])
            result += "\n"

        self.write_to_file("blocks/" + str(block_index), result)

    def merge_blocks(self, total_num_blocks):
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
            lines = self.read_from_file("blocks/" + str(block_num), blocks_offset[block_num],
                                        read_file_pointers[block_num], lines_to_read_per_block)
            for line in lines:
                blocks_offset[block_num] = blocks_offset[block_num] + len(line) + 1  # 1 for \n
                q.put(QueueItem(line, block_num))
                lines_per_block_mem[block_num] += 1

        freq_dict = {}
        # K_WAY
        while not q.empty():

            # Process current Item in the queue
            curr_item = q.get()
            curr_term = curr_item.get_term()
            curr_posting_list = curr_item.get_posting_list()
            curr_block = curr_item.get_block_num()

            lines_per_block_mem[curr_block] -= 1

            # Encountering new term, End of prev term
            if curr_term != term_to_write and term_to_write != '':
                docs_with_skip = self.build_list_with_skips(doc_ids_to_write)
                content = term_to_write + " " + " ".join(docs_with_skip) + "\n"
                result_doc_ids_to_write.append(content)
                result_term_to_write.append(term_to_write + " " + str(len(docs_with_skip)) + " " + str(
                    posting_file_line_offset) + "\n")  # Term Size Offset
                freq_dict[term_to_write] = len(docs_with_skip)

                posting_file_line_offset += len(content) + self.new_line_offset

                # Complete posting list of prev term, hence increment to indicate new line in posting.txt
                curr_lines_in_mem += 1

                # Reset for new term
                doc_ids_to_write = []

            if curr_lines_in_mem == self.MAX_LINES_TO_HOLD_IN_MEM:
                self.write_to_file(self.out_postings, "".join(result_doc_ids_to_write), True,
                                   write_posting_file_pointer)
                self.write_to_file(self.out_dict, "".join(result_term_to_write), True, write_dict_file_pointer)

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
                lines = self.read_from_file("blocks/" + str(curr_block), blocks_offset[curr_block],
                                            read_file_pointers[curr_block], lines_to_read_per_block)
                for line in lines:
                    blocks_offset[curr_block] = blocks_offset[curr_block] + len(line) + 1  # 1 for \n
                    q.put(QueueItem(line, curr_block))
                    lines_per_block_mem[curr_block] += 1

        # Add last Term and its' posting lists to result
        if len(doc_ids_to_write) > 0:
            docs_with_skip = self.build_list_with_skips(doc_ids_to_write)
            content = term_to_write + " " + " ".join(docs_with_skip) + "\n"
            result_doc_ids_to_write.append(content)
            result_term_to_write.append(term_to_write + " " + str(len(docs_with_skip)) + " " + str(
                posting_file_line_offset) + "\n")  # Term Size Offset
            freq_dict[term_to_write] = len(docs_with_skip)
        # Write result in mem to file
        self.write_to_file(self.out_postings, "".join(result_doc_ids_to_write), True, write_posting_file_pointer)
        self.write_to_file(self.out_dict, "".join(result_term_to_write), True, write_dict_file_pointer)
        print("Dictionary size: {}".format(len(freq_dict)))
        print("Posting list size: {}".format(sum(freq_dict.values())))
        self.write_to_file("freq_sorted_dict.txt", ["{} {}\n".format(item[0], item[1]) for item in
                                                    sorted(list(freq_dict.items()), key=lambda i: i[1], reverse=True)])

    def build_list_with_skips(self, posting_list):
        docs_with_skip = []
        jump = ceil(sqrt(len(posting_list)))

        for idx, posting in enumerate(posting_list):
            if idx % jump == 0 and (idx + jump) < len(posting_list):
                next_val = posting_list[idx + jump]
                docs_with_skip.append(posting + ";" + next_val)
            else:
                docs_with_skip.append(posting)

        return docs_with_skip

    def write_to_file(self, out_file, result, append=False, fw=None):
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

    def load_dictionary_from_mem(self):
        """
                Method to load the contents of dictionary.txt into self.dictionary set
                Called by constructor when search.py initialises inverted index class
        """
        if len(self.dictionary) != 0:
            return

        for term in self.read_from_file(self.out_dict):  # dictionary.txt is already sorted
            term = term.rstrip('\n').strip().split(" ")
            term_name = term[0]
            term_posting_len = term[1]
            offset = term[2]
            self.dictionary[term_name] = (term_posting_len, offset)

    def get_posting_list_for_term(self, term):
        """
                Method to obtain the list of posting list for input term.
                Params:
                    term: term value
                Returns:
                    Returns the list of posting list for given term
        """

        try:
            size_of_posting_list, offset = self.dictionary[term]
            line = self.read_from_file(self.out_postings, int(offset))
            split_line = line.rstrip('\n').split(" ")[1:]
            return split_line
        except:
            # Term not found
            return []

    def get_size_for_term(self, term):
        try:
            size_of_posting_list, offset = self.dictionary[term]
            return int(size_of_posting_list)
        except:
            return 0

    def read_from_file(self, in_file, offset=None, f=None, num_lines=1):
        """
                Method to Read in the contents of in_file.
                Params:
                    in_file: file path
                    offset: Optional offset to read from file
                    f: File Opener to in_file
                    num_lines: Lines to read
                Return:
                    Returns either all the lines or a single line
        """

        if f == None:
            f = open(in_file, 'r')

        if offset == None:
            return f.readlines()
        else:
            f.seek(offset)

            if num_lines == 1:
                return f.readline()

            lines = []
            for i in range(0, num_lines):
                new_line = f.readline()
                if len(new_line.strip()) == 0:
                    break
                lines.append(new_line)
            return lines


class QueueItem:
    def __init__(self, line, block_num):
        line = line.rstrip('\n').strip(' ')
        split_line = line.split(" ")
        self.term = split_line[0]  # What is the term
        self.posting_list = line.split(" ")[1:]  # Remove first item
        self.block_num = block_num  # Tell us what block file this item comes from

    def get_term(self):
        return self.term

    def get_posting_list(self):
        return self.posting_list

    def get_block_num(self):
        return int(self.block_num)

    # We compare by term values first. If two items have the same term values, then we will
    # compare their block number.
    def __eq__(self, other):
        return ((self.term, int(self.block_num)) == (other.get_term(), other.get_block_num()))

    def __ne__(self, other):
        return ((self.term, int(self.block_num)) != (other.get_term(), other.get_block_num()))

    def __lt__(self, other):
        return ((self.term, int(self.block_num)) < (other.get_term(), other.get_block_num()))

    def __le__(self, other):
        return ((self.term, int(self.block_num)) <= (other.get_term(), other.get_block_num()))

    def __gt__(self, other):
        return ((self.term, int(self.block_num)) > (other.get_term(), other.get_block_num()))

    def __ge__(self, other):
        return ((self.term, int(self.block_num)) >= (other.get_term(), other.get_block_num()))

    def __repr__(self):
        return "%s %s" % (self.term, int(self.block_num))