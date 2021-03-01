import getopt
import random
import sys

N = 100  # number of queries to generate for each type
M = 10  # number of terms in long queries


def random_op():
    return random.choice(["AND", "OR"])


def random_term(min_freq=0, max_freq=10000, with_not=False):
    filtered = [item[0] for item in freq_dict.items() if min_freq < item[1] < max_freq]
    if with_not:
        return random.choice(["NOT ", ""]) + random.choice(filtered)
    return random.choice(filtered)


def random_query(m, min_freq=0, max_freq=10000, brackets=True):
    out = []
    n = 0
    while n < m:
        if brackets and random.random() < 0.1:
            k = random.randint(1, m-n)
            out.append("({})".format(random_query(k, min_freq, max_freq, brackets=False)))
            n += k
        else:
            out.append(random_term(min_freq, max_freq, with_not=True))
            n += 1
        if n != m:
            out.append(random_op())

    return " ".join(out)


def usage():
    print("Usage: {} [-n N] [-m M]".format(sys.argv[0]))


if __name__ == '__main__':

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'n:m:')
        for o, a in opts:
            if o == '-n':
                N = int(a)
            elif o == '-m':
                M = int(a)
            else:
                assert False, "unhandled option {}".format(o)
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    freq_dict = {}
    queries = []
    with open("freq_sorted_dict.txt") as f:
        for line in f:
            term, freq = line.split(" ")
            freq_dict[term] = int(freq.strip())

        # single queries with >100 occurrences
        # for i in range(N):
        #     queries.append(random_term(min_freq=100))

        # single NOT queries with >100 occurrences
        # for i in range(N):
        #     queries.append("NOT {}".format(random_term(min_freq=100)))

        # AND queries with >100 occurrences each
        # for i in range(N):
        #     queries.append("{} AND {}".format(random_term(min_freq=100, with_not=True), random_term(min_freq=100, with_not=True)))

        # OR queries with >100 occurrences each
        # for i in range(N):
        #     queries.append("{} OR {}".format(random_term(min_freq=100, with_not=True), random_term(min_freq=100, with_not=True)))

        # M-term AND/OR queries
        # for i in range(N):
        #     query_term = []
        #     for j in range(M):
        #         query_term.append(random_term(min_freq=100, with_not=True))
        #         query_term.append(random.choice(["AND", "OR"]))
        #     queries.append(" ".join(query_term[:-1]))

        for i in range(N):
            queries.append(random_query(M, 100))

        with open("random_queries_1k.txt", 'w') as fw:
            fw.write("\n".join(queries))
