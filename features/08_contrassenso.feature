# language: pt
Funcionalidade: Manutenção do Sistema de Permissões
  Como administrador
  Eu preciso testar cenários de manutenção

  # ── Contradição Tipo 9: Contrassenso Formal (Widersinn) ─────────
  # Desabilita o motor de regras mas depende dele para validar.

  Cenário: Desabilitar validação e depois validar
    Dado que o sistema de validação está ativo
    Quando o administrador desabilita o sistema de validação
    Então o sistema verifica a permissão do usuário

  # ── Contradição Tipo 10: Contradição Performativa ───────────────
  # O cenário afirma que o sistema está offline mas executa ações nele.

  Cenário: Testar funcionalidade com sistema offline
    Dado que o sistema está offline
    E o sistema está indisponível
    Quando o usuario acessa o dashboard
    Então o usuario navega até o relatório financeiro
