This is the README file for A0173178X-A0172706E's submission

== Python Version ==

We're using Python Version <3.7.6 or replace version number> for
this assignment.

== General Notes about this assignment ==

Give an overview of your program, describe the important algorithms/steps 
in your program, and discuss your experiments in general.  A few paragraphs 
are usually sufficient.

There are two parts to this assignment:
1) The first is the construction of the indexes using SPIMI, provide a method to build skip
pointers and save the index into disk in the form of dictionary.txt and postings.txt.
2) The second is to load the dictionary into memory, parse and evaluate the query, search all the
document ids for the query and save the query results into the output file.

<<Indexing>>

(a) Reading Files
    The system reads the files in ascending order of their file names. For eg, 1.txt is read before 2.txt.
(b) Pre-processing
    For each file, in order to collect the vocabulary, we applied tokenisation and stemming on the document text.
    nltk.sent_tokenize() and nltk.word_tokenize() were used to tokenize sentences and words. Case folding is applied to all words.
    Stemmed values which only contain numbers are also removed. Stop words are not removed from the vocabulary.
    In order to reduce repeated stemming on the same words to improve speed of indexing, previously stemmed words are stored in stem_dict.
(c) Scalable Indexing Construction:
    SPIMI was implemented. We set 100000 to be the maximum number of lines that the memory can hold.
    We build the postings list of the terms as the term-docID pairs are processed.
    Terms are stored in a dictionary set. Posting lists are stored in the form of HashMap.
    When the number of pairs processed reaches the limit of 100000, we will then treat whatever that is currently held in memory to belong to a block.
    We will first sort the dictionary terms, then according to the sorted order, write their corresponding posting lists to the block file.
    Each line in the block file contains [A B] where A is the term and B is the list of doc ids.
    Once the entire content in memory has been written to a block file, we will then clear memory and continue processing the files.

    Eventually, we will process all the data files and have block files constructed along the way. The final step is now to
    merge these block files using the BISC merging method. In this method, we will open all the block files and read in X lines
    from each block file that was previously constructed. X is calculated to be Floor(100000/K) where K = number of block files.
    We will then perform K-Way merging.
    The dictionary.txt and posting.txt will be written.
(d) Skip Pointers:
    Following from (c), each line contains [A B] where B is [C C C C ... C]. C is either a single doc id or a single doc id appended by ; and the doc id
    of it's next skip, depending on its' position.
    Every X distance, the doc id will have an additional ; and doc id of it's next skip.
    During indexing, we define X to be ceil(sqrt(len(posting_list))).

<<Searching>>
(e) Parsing:
    TODO
    The Shunting-Yard Parser is used.
    
(f) Evaluation:
    TODO

    (OR)
    - We apply a Set Union on all the Ops

    (AND)
    (1) When we have to apply AND on operators without Negation, we will sort them by size and merge every two of them.
    - If the ops of AND is a primitive query term, we will apply skip pointers.
      Continuing from (d), during the search run time, for each C in B, we will check for the value after ; to see if the current doc_id has a skip pointer.
      The value gives us the next doc id value should the skip be taken. If it is present, we will compare the values and decide whether to apply the skip.
      If the skip is to be applied, according to the length of the list, the jump value will be calculated.
    - If the ops of AND is not a primitive query term, we will make use of python set intersection to do the work. It is more time efficient to build the intersection
      compared to constructing the skip pointers at run time.
    (2) When the Ops of AND are all Negated.
    - Applying De-Morgan's Law, we will perform UNION on the ops (without negation) and then negate the result.
    (3) When we have a mix of Negated and Non-Negated Ops
    - We will apply (1) for Non-Negated ops and compute its' difference with all the Negated Ops.

    (NOT)
    - If it is a single primitive NOT Term, we will take the diff of all the doc_id with the doc_id of the term.

== Files included with this submission ==

List the files in your submission here and provide a short 1 line
description of each file.  Make sure your submission's files are named
and formatted correctly.

(1) index.py: It takes in user's input and calls the appropriate functions in inverted_index.py to build index and save to memory.
(2) inverted_index.py: It contains the main logic of constructing the dictionary and posting lists. It contains methods to aid in processing search queries.
(3) query.py: It takes in all the queries and calls the appropriate functions in query.py and write the final returned results.
(4) search.py: It contains the main logic of parsing the input query and evaluating results.
(5) Essay.txt: It contains our answers to the essay questions.
(6) dictionary.txt: It contains the terms of the inverted index. Each line is in the format of [A B C]
    where A is the term value, B is the length of the posting_list for A and C is the offset value of the line containing the term in posting.txt file.
(7) postings.txt: Each line is in the format of [A B] where A is the term value and B are the document ids associated with it separated by space.
(8) README.txt: This file contains the overview of the assignment.

== Statement of individual work ==

Please put a "x" (without the double quotes) into the bracket of the appropriate statement.

[x] We, A0173178X-A0172706E, certify that I/we have followed the CS 3245 Information
Retrieval class guidelines for homework assignments.  In particular, I/we
expressly vow that I/we have followed the Facebook rule in discussing
with others in doing the assignment and did not take notes (digital or
printed) from the discussions.  

[ ] I/We, A0000000X, did not follow the class rules regarding homework
assignment, because of the following reason:

<Please fill in>

We suggest that we should be graded as follows:

<Please fill in>

== References ==

<Please list any websites and/or people you consulted with for this
assignment and state their role>
