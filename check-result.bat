python search.py -d dictionary.txt -p postings.txt -q test/queries-1.txt -o test/actual-results-1.txt
python search.py -d dictionary.txt -p postings.txt -q test/queries-2.txt -o test/actual-results-2.txt
python search.py -d dictionary.txt -p postings.txt -q test/queries-3.txt -o test/actual-results-3.txt

echo Test 1
FC test\actual-results-1.txt test\expected-outputs-1.txt
echo Test 2
FC test\actual-results-2.txt test\expected-outputs-2.txt
echo test 3
FC test\actual-results-3.txt test\expected-outputs-3.txt