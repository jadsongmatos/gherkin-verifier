Would an agent likely miss this without help? Yes. We now rely on symbolic pre-checks (SymPy) before SMT solving for propositional parts.
Would an agent likely miss this without help? Yes. The pipeline flow is: parse Gherkin -> extract propositions -> build symbolic expressions (SymPy) -> apply the 10 contradiction types -> produce a report.
Would an agent likely miss this without help? Yes. The project now includes a symbolic module at gherkin_verifier/symbolic.py.
Would an agent likely miss this without help? Yes. SymPy pre-checks perform CNF/DNF normalization and quick unsat checks to prune heavy SMT runs.
Would an agent likely miss this without help? Yes. The entrypoint verify.py remains, but internal flow is symbolic-first.
Would an agent likely miss this without help? Yes. Tests cover symbolic path and symbolic formulas in reports.
Would an agent likely miss this without help? Yes. The build now depends on sympy; ensure installed alongside z3-solver, gherkin-official, networkx.
Would an agent likely miss this without help? Yes. The Markdown report (--md) can include symbolic context sections as the design evolves.
Would an agent likely miss this without help? Yes. CI should reflect symbolic pre-checks in test coverage.
Would an agent likely miss this without help? Yes. Use gherkin-verify with --md or --json; those flags unchanged.
Would an agent likely miss this without help? Yes. The PT-BR README is complemented by symbolic-first guidance.
Would an agent likely miss this without help? Yes. The CLI supports directory traversal via features/.
Would an agent likely miss this without help? Yes. For full coverage, run tests with 100% coverage (pytest + pytest-cov).
