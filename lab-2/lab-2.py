from collections import Counter, OrderedDict, defaultdict
import operator
import random
from typing import Iterable, Literal

import numpy as np

def readfile(filename: Literal['hamlet', 'romeo', 'wiki_sample']):
  with open(f"resources/norm_{filename}.txt") as file:
    return file.read()

def ith(n: int) -> int:
  def curry(iterable: Iterable[int]):
    it = iter(iterable)
    for _ in range(n - 1): next(it, None)
    return next(it, None)
  return curry

def flatten(iterable: Iterable[Iterable]):
  return [item for sublist in iterable for item in sublist]

def normalize(weights: dict):
  total = sum(weights.values())
  for key in weights: weights[key] /= total
  return weights

def generate_words(weights: dict, *, k: int = 1):
  return random.choices(tuple(weights), weights=weights.values(), k=k)

def calculate_conditional_weights(text: str, degree: int):
  conditional_weights = {}
  ngrams = create_ngram_probabilities(text, degree)
  next_ngrams = create_ngram_probabilities(text, degree + 1)

  for ngram in next_ngrams:
    (main, last) = (tuple(ngram[:degree]), ngram[-1])

    if main not in conditional_weights: conditional_weights[main] = {}
    conditional_weights[main][last] = next_ngrams[ngram] / ngrams[main]

  for ngram in conditional_weights: normalize(conditional_weights[ngram])

  return conditional_weights

def create_ngram_probabilities(text: str, degree: int):
  words = text.split(' ')
  if degree == 0: return normalize(Counter(words))
  return normalize(Counter(tuple(words[i:i + degree]) for i in range(len(words) - degree + 1)))

def create_markov_chain_sentences(text: str, degree: int, *, k: int = 10, start: list[str] = None):
  ngram = start or generate_words(create_ngram_probabilities(text, 0))

  for deg in range(1, degree): ngram.extend(
    generate_words(calculate_conditional_weights(text, deg)[tuple(ngram)])
  )

  weights = calculate_conditional_weights(text, degree)

  result = ngram.copy()

  for i in range(k):
    result.extend(generate_words(weights[tuple(ngram)]))
    ngram = (*ngram[1:], result[-1])

  return ' '.join(result)

if __name__ == '__main__':
  [hamlet_text, romeo_text, wiki_sample_text] = map(readfile, ['hamlet', 'romeo', 'wiki_sample'])
  wiki_sample_text = wiki_sample_text

  print("1. Word frequencies.")
  words: Counter[str] = create_ngram_probabilities(wiki_sample_text, 0)
  print(f"Total unique words: {len(words)}")
  print(f"Which makes up {len(words) / words.total() * 100:.2f}% of all words")
  print(f"10 Most common words: {', '.join(map(ith(1), words.most_common(10)))}")
  print(f"30k Percentage of total: {sum(map(ith(2), words.most_common(30_000))) / words.total() * 100:.2f}%")
  print(f"6k Percentage of total: {sum(map(ith(2), words.most_common(6_000))) / words.total() * 100:.2f}%")

  print()
  print("2. First degree approximations.")
  hamlet_ngrams = create_ngram_probabilities(hamlet_text, 1)
  romeo_ngrams = create_ngram_probabilities(romeo_text, 1)
  wiki_sample_ngrams = create_ngram_probabilities(wiki_sample_text, 1)

  print(f"Hamlet: {' '.join(flatten(generate_words(hamlet_ngrams, k=42)))}")
  print(f"Romeo: {' '.join(flatten(generate_words(romeo_ngrams, k=42)))}")
  print(f"Wiki sample: {' '.join(flatten(generate_words(wiki_sample_ngrams, k=42)))}")

  print()
  print("3. Markov source based approximations.")
  print('- First degree approximations:')
  print(create_markov_chain_sentences(wiki_sample_text, 1, k=42))

  print()
  print('- Second degree approximations:')
  print(create_markov_chain_sentences(wiki_sample_text, 2, k=42))

  print()
  print('- Second degree approximations with a starting point:')
  print(create_markov_chain_sentences(wiki_sample_text, 2, k=42, start=['probability']))
