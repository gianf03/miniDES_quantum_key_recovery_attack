from qiskit import transpile, QuantumCircuit
from qiskit_aer import AerSimulator
import operator

# ==========================================
# 4. IL DIFFUSORE DI GROVER
# ==========================================
def build_diffuser(num_key_qubits):
    """
    Costruisce l'operatore di diffusione di Grover per amplificare 
    l'ampiezza di probabilità della chiave corretta.
    """
    qc = QuantumCircuit(num_key_qubits, name="Diffuser")
    
    # Applica Hadamard e Pauli-X a tutti i qubit
    qc.h(range(num_key_qubits))
    qc.x(range(num_key_qubits))
    
    # Applica un Multi-Controlled Z (simulato con X, H e MCX)
    qc.h(num_key_qubits - 1)
    qc.mcx(list(range(num_key_qubits - 1)), num_key_qubits - 1)
    qc.h(num_key_qubits - 1)
    

    # Ripristina con X e H
    qc.x(range(num_key_qubits))
    qc.h(range(num_key_qubits))
    
    return qc.to_gate()



def build_diffuser_not_simulated_mcz(num_key_qubits):
    """
    Diffusore di Grover con Multi-Controlled Z (MCZ) corretto.
    """

    qc = QuantumCircuit(num_key_qubits, name="Diffuser")

    # 1. Porta lo stato in |s> = H|0>
    qc.h(range(num_key_qubits))

    # 2. Applica X su tutti i qubit (mappa |0...0> -> |1...1>)
    qc.x(range(num_key_qubits))

    # 3. MCZ vero (phase flip su |11...1>)
    # In Qiskit il modo standard è usare MCX + phase flip globale
    # quindi si applica una Z controllata multi-qubit equivalente:

    qc.h(num_key_qubits - 1)
    qc.mcx(list(range(num_key_qubits - 1)), num_key_qubits - 1)
    qc.h(num_key_qubits - 1)

    # 4. Undo X
    qc.x(range(num_key_qubits))

    # 5. Undo H
    qc.h(range(num_key_qubits))

    return qc.to_gate()