from qiskit import transpile, QuantumCircuit
from qiskit_aer import AerSimulator
from oracle import build_sdes_oracle
from diffuser import build_diffuser
import operator

# Definizione coppia di cui si è in possesso (si sta conducendo un attacco KPA)
plaintext_target = '00000000'
ciphertext_target = '11111110' 


print("\n--- COPPIA SU CUI ESEGUIRE KEY RECOVERY ---\n")
print(f"Plaintext: {plaintext_target}")
print(f"Ciphertext: {ciphertext_target}\n")

# Parametri
TOTAL_QUBITS = 31
NUM_KEY_QUBITS = 10
PHASE_QUBIT = 30  # 31-esimo qubit

# Crezione circuito principale (31 qubit quantistici, di cui 10 destinati alla chiave che andranno misurati)
main_qc = QuantumCircuit(TOTAL_QUBITS, NUM_KEY_QUBITS)

# Si portano in superposizione i qubit della chiave
main_qc.h(range(NUM_KEY_QUBITS))

# Inizializzazione del qubit di fase allo stato |->
main_qc.x(PHASE_QUBIT)   # il qubit passa da |0> a |1> 
main_qc.h(PHASE_QUBIT)   # il qubit passa da |1> a |-> 

# Costruzione del gate associato all'oracolo (riguarda tutti qubit)
oracle_gate = build_sdes_oracle(plaintext_target, ciphertext_target)
# Costruzione del gate associato al diffuser (riguarda solo i qubit associati alla chiave)
diffuser_gate = build_diffuser(NUM_KEY_QUBITS)

iterations = 12

# Ripetizione dei due circuiti precedenti per iterations volte 
for i in range(iterations):
    main_qc.append(oracle_gate, range(TOTAL_QUBITS))
    main_qc.append(diffuser_gate, range(NUM_KEY_QUBITS))
    
# Misurazione finale
main_qc.measure(range(NUM_KEY_QUBITS), range(NUM_KEY_QUBITS))


fig = main_qc.draw('mpl', fold=-1, scale=1)
#fig.savefig('final_circuit.png', dpi=150, bbox_inches='tight')

# Inizializzazione del simulatore
simulator = AerSimulator(method='matrix_product_state') # Si rappresenta lo stato quantistico con il metodo MPS per aggirare i limiti della RAM (con statevector ci vorrebbero almeno 35 GB)

# Compilazione del circuito
compiled_circuit = transpile(main_qc, simulator)

print("--- ESECUZIONE ATTACCO ---\n")
# Avvio del simulatore e collezione dei risultati
shots = 8192
print("Simulazione cominciata!")
job = simulator.run(compiled_circuit, shots=shots)
result = job.result()
counts = result.get_counts()

print("Simulazione completata!\n")

# Analisi dei risultati
sorted_counts = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)

print("--- TOP 20 CHIAVI TROVATE ---\n")
for i in range(min(20, len(sorted_counts))):
    key_str, count = sorted_counts[i]
    
    # Qiskit stampa i bit dal più significativo al meno significativo (little-endian per le stringhe). Occorre quindi leggerli dall'ultimo al primo
    reversed_key = key_str[::-1] 
    
    prob = (count / shots) * 100          
    print(f"{i+1}. Chiave Binaria: {reversed_key} | Array: [{', '.join(reversed_key)}] -> Misurata {count} volte ({prob:.3f}%)")