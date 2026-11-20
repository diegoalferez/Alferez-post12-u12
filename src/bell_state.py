"""Paso 1 - Estado de Bell |Phi+> = (|00> + |11>) / sqrt(2)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # backend sin ventana: guarda la imagen directamente

from qiskit import QuantumCircuit
from qiskit.visualization import plot_histogram
from qiskit_aer import AerSimulator

CAPTURAS = Path(__file__).resolve().parent.parent / "capturas"


def bell_state_experiment(shots=1024):
    """Prepara el estado de Bell |Phi+> y lo mide `shots` veces."""
    qc = QuantumCircuit(2, 2)  # 2 qubits, 2 bits clasicos

    qc.h(0)                    # Hadamard en q0 -> superposicion
    qc.cx(0, 1)                # CNOT (control=q0, target=q1) -> entrelazamiento
    qc.measure([0, 1], [0, 1])

    simulator = AerSimulator()
    counts = simulator.run(qc, shots=shots, seed_simulator=42).result().get_counts()

    print(f"Resultados Bell |Phi+> ({shots} shots):")
    for state, count in sorted(counts.items()):
        print(f"  |{state}> : {count:4d} ({count / shots * 100:.1f}%)")

    # Solo deben aparecer |00> y |11>
    assert "01" not in counts and "10" not in counts, \
        "ERROR: aparecieron estados no entrelazados"
    print("OK: correlacion perfecta verificada")

    CAPTURAS.mkdir(exist_ok=True)
    fig = plot_histogram(counts, title="Estado de Bell |Phi+> (1024 shots)")
    fig.savefig(CAPTURAS / "bell_histogram.png", dpi=150)

    print(qc.draw(output="text"))
    return counts


if __name__ == "__main__":
    bell_state_experiment()
