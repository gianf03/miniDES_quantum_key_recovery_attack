from qiskit import QuantumCircuit
import numpy as np

# ==========================================
# 1. FUNZIONI DI ROUTING (Costo Quantistico: 0)
# ==========================================
def q_split(qubit_indices):
    mid = len(qubit_indices) // 2
    return qubit_indices[:mid], qubit_indices[mid:]

def q_merge(left, right):
    return left + right

def apply_pbox(qubit_indices, out_order):
    return [qubit_indices[i] for i in out_order]

class KeyGenerator:
    def __init__(self):
        self.P10_order = [2, 4, 1, 6, 3, 9, 0, 8, 7, 5]   # permutazione iniziale della chiave
        self.P8_order = [5, 2, 6, 3, 7, 4, 9, 8]          # permutazione trascurando i primi due bit della chiave
        self.LeftShift1_order = [1, 2, 3, 4, 0]           # shift di un bit a sinistra

    def get_subkeys_indices(self, key_qubits):
        x = apply_pbox(key_qubits, self.P10_order)        # permutazione iniziale della chiave di 10 bit
        left, right = q_split(x)                          # split della permutazione in due sotto-parti di 5 bit
        
        left = apply_pbox(left, self.LeftShift1_order)
        right = apply_pbox(right, self.LeftShift1_order)
        
        k1_indices = apply_pbox(q_merge(left, right), self.P8_order)     # primi due bit trascurati, si applica permutazione sui restanti 8
        
        left = apply_pbox(left, self.LeftShift1_order)
        right = apply_pbox(right, self.LeftShift1_order)
        
        k2_indices = apply_pbox(q_merge(left, right), self.P8_order)
        
        return k1_indices, k2_indices

# ==========================================
# 2. GENERATORE S-BOX REVERSIBILE (Costo Quantistico: Alto)
# ==========================================
def build_sbox_gate(sbox_matrix, name="SBox"):
    """
    Crea un gate quantistico a 6 qubit (4 input + 2 output ancilla)
    scrivendo la tabella di verità con porte Multi-Controlled-X (Toffoli).
    """

    # creo circuito con un registro di 6 qubit
    qc = QuantumCircuit(6, name=name)    
    
    # Cicliamo su tutti i 16 possibili input a 4 bit
    for val in range(16):
        # trasformo val in un binario di 4 bit (aggiungendo zeri davanti se necessario)
        b_str = format(val, '04b')    
        b0, b1, b2, b3 = int(b_str[0]), int(b_str[1]), int(b_str[2]), int(b_str[3])
        
        # Logica classica per trovare riga e colonna
        row = (b0 << 1) | b3
        col = (b1 << 1) | b2
        
        out_val = sbox_matrix[row][col]
        out_str = format(out_val, '02b')
        
        # i qubit di input che sono '0' vengono negati usando Pauli-x
        for i, bit in enumerate(b_str):
            if bit == '0':
                qc.x(i)
                
        # la porta MCX controlla tutti i qubit di input della S-box; se s1 = 1, il primo qubit ancilla viene negato applicando Pauli-x; se s2 = 1, il secondo qubit ancilla viene negato applicando Pauli-x
        if out_str[0] == '1':
            qc.mcx([0, 1, 2, 3], 4)
        if out_str[1] == '1':
            qc.mcx([0, 1, 2, 3], 5)
            
        # ripristino i bit di input che sono stati portati a 1 per applicare MCX. Operazione possibile perché nel mondo quantum le operazioni sono reversibili
        for i, bit in enumerate(b_str):
            if bit == '0':
                qc.x(i)
                
    # si restituisce il circuito trasformato in porta (da poter usare come bulding block per un circuito più complesso)
    return qc.to_gate()

# Matrici SBox classiche

SBox1_matrix = [[1, 0, 3, 2], [3, 2, 1, 0], [0, 2, 1, 3], [3, 1, 3, 2]]
SBox2_matrix = [[0, 1, 2, 3], [2, 0, 1, 3], [3, 0, 1, 0], [2, 1, 0, 3]]

sbox1_gate = build_sbox_gate(SBox1_matrix, "SBox1")
sbox2_gate = build_sbox_gate(SBox2_matrix, "SBox2")

# ==========================================
# 3. IL COSTRUTTORE DELL'ORACOLO S-DES (CORRETTO)
# ==========================================
def build_sdes_oracle(plaintext_bin_str, ciphertext_bin_str):
    """
    Costruisce l'oracolo di Grover per un Known Plaintext Attack (KPA).
    """
    
    # GESTIONE QUBIT:
    # Qubits 0-9: Chiave in superposizione (10 qubit)
    # Qubits 10-17: Spazio di lavoro per il cifrato (8 qubit)
    # Qubits 18-25: Ancillas per l'Espansione a 8 bit (8 qubit)
    # Qubits 26-29: Ancillas per l'Output delle S-Box (4 qubit)
    # Qubit 30: Qubit di Fase per Grover (1 qubit)
    TOTAL_QUBITS = 31
    qc = QuantumCircuit(TOTAL_QUBITS, name="S-DES_Oracle")
    
    key_qubits = list(range(10))
    work_text = list(range(10, 18))
    ancillas = list(range(18, 26))
    sbox_outs = list(range(26, 30))
    phase_qubit = 30
    
    key_gen = KeyGenerator()
    k1_idx, k2_idx = key_gen.get_subkeys_indices(key_qubits)
    
    # Ordini di permutazione
    IP_order = [1, 5, 2, 0, 3, 7, 4, 6]
    EP_order = [3, 0, 1, 2, 1, 2, 3, 0]
    SP_order = [1, 3, 2, 0]                # ??
    LP_order = [3, 0, 2, 4, 6, 1, 7, 5]    # ??

    # --- DEFINIZIONE DEL CALCOLO FORWARD (Cifratura) ---
    forward_qc = QuantumCircuit(TOTAL_QUBITS, name="S-DES_Forward")
    
    for i, bit in enumerate(plaintext_bin_str):
        if bit == '1':
            forward_qc.x(work_text[i])
            
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
    
    qc.append(forward_qc.to_gate(), range(TOTAL_QUBITS))
    
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
    
    return qc

# Esempio di utilizzo:
# KPA: Sappiamo che P = "11100011" produce C = "10101010" (valori fittizi di esempio)
# oracle_circuit = build_sdes_oracle('11100011', '10101010')
# oracle_circuit.draw('mpl')
