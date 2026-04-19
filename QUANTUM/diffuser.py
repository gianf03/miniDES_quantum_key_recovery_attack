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
    
    # Applica Hadamard e X a tutti i qubit
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