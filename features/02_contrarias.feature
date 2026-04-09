# language: pt
Funcionalidade: Política de Acesso Universal
  Como auditor
  Eu quero garantir que as políticas de acesso são consistentes

  # ── Contradição Tipo 2: Contrária (A vs E) ──────────────────────
  # Duas universais que não podem ser ambas verdadeiras.
  # "Todo X é P" vs "Nenhum X é P"

  Cenário: Todos os caixas têm acesso
    Dado que todo caixa está autenticado
    Então todo caixa tem acesso ao relatório financeiro

  Cenário: Nenhum caixa tem acesso
    Dado que nenhum caixa tem autorização especial
    Então nenhum caixa tem acesso ao relatório financeiro
