# Gherkin Formal Verifier

Verificador de contradições lógicas em especificações Gherkin (`.feature`) do Cucumber, baseado na lógica clássica aristotélica e em técnicas de verificação formal (SAT/SMT).

O sistema aplica o método dialético socrático de forma automatizada: extrai proposições lógicas de cenários Gherkin, normaliza-as em variáveis formais e submete o conjunto a solvers (Z3/SAT) e análise de grafos para detectar inconsistências que a linguagem natural esconde.

## Fundamento Filosófico

O projeto implementa uma versão computacional do **elenchus** socrático -- a arte de levar proposições a contradições lógicas para purificar o pensamento de falsas crenças. Assim como Aristóteles catalogou as formas de oposição no *Organon*, este verificador mapeia os 10 tipos de contradição da lógica clássica para verificações formais automatizadas:

| # | Tipo | Princípio Lógico | Ferramenta |
|---|------|-----------------|------------|
| 1 | **Contraditória** | Identidade e Não-Contradição: $A \wedge \neg A = \bot$ | Z3 SAT |
| 2 | **Contrária** | Quadrado Lógico (A vs E): ambas não podem ser verdadeiras | Z3 SAT |
| 3 | **Subcontrária** | Quadrado Lógico (I vs O): ambas não podem ser falsas | Z3 SAT |
| 4 | **Privativa** | Oposição Privativa: aptidão + posse + carência | Z3 FOL |
| 5 | **Relativa** | Correlatos: $R(a,b) \leftrightarrow R^{-1}(b,a)$ | Z3 FOL + NetworkX |
| 6 | **Autonegação** | Contrassenso husserliano: $\text{presupposes} \cap \text{negates} \neq \emptyset$ | Grafo de dependência + Z3 |
| 7 | **Modal** | Modalidades: $\square P \wedge \diamond \neg P \to \bot$ | Z3 axiomas modais |
| 8 | **Suplência** | *Quaternio terminorum*: equivocidade de termos | Análise contextual |
| 9 | **Contrassenso Formal** | *Widersinn* (Husserl): teoria que nega suas condições de possibilidade | Padrões + cruzamento |
| 10 | **Performativa** | Paralaxe Cognitiva: o ato contradiz o conteúdo | Padrões heurísticos |

## Instalação

```bash
pip install z3-solver gherkin-official networkx
```

Ou via requirements:

```bash
pip install -r requirements.txt
```

Requer Python 3.10+.

## Uso

### Verificar um arquivo

```bash
python verify.py features/01_contraditorias.feature
```

### Verificar um diretório inteiro

```bash
python verify.py features/
```

### Modos de saída

```bash
python verify.py features/ --summary    # resumo compacto
python verify.py features/ --json       # saída JSON (para integração CI)
python verify.py features/ --verbose    # inclui proposições extraídas
```

### Exit code

- `0` -- nenhuma contradição critica encontrada
- `1` -- contradições críticas detectadas (útil para CI/CD)

## Exemplo de Saída

Dado o arquivo `features/01_contraditorias.feature`:

```gherkin
# language: pt
Funcionalidade: Controle de Acesso à Tesouraria

  Cenário: Gerente com acesso à tesouraria
    Dado que o usuário é Gerente
    Então o usuário tem acesso à tesouraria

  Cenário: Gerente sem acesso à tesouraria
    Dado que o usuário é Gerente
    Então o usuário não tem acesso à tesouraria
```

O verificador produz:

```
========================================================================
  RELATÓRIO DE VERIFICAÇÃO FORMAL -- CONTRADIÇÕES LÓGICAS
========================================================================
  Arquivo:       features/01_contraditorias.feature
  Cenários:      4
  Proposições:   9
  Contradições:  4
    Críticas:    1
    Avisos:      3
------------------------------------------------------------------------

  [CRITICAL] #1: Contraditória (A ∧ ¬A)
  Contradição direta: 'o usuário tem acesso à tesouraria' contradiz
  'o usuário não tem acesso à tesouraria'
  Localização:
    -> features/01_contraditorias.feature:12 (Gerente com acesso à tesouraria)
    -> features/01_contraditorias.feature:16 (Gerente sem acesso à tesouraria)
  Fórmula: usuário|tem|tesouraria ∧ ¬usuário|tem|tesouraria = ⊥
  Z3: unsat
========================================================================
```

## Pipeline de Verificação

