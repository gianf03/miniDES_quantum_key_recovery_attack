from qiskit import QuantumCircuit, transpile
from qiskit_aer import Aer
from oracle import build_sbox_gate
from sdes import generate_keys

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



################################## TEST ORACOLO ####################################



from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from oracle import build_sdes_oracle

def test_oracle_on_known_key(plaintext, ciphertext, known_key_bin):
    """
    Inizializza la chiave in uno stato computazionale (non superposizione)
    e verifica che l'oracolo faccia phase kickback.
    """
    TOTAL_QUBITS = 31
    qc = QuantumCircuit(TOTAL_QUBITS, 1)
    
    # Imposta la chiave nota (stato |k> deterministico)
    for i, bit in enumerate(known_key_bin):
        if bit == '1':
            qc.x(i)
    
    # Inizializza il phase qubit in |->
    qc.x(30)
    qc.h(30)
    
    # Applica l'oracolo
    oracle_gate = build_sdes_oracle(plaintext, ciphertext).to_gate()
    qc.append(oracle_gate, range(TOTAL_QUBITS))
    
    # Misura il phase qubit in base X (se l'oracolo funziona, troveremo |+> o |->)
    qc.h(30)
    qc.measure(30, 0)
    
    sim = AerSimulator(method='matrix_product_state')
    compiled = transpile(qc, basis_gates=['cx', 'u', 'x', 'h', 'measure'], optimization_level=0)
    result = sim.run(compiled, shots=8192).result()
    counts = result.get_counts()
    
    print(f"Chiave testata: {known_key_bin}")
    print(f"Risultati misura qubit di fase: {counts}")
    # Se l'oracolo funziona: dovremmo vedere quasi solo '1' (stato |-> → misura 1)
    # Se l'oracolo NON funziona: distribuzione ~50/50

# Prima genera una coppia (P, C, K) con il tuo S-DES classico, poi:
test_oracle_on_known_key('00000000', '11111110', '0000111000' )  
# sostituisci con la chiave che classicamente produce quel ciphertext


################################ TESTING VALORI INTERMEDI #######################

from bitarray import bitarray

# Permutation function
def permute(bits, table):
    return bitarray([bits[i - 1] for i in table])

# Left shift function
def shift_left(bits, n):
    return bits[n:] + bits[:n]

# XOR function
def xor(bits1, bits2):
    return bits1 ^ bits2  # bitarray supports XOR directly

# S-Box Lookup
SBOXES = [
    [[1, 0, 3, 2], [3, 2, 1, 0], [0, 2, 1, 3], [3, 1, 3, 2]],
    [[0, 1, 2, 3], [2, 0, 1, 3], [3, 0, 1, 0], [2, 1, 0, 3]]
]

def s_box(bits, sbox):
    row, col = int(f"{bits[0]}{bits[3]}", 2), int(f"{bits[1]}{bits[2]}", 2)
    return bitarray(format(SBOXES[sbox][row][col], "02b"))



def debug_sdes_step_by_step(plaintext_bin, key_bin):
    from bitarray import bitarray
    
    pt = bitarray(plaintext_bin)
    key = bitarray(key_bin)
    key1, key2 = generate_keys(key)
    
    IP = [2, 6, 3, 1, 4, 8, 5, 7]
    bits = permute(pt, IP)
    
    print(f"Dopo IP:     {bits.to01()}")
    print(f"L0:          {bits[:4].to01()}")
    print(f"R0:          {bits[4:].to01()}")
    print(f"K1:          {key1.to01()}")
    print(f"K2:          {key2.to01()}")
    
    # Round 1
    EP = [4, 1, 2, 3, 2, 3, 4, 1]
    R_exp = permute(bits[4:], EP)
    print(f"R0 espanso:  {R_exp.to01()}")
    xor1 = xor(R_exp, key1)
    print(f"XOR con K1:  {xor1.to01()}")
    
    sb1 = s_box(xor1[:4], 0)
    sb2 = s_box(xor1[4:], 1)
    print(f"SBox1 out:   {sb1.to01()}")
    print(f"SBox2 out:   {sb2.to01()}")
    
    P4 = [2, 4, 3, 1]
    p4_out = permute(sb1 + sb2, P4)
    print(f"Dopo P4:     {p4_out.to01()}")
    
    new_L = xor(bits[:4], p4_out)
    print(f"Nuovo L1:    {new_L.to01()}")
    print(f"R1 (=R0):    {bits[4:].to01()}")

# Chiamalo con una chiave che sai essere corretta
debug_sdes_step_by_step('00000000', '0000111000')


