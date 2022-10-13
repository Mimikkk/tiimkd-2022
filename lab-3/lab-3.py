from collections import defaultdict
import math
from typing import Iterable, Literal, Counter

from numpy.core.defchararray import strip

def readfile(filename: Literal[
  'wiki_en', 'wiki_eo', 'wiki_et', 'wiki_ht', 'wiki_la', 'wiki_nv', 'wiki_so',
  'sample0', 'sample1', 'sample2', 'sample3', 'sample4', 'sample5'
]):
  if (filename.startswith('wiki')):
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

def normalize(weights: dict):
  total = sum(weights.values())
  for key in weights: weights[key] /= total
  return weights

def entropy(probability: float | Iterable[float], *, base: int) -> float:
  if isinstance(probability, Iterable):
    return sum(map(bit_entropy, probability))
  return -probability * math.log(probability, base)

def bit_entropy(probability: float | Iterable[float]) -> float:
  return entropy(probability, base=2)

def conditional_entropy(probability: float | Iterable[float], *, degree: int, base: int) -> float:
  return 0

def conditional_bit_entropy(probability: float | Iterable[float], *, degree: int) -> float:
  return conditional_entropy(probability, degree=degree, base=2)

alphabet = 'abcdefghijklmnopqrstuvwxyz 12334567890'
alphabet_weights = normalize(Counter(alphabet))

locale_to_language_map = {
  'en': 'english',
  'eo': 'esperanto',
  'et': 'estonian',
  'so': 'somali',
  'ht': 'haitian',
  'la': 'latin',
  'nv': 'navajo',
}

degrees = (1, 2, 3, 4, 5)
if __name__ == '__main__':
  print(f"1. Entropy.")
  print(f"Entropy of a english alphanumeric alphabet: {bit_entropy(alphabet_weights.values()):.2f}")

  print()
  print(f"2. Language recognition.")
  (english_text, esperanto_text, estonian_text, somali_text, haitian_text, latin_text, navajo_text) = map(
    readfile, map(lambda x: f"wiki_{x}", locale_to_language_map)
  )

  (sample_0_text, sample_1_text, sample_2_text, sample_3_text, sample_4_text, sample_5_text) = map(
    readfile, map(lambda x: f"sample{x}", range(6))
  )

  locale: str
  language: str
  bit_entropy_averages = defaultdict(float)
  for (locale, language) in locale_to_language_map.items():
    text: str = locals()[f"{language}_text"]
    print(f"Conditional entropy of {language.capitalize()}.")
    print(f"- Sample of the language: {text[:100].strip()}...")
    for degree in degrees:
      probabilities = []
      entropy_value = conditional_bit_entropy(probabilities, degree=degree)
      bit_entropy_averages[degree] += entropy_value
      print(f"- Degree {degree} bit entropy {entropy_value}.")
    print()
  for degree in bit_entropy_averages: bit_entropy_averages[degree] /= len(locale_to_language_map)

  print(
    f"Average bit entropies of given languages are:",
    *map(lambda x: f"- Degree {x[0]}: {x[1]:.2f}.", bit_entropy_averages.items()),
    sep='\n'
  )

  print()
  print("2. Is given sample a natural language?")
  for i in range(6):
    print(f"Sample nr. '{i}'.")
    sample_text: str = locals()[f"sample_{i}_text"]
    print(f"- Sample: {sample_text[:100].strip()}...")

    for degree in degrees:
      print(f"- Degree {degree}.")
      probabilities = []
      if (conditional_bit_entropy(probabilities, degree=1) > 0):
        print(f"  - It appears it may be a natural language.")
      else:
        print(f"  - It may be not a natural language.")
    print()
