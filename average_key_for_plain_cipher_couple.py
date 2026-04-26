from sdes import encrypt, generate_keys
import bitarray
# Analisi su tutte le 256 coppie (P, C) possibili
from collections import Counter
import random

distribution = Counter()
total_pairs_tested = 0

# APPROCCIO CORRETTO
for p in range(256):
    plaintext = format(p, '08b')
    
    # Pre-calcola TUTTI i ciphertext per questo plaintext
    ciphertext_counts = {}
    for k in range(1024):
        key = format(k, '010b')
        subKey1, subKey2 = generate_keys(bitarray.bitarray(key))
        ct = encrypt(bitarray.bitarray(plaintext), subKey1, subKey2)
        ct_str = ct.to01()  # Converte bitarray in stringa
        ciphertext_counts[ct_str] = ciphertext_counts.get(ct_str, 0) + 1
    
    # Ora per ogni ciphertext possibile, sappiamo già il conteggio
    for c in range(256):
        ciphertext = format(c, '08b')
        count = ciphertext_counts.get(ciphertext, 0)
        distribution[count] += 1
        total_pairs_tested += 1




print("Distribuzione numero di chiavi equivalenti per coppia (P,C):")
for num_keys, freq in sorted(distribution.items()):
    print(f"  {num_keys} chiavi equivalenti: {freq} coppie ({freq/total_pairs_tested*100:.1f}%)")

media = sum(k*v for k,v in distribution.items()) / total_pairs_tested
print(f"\nMedia chiavi equivalenti per coppia: {media:.2f}")
print(f"Valore atteso teorico: {1024/256:.2f}")  # = 4.0



