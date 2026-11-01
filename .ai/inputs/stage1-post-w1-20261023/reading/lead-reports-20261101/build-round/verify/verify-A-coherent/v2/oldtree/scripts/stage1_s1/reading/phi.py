"""The closed testing family Phi: a graphical weighted Bonferroni procedure (Bretz, Maurer, Brannath and Posch
2009), its intersection-union nodes, local levels and Holm (REV3 sections 4.1-4.3, 4.7; AMD B.2-B.3; LN-05, LN-21).

Nodes per contrast k: U_k (two-sided), O_k and L_k (one-sided, adverse; IUT nodes) and F_k (one-sided, toward
feasible). Weights and edges are exact fractions. Start weights (gamma = 0.1): U_k (1 - gamma)/K, O_k and L_k
gamma/(2K), F_k 0. Edges: U_k -> F_k 1/2, O_k 1/8, L_k 1/8, each other U_j (1/4)/(K - 1) (1/20 for K = 6, 1/8 for
K = 3); F_k -> L_k 1 (the R1.3 edge, LN-05); O_k -> L_k 1/2, U_k 1/2; L_k -> O_k 1/2, U_k 1/2.

The sequential rule: while some active node has p <= alpha w, reject it and update
    w_l <- w_l + w_j g_jl;  g_lk <- (g_lk + g_lj g_jk) / (1 - g_lj g_jl)   (0 when the denominator is 0).
The result does not depend on the order of rejections; the routine takes the smallest p among the candidates.
A node's local level is alpha w (one-sided for O, L, F; two-sided for U).

IUT nodes (REV3 4.3): O_k's p-value is max(p of O(m) - O(c) <= 0, p of O(m) - O(theta0) <= tau_O*); L_k's is
max(p of L(m) - L(c) <= 0, p of L(m) - L(a0) <= tau_L). F_k's p-value is 1 - the theta0 part's p-value, on the
same estimate, SE and df (REV3 3.6 item 4), so F_k and O_k never both reject.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as Fr

from scripts.stage1_s1.reading.settings import Refusal, fraction, settings

KINDS = ("U", "O", "L", "F")


@dataclass(frozen=True)
class Graph:
    nodes: tuple                         # ((kind, contrast), ...)
    weights: dict                        # node -> Fraction
    edges: dict                          # node -> {node -> Fraction}


def node(kind: str, contrast: str) -> tuple:
    return (kind, contrast)


def build_graph(contrasts, cfg: dict | None = None) -> Graph:
    """Phi on the named contrasts from the settings' weights (plan A: six; plan B: three, LN-21)."""
    cfg = cfg or settings()["phi"]
    contrasts = tuple(contrasts)
    k = len(contrasts)
    if k < 2:
        raise Refusal("Phi needs at least two contrasts")
    gamma, uu = fraction(cfg["gamma"]), fraction(cfg["u_to_u_total"])
    nodes = tuple(node(kind, c) for c in contrasts for kind in KINDS)
    weights = {n: Fr(0) for n in nodes}
    edges = {n: {m: Fr(0) for m in nodes if m != n} for n in nodes}
    for c in contrasts:
        u, o, l, f = node("U", c), node("O", c), node("L", c), node("F", c)
        weights[u] = (1 - gamma) / k
        weights[o] = gamma / (2 * k)
        weights[l] = gamma / (2 * k)
        edges[u][f] = fraction(cfg["u_to_f"])
        edges[u][o] = fraction(cfg["u_to_o"])
        edges[u][l] = fraction(cfg["u_to_l"])
        for other in contrasts:
            if other != c:
                edges[u][node("U", other)] = uu / (k - 1)
        edges[f][l] = fraction(cfg["f_to_l"])
        edges[o][l] = fraction(cfg["o_to_l"])
        edges[o][u] = fraction(cfg["o_to_u"])
        edges[l][o] = fraction(cfg["l_to_o"])
        edges[l][u] = fraction(cfg["l_to_u"])
    graph = Graph(nodes, weights, edges)
    check_graph(graph)
    return graph


