"""Quantum circuit visualisation."""

from typing import Optional


DEFAULT_LABELS = "abcdefghijklmnopqrstuvwxyz"


def iweave(iter1, iter2):
    """Yields from two iterables alternately."""
    it = iter(iter2)
    for item in iter1:
        yield item
        try:
            yield next(it)
        except StopIteration:
            break


def weave(iter1, iter2):
    """Creates a list of values alternating between two iterables."""
    return list(iweave(iter1, iter2))


def set_add_mod2(set_: set, item):
    """Adds `item` to the set if it doesn't exist, otherwise removes it."""
    if item in set_:
        set_.remove(item)
    else:
        set_.add(item)


def _str_findall(str_: str, char: str):
    """Yields indexes of all instances of `char`."""
    for idx, c in enumerate(str_):
        if c == char:
            yield idx


class BinaryExpression:
    """Representation of a boolean arithmetic expression."""

    # The underlying data structure is a set of frozensets. The frozensets
    # represent products of boolean variables, and the containing set represents
    # the sum (modulo 2) of these products.

    # Multiplication is equivalent to the union of frozensets. Addition modulo 2
    # is equivalent to the symmetric difference of containing sets.

    # If the frozensets contain integers, they can be used as indexes to a list
    # of labels so that the expression can be printed in a human-readable form.

    def __init__(self, expr: set[frozenset]):
        self.expr = set(frozenset(term) for term in expr)

    def __iter__(self):
        return iter(self.expr)

    def __contains__(self, item):
        return item in self.expr

    def __len__(self):
        return len(self.expr)

    def __eq__(self, other):
        if isinstance(other, BinaryExpression):
            return self.expr == other.expr
        return self.expr == other

    def multiply_by_term(self, term: set | frozenset):
        """Multiplies the expression by a single term, as a set."""
        result = set()
        for item in self:
            product = item.union(term)
            set_add_mod2(result, product)

        return self.__class__(result)

    def multiply_by_expr(self, expr: set[frozenset]):
        """Multiplies the expression by another, as a set of frozensets."""
        result = set()
        for term in expr:
            result ^= self.multiply_by_term(term).expr
        return self.__class__(result)

    def drawable(self, labels: str | list[str] = DEFAULT_LABELS):
        """Creates a human-readable algebraic expression."""

        def _interpret_term(t):
            if len(t) == 0:
                return "1"
            return "".join(labels[k] for k in t)

        return " ⨁ ".join(_interpret_term(t) for t in self.ordered_terms())

    def draw(self, labels: str | list[str] = DEFAULT_LABELS):
        """Prints a human-readable algebraic expression."""
        print(self.drawable(labels))

    @classmethod
    def one(cls):
        """Creates a binary expression representing 1."""
        return cls({frozenset()})

    def invert(self):
        """Adds 1 to the expression. Equivalent to a single-qubit not gate."""
        return self + self.one()

    def ordered_terms(self):
        """Returns a sorted collection of terms in the expression."""
        def key(x):
            return "".join(chr(i) for i in sorted(x))
        ordered = [sorted(f) for f in self.expr]
        return sorted(ordered, key=key)

    @staticmethod
    def _add_mod2(set_: set, other):
        """Helper for updating a binary expression."""
        if isinstance(other, BinaryExpression):
            set_.symmetric_difference_update(other.expr)
        elif isinstance(other, set[frozenset]):
            set_.symmetric_difference_update(other)
        elif isinstance(other, (set, frozenset)):
            set_add_mod2(set_, other)
        else:
            return NotImplemented

    def __add__(self, other):
        expr = self.expr.copy()
        if self._add_mod2(expr, other) is NotImplemented:
            return NotImplemented
        return self.__class__(expr)

    def __iadd__(self, other):
        if self._add_mod2(self.expr, other) is NotImplemented:
            return NotImplemented
        return self

    def __mul__(self, other):
        if isinstance(other, BinaryExpression):
            return self.multiply_by_expr(other.expr)
        if isinstance(other, set[frozenset]):
            return self.multiply_by_expr(other)
        if isinstance(other, (set, frozenset)):
            return self.multiply_by_term(other)
        return NotImplemented