def debug_sdes_step_by_step2(plaintext_bin, key_bin):
    from bitarray import bitarray
    from sdes import encrypt
    
    pt = bitarray(plaintext_bin)
    key = bitarray(key_bin)
    key1, key2 = generate_keys(key)
    
    IP = [2, 6, 3, 1, 4, 8, 5, 7]
    bits = permute(pt, IP)
    
    print(f"Dopo IP:     {bits.to01()}")
    print(f"L0:          {bits[:4].to01()}")
    print(f"R0:          {bits[4:].to01()}")
    print(f"K1:          {key1.to01()}")
    print(f"K2:          {key2.to01()}")
    
    # Round 1
    EP = [4, 1, 2, 3, 2, 3, 4, 1]
    R_exp = permute(bits[4:], EP)
    print(f"\n--- ROUND 1 ---")
    print(f"R0 espanso:  {R_exp.to01()}")
    xor1 = xor(R_exp, key1)
    print(f"XOR con K1:  {xor1.to01()}")
    sb1 = s_box(xor1[:4], 0)
    sb2 = s_box(xor1[4:], 1)
    print(f"SBox1 out:   {sb1.to01()}")
    print(f"SBox2 out:   {sb2.to01()}")
    P4 = [2, 4, 3, 1]
    p4_out = permute(sb1 + sb2, P4)
    print(f"Dopo P4:     {p4_out.to01()}")
    new_L = xor(bits[:4], p4_out)
    print(f"Nuovo L1:    {new_L.to01()}")
    print(f"R1 (=R0):    {bits[4:].to01()}")

    # Swap
    L1 = new_L
    R1 = bits[4:]
    after_swap_L = R1
    after_swap_R = L1
    print(f"\n--- DOPO SWAP ---")
    print(f"L:           {after_swap_L.to01()}")
    print(f"R:           {after_swap_R.to01()}")

    # Round 2
    print(f"\n--- ROUND 2 ---")
    R_exp2 = permute(after_swap_R, EP)
    print(f"R espanso:   {R_exp2.to01()}")
    xor2 = xor(R_exp2, key2)
    print(f"XOR con K2:  {xor2.to01()}")
    sb3 = s_box(xor2[:4], 0)
    sb4 = s_box(xor2[4:], 1)
    print(f"SBox1 out:   {sb3.to01()}")
    print(f"SBox2 out:   {sb4.to01()}")
    p4_out2 = permute(sb3 + sb4, P4)
    print(f"Dopo P4:     {p4_out2.to01()}")
    new_L2 = xor(after_swap_L, p4_out2)
    print(f"Nuovo L2:    {new_L2.to01()}")
    print(f"R2 (=R1):    {after_swap_R.to01()}")

    # IP_inv
    IP_inv = [4, 1, 3, 5, 7, 2, 8, 6]
    final = permute(new_L2 + after_swap_R, IP_inv)
    print(f"\n--- RISULTATO FINALE ---")
    print(f"L2+R2:       {(new_L2 + after_swap_R).to01()}")
    print(f"Ciphertext:  {final.to01()}")
    
    # Verifica con encrypt diretto
    expected = encrypt(pt, key1, key2)
    print(f"Atteso:      {expected.to01()}")
    print(f"Match:       {'✅' if final == expected else '❌'}")

debug_sdes_step_by_step2('00000000', '0000111000')




test_oracle_on_known_key('00000000', '11111110', '0000111000')

from bitarray import bitarray
from sdes import encrypt

target_keys = ['0101010000', '0000011000', '0001010000', '0100011000']

for k in target_keys:
    key = bitarray(k)
    key1, key2 = generate_keys(key)
    ct = encrypt(bitarray('00000000'), key1, key2)
    print(f"Chiave {k} → {ct.to01()}")



#### TEST VALORI INTERMEDI CLASSICO VS QUANTISTICO #####
from oracle import apply_pbox, q_split, KeyGenerator

