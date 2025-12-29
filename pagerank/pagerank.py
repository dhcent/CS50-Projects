import os
import random
import re
import sys

DAMPING = 0.85
SAMPLES = 10000


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python pagerank.py corpus")
    corpus = crawl(sys.argv[1])
    ranks = sample_pagerank(corpus, DAMPING, SAMPLES)
    print(f"PageRank Results from Sampling (n = {SAMPLES})")
    for page in sorted(ranks):
        print(f"  {page}: {ranks[page]:.4f}")
    ranks = iterate_pagerank(corpus, DAMPING)
    print(f"PageRank Results from Iteration")
    for page in sorted(ranks):
        print(f"  {page}: {ranks[page]:.4f}")


def crawl(directory):
    """
    Parse a directory of HTML pages and check for links to other pages.
    Return a dictionary where each key is a page, and values are
    a list of all other pages in the corpus that are linked to by the page.
    """
    pages = dict()

    # Extract all links from HTML files
    for filename in os.listdir(directory):
        if not filename.endswith(".html"):
            continue
        with open(os.path.join(directory, filename)) as f:
            contents = f.read()
            links = re.findall(r"<a\s+(?:[^>]*?)href=\"([^\"]*)\"", contents)
            pages[filename] = set(links) - {filename}

    # Only include links to other pages in the corpus
    for filename in pages:
        pages[filename] = set(
            link for link in pages[filename]
            if link in pages
        )

    return pages


def transition_model(corpus, page, damping_factor):
    """
    Return a probability distribution over which page to visit next,
    given a current page.

    With probability `damping_factor`, choose a link at random
    linked to by `page`. With probability `1 - damping_factor`, choose
    a link at random chosen from all pages in the corpus.
    """
    probability_dict = {}
    # Pages in terms of strings
    choices = corpus.get(page) # Probability of each page that is linked to current page.
    if len(choices) == 0:
        for pg in corpus:
            probability_dict[pg] = 1 / len(corpus)
        return probability_dict

    page_probability = (damping_factor / len(choices)) + ((1 - damping_factor) / len(corpus))

    

    # Iterate through each page in Corpus. If pg is linked, include page probability. Otherwise,
    # only include the randomness factor
    for pg in corpus:
        if pg in choices:
            probability_dict[pg] = page_probability
        else:
            probability_dict[pg] = (1 - damping_factor) / len(corpus)
    return probability_dict


def sample_pagerank(corpus, damping_factor, n):
    """
    Return PageRank values for each page by sampling `n` pages
    according to transition model, starting with a page at random.

    Return a dictionary where keys are page names, and values are
    their estimated PageRank value (a value between 0 and 1). All
    PageRank values should sum to 1.
    """
    counts = {}
    pages = []
    probabilities = []

    for pg in corpus:
        counts[pg] = 0

    # Randomize starting page
    page = random.choice(list(corpus.keys()))
    for i in range(n):
        counts[page] += 1

        # Get probability distribution, move information into 2 lists.
        probability_distributions = transition_model(corpus, page, DAMPING)
        for pg, probability in probability_distributions.items():
            pages.append(pg)
            probabilities.append(probability)

        # Randomly select page based on distribution. Clear when finished.
        page = random.choices(pages, probabilities, k=1)[0] # choices returns a list. we want the first pg in the list
        pages.clear()
        probabilities.clear()
    
    estimated_PR = {}
    for pg, count in counts.items():
        estimated_PR[pg] = count / n

    return estimated_PR


def iterate_pagerank(corpus, damping_factor):
    """
    Return PageRank values for each page by iteratively updating
    PageRank values until convergence.

    Return a dictionary where keys are page names, and values are
    their estimated PageRank value (a value between 0 and 1). All
    PageRank values should sum to 1.
    """
    page_ranks = {}
    for pg in corpus:
        page_ranks[pg] = 1 / len(corpus)
    while True:
        num_changed = 0
        for pg in page_ranks:
            # Sum neighbor page ranks
            total = 0
            for i in corpus:
                if len(corpus[i]) == 0:
                    total += page_ranks[i] / len(corpus)
                elif pg in corpus[i]:
                    total += page_ranks[i] / len(corpus[i])
                
            # Calculate new page rank in accordance to the formula
            new_page_rank = (1 - damping_factor) / len(corpus) + damping_factor * total
            # Record the number of vals changed
            if abs(new_page_rank - page_ranks[pg]) > 0.001:
                num_changed += 1
            page_ranks[pg] = new_page_rank
        if num_changed == 0:
            break
    return page_ranks
    


if __name__ == "__main__":
    main()
