"""
STRUTTURA GENERALE DEL DES:
Il cifrario a blocchi DES è una rete di Feistel a 16 round avente lunghezza di blocco pari a 64 bit e chiave di 56 bit (64 bit se si considerano anche quelli di parità ogni 7 bit). 
Ciascuna funzione di round prende in input una sottochiave di 48 bit di cui metà bit provengono dalla parte sx e gli altri 24 da quella dx della master key. L'algoritmo per ricavare le sottochiavi è pubblico.
Il blocco di input viene diviso in due sottoblocchi di 32 bit: quello destro diventa il sottoblocco sinistro del round successivo mentre quello sinistro viene dato in input alla funzione di round assieme alla sottochiave di 48 bit.
Step di un singolo round:
(1) i 32 bit del blocco vengono espansi a 48 bit:
(2) il blocco espanso viene posto in or esclusivo con la sottochiave di 48 bit;
(3) il risultato viene diviso in 8 gruppi di 6 bit. Ciascun gruppo è dato in input ad una S-box (pubbliche) che presi 6 bit ne restituisce 4: 
(4) si permutando i 32 bit così ottenuti.

Nel round finale è previsto anche la permutazione dei sottoblocchi per predisporre la decifratura.
"""