def verify_oracle_vs_classical(plaintext_bin, key_bin):
    from bitarray import bitarray
    
    pt = bitarray(plaintext_bin)
    key = bitarray(key_bin)
    key1, key2 = generate_keys(key)
    
    print("=" * 50)
    print(f"Plaintext: {plaintext_bin}")
    print(f"Key:       {key_bin}")
    print(f"K1:        {key1.to01()}")
    print(f"K2:        {key2.to01()}")
    
    # ---- CLASSICO ----
    IP = [2, 6, 3, 1, 4, 8, 5, 7]
    bits = permute(pt, IP)
    print(f"\n[CLASSICO] Dopo IP:  {bits.to01()}")
    print(f"[CLASSICO] L0:       {bits[:4].to01()}")
    print(f"[CLASSICO] R0:       {bits[4:].to01()}")
    
    # Round 1
    EP = [4, 1, 2, 3, 2, 3, 4, 1]
    R_exp = permute(bits[4:], EP)
    xor1 = xor(R_exp, key1)
    sb1 = s_box(xor1[:4], 0)
    sb2 = s_box(xor1[4:], 1)
    P4 = [2, 4, 3, 1]
    p4_out = permute(sb1 + sb2, P4)
    new_L = xor(bits[:4], p4_out)
    print(f"\n[CLASSICO] R0 espanso:   {R_exp.to01()}")
    print(f"[CLASSICO] XOR K1:       {xor1.to01()}")
    print(f"[CLASSICO] SBox1:        {sb1.to01()}")
    print(f"[CLASSICO] SBox2:        {sb2.to01()}")
    print(f"[CLASSICO] P4:           {p4_out.to01()}")
    print(f"[CLASSICO] L1=L0^P4:     {new_L.to01()}")
    print(f"[CLASSICO] R1=R0:        {bits[4:].to01()}")
    
    # Swap
    after_swap = bits[4:] + new_L  # R1 diventa L, L1 diventa R
    print(f"\n[CLASSICO] Dopo swap:    {after_swap.to01()}")
    print(f"[CLASSICO] L dopo swap:  {after_swap[:4].to01()}")
    print(f"[CLASSICO] R dopo swap:  {after_swap[4:].to01()}")
    
    # Round 2
    R_exp2 = permute(after_swap[4:], EP)
    xor2 = xor(R_exp2, key2)
    sb3 = s_box(xor2[:4], 0)
    sb4 = s_box(xor2[4:], 1)
    p4_out2 = permute(sb3 + sb4, P4)
    new_L2 = xor(after_swap[:4], p4_out2)
    print(f"\n[CLASSICO] R espanso R2: {R_exp2.to01()}")
    print(f"[CLASSICO] XOR K2:       {xor2.to01()}")
    print(f"[CLASSICO] SBox1:        {sb3.to01()}")
    print(f"[CLASSICO] SBox2:        {sb4.to01()}")
    print(f"[CLASSICO] P4:           {p4_out2.to01()}")
    print(f"[CLASSICO] L2=L^P4:      {new_L2.to01()}")
    print(f"[CLASSICO] R2=R:         {after_swap[4:].to01()}")
    
    IP_inv = [4, 1, 3, 5, 7, 2, 8, 6]
    final = permute(new_L2 + after_swap[4:], IP_inv)
    print(f"\n[CLASSICO] L2+R2:        {(new_L2 + after_swap[4:]).to01()}")
    print(f"[CLASSICO] Ciphertext:   {final.to01()}")
    
    # ---- QUANTISTICO (indici) ----
    print("\n" + "=" * 50)
    IP_order = [1, 5, 2, 0, 3, 7, 4, 6]
    EP_order = [3, 0, 1, 2, 1, 2, 3, 0]
    SP_order = [1, 3, 2, 0]
    LP_order = [3, 0, 2, 4, 6, 1, 7, 5]
    
    work_text = list(range(10, 18))
    current_text = apply_pbox(work_text, IP_order)
    L, R = q_split(current_text)
    
    print(f"[QUANTUM]  work_text:    {work_text}")
    print(f"[QUANTUM]  dopo IP:      {current_text}")
    print(f"[QUANTUM]  L0:           {L}")
    print(f"[QUANTUM]  R0:           {R}")
    
    # Mappa qubit → valore classico
    # work_text[i] corrisponde a plaintext[i] dopo init
    # Dopo IP, current_text[i] corrisponde a bits[i] del classico
    classic_after_ip = bits.to01()
    qubit_to_value = {work_text[i]: int(plaintext_bin[i]) for i in range(8)}
    
    def qubit_val(q):
        # trova la posizione originale di questo qubit in work_text
        orig_pos = work_text.index(q) if q in work_text else None
        return int(plaintext_bin[orig_pos]) if orig_pos is not None else '?'
    
    print(f"\n[QUANTUM]  L0 valori classici: {''.join(str(qubit_val(q)) for q in L)}")
    print(f"[QUANTUM]  R0 valori classici: {''.join(str(qubit_val(q)) for q in R)}")
    print(f"[CLASSICO] L0:                 {bits[:4].to01()}")
    print(f"[CLASSICO] R0:                 {bits[4:].to01()}")
    
    match_L = ''.join(str(qubit_val(q)) for q in L) == bits[:4].to01()
    match_R = ''.join(str(qubit_val(q)) for q in R) == bits[4:].to01()
    print(f"\nL0 match: {'✅' if match_L else '❌'}")
    print(f"R0 match: {'✅' if match_R else '❌'}")
    
    # Dopo swap
    L, R = R, L
    print(f"\n[QUANTUM]  L dopo swap: {L}")
    print(f"[QUANTUM]  R dopo swap: {R}")
    print(f"[QUANTUM]  L valori:    {''.join(str(qubit_val(q)) for q in L)}")
    print(f"[QUANTUM]  R valori:    {''.join(str(qubit_val(q)) for q in R)}")
    print(f"[CLASSICO] L dopo swap: {after_swap[:4].to01()}")
    print(f"[CLASSICO] R dopo swap: {after_swap[4:].to01()}")
    
    match_Ls = ''.join(str(qubit_val(q)) for q in L) == after_swap[:4].to01()
    match_Rs = ''.join(str(qubit_val(q)) for q in R) == after_swap[4:].to01()
    print(f"\nL dopo swap match: {'✅' if match_Ls else '❌'}")
    print(f"R dopo swap match: {'✅' if match_Rs else '❌'}")
    

    EP_order = [3, 0, 1, 2, 1, 2, 3, 0]
    ep_r2_qubit_indices = [R[EP_order[i]] for i in range(8)]
    print(f"\n[QUANTUM]  EP round 2 opera su qubit fisici: {ep_r2_qubit_indices}")
    print(f"[CLASSICO] EP round 2 opera su:              {after_swap[4:].to01()}")


    sbox_outs = list(range(26, 30))
    SP_order = [1, 3, 2, 0]
    p4_applied = apply_pbox(sbox_outs, SP_order)
    print(f"\n[QUANTUM]  sbox_outs fisici:  {sbox_outs}")
    print(f"[QUANTUM]  p4_out fisici:     {p4_applied}")
    print(f"[CLASSICO] SBox1+SBox2 out:   {(sb1+sb2).to01()}")
    print(f"[CLASSICO] Dopo P4:           {p4_out.to01()}")

    # Final text
    key_qubits = list(range(10))
    key_gen = KeyGenerator()
    k1_idx, k2_idx = key_gen.get_subkeys_indices(key_qubits)
    
    from oracle import q_merge
    final_text = apply_pbox(q_merge(L, R), LP_order)
    print(f"\n[QUANTUM]  L2+R2 (qubit): {q_merge(L, R)}")
    print(f"[QUANTUM]  final_text:     {final_text}")
    print(f"[CLASSICO] L2+R2:          {(new_L2 + after_swap[4:]).to01()}")
    print(f"\n✅ Se final_text[i] corrisponde alla posizione del bit i di L2+R2, LP_order è corretto")

verify_oracle_vs_classical('11001100', '0000111000')


##### TEST CIRCUITO QUANTISTICO DOPO ROUND 1 ####


