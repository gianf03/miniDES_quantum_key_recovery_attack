from qiskit import QuantumCircuit
import numpy as np
from utils import apply_pbox, q_split, q_merge
import KeyGenerator
from sbox import sbox1_gate, sbox2_gate

def build_sdes_oracle(plaintext_bin_str, ciphertext_bin_str):
    """
    Costruisce l'oracolo di Grover per un Known Plaintext Attack (KPA).
    """
    
    # GESTIONE QUBIT:
    # Qubits 0-9: Chiave in superposizione (10 qubit)
    # Qubits 10-17: Spazio di lavoro per il cifrato (8 qubit)
    # Qubits 18-25: Ancille per l'Espansione a 8 bit (8 qubit)
    # Qubits 26-29: Ancille per l'Output delle S-Box (4 qubit)
    # Qubit 30: Qubit di Fase per Grover (1 qubit)
    TOTAL_QUBITS = 31
    qc = QuantumCircuit(TOTAL_QUBITS, name="S-DES_Oracle")
    
    key_qubits = list(range(10))            # chiave di 10 bit
    work_text = list(range(10, 18))         # testo in chiaro di 8 bit
    ancillas = list(range(18, 26))
    sbox_outs = list(range(26, 30))
    phase_qubit = 30
    
    key_gen = KeyGenerator()
    k1_idx, k2_idx = key_gen.get_subkeys_indices(key_qubits)   # ottengo le sottochiavi dalla master key
    
    # Ordini di permutazione
    IP_order = [1, 5, 2, 0, 3, 7, 4, 6]
    EP_order = [3, 0, 1, 2, 1, 2, 3, 0]
    SP_order = [1, 3, 2, 0]                # ??
    LP_order = [3, 0, 2, 4, 6, 1, 7, 5]    # ??

    # --- DEFINIZIONE DEL CALCOLO FORWARD (Cifratura) ---
    forward_qc = QuantumCircuit(TOTAL_QUBITS, name="S-DES_Forward")
    
    """"
    # flip dei qubit a 1 del plaintext
    #for i, bit in enumerate(plaintext_bin_str):
    #    if bit == '1':
    #        forward_qc.x(work_text[i])
    """
            
    # si applica la permutazione iniziale al plaintext e poi lo si divide in due parti
    current_text = apply_pbox(work_text, IP_order)
    L, R = q_split(current_text)

    # --- ROUND 1 & 2 ---
    for round_num, k_idx in enumerate([k1_idx, k2_idx]):
        # a. Espansione
        for i, r_idx in enumerate(EP_order):
            forward_qc.cx(R[r_idx], ancillas[i])
            
        # b. XOR con chiave
        for i in range(8):
            forward_qc.cx(k_idx[i], ancillas[i])
            
        # c. S-Box
        forward_qc.append(sbox1_gate, ancillas[0:4] + sbox_outs[0:2])
        forward_qc.append(sbox2_gate, ancillas[4:8] + sbox_outs[2:4])
        
        # d. P4 (Applichiamo la permutazione sui nuovi qubit di output)
        p4_out = apply_pbox(sbox_outs, SP_order)
        
        # e. XOR con L
        for i in range(4):
            forward_qc.cx(p4_out[i], L[i])
            
        # f. Pulisci gli ancilla
        # Invertiamo le porte usando gli stessi identici qubit usati per l'andata
        forward_qc.append(sbox2_gate.inverse(), ancillas[4:8] + sbox_outs[2:4])
        forward_qc.append(sbox1_gate.inverse(), ancillas[0:4] + sbox_outs[0:2])
        
        for i in range(7, -1, -1):
            forward_qc.cx(k_idx[i], ancillas[i])
        for i in range(7, -1, -1):
            forward_qc.cx(R[EP_order[i]], ancillas[i])
            
        # g. Swap
        if round_num == 0:
            L, R = R, L

    # 3. LP
    final_text = apply_pbox(q_merge(L, R), LP_order)

    #### MODIFICA TEMPORANEA #####
    # PRIMA del forward (aggiungi prima di qc.append(forward_qc...))
    for i, bit in enumerate(plaintext_bin_str):
        if bit == '1':
            qc.x(work_text[i])
    
    qc.append(forward_qc.to_gate(), range(TOTAL_QUBITS))
    #### MODIFICA TEMPORANEA #####


    # --- FASE DEL MATCH ---
    for i, bit in enumerate(ciphertext_bin_str):
        if bit == '0':
            qc.x(final_text[i])
            
    qc.mcx(final_text, phase_qubit)
    
    for i, bit in enumerate(ciphertext_bin_str):
        if bit == '0':
            qc.x(final_text[i])
            
    # --- UNCOMPUTATION ---
    qc.append(forward_qc.inverse().to_gate(), range(TOTAL_QUBITS))


    ##### MODIFICA TEMPORANEA #####
    # DOPO l'uncomputation (aggiungi alla fine)
    for i, bit in enumerate(plaintext_bin_str):
        if bit == '1':
            qc.x(work_text[i])
    #### MODIFICA TEMPORANEA #####
    
    return qc
