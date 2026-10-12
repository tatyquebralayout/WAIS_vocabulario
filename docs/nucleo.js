/*
 * Núcleo adaptativo do treino, portado do backend em Python para rodar no navegador.
 * Adaptive core, ported from the Python backend so it runs in the browser.
 *
 * Origem · Source:
 *  - complexidade da palavra  → backend/app/services/word_complexity_analyzer.py
 *  - dificuldade do exercício → matriz C em backend/app/services/exercise_selection_service.py
 *  - Learning Efficiency (ZDP) → backend/app/services/scoring_service.py
 *  - seleção epsilon-greedy e atualização da habilidade → exercise_selection_service.py
 */
(function (raiz) {
  "use strict";

  var PESOS_COMPLEXIDADE = { lexical: 0.20, syllabic: 0.15, morphological: 0.25, semantic: 0.25, definition: 0.15 };
  var PREFIXOS = ["pre", "anti", "super", "inter", "trans", "contra", "re", "des", "in", "im"];
  var SUFIXOS = ["ção", "ismo", "ista", "mente", "dade", "ável", "ível", "oso", "izar", "ecer"];
  var ABSTRATAS = ["conceito", "ideia", "sentimento", "qualidade", "estado", "processo", "sistema",
    "propriedade", "característica", "princípio", "teoria", "emoção", "relação"];
  var CONCRETAS = ["objeto", "coisa", "lugar", "pessoa", "animal", "parte", "ferramenta", "comida", "corpo"];

  // Dificuldade base de cada tipo de exercício (matriz C) · Base difficulty per exercise type.
  var DIFICULDADE_BASE = { MCQ_definition: 4.0, define_word: 8.0 };
  // Impacto de cada tipo na habilidade · Impact of each type on ability.
  var IMPACTO_TIPO = { MCQ_definition: 0.15, define_word: 0.25 };
  var EPSILON = 0.1;
  var PESOS_COMBINACAO = { learning_efficiency: 0.4, engagement_factor: 0.4, frustration_risk: 0.2 };

  function limitar(v, min, max) { return Math.min(max, Math.max(min, v)); }

  function lexical(p) {
    var n = Array.from(p).length;
    if (n === 0) return 0;
    if (n <= 3) return 1; if (n <= 5) return 3; if (n <= 7) return 5;
    if (n <= 9) return 7; if (n <= 12) return 8.5; return 10;
  }

  function contarSilabas(p) {
    var m = String(p).toLowerCase().match(/[aeiouáéíóúâêôãõàü]+/g);
    return m ? m.length : 0;
  }

  function silabica(p) {
    if (!p) return 0;
    var s = contarSilabas(p) || Math.max(1, Math.floor(p.length / 3));
    if (s <= 1) return 1; if (s === 2) return 3; if (s === 3) return 5;
    if (s === 4) return 7; if (s === 5) return 8.5; return 10;
  }

  function morfologica(p) {
    if (!p) return 0;
    var w = p.toLowerCase(), n = 0;
    if (PREFIXOS.some(function (x) { return w.indexOf(x) === 0; })) n++;
    if (SUFIXOS.some(function (x) { return w.slice(-x.length) === x; })) n++;
    return n === 0 ? 1 : n === 1 ? 5 : 9;
  }

  function semantica(p, def) {
    if (!p && !def) return 3;
    var w = (p || "").toLowerCase(), d = (def || "").toLowerCase(), s = 5;
    if (ABSTRATAS.some(function (m) { return w.indexOf(m) >= 0; })) s += 2.5;
    else if (CONCRETAS.some(function (m) { return w.indexOf(m) >= 0; })) s -= 2.5;
    if (d) {
      var a = ABSTRATAS.filter(function (m) { return d.indexOf(m) >= 0; }).length;
      var c = CONCRETAS.filter(function (m) { return d.indexOf(m) >= 0; }).length;
      if (a > c) s += (a - c) * 1.5; else if (c > a) s -= (c - a) * 1.5;
    }
    return limitar(s, 0, 10);
  }

  // Fallback por tamanho da definição (o mesmo do Python quando o Flesch não está disponível).
  function definicao(def) {
    if (!def) return 3;
    var n = def.length;
    if (n < 50) return 1.5; if (n < 100) return 3; if (n < 150) return 5; if (n < 250) return 7; return 9;
  }

  // Frequência de uso: o Python lista essa métrica como "requer corpus de frequência".
  // Aqui ela vem da lista de palavras (raridade 1–3) e pesa 40% do score final.
  // Word frequency: the Python code lists it as "needs a frequency corpus"; here it comes
  // from the word list (rarity 1–3) and weighs 40% of the final score.
  var PESO_RARIDADE = 0.4;
  function raridade(r) { return r === 1 ? 1.5 : r === 2 ? 5 : r === 3 ? 9 : 5; }

  /** Complexidade composta 0–10 · Composite complexity 0–10 */
  function complexidade(p, def, rar) {
    var m = { lexical: lexical(p), syllabic: silabica(p), morphological: morfologica(p),
      semantic: semantica(p, def), definition: definicao(def) };
    var total = 0;
    for (var k in PESOS_COMPLEXIDADE) total += m[k] * PESOS_COMPLEXIDADE[k];
    m.frequency = raridade(rar);
    m.composite = limitar(total * (1 - PESO_RARIDADE) + m.frequency * PESO_RARIDADE, 0, 10);
    return m;
  }

  function rotulo(score) { return score < 3.5 ? "fácil" : score < 7 ? "média" : "difícil"; }

  function dificuldadeExercicio(tipo, compl) {
    var base = DIFICULDADE_BASE.hasOwnProperty(tipo) ? DIFICULDADE_BASE[tipo] : 5.0;
    return base + compl * 0.5;
  }

  /** Desafio na Zona de Desenvolvimento Proximal (scoring_service.py) */
  function desafio(dificuldade, habilidade) {
    var gap = dificuldade - habilidade;
    if (gap >= 0.2 && gap <= 0.8) return 1.0;
    if (gap < 0.2) return Math.min(1, Math.max(0.1, 1.0 - (0.2 - gap) * 1.5));
    return Math.min(1, Math.max(0.3, 1.0 - (gap - 0.8) * 1.0));
  }

  /**
   * Escolhe a próxima palavra · Picks the next word.
   * estado: { habilidade, progresso: { [palavra]: { tentativas, acertos, ultimaVez } }, recentes: [palavra] }
   */
  function proximaPalavra(palavras, estado, tipo, aleatorio) {
    var rnd = aleatorio || Math.random;
    var recentes = estado.recentes || [];
    var pool = palavras.filter(function (p) { return recentes.indexOf(p.palavra) < 0; });
    if (pool.length === 0) pool = palavras.slice();
    var candidatos = pool.map(function (p) {
      var c = complexidade(p.palavra, p.definicao, p.raridade).composite;
      var dif = dificuldadeExercicio(tipo, c);
      var prog = (estado.progresso || {})[p.palavra] || { tentativas: 0, acertos: 0 };
      var le = desafio(dif, estado.habilidade);
      var novidade = prog.tentativas === 0 ? 1 : 1 / (1 + prog.tentativas);
      var precisao = prog.tentativas ? prog.acertos / prog.tentativas : 0;
      var reforco = prog.tentativas && precisao < 1 ? 0.6 : 0; // palavras erradas voltam
      var ef = Math.max(novidade, reforco);
      var falhas = prog.tentativas ? 1 - precisao : 0;
      var fr = falhas * (dif - estado.habilidade > 0.8 ? 1 : 0.4);
      var score = le * PESOS_COMBINACAO.learning_efficiency + ef * PESOS_COMBINACAO.engagement_factor -
        fr * PESOS_COMBINACAO.frustration_risk;
      return { item: p, complexidade: c, dificuldade: dif, score: score };
    });
    if (rnd() < EPSILON) return candidatos[Math.floor(rnd() * candidatos.length)];
    var melhor = candidatos[0];
    candidatos.forEach(function (c) { if (c.score > melhor.score) melhor = c; });
    var empatados = candidatos.filter(function (c) { return Math.abs(c.score - melhor.score) < 1e-9; });
    return empatados[Math.floor(rnd() * empatados.length)];
  }

  /** Atualiza a habilidade estimada (update_user_cognitive_state) · Updates the estimated ability */
  function atualizarHabilidade(habilidade, acuracia, tipo, metricas) {
    var impacto = IMPACTO_TIPO.hasOwnProperty(tipo) ? IMPACTO_TIPO[tipo] : 0.15;
    var ajuste = (acuracia - 0.5) * 0.5;
    if (metricas) {
      if (acuracia > 0.75) ajuste += (metricas.semantic / 10 * 0.4 + metricas.morphological / 10 * 0.3) * 0.1;
      else if (acuracia < 0.25) ajuste += (metricas.syllabic / 10) * -0.05; // proxy de complexidade sintática
    }
    return limitar(habilidade + ajuste * impacto, 0, 10);
  }

  /** Pontuação 0/1/2 em acurácia · 0/1/2 points to accuracy */
  function acuraciaDePontos(pontos) { return pontos >= 2 ? 1 : pontos === 1 ? 0.5 : 0; }

  /** Embaralha (Fisher–Yates) · Shuffle */
  function embaralhar(lista, aleatorio) {
    var rnd = aleatorio || Math.random, a = lista.slice();
    for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(rnd() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }

  /** Três distratores de complexidade parecida · Three distractors of similar complexity */
  function opcoes(palavras, alvo, aleatorio) {
    var c0 = complexidade(alvo.palavra, alvo.definicao, alvo.raridade).composite;
    var outros = palavras.filter(function (p) { return p.palavra !== alvo.palavra; })
      .map(function (p) { return { p: p, d: Math.abs(complexidade(p.palavra, p.definicao, p.raridade).composite - c0) }; })
      .sort(function (a, b) { return a.d - b.d; })
      .slice(0, 8).map(function (x) { return x.p; });
    var distratores = embaralhar(outros, aleatorio).slice(0, 3);
    return embaralhar(distratores.concat([alvo]), aleatorio);
  }

  var api = {
    complexidade: complexidade, rotulo: rotulo, dificuldadeExercicio: dificuldadeExercicio, desafio: desafio,
    proximaPalavra: proximaPalavra, atualizarHabilidade: atualizarHabilidade, acuraciaDePontos: acuraciaDePontos,
    embaralhar: embaralhar, opcoes: opcoes, contarSilabas: contarSilabas
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else raiz.WaisNucleo = api;
})(typeof self !== "undefined" ? self : this);