def test_round1_output(plaintext_bin, key_bin):
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    from bitarray import bitarray
    
    TOTAL_QUBITS = 31
    qc = QuantumCircuit(TOTAL_QUBITS, 4)  # 4 bit classici per misurare L
    
    # Init chiave
    for i, bit in enumerate(key_bin):
        if bit == '1':
            qc.x(i)
    
    # Init plaintext
    for i, bit in enumerate(plaintext_bin):
        if bit == '1':
            qc.x(10 + i)
    
    # Replica manuale del round 1 dall'oracolo
    from oracle import KeyGenerator, apply_pbox, q_split, sbox1_gate, sbox2_gate
    
    key_qubits = list(range(10))
    work_text = list(range(10, 18))
    ancillas = list(range(18, 26))
    sbox_outs = list(range(26, 30))
    
    IP_order = [1, 5, 2, 0, 3, 7, 4, 6]
    EP_order = [3, 0, 1, 2, 1, 2, 3, 0]
    SP_order = [1, 3, 2, 0]
    
    key_gen = KeyGenerator()
    k1_idx, k2_idx = key_gen.get_subkeys_indices(key_qubits)
    
    current_text = apply_pbox(work_text, IP_order)
    L, R = q_split(current_text)
    
    # Round 1
    for i, r_idx in enumerate(EP_order):
        qc.cx(R[r_idx], ancillas[i])
    for i in range(8):
        qc.cx(k1_idx[i], ancillas[i])
    
    qc.append(sbox1_gate, ancillas[0:4] + sbox_outs[0:2])
    qc.append(sbox2_gate, ancillas[4:8] + sbox_outs[2:4])
    
    p4_out = apply_pbox(sbox_outs, SP_order)
    for i in range(4):
        qc.cx(p4_out[i], L[i])
    
    # Misura L dopo round 1 (dovrebbe essere L1 = L0 XOR P4)
    print(f"Misuro i qubit fisici di L: {L}")
    for i, q in enumerate(L):
        qc.measure(q, i)
    
    sim = AerSimulator(method='matrix_product_state')
    compiled = transpile(qc, basis_gates=['cx', 'u', 'x', 'h', 'measure'],
                        optimization_level=0)
    result = sim.run(compiled, shots=1).result()
    counts = result.get_counts()
    measured = list(counts.keys())[0][::-1]  # reverse per little-endian
    
    # Calcolo classico atteso
    pt = bitarray(plaintext_bin)
    key = bitarray(key_bin)
    key1, key2 = generate_keys(key)
    IP = [2, 6, 3, 1, 4, 8, 5, 7]
    bits = permute(pt, IP)
    EP = [4, 1, 2, 3, 2, 3, 4, 1]
    R_exp = permute(bits[4:], EP)
    xor1 = xor(R_exp, key1)
    sb1 = s_box(xor1[:4], 0)
    sb2 = s_box(xor1[4:], 1)
    P4 = [2, 4, 3, 1]
    p4_classical = permute(sb1 + sb2, P4)
    L1_classical = xor(bits[:4], p4_classical).to01()
    
    print(f"[QUANTUM]  L dopo round 1: {measured}")
    print(f"[CLASSICO] L dopo round 1: {L1_classical}")
    print(f"Match: {'✅' if measured == L1_classical else '❌ BUG NEL ROUND 1'}")

test_round1_output('11001100', '0000111000')


def f_function(bits, key):
    EP, P4 = [4, 1, 2, 3, 2, 3, 4, 1], [2, 4, 3, 1]
    R_expanded = permute(bits[4:], EP)
    xor_result = xor(R_expanded, key)
    sbox_output = s_box(xor_result[:4], 0) + s_box(xor_result[4:], 1)
    return xor(bits[:4], permute(sbox_output, P4)) + bits[4:]


def test_round2_output(plaintext_bin, key_bin):
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    from bitarray import bitarray

    
    
    TOTAL_QUBITS = 31
    qc = QuantumCircuit(TOTAL_QUBITS, 8)  # 8 bit: 4 per L2, 4 per R2
    
    # Init chiave
    for i, bit in enumerate(key_bin):
        if bit == '1':
            qc.x(i)
    
    # Init plaintext
    for i, bit in enumerate(plaintext_bin):
        if bit == '1':
            qc.x(10 + i)
    
    from oracle import KeyGenerator, apply_pbox, q_split, q_merge, sbox1_gate, sbox2_gate
    
    key_qubits = list(range(10))
    work_text = list(range(10, 18))
    ancillas = list(range(18, 26))
    sbox_outs = list(range(26, 30))
    
    IP_order = [1, 5, 2, 0, 3, 7, 4, 6]
    EP_order = [3, 0, 1, 2, 1, 2, 3, 0]
    SP_order = [1, 3, 2, 0]
    LP_order = [3, 0, 2, 4, 6, 1, 7, 5]
    
    key_gen = KeyGenerator()
    k1_idx, k2_idx = key_gen.get_subkeys_indices(key_qubits)
    
    current_text = apply_pbox(work_text, IP_order)
    L, R = q_split(current_text)
    
    for round_num, k_idx in enumerate([k1_idx, k2_idx]):
        for i, r_idx in enumerate(EP_order):
            qc.cx(R[r_idx], ancillas[i])
        for i in range(8):
            qc.cx(k_idx[i], ancillas[i])
        
        qc.append(sbox1_gate, ancillas[0:4] + sbox_outs[0:2])
        qc.append(sbox2_gate, ancillas[4:8] + sbox_outs[2:4])
        
        p4_out = apply_pbox(sbox_outs, SP_order)
        for i in range(4):
            qc.cx(p4_out[i], L[i])
        
        # Uncompute ancilla
        qc.append(sbox2_gate.inverse(), ancillas[4:8] + sbox_outs[2:4])
        qc.append(sbox1_gate.inverse(), ancillas[0:4] + sbox_outs[0:2])
        for i in range(7, -1, -1):
            qc.cx(k_idx[i], ancillas[i])
        for i in range(7, -1, -1):
            qc.cx(R[EP_order[i]], ancillas[i])
        
        if round_num == 0:
            L, R = R, L
    
    # Misura L e R finali (prima di LP)
    print(f"L fisici: {L}")
    print(f"R fisici: {R}")
    for i, q in enumerate(L):
        qc.measure(q, i)
    for i, q in enumerate(R):
        qc.measure(q, 4 + i)
    
    sim = AerSimulator(method='matrix_product_state')
    compiled = transpile(qc, basis_gates=['cx', 'u', 'x', 'h', 'measure'],
                        optimization_level=0)
    result = sim.run(compiled, shots=1).result()
    counts = result.get_counts()
    measured = list(counts.keys())[0][::-1]
    L2_measured = measured[:4]
    R2_measured = measured[4:]
    
    # Classico
    pt = bitarray(plaintext_bin)
    key = bitarray(key_bin)
    key1, key2 = generate_keys(key)
    IP = [2, 6, 3, 1, 4, 8, 5, 7]
    bits = permute(pt, IP)
    bits = f_function(bits, key1)
    bits = bits[4:] + bits[:4]  # swap
    bits = f_function(bits, key2)
    # Prima di IP_inv: bits[:4] = L2, bits[4:] = R2
    
    print(f"\n[QUANTUM]  L2: {L2_measured}")
    print(f"[CLASSICO] L2: {bits[:4].to01()}")
    print(f"L2 match: {'✅' if L2_measured == bits[:4].to01() else '❌'}")
    
    print(f"\n[QUANTUM]  R2: {R2_measured}")
    print(f"[CLASSICO] R2: {bits[4:].to01()}")
    print(f"R2 match: {'✅' if R2_measured == bits[4:].to01() else '❌'}")

