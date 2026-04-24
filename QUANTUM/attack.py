from qiskit import transpile, QuantumCircuit
from qiskit_aer import AerSimulator

from oracle import build_sdes_oracle
from diffuser import build_diffuser, build_diffuser_not_simulated_mcz

import matplotlib.pyplot as plt
import operator

print("🤖 Inizializzazione dell'Attacco KPA Quantistico con S-DES...")
    
# Valori di esempio (assicurati che corrispondano a una vera coppia generata dal tuo S-DES classico)
plaintext_target = '00000000'
ciphertext_target = '11111110' 

# NUOVI PARAMETRI AGGIORNATI
TOTAL_QUBITS = 31
NUM_KEY_QUBITS = 10
PHASE_QUBIT = 30  # L'ultimo qubit della nuova architettura a 31

# Creiamo il circuito principale (31 qubit quantistici, 10 bit classici per leggere la chiave)
main_qc = QuantumCircuit(TOTAL_QUBITS, NUM_KEY_QUBITS)

print("   -> Preparazione degli stati in superposizione...")
# 1. Superposizione della chiave
main_qc.h(range(NUM_KEY_QUBITS))

# 2. Inizializzazione del qubit di Fase allo stato |->
main_qc.x(PHASE_QUBIT)
main_qc.h(PHASE_QUBIT)

print("   -> Costruzione dei gate...")
oracle_gate = build_sdes_oracle(plaintext_target, ciphertext_target).to_gate()
#diffuser_gate = build_diffuser(NUM_KEY_QUBITS)
diffuser_gate = build_diffuser_not_simulated_mcz(NUM_KEY_QUBITS)

iterations = 1 # Manteniamo a 1 per non bloccare il PC  

print(f"   -> Aggiunta di {iterations} iterazioni di Grover al circuito...")
for i in range(iterations):
    # Aggiungi Oracolo su tutti e 31 i qubit
    main_qc.append(oracle_gate, range(TOTAL_QUBITS))
    # Aggiungi Diffusore SOLO sui 10 qubit della chiave (da 0 a 9)
    main_qc.append(diffuser_gate, range(NUM_KEY_QUBITS))
    
# 3. Misurazione
main_qc.measure(range(NUM_KEY_QUBITS), range(NUM_KEY_QUBITS))

# --- STAMPA DEL CIRCUITO ---
print("\n🎨 Generazione della mappa del circuito...")
# Stampiamo una versione testuale (fold disattivato per non spezzare le linee se lo schermo è largo)
# Nota: su terminali piccoli potrebbe andare a capo in modo confusionario.
main_qc.draw('mpl', fold=-1)
#print(main_qc.draw('text', fold=-1))

# Se vuoi l'immagine bella su Jupyter Notebook o salvarla come file:
# fig = main_qc.draw('mpl')
# fig.savefig("circuito_grover_sdes.png")

# --- ESECUZIONE SIMULATORE ---
print("\n🚀 Avvio del simulatore quantistico (Qiskit Aer)...")



print("⏳ Attendi, il calcolo della matrice a 31 qubit richiederà un po' di tempo...")

#simulator = AerSimulator()

# Usiamo il metodo MPS per aggirare i limiti della RAM
simulator = AerSimulator(method='matrix_product_state')

compiled_circuit = transpile(main_qc, simulator)

# Riduciamo gli shots a 512 o 1024. Più sono alti, più è accurata la statistica.
job = simulator.run(compiled_circuit, shots=8192)
result = job.result()
counts = result.get_counts()

print("✅ Simulazione completata!\n")

# ==========================================
# 6. ANALISI DEI RISULTATI
# ==========================================
sorted_counts = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)

print("--- TOP 20 CHIAVI TROVATE (Probabilità più alte) ---")
for i in range(min(20, len(sorted_counts))):
    key_str, count = sorted_counts[i]
    
    # Qiskit stampa i bit dal più significativo al meno significativo (little-endian per le stringhe).
    # Lo raddrizziamo con [::-1] per farlo corrispondere all'array Python [k0, k1, k2...]
    reversed_key = key_str[::-1] 
    
    prob = (count / 1024) * 100
    print(f"{i+1}. Chiave Binaria: {reversed_key} | Array: [{', '.join(reversed_key)}] -> Misurata {count} volte ({prob:.1f}%)")
    
print("\n💡 Nota: Per distaccare nettamente la chiave corretta dalle altre servono ~25 iterazioni.")


plt.show()