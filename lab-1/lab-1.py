from collections import Counter
import random
from typing import Literal

alphabet_weights = Counter(' abcdefghijklmnopqrstuvwxyz')
def readfile(filename: Literal['hamlet', 'romeo', 'wiki_sample']):
  with open(f"resources/norm_{filename}.txt") as file:
    return file.read()

def average_length(text: str):
  words = text.split(' ')
  return sum(map(len, words)) / len(words)

def generate_letters(n: int, weights: dict):
  return random.choices(tuple(weights), weights=weights.values(), k=n)

def create_ngrams(text: str, n: int = 1):
  return normalize(Counter(text[i:i + n] for i in range(len(text) - n + 1)))

def normalize(weights: dict):
  total = sum(weights.values())
  for key in weights: weights[key] /= total
  return weights

def calculate_conditional_weights(text: str, n: int):
  conditional_weights = {}
  ngrams = create_ngrams(text, n)
  next_ngrams = create_ngrams(text, n + 1)

  for ngram in ngrams:
    conditional_weights[ngram] = {}

    for letter in alphabet_weights:
      new_key = ngram + letter

      if new_key in next_ngrams:
        conditional_weights[ngram][letter] = next_ngrams[new_key] / ngrams[ngram]
    normalize(conditional_weights[ngram])

  return conditional_weights

def create_markov_chain_sentences(n: int, degree: int, start: str, weights: dict):
  result = start
  while len(result) < n and (ngram := result[-degree:]):
    if ngram not in weights:
      [generated] = generate_letters(1, alphabet_weights)
    else:
      [generated] = generate_letters(1, weights[ngram])

    result += generated

  return result

if __name__ == '__main__':
  print()
  print("1. Zero degree.")
  gibberish_text = ''.join(generate_letters(n=10000, weights=alphabet_weights))
  print(f"Gibberish: {gibberish_text[:100]}...")
  print(f"Average gibberish word length: {average_length(gibberish_text)}")

  text = readfile('hamlet')

  print()
  print("2. Letter weights.")
  print(create_ngrams(text, 1))

  print()
  print("3. First degree.")
  weights = create_ngrams(text, 1)
  first_degree_text = ''.join(generate_letters(n=10000, weights=weights))

  print(f'Generated average word length: {average_length(first_degree_text)}')
  print(f'Original average word length: {average_length(text)}')

  print()
  print("4. Conditional weigths of letters.")
  common = Counter(text).most_common(2)
  print(f"Most common: {common}")

  conditional_weights = calculate_conditional_weights(text, 1)
  for (letter, _) in common: print(f"Weights after {letter}: \n{conditional_weights[letter]}")

  print()
  print("5. Markov approximations.")
  for degree in [1, 3, 5]:
    print(f"- degree: {degree}")

    weights = calculate_conditional_weights(text, degree)
    n_degree_text = create_markov_chain_sentences(n=10000, degree=degree, start='probability', weights=weights)

    print(f"Generated text: {n_degree_text[:100]}...")
    print(f"Average word length: {average_length(n_degree_text)}")
    print()