test_round2_output('11001100', '0000111000')



def test_l_before_round2(plaintext_bin, key_bin):
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    from bitarray import bitarray
    from oracle import KeyGenerator, apply_pbox, q_split, sbox1_gate, sbox2_gate

    TOTAL_QUBITS = 31
    qc = QuantumCircuit(TOTAL_QUBITS, 4)

    for i, bit in enumerate(key_bin):
        if bit == '1':
            qc.x(i)
    for i, bit in enumerate(plaintext_bin):
        if bit == '1':
            qc.x(10 + i)

    key_qubits = list(range(10))
    work_text = list(range(10, 18))
    ancillas = list(range(18, 26))
    sbox_outs = list(range(26, 30))

    IP_order = [1, 5, 2, 0, 3, 7, 4, 6]
    EP_order = [3, 0, 1, 2, 1, 2, 3, 0]
    SP_order = [1, 3, 2, 0]

    key_gen = KeyGenerator()
    k1_idx, k2_idx = key_gen.get_subkeys_indices(key_qubits)

    current_text = apply_pbox(work_text, IP_order)
    L, R = q_split(current_text)

    # Solo round 1 + uncompute + swap
    for i, r_idx in enumerate(EP_order):
        qc.cx(R[r_idx], ancillas[i])
    for i in range(8):
        qc.cx(k1_idx[i], ancillas[i])

    qc.append(sbox1_gate, ancillas[0:4] + sbox_outs[0:2])
    qc.append(sbox2_gate, ancillas[4:8] + sbox_outs[2:4])

    p4_out = apply_pbox(sbox_outs, SP_order)
    for i in range(4):
        qc.cx(p4_out[i], L[i])

    qc.append(sbox2_gate.inverse(), ancillas[4:8] + sbox_outs[2:4])
    qc.append(sbox1_gate.inverse(), ancillas[0:4] + sbox_outs[0:2])
    for i in range(7, -1, -1):
        qc.cx(k1_idx[i], ancillas[i])
    for i in range(7, -1, -1):
        qc.cx(R[EP_order[i]], ancillas[i])

    # Swap
    L, R = R, L

    # Misura L prima del round 2 → dovrebbe essere R0 originale
    print(f"L prima del round 2 (qubit fisici): {L}")
    for i, q in enumerate(L):
        qc.measure(q, i)

    sim = AerSimulator(method='matrix_product_state')
    compiled = transpile(qc, basis_gates=['cx', 'u', 'x', 'h', 'measure'],
                        optimization_level=0)
    result = sim.run(compiled, shots=1).result()
    counts = result.get_counts()
    measured = list(counts.keys())[0][::-1]

    # Classico: L dopo swap = R0
    from bitarray import bitarray
    pt = bitarray(plaintext_bin)
    key = bitarray(key_bin)
    key1, key2 = generate_keys(key)
    IP = [2, 6, 3, 1, 4, 8, 5, 7]
    bits = permute(pt, IP)
    bits = f_function(bits, key1)
    after_swap_L = bits[4:].to01()  # R1 = R0

    print(f"[QUANTUM]  L prima round 2: {measured}")
    print(f"[CLASSICO] L prima round 2: {after_swap_L}")
    print(f"Match: {'✅' if measured == after_swap_L else '❌ BUG NELLO SWAP O UNCOMPUTE'}")

test_l_before_round2('11001100', '0000111000')


def test_sbox_outs_after_round1(plaintext_bin, key_bin):
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    from oracle import KeyGenerator, apply_pbox, q_split, sbox1_gate, sbox2_gate

    TOTAL_QUBITS = 31
    qc = QuantumCircuit(TOTAL_QUBITS, 4)

    for i, bit in enumerate(key_bin):
        if bit == '1':
            qc.x(i)
    for i, bit in enumerate(plaintext_bin):
        if bit == '1':
            qc.x(10 + i)

    key_qubits = list(range(10))
    work_text = list(range(10, 18))
    ancillas = list(range(18, 26))
    sbox_outs = list(range(26, 30))

    IP_order = [1, 5, 2, 0, 3, 7, 4, 6]
    EP_order = [3, 0, 1, 2, 1, 2, 3, 0]
    SP_order = [1, 3, 2, 0]

    key_gen = KeyGenerator()
    k1_idx, k2_idx = key_gen.get_subkeys_indices(key_qubits)

    current_text = apply_pbox(work_text, IP_order)
    L, R = q_split(current_text)

    # Round 1 completo con uncompute
    for i, r_idx in enumerate(EP_order):
        qc.cx(R[r_idx], ancillas[i])
    for i in range(8):
        qc.cx(k1_idx[i], ancillas[i])

    qc.append(sbox1_gate, ancillas[0:4] + sbox_outs[0:2])
    qc.append(sbox2_gate, ancillas[4:8] + sbox_outs[2:4])

    p4_out = apply_pbox(sbox_outs, SP_order)
    for i in range(4):
        qc.cx(p4_out[i], L[i])

    qc.append(sbox2_gate.inverse(), ancillas[4:8] + sbox_outs[2:4])
    qc.append(sbox1_gate.inverse(), ancillas[0:4] + sbox_outs[0:2])
    for i in range(7, -1, -1):
        qc.cx(k1_idx[i], ancillas[i])
    for i in range(7, -1, -1):
        qc.cx(R[EP_order[i]], ancillas[i])

    # Misura sbox_outs — dovrebbero essere tutti |0⟩
    print(f"sbox_outs fisici: {sbox_outs}")
    for i, q in enumerate(sbox_outs):
        qc.measure(q, i)

    sim = AerSimulator(method='matrix_product_state')
    compiled = transpile(qc, basis_gates=['cx', 'u', 'x', 'h', 'measure'],
                        optimization_level=0)
    result = sim.run(compiled, shots=1).result()
    counts = result.get_counts()
    measured = list(counts.keys())[0][::-1]

    print(f"[QUANTUM] sbox_outs dopo round 1 + uncompute: {measured}")
    print(f"Atteso: 0000")
    print(f"Match: {'✅ sbox_outs puliti' if measured == '0000' else '❌ BUG UNCOMPUTATION SBOX'}")

