"""Paso 4 - Grover (2 qubits) bajo un NoiseModel despolarizante."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from qiskit.visualization import plot_histogram
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

from grover import build_grover_circuit  # mismo circuito del Paso 3

CAPTURAS = Path(__file__).resolve().parent.parent / "capturas"


def build_noise_model(p1q=0.001, p2q=0.01):
    """Ruido despolarizante: p1q por puerta de 1 qubit (h, x), p2q por puerta de 2 qubits (cz).

    ~0.1 % y ~1 % son ordenes de magnitud tipicos de procesadores
    superconductores NISQ.
    """
    noise_model = NoiseModel()
    noise_model.add_all_qubit_quantum_error(depolarizing_error(p1q, 1), ["h", "x"])
    noise_model.add_all_qubit_quantum_error(depolarizing_error(p2q, 2), ["cz"])
    return noise_model


def grover_noise_experiment(target="11", shots=1024):
    qc = build_grover_circuit(target)

    # Linea base: simulacion ideal
    counts_ideal = AerSimulator().run(qc, shots=shots, seed_simulator=42).result().get_counts()

    # Simulacion con ruido en cada puerta
    noisy_sim = AerSimulator(noise_model=build_noise_model())
    counts_noisy = noisy_sim.run(qc, shots=shots, seed_simulator=42).result().get_counts()

    p_ideal = counts_ideal.get(target, 0) / shots
    p_noisy = counts_noisy.get(target, 0) / shots

    print(f"Grover |{target}> sin ruido: {p_ideal * 100:.1f}%")
    print(f"Grover |{target}> con ruido: {p_noisy * 100:.1f}%")
    print(f"Degradacion: {(p_ideal - p_noisy) * 100:.1f} puntos porcentuales")
    print(f"Counts con ruido: {dict(sorted(counts_noisy.items()))}")

    CAPTURAS.mkdir(exist_ok=True)
    fig, axs = plt.subplots(1, 2, figsize=(10, 4))
    estados = ["00", "01", "10", "11"]  # se muestran los 4 estados aunque su conteo sea 0
    plot_histogram({e: counts_ideal.get(e, 0) for e in estados}, ax=axs[0])
    plot_histogram({e: counts_noisy.get(e, 0) for e in estados}, ax=axs[1])
    axs[0].set_title("Sin ruido")
    axs[1].set_title("Con ruido (despolarizante)")
    fig.tight_layout()
    fig.savefig(CAPTURAS / "grover_noise_comparison.png", dpi=150)
    return p_ideal, p_noisy


def grover_noise_sweep(target="11", shots=4096, p2q_values=(0.01, 0.03, 0.05, 0.10)):
    """Complemento: como cae la probabilidad de exito al subir la tasa de error de 2 qubits."""
    qc = build_grover_circuit(target)
    print("\nBarrido de p2q (p1q = 0.001 fijo):")
    for p2q in p2q_values:
        sim = AerSimulator(noise_model=build_noise_model(p2q=p2q))
        counts = sim.run(qc, shots=shots, seed_simulator=42).result().get_counts()
        print(f"  p2q = {p2q * 100:4.1f}% -> exito |{target}> = {counts.get(target, 0) / shots * 100:.1f}%")


if __name__ == "__main__":
    grover_noise_experiment()
    grover_noise_sweep()