```
.feature (Gherkin)
    |
    v
[1] Parser (gherkin-official)
    Extrai cenários, steps, tags da estrutura Gherkin
    |
    v
[2] Extrator de Proposições
    Converte steps em proposições lógicas:
    sujeito, predicado, objeto, negação, quantificador, modalidade
    |
    v
[3] Anotações Ontológicas (via tags)
    @apt-...          -> aptidões (privativa)
    @rel-...          -> relações correlativas (relativa)
    @presupposes-...  -> pressuposições (autonegação)
    @negates-...      -> negações de fundamento (autonegação)
    |
    v
[4] 10 Engines de Verificação Formal
    Z3 SAT/SMT, lógica de primeira ordem, grafos dirigidos
    |
    v
[5] Relatório
    Tipo, severidade, localização, fórmula formal, resultado Z3
```

## Os 10 Tipos de Contradição

### 1. Contraditória (A ∧ ¬A)

A oposição mais radical. Um ser é afirmado e negado ao mesmo tempo, sob o mesmo aspecto.

```gherkin
Cenário: Gerente com acesso
  Então o usuário tem acesso à tesouraria

Cenário: Gerente sem acesso
  Então o usuário não tem acesso à tesouraria
```

**Verificação:** `SAT(A ∧ ¬A) → unsat`

O sistema detecta que ambos os cenários compartilham o mesmo contexto (mesmo Given) e geram conclusões opostas. Cenários com precondições diferentes (ex: "credenciais válidas" vs "credenciais inválidas") **não** geram falso positivo.

### 2. Contrária (A vs E)

Duas proposições universais que não podem ser ambas verdadeiras, mas podem ser ambas falsas. Admite meio-termo.

```gherkin
Cenário: Todos os caixas têm acesso
  Então todo caixa tem acesso ao relatório financeiro

Cenário: Nenhum caixa tem acesso
  Então nenhum caixa tem acesso ao relatório financeiro
```

**Verificação:**
- `SAT(A ∧ E) → insatisfatível` (não podem coexistir)
- `SAT(¬A ∧ ¬E) → satisfatível` (meio-termo: "algum caixa tem acesso parcial")

### 3. Subcontrária (I vs O)

Duas proposições particulares que podem ser ambas verdadeiras, mas não podem ser ambas falsas.

**Verificação:** `SAT(¬I ∧ ¬O) → insatisfatível` com axioma `Or(I, O)`

### 4. Privativa (Apt ∧ Has ∧ Priv)

Oposição entre uma perfeição (posse) e a carência dessa perfeição (privação) em um sujeito apto. A pedra não é "cega" (mera carência); o homem sem visão é cego (privação).

```gherkin
@apt-usuario_autenticado-acesso_relatorio
Cenário: Usuário com acesso
  Então o usuario_autenticado tem acesso_relatorio

@apt-usuario_autenticado-acesso_relatorio
Cenário: Usuário sem acesso (privação)
  Então o usuario_autenticado não tem acesso_relatorio
```

**Modelo de três predicados em Z3 FOL:**

```
Apt(S, P)  -- sujeito é apto a possuir a propriedade
Has(S, P)  -- sujeito efetivamente possui
Priv(S, P) -- sujeito é privado (derivado: Apt ∧ ¬Has)

Axioma: Has(s,p) ∧ Priv(s,p) → ⊥
```

O solver distingue:
- **Posse legítima:** Apt=true, Has=true, Priv=false
- **Privação:** Apt=true, Has=false, Priv=true
- **Mera carência:** Apt=false, Has=false, Priv=false (sem contradição)

### 5. Relativa (violação de correlatos)

Termos que se definem mutuamente: pai/filho, gerente/subordinado, dobro/metade. Quatro tipos de violação:

| Tipo | Violação | Exemplo |
|------|---------|---------|
| 1 | Assimetria de recíproca | `Controls(a,b) ∧ ¬Controlled(b,a)` |
| 2 | Existência sem correlato | Gerente sem subordinado definido |
| 3 | Destruição unilateral | Deletar cargo sem invalidar ocupante |
| 4 | Graus inconsistentes | A depende muito de B, B não depende de A |

```gherkin
@rel-gerente-subordinado-controla-controlado_por
Cenário: João é gerente de Maria
  Então o gerente controla o subordinado Maria

@rel-gerente-subordinado-controla-controlado_por
Cenário: Maria não é subordinada de ninguém
  Então a subordinado Maria não é controlado_por nenhum gerente
```