test_sbox_outs_after_round1('11001100', '0000111000')


def test_sbox_round2(plaintext_bin, key_bin):
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    from oracle import KeyGenerator, apply_pbox, q_split, sbox1_gate, sbox2_gate

    TOTAL_QUBITS = 31
    qc = QuantumCircuit(TOTAL_QUBITS, 4)

    for i, bit in enumerate(key_bin):
        if bit == '1':
            qc.x(i)
    for i, bit in enumerate(plaintext_bin):
        if bit == '1':
            qc.x(10 + i)

    key_qubits = list(range(10))
    work_text = list(range(10, 18))
    ancillas = list(range(18, 26))
    sbox_outs = list(range(26, 30))

    IP_order = [1, 5, 2, 0, 3, 7, 4, 6]
    EP_order = [3, 0, 1, 2, 1, 2, 3, 0]
    SP_order = [1, 3, 2, 0]

    key_gen = KeyGenerator()
    k1_idx, k2_idx = key_gen.get_subkeys_indices(key_qubits)

    current_text = apply_pbox(work_text, IP_order)
    L, R = q_split(current_text)

    # Round 1 completo
    for i, r_idx in enumerate(EP_order):
        qc.cx(R[r_idx], ancillas[i])
    for i in range(8):
        qc.cx(k1_idx[i], ancillas[i])
    qc.append(sbox1_gate, ancillas[0:4] + sbox_outs[0:2])
    qc.append(sbox2_gate, ancillas[4:8] + sbox_outs[2:4])
    p4_out = apply_pbox(sbox_outs, SP_order)
    for i in range(4):
        qc.cx(p4_out[i], L[i])
    qc.append(sbox2_gate.inverse(), ancillas[4:8] + sbox_outs[2:4])
    qc.append(sbox1_gate.inverse(), ancillas[0:4] + sbox_outs[0:2])
    for i in range(7, -1, -1):
        qc.cx(k1_idx[i], ancillas[i])
    for i in range(7, -1, -1):
        qc.cx(R[EP_order[i]], ancillas[i])

    # Swap
    L, R = R, L

    # Round 2 — solo EP + XOR K2 + SBox, SENZA il CX con L
    for i, r_idx in enumerate(EP_order):
        qc.cx(R[r_idx], ancillas[i])
    for i in range(8):
        qc.cx(k2_idx[i], ancillas[i])
    qc.append(sbox1_gate, ancillas[0:4] + sbox_outs[0:2])
    qc.append(sbox2_gate, ancillas[4:8] + sbox_outs[2:4])

    # Misura sbox_outs prima del CX con L
    print(f"sbox_outs fisici: {sbox_outs}")
    for i, q in enumerate(sbox_outs):
        qc.measure(q, i)

    sim = AerSimulator(method='matrix_product_state')
    compiled = transpile(qc, basis_gates=['cx', 'u', 'x', 'h', 'measure'],
                        optimization_level=0)
    result = sim.run(compiled, shots=1).result()
    counts = result.get_counts()
    measured = list(counts.keys())[0][::-1]

    # Classico: cosa dovrebbe contenere sbox_outs dopo round 2?
    from bitarray import bitarray
    pt = bitarray(plaintext_bin)
    key = bitarray(key_bin)
    key1, key2 = generate_keys(key)
    IP = [2, 6, 3, 1, 4, 8, 5, 7]
    EP = [4, 1, 2, 3, 2, 3, 4, 1]
    P4 = [2, 4, 3, 1]
    bits = permute(pt, IP)
    bits = f_function(bits, key1)
    bits = bits[4:] + bits[:4]
    R_exp2 = permute(bits[4:], EP)
    xor2 = xor(R_exp2, key2)
    sb3 = s_box(xor2[:4], 0)
    sb4 = s_box(xor2[4:], 1)
    sbox_classical = (sb3 + sb4).to01()

    print(f"[QUANTUM]  sbox_outs round 2: {measured}")
    print(f"[CLASSICO] sbox_outs round 2: {sbox_classical}")
    print(f"Match: {'✅' if measured == sbox_classical else '❌ BUG NELLE SBOX ROUND 2'}")

test_sbox_round2('11001100', '0000111000')



