# language: pt
Funcionalidade: Regras Obrigatórias de Compliance
  Como auditor de compliance
  Eu preciso que as regras obrigatórias sejam consistentes

  # ── Contradição Tipo 7: Modal ───────────────────────────────────
  # Necessário(P) ∧ Impossível(P) → ⊥

  Cenário: Relatório obrigatório
    Dado que o relatório é obrigatório
    Então o gerente deve gerar o relatório mensal

  Cenário: Relatório impossível
    Dado que o sistema não pode gerar relatórios
    Então o gerente não pode gerar o relatório mensal
