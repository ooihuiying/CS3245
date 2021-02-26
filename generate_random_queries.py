import random

N = 100  # number of queries to generate for each type
M = 10  # number of terms in long queries


def random_term(min_freq=0, max_freq=10000, with_not=False):
    filtered = [item[0] for item in freq_dict.items() if min_freq < item[1] < max_freq]
    if with_not:
        return random.choice(["NOT ", ""]) + random.choice(filtered)
    return random.choice(filtered)


if __name__ == '__main__':
    freq_dict = {}
    queries = []
    with open("freq_sorted_dict.txt") as f:
        for line in f:
            term, freq = line.split(" ")
            freq_dict[term] = int(freq.strip())

        # single queries with >100 occurrences
        for i in range(N):
            queries.append(random_term(min_freq=100))

        # single NOT queries with >100 occurrences
        for i in range(N):
            queries.append("NOT {}".format(random_term(min_freq=100)))

        # AND queries with >100 occurrences each
        for i in range(N):
            queries.append("{} AND {}".format(random_term(min_freq=100, with_not=True), random_term(min_freq=100, with_not=True)))

        # OR queries with >100 occurrences each
        for i in range(N):
            queries.append("{} OR {}".format(random_term(min_freq=100, with_not=True), random_term(min_freq=100, with_not=True)))

        # M-term AND/OR queries
        for i in range(N):
            query_term = []
            for j in range(M):
                query_term.append(random_term(min_freq=100, with_not=True))
                query_term.append(random.choice(["AND", "OR"]))
            queries.append(" ".join(query_term[:-1]))

        with open("random_queries.txt", 'w') as fw:
            fw.write("\n".join(queries))