**Verificação:** Z3 FOL (reciprocidade e simultaneidade) + NetworkX (grafos dirigidos para assimetria de graus).

### 6. Autonegação

A proposição destrói os fundamentos que ela própria pressupõe. Três formas:

| Forma | Estrutura | Exemplo |
|-------|----------|---------|
| Performativa | `Afirma(S, P) ∧ P → ¬Exists(S)` | Hume nega o "eu" que escreve |
| Epistêmica | `Afirma(S, P) ∧ P → ¬Knowable(P)` | Kant nega a cognoscibilidade |
| Fundacional | `T ∧ T → ¬Valid(Logic)` | Ceticismo nega a verdade |

```gherkin
@presupposes-autenticacao-sessao_ativa
@negates-sessao_ativa
Cenário: Regra que destrói sua própria base
  Dado que o sistema de autenticacao está ativo
  Quando o administrador desabilita a sessao_ativa
  Então o sistema verifica a autenticacao do usuário
```

**Verificação:** `presupposes ∩ negates ≠ ∅` (grafo de dependência) + reductio ad absurdum via Z3 (Then contradiz Given).

### 7. Modal

Conflito entre modalidades: necessidade, possibilidade, impossibilidade.

```gherkin
Cenário: Relatório obrigatório
  Então o gerente deve gerar o relatório mensal

Cenário: Relatório impossível
  Então o gerente não pode gerar o relatório mensal
```

**Verificação:** Axiomas modais em Z3:
- `Necessary(P) → ¬Impossible(P)`
- `Impossible(P) → ¬Possible(P)`
- `Necessary(P) → Possible(P)`

### 8. Suplência (*Quaternio Terminorum*)

O mesmo termo muda de significado entre cenários, invalidando o raciocínio como um sofisma dos quatro termos.

```gherkin
Cenário: Usuário autenticado tem acesso
  Dado que o usuario está autenticado
  Então o usuario tem acesso ao dashboard

Cenário: Usuário anônimo não tem acesso
  Dado que o usuario é anônimo
  Então o usuario não tem acesso ao dashboard
```

O termo "usuario" na primeira aceção refere-se a um autenticado; na segunda, a um anônimo. O verificador detecta que o predicado "tem" produz resultados opostos para o mesmo sujeito em cenários com contextos semânticos diferentes.

### 9. Contrassenso Formal (*Widersinn*)

Uma teoria que nega as condições necessárias para a existência de qualquer verdade ou teoria (Husserl). No software: desabilitar o motor de regras e depois depender dele.

```gherkin
Cenário: Desabilitar validação e depois validar
  Quando o administrador desabilita o sistema de validação
  Então o sistema verifica a permissão do usuário
```

**Verificação:** Detecta co-ocorrência de verbo destrutivo + alvo do sistema, cruzada com steps que dependem desse sistema.

### 10. Contradição Performativa

O ato de executar o cenário contradiz o que ele afirma. Paralaxe cognitiva: o eixo da construção teórica se desloca do eixo da experiência.

```gherkin
Cenário: Testar funcionalidade com sistema offline
  Dado que o sistema está offline
  E o sistema está indisponível
  Quando o usuario acessa o dashboard
  Então o usuario navega até o relatório financeiro
```

O cenário afirma indisponibilidade mas executa ações que requerem disponibilidade.

## Anotações Ontológicas via Tags

Para verificações que requerem informação além do texto dos steps (privativa, relativa, autonegação), o sistema aceita tags Gherkin com formato `@prefixo-arg1-arg2-...`:

| Tag | Tipo | Significado |
|-----|------|------------|
| `@apt-sujeito-propriedade` | Privativa | Declara que o sujeito é apto a possuir a propriedade |
| `@rel-roleA-roleB-relação-inversa` | Relativa | Declara par correlativo com relação e inversa |
| `@presupposes-cond1-cond2` | Autonegação | O cenário pressupõe estas condições |
| `@negates-cond1` | Autonegação | O cenário nega/destrói estas condições |

## Consciência de Contexto

O verificador distingue **ramos condicionais legítimos** de **contradições reais**. Cenários com precondições (Given/When) diferentes representam ramos do comportamento, não contradições:

```gherkin
# Isto NÃO é contradição -- contextos diferentes
Cenário: Login bem-sucedido
  Quando o usuario insere credenciais válidas
  Então o usuario tem acesso ao sistema

Cenário: Login falho
  Quando o usuario insere credenciais inválidas
  Então o usuario não tem acesso ao sistema
```

