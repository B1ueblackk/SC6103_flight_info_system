import math

def bytes_to_binary_string(data: bytes) -> str:
    # Convert each byte to an 8-bit binary string and join them into a single string
    return ''.join(format(byte, '08b') for byte in data)

def string_to_binary_string(data: str) -> str:
    return bytes_to_binary_string(data.encode('utf-8'))

def binary_string_to_string(binary_string: str) -> str:
    # Split binary string into 8-bit chunks
    chars = [binary_string[i:i + 8] for i in range(0, len(binary_string), 8)]
    # Convert each 8-bit binary number into its corresponding character
    text = ''.join([chr(int(char, 2)) for char in chars])
    return text

def calculate_parity(bits, positions):
    return sum(bits[pos - 1] for pos in positions) % 2

def encode(binary_string):
    n = len(binary_string)
    r = 0
    while (2**r) < (n + r + 1):
        r += 1

    # Initialize the array with redundant bits
    hamming_code = [0] * (n + r)
    j = 0

    for i in range(1, len(hamming_code) + 1):
        if i == 2**j:
            j += 1
        else:
            hamming_code[i - 1] = int(binary_string[0])
            binary_string = binary_string[1:]

    # Calculate redundant bits
    for i in range(r):
        positions = [pos for pos in range(1, len(hamming_code) + 1) if pos & (2**i)]
        hamming_code[2**i - 1] = calculate_parity(hamming_code, positions)

    return ''.join(map(str, hamming_code))

def decode(hamming_code):
    n = len(hamming_code)
    r = int(math.log2(n + 1))
    error_pos = 0
    flag = True
    # Check for error positions
    for i in range(r):
        positions = [pos for pos in range(1, n + 1) if pos & (2**i)]
        parity = calculate_parity(list(map(int, hamming_code)), positions)
        if parity != 0:
            error_pos += 2**i

    # Correct error
    if error_pos != 0:
        print(f"Error found at position: {error_pos}, correcting...")
        corrected_code = list(hamming_code)
        corrected_code[error_pos - 1] = '0' if hamming_code[error_pos - 1] == '1' else '1'
        hamming_code = ''.join(corrected_code)
        flag = False
    # Remove redundant bits
    decoded_bits = []
    j = 0
    for i in range(1, n + 1):
        if i != 2**j:
            decoded_bits.append(hamming_code[i - 1])
        else:
            j += 1

    return flag, ''.join(decoded_bits)

# Use your string conversion methods to integrate Hamming code encoding and decoding
def string_to_hamming_code(data: str) -> str:
    binary_string = string_to_binary_string(data)
    encoded_data = encode(binary_string)
    return encoded_data

def hamming_code_to_string(hamming_code: str) -> (bool, str):
    flag, decoded_binary_string = decode(hamming_code)
    return flag, binary_string_to_string(decoded_binary_string)


if __name__ == '__main__':
    input_str = "Hello"
    encoded_hamming = string_to_hamming_code(input_str)
    print(f"Hamming code encoded result: {encoded_hamming}")

    flag, decoded_str = hamming_code_to_string("0000100110000111001010110110001110110001101111")
    print(flag)
    print(f"Decoded string: {decoded_str}")