"""
Gherkin Formal Verifier — Verificador de Contradições Lógicas em especificações Gherkin.

Detecta 10 tipos de contradições baseados na lógica clássica:
1. Contraditórias (A ∧ ¬A)
2. Contrárias (universais incompatíveis)
3. Subcontrárias (particulares que não podem ser ambas falsas)
4. Privativas (aptidão + carência)
5. Relativas (correlatos assimétricos)
6. Autonegação (proposição destrói seus próprios fundamentos)
7. Modais (necessidade vs possibilidade)
8. Suplência (ambiguidade de termos)
9. Contrassenso formal (regras que negam a lógica)
10. Contradição performativa (ato contradiz conteúdo)
"""
