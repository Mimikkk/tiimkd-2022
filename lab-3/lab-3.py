from collections import defaultdict
import math
from typing import Iterable, Literal, Counter

def readfile(filename: Literal[
  'wiki_en', 'wiki_eo', 'wiki_et', 'wiki_ht', 'wiki_la', 'wiki_nv', 'wiki_so',
  'sample0', 'sample1', 'sample2', 'sample3', 'sample4', 'sample5'
]):
  if filename.startswith('wiki'):
    return readfile(f"norm_{filename}")

  with open(f"resources/{filename}.txt") as file:
    return file.read()

def ith(n: int) -> int:
  def curry(iterable: Iterable[int]):
    it = iter(iterable)
    for _ in range(n - 1): next(it, None)
    return next(it, None)
  return curry

def flatten(iterable: Iterable[Iterable]):
  return [item for sublist in iterable for item in sublist]

def about_between(value: float, min: float, max: float, *, modifier: float = 0) -> bool:
  return min * (1 - modifier) <= value <= max * (1 + modifier)

def normalize(weights: dict):
  total = sum(weights.values())
  for key in weights: weights[key] /= total
  return weights

def entropy(probability: float | Iterable[float] | dict[str, float], *, base: int) -> float:
  if isinstance(probability, dict):
    return entropy(probability.values(), base=base)
  if isinstance(probability, Iterable):
    return sum(map(lambda x: entropy(x, base=base), probability))
  return -probability * math.log(probability, base)

def bit_entropy(probability: float | Iterable[float] | dict[str, float]) -> float:
  return entropy(probability, base=2)

def conditional_entropy(weights, conditional_weights, *, base: int) -> float:
  if len(next(iter(weights))) == 1:
    return entropy(weights, base=base)
  return -sum(
    weights[(*x, y)] * math.log(probability, base)
    for (x, conditions) in conditional_weights.items()
    for (y, probability) in conditions.items()
  )

def conditional_bit_entropy(weights, conditional_weights) -> float:
  return conditional_entropy(weights, conditional_weights, base=2)

def create_ngram_weights(text: str, degree: int, *, kind: Literal['letters', 'words']):
  items = text if kind == 'letters' else text.split()
  if degree == 0: return normalize(Counter[any](items))
  return normalize(Counter[any](tuple(items[i:i + degree]) for i in range(len(items) - degree + 1)))

def calculate_conditional_weights(text, degree, *, kind: Literal['letters', 'words']):
  if degree == 0: return create_ngram_weights(text, degree, kind=kind)
  conditional_weights = {}
  ngrams = create_ngram_weights(text, degree, kind=kind)
  next_ngrams = create_ngram_weights(text, degree + 1, kind=kind)

  for ngram in next_ngrams:
    (main, last) = (ngram[:-1], ngram[-1])

    if main not in conditional_weights: conditional_weights[main] = {}
    conditional_weights[main][last] = next_ngrams[ngram] / ngrams[main]

  return conditional_weights

alphabet = 'abcdefghijklmnopqrstuvwxyz 12334567890'
alphabet_weights = create_ngram_weights(alphabet, 0, kind="letters")

locale_to_language_map = {
  'en': 'english',
  'eo': 'esperanto',
  'et': 'estonian',
  'so': 'somali',
  'ht': 'haitian',
  'la': 'latin',
  'nv': 'navajo',
}

degrees = (0, 1, 2, 3, 4)
kinds = ("words", "letters")
if __name__ == '__main__':
  print(f"1. Entropy.")
  print(f"Entropy of a english alphanumeric alphabet: {bit_entropy(alphabet_weights):.2f}")

  print(f"2a. Language entropy.")
  (english_text, esperanto_text, estonian_text, somali_text, haitian_text, latin_text, navajo_text) = map(
    lambda text: text[:80_000],
    map(readfile, map(lambda x: f"wiki_{x}", locale_to_language_map))
  )

  (sample_0_text, sample_1_text, sample_2_text, sample_3_text, sample_4_text, sample_5_text) = map(
    readfile, map(lambda x: f"sample{x}", range(6))
  )

  words_bit_entropy_mins = defaultdict(lambda: float('inf'))
  words_bit_entropy_maxes = defaultdict(float)
  letters_bit_entropy_mins = defaultdict(lambda: float('inf'))
  letters_bit_entropy_maxes = defaultdict(float)
  locale: str
  language: str
  mins: defaultdict[float]
  maxes: defaultdict[float]
  for (locale, language) in locale_to_language_map.items():
    text: str = locals()[f"{language}_text"]
    print(f"Conditional entropy of {language.capitalize()}.")
    print(f"- Sample of the language: {text[:100].strip()}...")
    for kind in kinds:
      mins = locals()[f"{kind}_bit_entropy_mins"]
      maxes = locals()[f"{kind}_bit_entropy_maxes"]
      for degree in degrees:
        weights = create_ngram_weights(text, degree + 1, kind=kind)
        conditional_weights = calculate_conditional_weights(text, degree, kind=kind)
        value = conditional_bit_entropy(weights, conditional_weights)
        mins[degree] = min(mins[degree], value)
        maxes[degree] = max(maxes[degree], value)

        print(f"  - {degree}-degree conditional bit entropy ({kind}): {value:.2f}")
    print()

  for kind in kinds:
    mins = locals()[f"{kind}_bit_entropy_mins"]
    maxes = locals()[f"{kind}_bit_entropy_maxes"]
    print(
      f"Min/Max bit entropies ({kind}) of given language:",
      *map(lambda x: f"- {x[0]}-degree: {x[1]:.2f} - {x[2]:.2f}.", zip(degrees, mins.values(), maxes.values())),
      sep='\n'
    )

  print()
  print("2b. Is given sample a natural language?")
  for i in range(6):
    print(f"Sample nr. '{i}'.")
    text: str = locals()[f"sample_{i}_text"][:80_000]
    print(f"- Sample: {text[:100].strip()}...")

    for kind in kinds:
      mins = locals()[f"{kind}_bit_entropy_mins"]
      maxes = locals()[f"{kind}_bit_entropy_maxes"]

      valid_count = 0
      for degree in degrees:
        weights = create_ngram_weights(text, degree + 1, kind=kind)
        conditional_weights = calculate_conditional_weights(text, degree, kind=kind)
        value = conditional_bit_entropy(weights, conditional_weights)
        print(f"  - {degree}-degree conditional bit entropy ({kind}): {value:.2f}.")

        if about_between(value, mins[degree], maxes[degree]):
          valid_count += 1
          print(f"- {degree}-degree ({kind}): Is within acceptable range.")
        else:
          print(f"- {degree}-degree ({kind}): Is not within acceptable range.")
      if valid_count / len(degrees) >= 0.5:
        print(f"  - ({kind}): It appears it may be a natural language.")
      else:
        print(f"  - ({kind}): It may be not a natural language.")
    print()
