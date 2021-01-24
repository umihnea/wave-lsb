import argparse
import logging
import os
import sys

import bitarray
import numpy as np
from scipy.io.wavfile import read, write


def bits(n: int):
    return [0 if x == '0' else 1 for x in np.binary_repr(n, width=8)]


def erase_lsb(x):
    return x & ~1


def encode(logger, cover_file, output_file, message: str) -> int:
    message_bytes = bytearray()
    message_bytes.extend([ord(character) for character in message])
    message_bytes.extend(b'\0')  # Add a sequence terminator

    rate, wav_data = read(cover_file)

    initial_shape = wav_data.shape
    flat_data = wav_data.flatten()

    # sparse_message contains the bits for each character in message_bytes
    # extended to fit the data type in the wav_file
    message_bit_length = len(message_bytes) * 8
    if flat_data.shape[0] < message_bit_length:
        logger.error(
            "Cover file too small for message. cover: %d bytes < message: %d bits.",
            flat_data.shape[0],
            message_bit_length
        )
        return 1

    sparse_message = np.empty(message_bit_length, dtype=flat_data.dtype)
    i = 0
    for byte in message_bytes:
        for bit in bits(byte):
            sparse_message[i] = bit
            i += 1

    # Perform LSB substitution on the cover data
    # final byte = (initial byte & ~1) | message bit
    data = np.copy(flat_data)
    data[0: message_bit_length] = np.bitwise_or(
        erase_lsb(data[0: message_bit_length]),
        sparse_message
    )

    data = data.reshape(initial_shape)
    write(output_file, rate, data)

    return 0


def decode(logger, input_file) -> str:
    sequence = []
    rate, wav_data = read(input_file)
    flat_data = wav_data.flatten()

    start = 0
    chunk_size = 8
    while start < flat_data.shape[0]:
        chunk = flat_data[start:start + chunk_size]
        start += chunk_size

        # Recompose a byte from the LSBs of the values
        # from the current chunk, then map it to an ASCII.
        lsb_byte = bitarray.bitarray([x & 1 for x in chunk])
        character = lsb_byte.tobytes().decode("ascii")

        if ord(character) == 0:
            break

        sequence.append(character)

    return "".join(sequence)


def valid_for_encoding(args) -> bool:
    if args.path is None or args.message is None or args.output is None:
        return False

    if not os.path.isfile(args.path):
        return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Use a LSB technique to encode a message in a wave file.",
    )
    parser.add_argument("path", help="path to cover file for encoding or to input file for decoding")
    parser.add_argument("-d", "--decode", action="store_true", help="if set, the input file will be decoded")
    parser.add_argument("-m", "--message", help="message to encode in encoding mode")
    parser.add_argument("-o", "--output", help="output file name")

    logging.basicConfig(level=logging.DEBUG)

    args = parser.parse_args()
    if args.decode:
        message = decode(logging.getLogger("decode"), args.path)
        print(message)
        print()
        return

    if not valid_for_encoding(args):
        print("Invalid arguments for encoding. --message and --output are necessary.")
        sys.exit(1)

    code = encode(
        logging.getLogger("encode"),
        args.path,
        args.output,
        args.message
    )

    sys.exit(code)


if __name__ == "__main__":
    main()
