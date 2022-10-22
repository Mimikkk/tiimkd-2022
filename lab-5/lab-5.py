from collections import Counter
import math
from typing import Iterable, Literal

from bitarray import bitarray
import operator

alphanumeric = ' abcdefghijklmnopqrstuvwxyz0123456789'

def readfile(filename: str, mode: Literal['r', 'rb', 'r+b'] = 'r') -> str:
  with open(filename, mode) as file:
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

def calculate_average_length(weights: dict[str, float], encoding: dict[str, str]):
  return sum(map(lambda x: len(encoding[x]) * weights[x], weights))

def create_weights(text: str):
  return normalize(Counter(text))

def create(weights: dict[str, float]) -> dict[str, float]:
  sorted_weights = dict(sorted(weights.items(), key=operator.itemgetter(1), reverse=False))
  class Node(object):
    def __init__(self, label=None, probability=None, left=None, right=None):
      self.left = left
      self.right = right
      self.is_leaf = not left and not right

      if self.is_leaf:
        self.label = label
        self.probability = probability
      elif left and right:
        self.label = left.label + right.label
        self.probability = left.probability + right.probability

    @classmethod
    def from_weights(cls, weights: dict[str, float]):
      return cls.from_items(weights.items())

    @classmethod
    def from_items(cls, items: Iterable[tuple[str, float]]):
      return cls.from_nodes(map(lambda x: cls(*x), items))

    @classmethod
    def from_nodes(cls, nodes: Iterable['Node']):
      nodes = list(nodes)
      while len(nodes) > 1:
        nodes.sort(key=lambda x: x.probability)
        nodes = [cls(left=nodes[0], right=nodes[1])] + nodes[2:]
      return nodes[0]

  encoding = {}
  stack = [(Node.from_weights(sorted_weights), '')]
  while stack:
    node, key = stack.pop()

    if node.is_leaf:
      encoding[node.label] = key
    else:
      if node.left: stack.append((node.left, f'{key}0'))
      if node.right: stack.append((node.right, f'{key}1'))

  return ':'.join(map(''.join, encoding.items()))

def create_encoding(code: str) -> dict[str, str]:
  return dict(map(lambda x: (x[0], x[1:]), code.split(':')))

def create_decoding(code: str) -> dict[str, str]:
  return {v: k for (k, v) in create_encoding(code).items()}

def encode(text: str, encoding: dict[str, str]):
  encoded = bitarray(''.join(map(encoding.get, text)))

  # It's to add extra space at the end of the encoding so its
  # length is a multiple of byte.
  filling = (len(encoded) + 3) % 8
  offset = 8 - filling if filling != 0 else 0
  code_offset = bitarray(bin(offset)[2:].zfill(3))
  encoded = code_offset + encoded

  return encoded

def decode(encoded: bitarray, decoding: dict[str, str]):
  min_code_len = min(map(len, decoding))

  # It's to prevent extra symbols from the overflow of the last byte.
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

def save(encoded: bitarray, code: str, name: str):
  with open(f"results/{name}.encoded", 'wb') as file:
    file.write(encoded.tobytes())

  with open(f"results/{name}.code", 'w') as file:
    file.write(code)

def load(name: str):
  (encoded := bitarray()).frombytes(readfile(f'results/{name}.encoded', 'rb'))
  code = readfile(f'results/{name}.code')
  return encoded, code

def verify():
  try:
    original = 'test text'
    code = create(Counter(original))
    encoded = encode(original, create_encoding(code))
    decoded = decode(encoded, create_decoding(code))
    assert original == decoded
    print('Encoding and decoding is correct')
  except AssertionError:
    print('Encoding and decoding is incorrect')

if __name__ == '__main__':
  verify()

  original = readfile('resources/norm_wiki_sample.txt')[:80000]
  weights = create_weights(original)
  entropy = calculate_entropy(weights, base=2)

  print()
  print("1. Coding effectivity.")
  print(f'Entropy (letters): {entropy}')
  bits = 6
  print(f'Average code length: {bits} bits')
  print(f'Coding effectivity from the previous laboratory: {entropy / bits * 100:.2f}%')

  print()
  print(f"2. Huffman encoding.")

  weights = create_weights(original)
  code = create(weights)
  encoding = create_encoding(code)
  average_length = calculate_average_length(weights, encoding)
  print(f"Average code length: {average_length:.2f} bits")
  print(f'Coding effectivity: {entropy / average_length * 100:.2f}%')

  encoded = encode(original, encoding)
  filename = 'test'
  save(encoded, code, filename)
  encoded, code = load(filename)
  decoded = decode(encoded, create_decoding(code))
  print(f"Original text is: {original[:100]}...")
  print(f"Decoded text is:  {decoded[:100]}...")
