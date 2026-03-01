import marimo

__generated_with = "0.17.7"
app = marimo.App(app_title="qcircuit exploration")


@app.cell
def _(mo):
    mo.md(r"""
    # qcircuit exploration

    Add gates to the circuit to view their effect on input qubits. A gate is entered using its string representation, which consists of a sequence of characters indicating the action of the gate on the input qubits, from top to bottom. The available characters and their actions are described below:

    - `'I'` is the identity operation and has no effect
    - `'+'` is the target of a controlled not operation
    - `'X'` is one of two targets for a controlled swap operation
    - `'C'` is a control qubit
    - `'O'` is an inverted control qubit

    e.g. "CIC+" applies a controlled not operation to the fourth qubit, using qubits one and three as controls.
    """)
    return


@app.cell
def _(mo):
    remove_button = mo.ui.run_button(label="Remove last gate")
    gate_str = mo.ui.text(label="Enter gate string:").form(
        submit_button_label="Add gate",
        clear_on_submit=True,
    )
    mo.vstack([gate_str, remove_button])
    return gate_str, remove_button


@app.cell
def create_circuit(circ, gate_str, remove_button):
    if remove_button.value:
        circ.gates.pop()
        circ.resize_circuit()
    elif gate_str.value:
        circ.add_gate(gate=gate_str.value, resize_circuit=True)
    length = len(circ)
    circ
    return (length,)


@app.cell
def _(length, mo):
    rslider = mo.ui.range_slider(0, length, show_value=True)
    rslider
    return (rslider,)


@app.cell
def _(circ, rslider):
    circ[rslider.value[0]:rslider.value[1]]
    return


@app.cell
def _():
    import marimo as mo
    from circuit import BinaryExpression, Gate, Circuit
    return Circuit, mo


@app.cell
def _(Circuit):
    circ = Circuit(["I+C", "+CC", "C+C", "I+C", "CI+"], 3)
    return (circ,)


if __name__ == "__main__":
    app.run()