O sistema compara a assinatura de contexto (todos os steps Given + When) entre cenários antes de reportar contradições dos tipos 1 (contraditória) e afins.

## Integração CI/CD

O exit code `1` para contradições críticas permite integração direta:

```yaml
# GitHub Actions
- name: Verificar contradições lógicas
  run: python verify.py features/ --summary
```

```bash
# Script de CI
python verify.py features/ --json > contradictions.json
if [ $? -ne 0 ]; then
  echo "Especificações contêm contradições lógicas!"
  exit 1
fi
```

## Estrutura do Projeto

```
cucumber/
 ├── verify.py                          # CLI
├── requirements.txt
├── features/                          # Exemplos .feature
│   ├── 01_contraditorias.feature
│   ├── 02_contrarias.feature
│   ├── 03_privativas.feature
│   ├── 04_relativas.feature
│   ├── 05_autonegacao.feature
│   ├── 06_modais.feature
│   ├── 07_suplencia.feature
│   ├── 08_contrassenso.feature
│   └── 09_consistente.feature         # controle (sem contradições)
└── gherkin_verifier/
    ├── domain.py                      # Proposition, Quantifier, Modality
    ├── parser.py                      # Parsing via gherkin-official
    ├── extractor.py                   # Extração de proposições dos steps
    ├── engine.py                      # Orquestrador + relatório
    └── contradictions/
        ├── contradictory.py           # Tipo 1: SAT
        ├── contrary.py                # Tipo 2: universais
        ├── subcontrary.py             # Tipo 3: particulares
        ├── privative.py               # Tipo 4: Z3 FOL
        ├── relative.py                # Tipo 5: Z3 + grafos
        ├── self_negation.py           # Tipo 6: grafo + reductio
        ├── modal.py                   # Tipo 7: axiomas modais
        ├── suppositio.py              # Tipo 8: equivocidade
    └── countersense.py            # Tipos 9-10: Widersinn + performativa
```

## Abordagem simbólica

- Antes de acionar o solver SMT (Z3), o pipeline aplica uma etapa de análise simbólica usando SymPy para normalizar e simplificar as proposições extraídas dos cenários (CNF/DNF, simplificações lógicas).
- Essa etapa de pré-verificação identifica tautologias, contradições simples (A ∧ ¬A) e padrões de equivalência antes de consultar o SMT, reduzindo custos computacionais.
- O módulo simbólico fica em `gherkin_verifier/symbolic.py` e é usado como camada intermediária entre a extração de proposições e a verificação SMT.
- Casos de Lógica de Primeira Ordem com quantificadores (privativas, relativas, autonegações) continuam sob a responsabilidade do SMT (Z3); a camada simbólica lida apenas com proposições proposicionais e normalização.
- O relatório pode incluir fórmulas simbólicas legíveis para auditoria, quando apropriado, facilitando debugging e entendimento das regras verificadas.

## Limitações

- **Extração de proposições** depende de pattern-matching em PT-BR e EN. Frases com estrutura sintática incomum podem não ser parseadas. O modo `--verbose` mostra as proposições extraídas para diagnóstico.
- **Contradições privativas e relativas** requerem anotação explícita via tags (`@apt-...`, `@rel-...`) pois a aptidão ontológica e a estrutura correlativa não são deriváveis apenas do texto.
- **Lógica temporal** (LTL/CTL) para irreversibilidade aristotélica e contradições de destruição unilateral no tempo não está implementada nesta versão.
- A lógica formal opera com **esquemas limitados** de relações entre sentenças. Como adverte Aristóteles, a realidade é ilimitada e certas tensões ontológicas não se resolvem por coerência linear -- o verificador detecta contradições formais, não julga se uma tensão é filosoficamente legítima.

## Referências Conceituais

- **Aristóteles** -- *Organon* (Categorias, Da Interpretação, Analíticos): princípio da não-contradição, quadrado lógico, oposições entre conceitos
- **Edmund Husserl** -- *Prolegômenos à Lógica Pura*: contrassenso formal (*Widersinn*), teorias que se suprimem a si mesmas
- **Mário Ferreira dos Santos** -- *Lógica e Dialética*: oposição privativa, suplência, dialética concreta
- **Olavo de Carvalho** -- paralaxe cognitiva, contradição existencial, níveis de contradição (lógica, ontológica, espiritual)

## Nota de PR
Este branch integra a camada de checagem simbólica via SymPy.

