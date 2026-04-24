from qiskit import QuantumCircuit, transpile
from qiskit_aer import Aer
from oracle import build_sbox_gate

def test_sbox_gate(sbox_gate, sbox_matrix):

    backend = Aer.get_backend("aer_simulator")

    for val in range(16):

        # input binario
        b = format(val, "04b")
        x1, x2, x3, x4 = map(int, b)

        qc = QuantumCircuit(6, 6)

        # set input
        if x1: qc.x(0)
        if x2: qc.x(1)
        if x3: qc.x(2)
        if x4: qc.x(3)

        # applica S-box
        qc.append(sbox_gate, [0,1,2,3,4,5])

        # misura
        qc.measure(range(6), range(6))

        result = backend.run(transpile(qc, backend), shots=1).result()
        bitstring = list(result.get_counts().keys())[0][::-1]

        # estrai output s1 s2
        s1 = int(bitstring[4])
        s2 = int(bitstring[5])
        out = (s1 << 1) | s2

        # calcolo atteso classico
        row = (x1 << 1) | x4
        col = (x2 << 1) | x3
        expected = sbox_matrix[row][col]

        print(b, "->", out, "| expected:", expected)


SBox1_matrix = [[1, 0, 3, 2], [3, 2, 1, 0], [0, 2, 1, 3], [3, 1, 3, 2]]
SBox2_matrix = [[0, 1, 2, 3], [2, 0, 1, 3], [3, 0, 1, 0], [2, 1, 0, 3]]

sbox1_gate = build_sbox_gate(SBox1_matrix, "SBox1")
sbox2_gate = build_sbox_gate(SBox2_matrix, "SBox2")


test_sbox_gate(sbox1_gate, SBox1_matrix)
test_sbox_gate(sbox2_gate, SBox2_matrix)

