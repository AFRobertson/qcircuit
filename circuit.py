"""Quantum circuit visualisation."""

from typing import Optional


def iweave(iter1, iter2):
    it = iter(iter2)
    for item in iter1:
        yield item
        try:
            yield next(it)
        except StopIteration:
            break


def weave(iter1, iter2):
    return list(iweave(iter1, iter2))


def set_add_mod2(set_: set, item):
    if item in set_:
        set_.remove(item)
    else:
        set_.add(item)


def _add_mod2(set_: set, other):
    if isinstance(other, BinaryExpression):
        set_.symmetric_difference_update(other.expr)
    elif isinstance(other, set[frozenset]):
        set_.symmetric_difference_update(other)
    elif isinstance(other, (set, frozenset)):
        set_add_mod2(set_, other)
    else:
        return NotImplemented


def _str_findall(str_: str, char: str):
    for idx, c in enumerate(str_):
        if c == char:
            yield idx


class BinaryExpression:
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
        result = set()
        for item in self:
            product = item.union(term)
            set_add_mod2(result, product)

        return self.__class__(result)

    def multiply_by_expr(self, expr: set[frozenset]):
        result = set()
        for term in expr:
            result ^= self.multiply_by_term(term).expr
        return self.__class__(result)

    def drawable(self, labels: str | list[str] = "abcdefghijklmnopqrstuvwxyz"):
        """Creates a human-readable algebraic expression."""
        def _interpret_term(t: set):
            if len(t) == 0:
                return "1"
            return "".join(labels[k] for k in t)

        return " ⨁ ".join(_interpret_term(t) for t in self.ordered_terms())

    @classmethod
    def one(cls):
        """Creates a binary expression representing 1."""
        return cls({frozenset()})

    def invert(self):
        """Adds 1 to the expression. Equivalent to a single-qubit not gate."""
        return self + self.one()

    def ordered_terms(self):
        def key(x):
            return "".join(chr(i) for i in sorted(x))
        return sorted(self.expr, key=key)

    def __add__(self, other):
        expr = self.expr.copy()
        if _add_mod2(expr, other) is NotImplemented:
            return NotImplemented
        return self.__class__(expr)

    def __iadd__(self, other):
        if _add_mod2(self.expr, other) is NotImplemented:
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

    @property
    def size(self):
        return len(self.sequence)

    def __len__(self):
        return self.size

    def __repr__(self):
        return f"{self.__class__.__name__}({self.sequence!r})"

    __str__ = __repr__

    def symbols(self):
        seq = self.sequence

        symbols = [self.singletons[c] for c in seq]

        parts = seq.partition(seq.strip("I"))
        l, m, r = [len(part) for part in parts]

        midrow = l * ["   "] + (m - 1) * [" | "] + r * ["   "]

        assert len(midrow) == len(symbols) - 1
        return weave(symbols, midrow)

    def draw(self):
        print(*self.symbols(), sep="\n")

    def validate(self):
        repr = self.sequence
        valid = (
            all(c in self.singletons for c in repr)
            and not ("+" in repr and "X" in repr)
            and (
                repr.count("+") == 1
                or (
                    repr.count("X") == 2
                    and repr.count("C") > 0
                )
            )
        )
        if not valid:
            raise ValueError("invalid string representation.")

    def _apply_cnot(self, states: list[BinaryExpression]):
        control = _str_findall(self.sequence, "C")
        target = self.sequence.find("+")

        product = states[next(control)]
        for idx in control:
            product *= states[idx]

        result = states[target] + product
        return states[:target] + [result] + states[target + 1:]

    def _apply_fredkin(self, states: list[BinaryExpression]):
        seq = self.sequence
        control = states[seq.find("C")]
        l, r = seq.find("X"), seq.rfind("X")

        summand = control * (states[l] + states[r])
        lswap = summand + states[l]
        rswap = summand + states[r]

        return states[:l] + [lswap] + states[l + 1:r] + [rswap] + states[r + 1:]

    def apply(self, states: list[BinaryExpression]):
        states = list(states)
        if "+" in self.sequence:
            return self._apply_cnot(states)
        if "X" in self.sequence:
            return self._apply_fredkin(states)


class Circuit:
    def __init__(self, n_qubits: int = None, gates: list[str] = None):
        self.__n_qubits = n_qubits
        if n_qubits is None:
            self.__n_qubits = max(len(gate) for gate in gates)

        self.gates: list[Gate] = []
        for gate in gates:
            self.add_gate(gate)

    @property
    def width(self):
        return self.__n_qubits

    @property
    def length(self):
        return len(self)

    def __len__(self):
        return len(self.gates)

    def __getitem__(self, index):
        item = self.gates[index]

        if isinstance(item, Gate):
            return item
        return self.__class__(self.width, gates=item)

    def add_gate(self, gate: str | Gate):
        if isinstance(gate, str):
            gate = Gate(gate)

        gate.sequence = gate.sequence.ljust(self.width, "I")
        self.gates.append(gate)

    def _format_labels(self, labels: str | list[str]):
        labels = labels[:self.width]
        length = max(len(l) for l in labels) + 1
        labels = [l.ljust(length) for l in labels]
        spaces = [" " * length] * (self.width - 1)
        return weave(labels, spaces)

    def _format_output(self, labels: str | list[str]):
        output = [" " + expr.drawable(labels) for expr in self.run()]
        spaces = [""] * (self.width)
        return weave(output, spaces)

    def draw(self, labels: Optional[str | list[str]] = None):
        symbols = [gate.symbols() for gate in self.gates]

        if labels is not None:
            output = self._format_output(labels)
            labels = self._format_labels(labels)
            symbols = [labels] + symbols + [output]

        for line in zip(*symbols):
            print(*line, sep="")

    def initial_state(self):
        states = []
        for i in range(self.width):
            states.append(BinaryExpression({frozenset([i])}))
        return states

    def run(self, states: list[BinaryExpression] = None):
        if states is None:
            states = self.initial_state()

        for gate in self.gates:
            states = gate.apply(states)

        return states