def test_ancilla_after_round1(plaintext_bin, key_bin):
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    from oracle import KeyGenerator, apply_pbox, q_split, sbox1_gate, sbox2_gate

    TOTAL_QUBITS = 31
    qc = QuantumCircuit(TOTAL_QUBITS, 8)  # 8 bit per misurare tutti gli ancilla

    for i, bit in enumerate(key_bin):
        if bit == '1':
            qc.x(i)
    for i, bit in enumerate(plaintext_bin):
        if bit == '1':
            qc.x(10 + i)

    key_qubits = list(range(10))
    work_text = list(range(10, 18))
    ancillas = list(range(18, 26))
    sbox_outs = list(range(26, 30))

    IP_order = [1, 5, 2, 0, 3, 7, 4, 6]
    EP_order = [3, 0, 1, 2, 1, 2, 3, 0]
    SP_order = [1, 3, 2, 0]

    key_gen = KeyGenerator()
    k1_idx, k2_idx = key_gen.get_subkeys_indices(key_qubits)

    current_text = apply_pbox(work_text, IP_order)
    L, R = q_split(current_text)

    # Round 1 completo con uncompute
    for i, r_idx in enumerate(EP_order):
        qc.cx(R[r_idx], ancillas[i])
    for i in range(8):
        qc.cx(k1_idx[i], ancillas[i])
    qc.append(sbox1_gate, ancillas[0:4] + sbox_outs[0:2])
    qc.append(sbox2_gate, ancillas[4:8] + sbox_outs[2:4])
    p4_out = apply_pbox(sbox_outs, SP_order)
    for i in range(4):
        qc.cx(p4_out[i], L[i])
    qc.append(sbox2_gate.inverse(), ancillas[4:8] + sbox_outs[2:4])
    qc.append(sbox1_gate.inverse(), ancillas[0:4] + sbox_outs[0:2])
    for i in range(7, -1, -1):
        qc.cx(k1_idx[i], ancillas[i])
    for i in range(7, -1, -1):
        qc.cx(R[EP_order[i]], ancillas[i])

    # Misura ancilla — dovrebbero essere tutti |0⟩
    print(f"ancilla fisici: {ancillas}")
    for i, q in enumerate(ancillas):
        qc.measure(q, i)

    sim = AerSimulator(method='matrix_product_state')
    compiled = transpile(qc, basis_gates=['cx', 'u', 'x', 'h', 'measure'],
                        optimization_level=0)
    result = sim.run(compiled, shots=1).result()
    counts = result.get_counts()
    measured = list(counts.keys())[0][::-1]

    print(f"[QUANTUM] ancilla dopo round 1 + uncompute: {measured}")
    print(f"Atteso: 00000000")
    print(f"Match: {'✅ ancilla puliti' if measured == '00000000' else '❌ BUG ANCILLA SPORCHI'}")

test_ancilla_after_round1('11001100', '0000111000')

def test_ep_only_round2(plaintext_bin, key_bin):
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    from oracle import KeyGenerator, apply_pbox, q_split, sbox1_gate, sbox2_gate

    TOTAL_QUBITS = 31
    qc = QuantumCircuit(TOTAL_QUBITS, 8)

    for i, bit in enumerate(key_bin):
        if bit == '1':
            qc.x(i)
    for i, bit in enumerate(plaintext_bin):
        if bit == '1':
            qc.x(10 + i)

    key_qubits = list(range(10))
    work_text = list(range(10, 18))
    ancillas = list(range(18, 26))
    sbox_outs = list(range(26, 30))

    IP_order = [1, 5, 2, 0, 3, 7, 4, 6]
    EP_order = [3, 0, 1, 2, 1, 2, 3, 0]
    SP_order = [1, 3, 2, 0]

    key_gen = KeyGenerator()
    k1_idx, k2_idx = key_gen.get_subkeys_indices(key_qubits)

    current_text = apply_pbox(work_text, IP_order)
    L, R = q_split(current_text)

    # Round 1 completo
    for i, r_idx in enumerate(EP_order):
        qc.cx(R[r_idx], ancillas[i])
    for i in range(8):
        qc.cx(k1_idx[i], ancillas[i])
    qc.append(sbox1_gate, ancillas[0:4] + sbox_outs[0:2])
    qc.append(sbox2_gate, ancillas[4:8] + sbox_outs[2:4])
    p4_out = apply_pbox(sbox_outs, SP_order)
    for i in range(4):
        qc.cx(p4_out[i], L[i])
    qc.append(sbox2_gate.inverse(), ancillas[4:8] + sbox_outs[2:4])
    qc.append(sbox1_gate.inverse(), ancillas[0:4] + sbox_outs[0:2])
    for i in range(7, -1, -1):
        qc.cx(k1_idx[i], ancillas[i])
    for i in range(7, -1, -1):
        qc.cx(R[EP_order[i]], ancillas[i])

    # Swap
    L, R = R, L

    # Round 2 — solo EP
    for i, r_idx in enumerate(EP_order):
        qc.cx(R[r_idx], ancillas[i])

    # Misura ancilla dopo solo EP
    print(f"R fisici usati in EP round 2: {R}")
    for i, q in enumerate(ancillas):
        qc.measure(q, i)

    sim = AerSimulator(method='matrix_product_state')
    compiled = transpile(qc, basis_gates=['cx', 'u', 'x', 'h', 'measure'],
                        optimization_level=0)
    result = sim.run(compiled, shots=1).result()
    counts = result.get_counts()
    measured = list(counts.keys())[0][::-1]

    # Classico — solo EP(R_swap)
    from bitarray import bitarray
    pt = bitarray(plaintext_bin)
    key = bitarray(key_bin)
    key1, key2 = generate_keys(key)
    IP = [2, 6, 3, 1, 4, 8, 5, 7]
    EP = [4, 1, 2, 3, 2, 3, 4, 1]
    bits = permute(pt, IP)
    bits = f_function(bits, key1)
    bits = bits[4:] + bits[:4]
    R_exp2 = permute(bits[4:], EP)

    print(f"[QUANTUM]  ancilla dopo EP round 2: {measured}")
    print(f"[CLASSICO] EP(R) round 2:           {R_exp2.to01()}")
    print(f"Match: {'✅' if measured == R_exp2.to01() else '❌ BUG IN EP ROUND 2'}")

test_ep_only_round2('11001100', '0000111000')



