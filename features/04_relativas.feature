# language: pt
Funcionalidade: Hierarquia Organizacional
  Como sistema de RH
  Eu preciso manter a consistência dos correlatos

  # ── Contradição Tipo 5: Relativa (violação de correlatos) ────────
  # R(a,b) ∧ ¬R⁻¹(b,a) — assimetria de recíproca

  @rel-gerente-subordinado-controla-controlado_por
  Cenário: João é gerente de Maria
    Dado que o gerente João está ativo
    Então o gerente controla o subordinado Maria

  @rel-gerente-subordinado-controla-controlado_por
  Cenário: Maria não é subordinada de ninguém (contradição relativa)
    Dado que a subordinado Maria está ativa
    Então a subordinado Maria não é controlado_por nenhum gerente
