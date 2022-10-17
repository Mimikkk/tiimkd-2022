from collections import Counter
from bitarray import bitarray
from math import log2, ceil

def create(frequencies: dict[str, int]) -> str:
  return ''.join(sorted(frequencies, key=frequencies.get, reverse=True))

def create_encoding(code: str) -> dict[str, str]:
  required_bits = ceil(log2(len(code)))
  return {letter: f"{i:0{required_bits}b}" for (i, letter) in enumerate(code)}

def create_decoding(code: str) -> dict[str, str]:
  return {v: k for (k, v) in create_encoding(code).items()}

def readfile(filename: str) -> str:
  with open(filename, 'r') as file:
    return file.read()

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
  decoded = ''
  code_length = len(tuple(decoding)[0])

  position = 3
  offset = int(encoded[:position].to01(), 2)
  for i in range(position, len(encoded) - offset, code_length):
    decoded += decoding[encoded[i:i + code_length].to01()]
  return decoded

def save(encoded: bitarray, code: str, name: str):
  with open(f'results/{name}.encoded', 'wb') as file:
    file.write(encoded)

  with open(f'results/{name}.code', 'w') as file:
    file.write(code)

def load(name: str):
  with open(f"results/{name}.encoded", 'rb') as file:
    encoded = bitarray()
    encoded.fromfile(file)

  with open(f"results/{name}.code", 'r') as file:
    code = file.read()

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
  original = readfile('resources/norm_wiki_sample.txt')
  print(f"original text: {original[:100]}...")

  filename = 'test'
  code = create(Counter(original))
  decoding = create_decoding(code)
  encoded = encode(original, create_encoding(code))
  save(encoded, code, filename)

  encoded, code = load(filename)
  decoded = decode(encoded, create_decoding(code))
  print(f"Decoded text:  {decoded[:100]}...")