def holm_graph(nodes) -> Graph:
    """The Holm graph: equal weights, every rejected node's weight shared equally among the rest."""
    nodes = tuple(nodes)
    n = len(nodes)
    weights = {m: Fr(1, n) for m in nodes}
    edges = {m: {o: (Fr(1, n - 1) if n > 1 else Fr(0)) for o in nodes if o != m} for m in nodes}
    return Graph(nodes, weights, edges)


def check_graph(graph: Graph) -> None:
    if sum(graph.weights.values()) != 1:
        raise Refusal("the graph's weights do not sum to 1")
    for n in graph.nodes:
        total = sum(graph.edges[n].values())
        if total not in (0, 1):
            raise Refusal(f"the passing row of {n} sums to {total}, not 0 or 1")
        if any(v < 0 for v in graph.edges[n].values()) or graph.weights[n] < 0:
            raise Refusal("a weight is negative")


def update(graph: Graph, j) -> Graph:
    """Remove the rejected node j (Bretz et al. 2009, Algorithm 1), exactly."""
    rest = tuple(n for n in graph.nodes if n != j)
    weights = {l: graph.weights[l] + graph.weights[j] * graph.edges[j][l] for l in rest}
    edges = {}
    for l in rest:
        edges[l] = {}
        for k in rest:
            if k == l:
                continue
            den = 1 - graph.edges[l][j] * graph.edges[j][l]
            edges[l][k] = (graph.edges[l][k] + graph.edges[l][j] * graph.edges[j][k]) / den if den != 0 else Fr(0)
    return Graph(rest, weights, edges)


def levels(graph: Graph, alpha: Fr) -> dict:
    return {n: alpha * graph.weights[n] for n in graph.nodes}


@dataclass(frozen=True)
class Outcome:
    rejected: tuple                      # in rejection order
    level_at_rejection: dict             # node -> Fraction (the local level the node was tested at)
    final_levels: dict                   # node -> Fraction for the nodes left standing
    start_levels: dict


def run(graph: Graph, pvalues: dict, alpha=Fr(1, 20), tolerance: float = 1e-12) -> Outcome:
    """The sequentially rejective procedure on p-values (node -> float in [0, 1])."""
    if set(pvalues) != set(graph.nodes):
        raise Refusal("the p-values do not name exactly the graph's nodes")
    for n, p in pvalues.items():
        if isinstance(p, bool) or not isinstance(p, (int, float)) or not (0.0 <= p <= 1.0):
            raise Refusal(f"the p-value of {n} is not a number in [0, 1]")
    alpha = Fr(alpha)
    start = levels(graph, alpha)
    current = graph
    rejected, at = [], {}
    while True:
        lv = levels(current, alpha)
        candidates = [n for n in current.nodes if pvalues[n] <= float(lv[n]) * (1.0 + tolerance)]
        if not candidates:
            break
        j = min(candidates, key=lambda n: (pvalues[n], current.nodes.index(n)))
        rejected.append(j)
        at[j] = lv[j]
        current = update(current, j)
    return Outcome(tuple(rejected), at, levels(current, alpha), start)


def holm(pvalues: dict, alpha: float = 0.05) -> set:
    """Holm's step-down procedure, for the test that the graph routine equals Holm on a Holm graph."""
    order = sorted(pvalues, key=lambda n: pvalues[n])
    n = len(order)
    rejected = set()
    for i, name in enumerate(order):
        if pvalues[name] <= alpha / (n - i) * (1.0 + 1e-12):
            rejected.add(name)
        else:
            break
    return rejected


def iut(p_a: float, p_b: float) -> float:
    """The intersection-union p-value: the larger of the two parts' one-sided p-values."""
    return max(p_a, p_b)
