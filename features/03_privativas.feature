# language: pt
Funcionalidade: Permissões de Usuário Autenticado
  Como sistema de autorização
  Eu preciso garantir consistência entre aptidão e permissão

  # ── Contradição Tipo 4: Privativa (Apt ∧ Has ∧ Priv) ────────────
  # Sujeito apto está simultaneamente em posse e em privação.

  @apt-usuario_autenticado-acesso_relatorio
  Cenário: Usuário autenticado com acesso ao relatório
    Dado que o usuario_autenticado está logado
    Então o usuario_autenticado tem acesso_relatorio

  @apt-usuario_autenticado-acesso_relatorio
  Cenário: Usuário autenticado sem acesso ao relatório (privação)
    Dado que o usuario_autenticado está logado
    E o usuario_autenticado tem perfil básico
    Então o usuario_autenticado não tem acesso_relatorio

  # ── Mera Carência (sem contradição) ─────────────────────────────
  # O objeto inanimado não é apto, então a ausência não é privação.

  Cenário: Objeto sem acesso (carência, não privação)
    Dado que o objeto_inanimado existe no sistema
    Então o objeto_inanimado não tem acesso_relatorio
