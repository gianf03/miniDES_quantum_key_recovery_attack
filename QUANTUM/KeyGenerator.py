from utils import apply_pbox, q_split, q_merge

class KeyGenerator:
    def __init__(self):
        self.P10_order = [2, 4, 1, 6, 3, 9, 0, 8, 7, 5]   # permutazione iniziale della chiave
        self.P8_order = [5, 2, 6, 3, 7, 4, 9, 8]          # permutazione trascurando i primi due bit della chiave
        self.LeftShift1_order = [1, 2, 3, 4, 0]           # shift di un bit a sinistra
        self.LeftShift2_order = [2, 3, 4, 0, 1] 

    def get_subkeys_indices(self, key_qubits):
        x = apply_pbox(key_qubits, self.P10_order)        # permutazione iniziale della chiave di 10 bit
        left, right = q_split(x)                          # split della permutazione in due sotto-parti di 5 bit
        
        leftK1 = apply_pbox(left, self.LeftShift1_order)
        rightK1 = apply_pbox(right, self.LeftShift1_order)
        
        k1_indices = apply_pbox(q_merge(leftK1, rightK1), self.P8_order)
        
        leftK2 = apply_pbox(leftK1, self.LeftShift2_order)
        rightK2 = apply_pbox(rightK1, self.LeftShift2_order)
        
        k2_indices = apply_pbox(q_merge(leftK2, rightK2), self.P8_order)
        
        return k1_indices, k2_indices