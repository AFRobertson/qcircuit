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
    - `0` (zero) sets the bit to zero for use as an ancillary
    - `1` (one) sets the bit to one for use as an ancillary

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


@app.cell(hide_code=True)
def _(ExponentExpression, mo):
    def set_polynomial_mode(value):
        ExponentExpression.INTEGER_POLYNOMIAL_MODE = value

    polynomial_mode_switch = mo.ui.switch(
        value=True,
        label="Convert exponents to polynomials",
        on_change=set_polynomial_mode,
    )

    gate_str = mo.ui.text(label="Enter gate string:")
    insert_idx = mo.ui.number(value=None, label="at index:")
    add_gate_button = mo.ui.run_button(label="Add gate")
    remove_button = mo.ui.run_button(label="Remove gate", kind="warn")
    clear_button = mo.ui.run_button(label="Clear circuit", kind="danger")

    mo.vstack([
        mo.md("### Add gates to the circuit"),
        mo.hstack([gate_str, add_gate_button, insert_idx], justify="start"),
        mo.hstack([remove_button, clear_button], justify="start"),
        polynomial_mode_switch,
    ])
    return (
        add_gate_button,
        clear_button,
        gate_str,
        insert_idx,
        polynomial_mode_switch,
        remove_button,
    )


@app.cell(hide_code=True)
def create_circuit(
    add_gate_button,
    circ,
    clear_button,
    gate_str,
    insert_idx,
    polynomial_mode_switch,
    remove_button,
):
    polynomial_mode_switch
    if remove_button.value:
        idx = insert_idx.value
        if idx is not None and idx < 0:
            idx -= 1
        if idx is None:
            idx = -1
        circ.gates.pop(idx)
        circ.resize_circuit()
    if clear_button.value:
        circ.gates.clear()
        circ.resize_circuit()
    elif add_gate_button.value:
        if insert_idx.value is None:
            circ.add_gate(gate=gate_str.value, resize_circuit=True)
        else:
            circ.insert_gate(insert_idx.value, gate_str.value, resize_circuit=True)
    length = len(circ)
    circ
    return (length,)


@app.cell
def _(length, mo):
    rslider = mo.ui.range_slider(0, length, show_value=True, full_width=length > 30)
    rslider
    return (rslider,)


@app.cell
def _(circ, rslider):
    circ[rslider.value[0]:rslider.value[1]]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Truth table
    """)
    return


@app.cell
def _(circ, length, mo):
    mo.stop(length == 0)
    circ.truth_table()
    return


@app.cell
def _(mo):
    save_str = mo.ui.text(label="Enter filepath:").form(
        label="Save circuit to JSON file",
        submit_button_label="Save circuit",
        clear_on_submit=True,
        show_clear_button=True,
    )
    save_str
    return (save_str,)


@app.cell(hide_code=True)
def _(circ, mo, os, save_str):
    _text = ""
    if (path := save_str.value):
        if "." not in path:
            path += ".json"
        if not os.path.exists(path):
            circ.save(path)
            _text = f"Circuit saved to {path}"
        else:
            _text = "Path already exists"
    mo.md(_text)
    return


@app.cell
def _(circ, length):
    length
    [g.sequence for g in circ.gates]
    return


@app.cell
def _():
    import os
    import marimo as mo
    from circuit import BooleanExpression, ExponentExpression, Gate, Circuit

    return Circuit, ExponentExpression, mo, os


if __name__ == "__main__":
    app.run()
