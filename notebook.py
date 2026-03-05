import marimo

__generated_with = "0.20.2"
app = marimo.App(app_title="qcircuit exploration")


@app.cell
def _(mo):
    mo.md(r"""
    # qcircuit exploration

    Add gates to the circuit to view their effect on input qubits. A gate is entered using its string representation, which consists of a sequence of characters indicating the action of the gate on the input qubits, from top to bottom. The available characters and their actions are described below:

    - `I` is the identity operation and has no effect
    - `+` is the target of a controlled not operation
    - `X` is one of two targets for a controlled swap operation
    - `C` is a control qubit
    - `O` is an inverted control qubit
    - `U` is a generic unitary operation
    - `U'` is the inverse of U

    e.g. "CIC+" applies a controlled not operation to the fourth qubit, using qubits one and three as controls.
    """)
    return


@app.cell
def _(mo):
    browser_form = mo.ui.file_browser(
        "./examples/",
        filetypes=[".json"],
        multiple=False,
        restrict_navigation=True,
        label="Select saved circuit...",
    ).form(
        label="Load a circuit from a JSON file",
        submit_button_label="Load circuit",
    )
    browser_form
    return (browser_form,)


@app.cell
def _(Circuit, browser_form):
    if browser_form.value:
        circ = Circuit.load(browser_form.value[0].id)
    else:
        circ = Circuit.load("examples/2-controlled-U.json")
    return (circ,)


@app.cell
def _(mo):
    remove_button = mo.ui.run_button(label="Remove last gate")
    clear_button = mo.ui.run_button(label="Clear circuit")
    gate_str = mo.ui.text(label="Enter gate string:").form(
        label="Add gates to the circuit",
        submit_button_label="Add gate",
        clear_on_submit=True,
    )
    mo.vstack([gate_str, mo.hstack([remove_button, clear_button], justify="start")])
    return clear_button, gate_str, remove_button


@app.cell
def create_circuit(circ, clear_button, gate_str, remove_button):
    if remove_button.value:
        circ.gates.pop()
        circ.resize_circuit()
    if clear_button.value:
        circ.gates.clear()
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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### truth table
    """)
    return


@app.cell
def _(circ, gate_str, remove_button):
    remove_button
    gate_str
    circ.truth_table()
    return


@app.cell
def _(mo):
    save_str = mo.ui.text(label="Enter filepath:").form(
        label="Save circuit to JSON file",
        submit_button_label="Save circuit",
        clear_on_submit=True,
    )
    save_str
    return (save_str,)


@app.cell
def _(circ, save_str):
    if (path := save_str.value):
        circ.save(path)
        if "." not in path:
            path += ".json"
        print(f"Circuit saved to {path}")
    return


@app.cell
def _(circ, gate_str):
    gate_str
    [g.sequence for g in circ.gates]
    return


@app.cell
def _():
    import marimo as mo
    from circuit import BooleanExpression, Gate, Circuit

    return Circuit, mo


if __name__ == "__main__":
    app.run()
