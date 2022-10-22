from itertools import pairwise, islice, takewhile
import os
from typing import Literal, Iterable
from bitarray import bitarray
from math import log2, ceil
from operator import itemgetter

# region [[Utilities]]
def readfile(filename: str, mode: Literal['r', 'rb', 'r+b'] = 'rb') -> str:
  with open(filename, mode) as file:
    return file.read()

def format_size(size: int):
  sizes = ['b', 'Kib', 'Mib', 'Gib', 'Tib', 'Pib', 'Eib', 'Zib', 'Yib']
  i = 0
  while size >= 1024 and i < len(sizes) - 1:
    size /= 1024
    i += 1

  if i == 0: return f"{size} {sizes[i]}"
  return f"{size:.2f} {sizes[i]}"

def to_int(bitarray: bitarray) -> int:
  return int(bitarray.to01(), 2)

def safeconcat(a, b):
  a = a if isinstance(a, tuple) else (a,)
  b = b if isinstance(b, tuple) else (b,)
  return (*a, *b)
# endregion

def encode(text: str, max_size: int = None) -> tuple[bitarray, dict[int, str]]:
  def encode(text: list[int], encoding: dict[int, str]):
    encoded = bitarray(''.join(map(encoding.get, text)))

    # It's to add extra space at the end of the encoding so its
    # length is a multiple of byte.
    filling = (len(encoded) + 3) % 8
    offset = 8 - filling if filling != 0 else 0
    code_offset = bitarray(bin(offset)[2:].zfill(3))
    encoded = code_offset + encoded
    return encoded

  encoded = []
  encoded_chars = dict(map(reversed, enumerate(set(text))))

  [current, *rest] = text
  for next in rest:
    combined = safeconcat(current, next)
    if combined in encoded_chars:
      current = combined
      continue

    if max_size is None or not len(encoded_chars) >= max_size:
      encoded_chars[combined] = len(encoded_chars)

    encoded.append(encoded_chars[current])
    current = next
  encoded.append(encoded_chars[current])

  code_len = ceil(log2(len(encoded_chars)))
  encoding = {n: f'{n:0{code_len}b}' for n in encoded_chars.values()}
  code = f"{code_len}:{':'.join(map(str, set(text)))}"

  return encode(encoded, encoding), code

def decode(encoded: bitarray, decoding: dict[int | Literal['bits'], int]):
  text_len = len(encoded)
  code_len = decoding['bits']
  decoding = dict(decoding)
  decoding.pop('bits')

  code: bitarray
  codes = tuple(map(
    to_int,
    (encoded[i:i + code_len] for i in range(3, text_len, code_len))
  ))

  count = len(decoding)
  sequence = decoding[codes[0]]
  current = sequence
  result = [sequence]
  for (previous, next) in pairwise(codes):
    sequence = safeconcat(decoding[previous], current) \
      if next not in decoding \
      else decoding[next]
    current = sequence[0] if isinstance(sequence, tuple) else sequence
    decoding[count] = safeconcat(decoding[previous], current)
    count += 1
    result.extend(sequence if isinstance(sequence, tuple) else (sequence,))

  return bytes(result)

def save(name: str, encoded: bitarray, code: str):
  os.makedirs(os.path.dirname(f'results/{name}'), exist_ok=True)

  with open(f'results/{name}.encoded', 'wb') as file:
    file.write(encoded.tobytes())

  with open(f'results/{name}.code', 'wb') as file:
    (code_len, *codes) = map(int, code.split(":"))
    file.write(bytes([code_len, *codes]))

def load(name: str) -> tuple[bitarray, str]:
  # Remove overflow bits.
  (encoded := bitarray()).frombytes(readfile(f"results/{name}.encoded", 'rb'))
  for _ in range(to_int(encoded[:3])): encoded.pop()

  (code_len, *codes) = readfile(f"results/{name}.code", 'rb')
  code = f"{code_len}:{':'.join(map(str, codes))}"

  return encoded, code

def create_decoding(code: str) -> dict[int | Literal['bits'], int]:
  (code_len, *codes) = map(int, code.split(':'))
  decoding = dict(enumerate(codes))
  decoding['bits'] = code_len
  return decoding

def verify():
  try:
    original = 'test text'
    (encoded, code) = encode(original, size)
    decoded = decode(encoded, create_decoding(code))
    assert original == decoded
    print('Encoding and decoding is correct')
  except AssertionError:
    print('Encoding and decoding is incorrect')

sizes = ((None, "full"), (2 ** 10, f"{2 ** 10}"),)
if __name__ == '__main__':
  filename = "norm_wiki_sample.txt"
  original = readfile(f"resources/{filename}")[:800000]
  print(f"Size before compression: {format_size(len(original) * 8)}.")

  for (size, subdir) in sizes:
    name = f'{subdir}_{filename}'

    (encoded, code) = encode(original, size)
    save(name, encoded, code)

    (encoded, code) = load(name)
    decoding = create_decoding(code)
    decoded = decode(encoded, decoding)

    assert original == decoded
    print()
    print(f"Original text: {original[:100]}...")
    print(f"Decoded text : {decoded[:100]}...")
    print(f'Dictionary size: {size or "unlimited"} codes.')
    print(f'Size after compression: {format_size(len(encoded))}.')
    print(f"Compression ratio: {len(encoded) / (len(original) * 8) * 100:.2f}%.")