def test_k2(plaintext_bin, key_bin):
    from oracle import KeyGenerator, apply_pbox, q_split
    from bitarray import bitarray

    key_qubits = list(range(10))
    key_gen = KeyGenerator()
    k1_idx, k2_idx = key_gen.get_subkeys_indices(key_qubits)

    print(f"[QUANTUM] k1_idx (qubit fisici): {k1_idx}")
    print(f"[QUANTUM] k2_idx (qubit fisici): {k2_idx}")

    # Classico
    key = bitarray(key_bin)
    key1, key2 = generate_keys(key)
    print(f"[CLASSICO] K1: {key1.to01()}")
    print(f"[CLASSICO] K2: {key2.to01()}")

    # Mappa qubit fisico → valore del bit di chiave
    print(f"\nMappa qubit → valore chiave (key_bin={key_bin}):")
    for i, q in enumerate(k2_idx):
        key_pos = key_qubits.index(q) if q in key_qubits else '?'
        bit_val = key_bin[key_pos] if key_pos != '?' else '?'
        classical_bit = key2.to01()[i]
        match = '✅' if bit_val == classical_bit else '❌'
        print(f"  k2_idx[{i}] = qubit {q} → key_bin[{key_pos}] = {bit_val} | classico K2[{i}] = {classical_bit} {match}")

test_k2('11001100', '0000111000')



def debug_keygen(key_bin):
    from oracle import KeyGenerator, apply_pbox, q_split, q_merge
    from bitarray import bitarray

    key_qubits = list(range(10))
    
    P10_order = [2, 4, 1, 6, 3, 9, 0, 8, 7, 5]
    P8_order = [5, 2, 6, 3, 7, 4, 9, 8]
    LeftShift1_order = [1, 2, 3, 4, 0]

    # Quantum step by step
    x = apply_pbox(key_qubits, P10_order)
    print(f"[QUANTUM] dopo P10:        {x}")
    
    left, right = x[:5], x[5:]
    print(f"[QUANTUM] left:            {left}")
    print(f"[QUANTUM] right:           {right}")
    
    left = apply_pbox(left, LeftShift1_order)
    right = apply_pbox(right, LeftShift1_order)
    print(f"[QUANTUM] dopo shift1 L:   {left}")
    print(f"[QUANTUM] dopo shift1 R:   {right}")
    
    k1 = apply_pbox(q_merge(left, right), P8_order)
    print(f"[QUANTUM] k1_idx:          {k1}")
    
    left = apply_pbox(left, LeftShift1_order)
    right = apply_pbox(right, LeftShift1_order)
    print(f"[QUANTUM] dopo shift2 L:   {left}")
    print(f"[QUANTUM] dopo shift2 R:   {right}")
    
    k2 = apply_pbox(q_merge(left, right), P8_order)
    print(f"[QUANTUM] k2_idx:          {k2}")

    # Classico step by step
    key = bitarray(key_bin)
    P10 = [3, 5, 2, 7, 4, 10, 1, 9, 8, 6]
    P8  = [6, 3, 7, 4, 8, 5, 10, 9]
    
    
    key_p10 = permute(key, P10)
    print(f"\n[CLASSICO] dopo P10:       {key_p10.to01()}")
    
    L, R = key_p10[:5], key_p10[5:]
    print(f"[CLASSICO] L:              {L.to01()}")
    print(f"[CLASSICO] R:              {R.to01()}")
    
    L = shift_left(L, 1)
    R = shift_left(R, 1)
    print(f"[CLASSICO] dopo shift1 L:  {L.to01()}")
    print(f"[CLASSICO] dopo shift1 R:  {R.to01()}")
    
    k1_c = permute(L + R, P8)
    print(f"[CLASSICO] K1:             {k1_c.to01()}")
    
    L = shift_left(L, 2)
    R = shift_left(R, 2)
    print(f"[CLASSICO] dopo shift2 L:  {L.to01()}")
    print(f"[CLASSICO] dopo shift2 R:  {R.to01()}")
    
    k2_c = permute(L + R, P8)
    print(f"[CLASSICO] K2:             {k2_c.to01()}")

    # Confronto finale
    print(f"\n[QUANTUM]  k1 qubit vals: {''.join(key_bin[q] for q in k1)}")
    print(f"[CLASSICO] K1:            {k1_c.to01()}")
    print(f"K1 match: {'✅' if ''.join(key_bin[q] for q in k1) == k1_c.to01() else '❌'}")
    
    print(f"\n[QUANTUM]  k2 qubit vals: {''.join(key_bin[q] for q in k2)}")
    print(f"[CLASSICO] K2:            {k2_c.to01()}")
    print(f"K2 match: {'✅' if ''.join(key_bin[q] for q in k2) == k2_c.to01() else '❌'}")

debug_keygen('0000111000')


test_oracle_on_known_key('00000000', '11111110', '0000111000')
test_oracle_on_known_key('00000000', '10010110', '0000111001')
test_oracle_on_known_key('00000000', '11111110', '0000011000')



def test_oracle_correctly(plaintext, ciphertext, known_key_bin):
    TOTAL_QUBITS = 31
    qc = QuantumCircuit(TOTAL_QUBITS, 1)
    
    # Chiave in SUPERPOSIZIONE (non stato deterministico)
    for i in range(30):
        qc.h(i)
    
    # Phase qubit in |->
    qc.x(30)
    qc.h(30)
    
    # Applica oracolo
    oracle_gate = build_sdes_oracle(plaintext, ciphertext).to_gate()
    qc.append(oracle_gate, range(TOTAL_QUBITS))
    
    # Torna alla base computazionale per la chiave
    for i in range(30):
        qc.h(i)
    
    # Misura phase qubit in base X
    qc.h(30)
    qc.measure(30, 0)
    
    sim = AerSimulator(method='matrix_product_state')
    compiled = transpile(qc, basis_gates=['cx', 'u', 'x', 'h', 'measure'], optimization_level=0)
    result = sim.run(compiled, shots=8192).result()
    counts = result.get_counts()
    
    print(f"Risultati con chiave in superposizione: {counts}")
    # Se l'oracolo funziona correttamente, vedrai interferenza




KEY_BITS = 10  # esempio, cambia con il tuo

for k in range(2**KEY_BITS):
    key_bin = format(k, f'0{KEY_BITS}b')
    test_oracle_correctly('00000000', '11111110', key_bin)
