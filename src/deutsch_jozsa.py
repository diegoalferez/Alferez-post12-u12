"""Paso 2 - Algoritmo de Deutsch-Jozsa para n = 2 qubits de entrada."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

from qiskit import QuantumCircuit
from qiskit.visualization import plot_histogram
from qiskit_aer import AerSimulator

CAPTURAS = Path(__file__).resolve().parent.parent / "capturas"


def oracle_constante(n):
    """Oraculo constante f(x) = 0: no aplica ninguna puerta (n + 1 qubits, con ancilla)."""
    return QuantumCircuit(n + 1)


def oracle_balanceada(n):
    """Oraculo balanceado f(x) = x0 XOR x1 ...: CNOT de cada qubit de entrada al ancilla."""
    qc = QuantumCircuit(n + 1)
    for i in range(n):
        qc.cx(i, n)
    return qc


def deutsch_jozsa(oracle_qc, n, shots=1024):
    """Ejecuta Deutsch-Jozsa con el oraculo dado y devuelve los counts."""
    qc = QuantumCircuit(n + 1, n)

    qc.x(n)                     # ancilla en |1>
    qc.h(range(n + 1))          # H en todos: entradas en superposicion, ancilla en |->

    qc.compose(oracle_qc, inplace=True)   # UNA sola evaluacion del oraculo

    qc.h(range(n))              # interferencia sobre los qubits de entrada
    qc.measure(range(n), range(n))  # se miden solo las entradas, no el ancilla

    return AerSimulator().run(qc, shots=shots).result().get_counts()


if __name__ == "__main__":
    n = 2
    counts_c = deutsch_jozsa(oracle_constante(n), n)
    print(f"Constante : {counts_c}")   # esperado: {'00': 1024}

    counts_b = deutsch_jozsa(oracle_balanceada(n), n)
    print(f"Balanceada: {counts_b}")   # esperado: sin '00'

    assert "00" in counts_c, "Error: oraculo constante no retorno 00"
    assert "00" not in counts_b, "Error: oraculo balanceado retorno 00"
    print("OK: Deutsch-Jozsa verifica correctamente")

    CAPTURAS.mkdir(exist_ok=True)
    fig = plot_histogram([counts_c, counts_b],
                         legend=["Oraculo constante", "Oraculo balanceado"],
                         title="Deutsch-Jozsa (n=2, 1024 shots)")
    fig.savefig(CAPTURAS / "deutsch_jozsa.png", dpi=150)
