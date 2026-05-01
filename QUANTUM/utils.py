def q_split(qubit_indices):
    mid = len(qubit_indices) // 2
    return qubit_indices[:mid], qubit_indices[mid:]

def q_merge(left, right):
    return left + right

def apply_pbox(qubit_indices, out_order):
    return [qubit_indices[i] for i in out_order]