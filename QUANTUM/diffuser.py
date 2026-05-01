from qiskit import transpile, QuantumCircuit

def build_diffuser(num_key_qubits):

    qc = QuantumCircuit(num_key_qubits, name="Diffuser")

    # 1. Porta tutti i qubit in superposizione 
    qc.h(range(num_key_qubits))

    # 2. Applica Pauli-X su tutti i qubit
    qc.x(range(num_key_qubits))

    # 3. Applica MCZ (decomposto come H + MCX + H sul qubit di fase)
    qc.h(num_key_qubits - 1)
    qc.mcx(list(range(num_key_qubits - 1)), num_key_qubits - 1)
    qc.h(num_key_qubits - 1)

    # 4. Riflessione intorno alla media (gli stati sopra la media vengono attenuati, quelli sotto la media vengono amplificati). Il tutto avviene in maniera speculare rispetto alla media
    qc.x(range(num_key_qubits)) # undo Pauli-X
    qc.h(range(num_key_qubits)) # undo Hadamard

    return qc.to_gate()