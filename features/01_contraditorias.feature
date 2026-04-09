# language: pt
Funcionalidade: Controle de Acesso à Tesouraria
  Como administrador do sistema
  Eu quero definir regras de acesso
  Para garantir a segurança financeira

  # ── Contradição Tipo 1: Contraditória (A ∧ ¬A) ──────────────────
  # O mesmo sujeito possui e não possui o mesmo atributo.

  Cenário: Gerente com acesso à tesouraria
    Dado que o usuário é Gerente
    Então o usuário tem acesso à tesouraria

  Cenário: Gerente sem acesso à tesouraria
    Dado que o usuário é Gerente
    Então o usuário não tem acesso à tesouraria

  # ── Contradição Indireta via Implicação ──────────────────────────

  Regra: Regras de Permissão por Cargo

    Cenário: Caixa com acesso via permissão de gerente
      Dado que o usuário é Caixa
      E o Caixa possui as permissões de Gerente
      Então o usuário tem acesso à tesouraria

    Cenário: Caixa sem acesso direto
      Dado que o usuário é Caixa
      Então o usuário não tem acesso à tesouraria