class Gate:
    """Simple quantum CNOT or Fredkin gate.

    Parameters
    ----------
    sequence (str with elements from {'I', '+', 'X', 'C', 'O'})
        A string representing the action of the gate on the qubits from top to
        bottom:
            - `'I'` is the identity operation and has no effect
            - `'+'` is the target of a controlled not operation
            - `'X'` is one of two targets for a controlled swap operation
            - `'C'` is a control qubit
            - `'O'` is an inverted control qubit
    """

    singletons = {
        "I": "---",
        "i": "-|-",
        "+": "-⨁-",  # "-⊕-",
        "C": "-●-",
        "O": "-○-",
        "X": "-✕-",
    }

    def __init__(self, sequence: str):
        sequence = sequence.upper()
        midseq = sequence.strip("I").replace("I", "i")
        self.sequence = sequence.replace(midseq.upper(), midseq)
        self.validate()

    def __len__(self):
        return len(self.sequence)

    size = property(__len__, doc="The number of input qubits for the gate.")

    @property
    def min_size(self):
        """The minimum size the gate can be resized to."""
        return len(self.sequence.rstrip("I"))

    @property
    def acting_size(self):
        """The actual number of qubits acted on by the gate."""
        return len(self.sequence.upper().replace("I", ""))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.sequence!r})"

    __str__ = __repr__

    def symbols(self):
        """Creates a list of symbols which graphically represent the gate."""

        seq = self.sequence
        symbols = [self.singletons[c] for c in seq]

        parts = seq.partition(seq.strip("I"))
        l, m, r = [len(part) for part in parts]

        midrow = l * ["   "] + (m - 1) * [" | "] + r * ["   "]

        return weave(symbols, midrow)

    def draw(self):
        """Prints a graphical representation of the gate."""
        print(*self.symbols(), sep="\n")

    def validate(self):
        """Validates the sequence representation of the gate."""
        seq = self.sequence
        valid = (
            all(c in self.singletons for c in seq)
            and not ("+" in seq and "X" in seq)
            and (
                seq.count("+") == 1
                or seq.count("X") == 2
            )
        )
        if not valid:
            raise ValueError("invalid string representation.")

    def _get_control(self, states: list[BinaryExpression]):
        """Returns a product of the control states."""

        control = _str_findall(self.sequence, "C")
        anticontrol = _str_findall(self.sequence, "O")

        try:
            product = states[next(control)]
        except StopIteration:
            product = BinaryExpression.one()

        for idx in control:
            product *= states[idx]
        for idx in anticontrol:
            product *= states[idx].invert()

        return product

    def _apply_cnot(self, states: list[BinaryExpression]):
        """Applies a controlled not operation."""
        target = self.sequence.find("+")
        result = states[target] + self._get_control(states)
        return states[:target] + [result] + states[target + 1:]

    def _apply_fredkin(self, states: list[BinaryExpression]):
        """Applies a controlled swap operation."""

        seq = self.sequence
        l, r = seq.find("X"), seq.rfind("X")

        summand = self._get_control(states) * (states[l] + states[r])
        lswap = summand + states[l]
        rswap = summand + states[r]

        return states[:l] + [lswap] + states[l + 1:r] + [rswap] + states[r + 1:]

    def apply(self, states: list[BinaryExpression]):
        """Applies the gate to a list of states, returning the output."""
        states = list(states)
        if "+" in self.sequence:
            return self._apply_cnot(states)
        if "X" in self.sequence:
            return self._apply_fredkin(states)
        return states

    def resize(self, size: int):
        """Resizes the gate."""

        base = self.sequence.rstrip("I")
        if len(base) > size:
            raise ValueError(
                f"target size {size} is less than "
                f"the minimum for the gate ({len(base)})."
            )
        self.sequence = base.ljust(size, "I")

    def __or__(self, other):
        if isinstance(other, str):
            other = Gate(other)
        if isinstance(other, Gate):
            return Circuit([self, other])
        if isinstance(other, Circuit):
            return Circuit([self] + other.gates, max(self.size, other.width))


