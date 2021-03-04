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
    For each file, in order to collect the vocabulary, we apply tokenisation and stemming on the document text.
    nltk.sent_tokenize() and nltk.word_tokenize() are used to tokenize sentences and words. Case folding is applied to all words.
    Punctuations are stripped. Stemmed values which only contain numbers are also removed. Stop words are not removed from the vocabulary.
    In order to reduce repeated stemming on the same words to improve speed of indexing, previously stemmed words are stored in stem_dict.
(c) Scalable Indexing Construction:
    SPIMI is implemented. We set 100000 to be the maximum number of lines that the memory can hold.
    We build the postings list of the terms as the term-docID pairs are processed.
    Terms are stored in a dictionary set. Posting lists are stored in the form of HashMap.
    When the number of pairs processed reaches the limit of 100000, we will then treat whatever that is currently held in memory to belong to a block.
    We will first sort the dictionary terms, then according to the sorted order, write their corresponding posting lists to the block file.
    Each line in the block file contains a term and a list of document ids.
    Once the entire content in memory has been written to a block file, we will then clear memory and continue processing the files.

    Eventually, we will process all the data files and have block files constructed along the way. The final step is now to
    merge these block files using the BISC merging method. In this method, we will open all the block files and read in X lines
    from each block file that was previously constructed. X is calculated to be Floor(100000/K) where K = number of block files.
    We will then perform K-Way merging.
    The dictionary.txt and posting.txt will be written.
(d) Skip Pointers:
    A skip pointer is added to the posting list every ceil(sqrt(len(posting_list))) items. It is stored inline with the
    document ids in the form "docID;skipID", where skipID is the docID the skip refers to.
    The final posting list has the form
    <term> <docID>;<skipID> <docID> ...

(e) Misc:
    The indexing phase also generates a list of all document ids, {all_doc_ids}, as well as a
    list of tokens sorted by frequency.
    The project also includes a utility script to generate random queries for testing.

<<Searching>>
(e) Parsing:
    We implement a tokeniser to parse the queries, which also recursively parses parenthesis.
    We then convert the tokenised query into an AST, implemented with the Query classes.
    When constructing the AST, we also flatten the operations where possible.

(f) Evaluation:
    (QueryTerm)
    - Returns the posting list associated with the term by looking up the dictionary and seeking
    to the specified offset in the postings file.

    (OR)
    - We use python's built in set union on all the evaluated operands

    (AND)
    (1) When we have to apply AND on operators without Negation, we will sort them by size and merge every two of them.
    - If the ops of AND is a primitive query term, we will apply skip pointers.
      Continuing from (d), during the search run time, for each C in B, we will check for the value after ; to see if the current doc_id has a skip pointer.
      The value gives us the next doc id value should the skip be taken. If it is present and does not have the pre-set val of -1, we will compare the values
      and decide whether to apply the skip.
      If the skip is to be applied, according to the length of the list, the jump value will be calculated.
    - If the ops of AND is not a primitive query term, we will make use of python set intersection to do the work. It is more time efficient to build the intersection
      compared to constructing the skip pointers at run time.
    (2) When the ops of AND are all Negated.
    - Applying De-Morgan's Law, we will perform UNION on the ops (without negation) and then negate the result.
    (3) When we have a mix of Negated and Non-Negated Ops
    - We will apply (1) for Non-Negated ops and compute its' difference with all the Negated Ops.

    (NOT)
    - Not is lazily evaluated, implemented with an is_flipped flag
    - It will only be evaluated if the output of the NOT operator is immediately needed, such as
    in the case where the root query is a NOT query, or when it is evaluated as part of an operand in an OR operator.
    - The NOT operator is evaluated using {all_doc_ids} - {matches}


Misc:
We initially used python set intersection, union, and difference operators for the merging, which was faster (~2x)
compared to the iterative merge implemented in this submitted version, even with skip lists.

== Files included with this submission ==

List the files in your submission here and provide a short 1 line
description of each file.  Make sure your submission's files are named
and formatted correctly.

(1) index.py: It takes in user's input and calls the appropriate functions in inverted_index.py to build index and save to memory.
(2) inverted_index.py: It contains the main logic of constructing the dictionary and posting lists. It contains methods to aid in processing search queries.
(3) query.py: It takes in all the queries and calls the appropriate functions in query.py and write the final returned results.
(4) search.py: It contains the main logic of parsing the input query and evaluating results.
(5) ESSAY.txt: It contains our answers to the essay questions.
(6) dictionary.txt: It contains the terms of the inverted index. Each line is in the format of [A B C]
    where A is the term value, B is the length of the posting_list for A and C is the offset value of the line containing the term in posting.txt file.
(7) postings.txt: Each line is in the format of [A B] where A is the term value and B are the document ids associated with it separated by space.
(8) README.txt: This file contains the overview of the assignment.
(9) generate_random_queries.py: Utility script to generate N queries with M terms each, mainly to test efficiency.

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
