from qiskit import QuantumCircuit

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