class Circuit:
    """A quantum circuit of simple gates.

    Parameters
    ----------
    gates (list[str | Gate])
        The gates comprising the circuit, either as a list of `circuit.Gate`
        objects or a list of `str` representations of the gates.
    n_qubits (int)
        The number of wires in the circuit. If None, it will be set to the
        maximum size among the gates. Any gates smaller in size than this
        value will be resized to fit.
    """

    def __init__(self, gates: list[str | Gate], n_qubits: int = None):
        self.__n_qubits = n_qubits
        if n_qubits is None:
            self.__n_qubits = max(len(gate) for gate in gates)

        self.gates: list[Gate] = []
        for gate in gates:
            self.add_gate(gate)

    @property
    def width(self):
        """The number of wires in the circuit."""
        return self.__n_qubits

    n_qubits = width

    @property
    def length(self):
        """The number of gates in the circuit."""
        return len(self)

    @property
    def min_width(self):
        """The minimum width the circuit can be resized to."""
        return max(gate.min_size for gate in self.gates)

    def __len__(self):
        return len(self.gates)

    def __getitem__(self, index):
        item = self.gates[index]

        if isinstance(item, Gate):
            return item
        return self.__class__(item, self.width)

    def resize_circuit(self, n_qubits: int = None):
        """Resizes the circuit and its gates.

        Resizes to a width of `n_qubits`. If `n_qubits` is None, the circuit
        will be resized to `self.min_width`.
        """

        min_width = self.min_width
        if n_qubits is None:
            n_qubits = min_width

        if n_qubits < min_width:
            raise ValueError(
                f"target width {n_qubits} is less than "
                f"the minimum for the circuit ({min_width})."
            )

        for gate in self.gates:
            gate.resize(n_qubits)

        self.__n_qubits = n_qubits

    def _conform(self, gate: str | Gate, resize_circuit: bool = False):
        """Conforms the gate or optionally the circuit to fit the other."""

        if isinstance(gate, str):
            gate = Gate(gate)

        if gate.size > self.width:
            if resize_circuit:
                self.resize_circuit(gate.size)
            else:
                raise ValueError("gate is larger than width of circuit.")
        elif gate.size < self.width:
            gate.resize(self.width)

        return gate

    def add_gate(self, gate: str | Gate, resize_circuit: bool = False):
        """Adds a gate to the end of the circuit.

        Parameters
        ----------
        gate (str | Gate)
            The gate to be added. Can be a `circuit.Gate` object or a string
            representation of the gate.
        resize_circuit (bool, default False)
            Whether to expand the width of the circuit if the gate is larger
            than it. If False, it will raise a ValueError instead.
        """
        gate = self._conform(gate, resize_circuit)
        self.gates.append(gate)

    def insert_gate(
        self, index: int, gate: str | Gate, resize_circuit: bool = False
    ):
        """Inserts a gate into the circuit at the specified index.

        Parameters
        ----------
        index (int)
            The index at which to insert the gate.
        gate (str | Gate)
            The gate to be added. Can be a `circuit.Gate` object or a string
            representation of the gate.
        resize_circuit (bool, default False)
            Whether to expand the width of the circuit if the gate is larger
            than it. If False, it will raise a ValueError instead.
        """
        gate = self._conform(gate, resize_circuit)
        self.gates.insert(index, gate)

    def _format_labels(self, labels: str | list[str]):
        """Formats the labels so that they can be drawn."""
        labels = labels[:self.width]
        length = max(len(l) for l in labels) + 1
        labels = [l.ljust(length) for l in labels]
        spaces = [" " * length] * (self.width - 1)
        return weave(labels, spaces)

    def _format_output(self, labels: str | list[str]):
        """Formats the output states so that they can be drawn."""
        output = [" " + expr.drawable(labels) for expr in self.run()]
        spaces = [""] * (self.width)
        return weave(output, spaces)

    def draw(self, labels: Optional[str | list[str]] = None):
        """Prints a graphical representation of the circuit."""

        if labels is None:
            labels = DEFAULT_LABELS

        symbols = [gate.symbols() for gate in self.gates]

        if len(labels) >= self.width:
            output = self._format_output(labels)
            labels = self._format_labels(labels)
            symbols = [labels] + symbols + [output]

        for line in zip(*symbols):
            print(*line, sep="")

    def initial_state(self):
        """Creates the initial state for the circuit."""
        states = []
        for i in range(self.width):
            states.append(BinaryExpression({frozenset([i])}))
        return states

    def run(self, states: list[BinaryExpression] = None):
        """Applies each gate in sequence to the given input states."""

        if states is None:
            states = self.initial_state()

        for gate in self.gates:
            states = gate.apply(states)

        return states

    def __or__(self, other):
        cls = self.__class__
        if isinstance(other, str):
            other = Gate(other)
        if isinstance(other, Gate):
            return cls(self.gates + [other], self.width)
        if isinstance(other, Circuit):
            return cls(self.gates + other.gates, max(self.width, other.width))

    def __ior__(self, other):
        if isinstance(other, str):
            other = Gate(other)
        if isinstance(other, Gate):
            self.add_gate(other, resize_circuit=True)
        elif isinstance(other, Circuit):
            for gate in other.gates:
                self.add_gate(gate, resize_circuit=True)
        return self
