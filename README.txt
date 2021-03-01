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
    We only construct skip pointers when it is required from the query file. A function is exposed to take in a posting list and
    it will return another list which contains the index to jump to at a particular index of the list. The heuristic is to use
    evenly spaced skip pointers.

<<Searching>>
(e) Parsing:
    TODO
(f) Evaluation:
    TODO
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
