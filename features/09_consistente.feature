# language: pt
Funcionalidade: Fluxo de Login Consistente
  Como sistema de autenticação
  Eu preciso que o fluxo de login seja logicamente consistente

  # ── Sem contradições — cenário de controle ──────────────────────

  Cenário: Login bem-sucedido
    Dado que o usuario está na página de login
    Quando o usuario insere credenciais válidas
    Então o usuario tem acesso ao sistema

  Cenário: Login falho
    Dado que o usuario está na página de login
    Quando o usuario insere credenciais inválidas
    Então o usuario não tem acesso ao sistema
