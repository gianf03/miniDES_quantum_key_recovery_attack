from sdes import generate_keys, decrypt
import bitarray
import time
import os


def brute_force(plaintext, ciphertext):

    keyCounter = 0
    
    for key in range(0, 1024):
        bitKey = bin(key)[2:].zfill(10)

        #print()

        subKey1, subKey2 = generate_keys(bitarray.bitarray(bitKey))
        decryption = decrypt(ciphertext, subKey1, subKey2)

        if (decryption == plaintext):
            print("Chiave usata:\t", bitKey)
            keyCounter += 1


    print(f"\nTotale chiavi:\t {keyCounter}")

    return keyCounter



#plaintext = bitarray.bitarray("10101010")
#ciphertext = bitarray.bitarray("00000111")


for p in range(256):
    for c in range(256):
        plaintext = bitarray.bitarray(f"{p:08b}")
        ciphertext = bitarray.bitarray(f"{c:08b}")

        print("\n")
        print("Plaintext:\t", plaintext.to01())
        print("Ciphertext:\t", ciphertext.to01())

        print("\n")
        start = time.perf_counter_ns()
        keyCounter = brute_force(plaintext, ciphertext)
        end = time.perf_counter_ns()

        elapsed_time = end - start
        print(f"\n{elapsed_time} ns")
        
        if keyCounter == 16:
            os._exit(0)



