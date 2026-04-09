# language: pt
Funcionalidade: Gestão de Usuários
  Como sistema de gestão
  Eu preciso que o termo "usuário" seja usado de forma unívoca

  # ── Contradição Tipo 8: Suplência (quaternio terminorum) ─────────
  # O mesmo termo "usuario" muda de significado entre cenários.

  Cenário: Usuário autenticado tem acesso
    Dado que o usuario está autenticado
    Então o usuario tem acesso ao dashboard

  Cenário: Usuário anônimo não tem acesso
    Dado que o usuario é anônimo
    Então o usuario não tem acesso ao dashboard
