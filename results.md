**Word Normalising** 

*  Removing Numbers from dictionary terms

There are a total of 32375 terms. 
If we add the check for removing numerical values with w_token.isnumeric(), the total number of terms reduces to 20939. 
Note that there are still terms comprising of a mix of integers and alphabets such as 109billion etc.

*  Removing Stop words

HY: Currently i am not too sure if we should remove stop words. In the case that the query term is a stop word, then we will not be able to perform search? Therefore, the current implementation does not remove stop words.

