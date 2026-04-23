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

def left_shift(lst, n):
    return lst[n:] + lst[:n]

class KeyGenerator:   # nel file vecchio la classe era QuantumKeyGenerator, ma non c'è nulla di quantistico qui
    def __init__(self):
        self.P10_order = [2, 4, 1, 6, 3, 9, 0, 8, 7, 5]
        self.P8_order = [5, 2, 6, 3, 7, 4, 9, 8]
        self.LeftShift1_order = [1, 2, 3, 4, 0]

    def get_subkeys_indices(self, key_qubits):
        x = apply_pbox(key_qubits, self.P10_order)
        left, right = q_split(x)
        
        left = left_shift(left, 1)
        right = left_shift(right, 1)
        
        k1_indices = apply_pbox(q_merge(left, right), self.P8_order)
        
        left = left_shift(left, 2)
        right = left_shift(right, 2)
        
        k2_indices = apply_pbox(q_merge(left, right), self.P8_order)
        
        return k1_indices, k2_indices

# il processo di conversione da modello classico a circuito qunatistico reversbile è il seguente: 1. si realizza mappa di Karnaugh, 
def sbox1_optimized():
    qc = QuantumCircuit(6, name="SBox1_opt")
    # qubit:
    # 0 = x1
    # 1 = x2
    # 2 = x3
    # 3 = x4
    # 4 = s1 (S1 bit 1)
    # 5 = s2 (S1 bit 2)

    
    # s1 = x1 XOR x3 (x2 AND NOT x4)    
    # S1 - bit 1
    qc.ccx(1, 3, 4)  # x2 AND x4
    qc.cx(0, 4)      # x1 XOR
    qc.cx(2, 4)      # x3 XOR

    # s2 = (x1 AND x4) XOR x2 XOR x3
    # S1 - bit 2 
    qc.ccx(0, 3, 5)  # x1 AND x4
    qc.cx(1, 5)      # x2 XOR
    qc.cx(2, 5)      # x3 XOR

    return qc.to_gate()


