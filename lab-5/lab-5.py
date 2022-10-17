from collections import Counter
import math
from typing import Iterable

from bitarray import bitarray
import operator

alphanumeric = ' abcdefghijklmnopqrstuvwxyz0123456789'

class Tree(object):
  def __init__(self, label=None, prob=None, left=None, right=None):
    self.left = left
    self.right = right
    self.label = label if not left and not right else left.label + right.label
    self.probability = prob if not left and not right else left.probability + right.probability
    self.isLeaf = not left and not right

  def __repr__(self):
    if self.isLeaf:
      return f'"{self.label}": {self.probability}'
    return f'"{self.label}": {{{self.left}, {self.right}}}'

class TreeList(object):
  def __init__(self, trees: list[Tree]):
    self.inner = sorted(trees, key=lambda x: x.probability)

  def append(self, tree: Tree):
    self.inner.append(tree)
    self.inner.sort(key=lambda x: x.probability)

  def __len__(self):
    return len(self.inner)

  def pop(self, index: int) -> Tree:
    return self.inner.pop(index)

  def __getitem__(self, index: int) -> Tree:
    return self.inner[index]

  def __str__(self):
    return ' '.join(self.inner)

  def __repr__(self):
    return self.inner

def readfile(filename: str) -> str:
  with open(filename, 'r') as file:
    return file.read()

def normalize(weights: dict[str, float]) -> dict[str, float]:
  total = sum(weights.values())
  for key in weights: weights[key] /= total
  return weights

def calculate_entropy(probability: float | Iterable[float] | dict[str, float], *, base: int) -> float:
  if isinstance(probability, dict):
    return calculate_entropy(probability.values(), base=base)
  if isinstance(probability, Iterable):
    return sum(map(lambda x: calculate_entropy(x, base=base), probability))
  return -probability * math.log(probability, base)

def create_encoding_recursively(tree: Tree, encoding: dict[str, int], key: str):
  if tree.isLeaf:
    encoding[tree.label] = key
    return
  else:
    key += '0'
    create_encoding_recursively(tree.left, encoding, key)
    key = key[:-1] + '1'
    create_encoding_recursively(tree.right, encoding, key)

def create_tree(weights: dict[str, float]):
  trees = TreeList([Tree(key, value) for key, value in weights.items()])
  while (len(trees) != 1):
    trees.append(Tree(left=trees.pop(0), right=trees.pop(0)))
  return trees[0]

def create_sorted_letter_weights(text: str):
  letters = normalize(Counter(text))
  return dict(sorted(letters.items(), key=operator.itemgetter(1), reverse=False))

def create(weights: dict[str, float]) -> tuple[dict[str, str], dict[str, str]]:
  encoding = {}
  create_encoding_recursively(create_tree(weights), encoding, '')
  decoding = {value: key for key, value in encoding.items()}
  return encoding, decoding

def create_encoding(code: str) -> dict[str, str]:
  return

def create_decoding(code: str) -> dict[str, str]:
  return {v: k for (k, v) in create_encoding(code).items()}

def encode(text: str, encoding: dict[str, str]):
  encoded = bitarray()
  for letter in map(encoding.__getitem__, text):
    encoded.extend(letter)

  filling = (len(encoded) + 3) % 8
  offset = 8 - filling if filling != 0 else 0
  code_offset = bitarray(bin(offset)[2:].zfill(3))
  encoded = code_offset + encoded

  return encoded

def decode(encoded: bitarray, decoding: dict[str, str]):
  min_code_len = min(map(len, decoding))

  position = 3
  offset = int(encoded[:position].to01(), 2)
  decoded = ''
  while position < len(encoded) - offset:
    code_len = min_code_len
    while (code := encoded[position:position + code_len].to01()) \
        not in decoding:
      code_len += 1
    decoded += decoding[code]
    position += code_len

  return decoded

def save(encoded: bitarray, encoding: dict[str, str], name: str):
  with open(f"results/{name}.encoded", 'wb') as file:
    file.write(encoded.tobytes())

  with open(f"results/{name}.code", 'w') as file:
    for key, value in encoding.items():
      file.write(key + value + "\n")

def load(name: str):
  with open(f'results/{name}.encoded', 'rb') as file:
    encoded = bitarray()
    encoded.frombytes(file.read())

  encoding = {}
  with open(f'results/{name}.code', 'r') as file:
    for line in file.readlines():
      s = line.replace('\n', '')
      encoding[s[0]] = s[1:]

  decoding = {value: key for key, value in encoding.items()}
  return encoded, encoding, decoding

def verify():
  try:
    text = 'text to verify correctness of encoding and decoding algorithm'
    encoding, decoding = create(create_sorted_letter_weights(text))
    encoded = encode(text, encoding)
    decoded = decode(encoded, decoding)
    assert text == decoded
    print('Encoding and decoding is correct')
  except AssertionError:
    print('Encoding and decoding is incorrect')

if __name__ == '__main__':
  verify()
  print()

  text = readfile('resources/norm_wiki_sample.txt')

  weights = create_sorted_letter_weights(text)
  entropy = calculate_entropy(weights, base=2)
  print(f'Entropy (letters): {entropy}')
  bits = 6
  print(f'Average code length: {bits} bits')
  print(f'Coding effectivity from the previous laboratory: {entropy / bits * 100:.2f}%')

  weights = create_sorted_letter_weights(text)
  encoding, decoding = create(weights)

  average_length = sum(len(key) * weights[v] for v, key in encoding.items())
  print()
  print(f"Average code length: {average_length:.2f} bits")
  print(f'Coding effectivity: {entropy / average_length * 100:.2f}%')

  encoded = encode(text, encoding)
  save(encoded, encoding, 'test')

  encoded, encoding, decoding = load('test')
  decoded = decode(encoded, decoding)
