"""Paso 3 - Algoritmo de Grover para n = 2 qubits (espacio de 4 elementos)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

from qiskit import QuantumCircuit
from qiskit.visualization import plot_histogram
from qiskit_aer import AerSimulator

CAPTURAS = Path(__file__).resolve().parent.parent / "capturas"


def build_grover_circuit(target="11"):
    """Circuito de Grover de 1 iteracion para el estado `target` (cadena 'q1q0').

    Qiskit usa orden little-endian: el caracter de la derecha es el qubit 0.
    Por eso se recorre `target` invertido al decidir que qubits llevan X.
    """
    qc = QuantumCircuit(2, 2)

    # 1) Superposicion uniforme
    qc.h([0, 1])

    # 2) Oraculo de fase: CZ marca |11>; las X convierten el target en |11>
    zeros = [i for i, bit in enumerate(reversed(target)) if bit == "0"]
    if zeros:
        qc.x(zeros)
    qc.cz(0, 1)
    if zeros:
        qc.x(zeros)

    # 3) Difusor (inversion alrededor de la media)
    qc.h([0, 1])
    qc.x([0, 1])
    qc.cz(0, 1)
    qc.x([0, 1])
    qc.h([0, 1])

    qc.measure([0, 1], [0, 1])
    return qc


def grover_2qubits(target="11", shots=1024):
    """Ejecuta Grover buscando `target` y guarda el histograma."""
    qc = build_grover_circuit(target)
    counts = AerSimulator().run(qc, shots=shots).result().get_counts()

    print(f"Grover buscando |{target}> ({shots} shots):")
    for state, count in sorted(counts.items()):
        print(f"  |{state}>: {count:4d} ({count / shots * 100:.1f}%)")

    top = max(counts, key=counts.get)
    veredicto = "CORRECTO" if top == target else "ERROR"
    print(f"Estado mas probable: |{top}> - {veredicto}")

    CAPTURAS.mkdir(exist_ok=True)
    fig = plot_histogram(counts, title=f"Grover n=2, objetivo |{target}>")
    fig.savefig(CAPTURAS / f"grover_{target}.png", dpi=150)
    return counts


if __name__ == "__main__":
    for t in ["00", "01", "10", "11"]:
        grover_2qubits(target=t)
        print()
