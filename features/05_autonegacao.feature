# language: pt
Funcionalidade: Sistema de Autenticação
  Como sistema de segurança
  Eu preciso garantir que as regras não se autonenam

  # ── Contradição Tipo 6: Autonegação ─────────────────────────────
  # A proposição destrói os fundamentos que ela pressupõe.

  @presupposes-autenticacao-sessao_ativa
  @negates-sessao_ativa
  Cenário: Regra que destrói sua própria base (autonegação)
    Dado que o sistema de autenticacao está ativo
    Quando o administrador desabilita a sessao_ativa
    Então o sistema verifica a autenticacao do usuário

  # ── Autonegação via Given/Then ──────────────────────────────────

  Cenário: Then contradiz Given (autonegação estrutural)
    Dado que o usuario tem acesso ao painel
    Quando o usuario executa ação no painel
    Então o usuario não tem acesso ao painel
