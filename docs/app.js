/* Interface do treino · Practice UI. Dados ficam em localStorage · Data stays in localStorage. */
(function () {
  "use strict";
  var P = window.WAIS_PALAVRAS, N = window.WaisNucleo;
  var CHAVE = "wais-vocabulario-v1";
  var HABILIDADE_INICIAL = 4.6;
  var $ = function (id) { return document.getElementById(id); };

  var el = {
    palavra: $("palavra"), formEscolha: $("form-escolha"), opcoes: $("opcoes"),
    formEscrita: $("form-escrita"), resposta: $("resposta"), auto: $("autoavaliacao"),
    retorno: $("retorno"), proxima: $("proxima"), recomecar: $("recomecar"),
    nPalavras: $("n-palavras"), nCertas: $("n-certas"), nSeq: $("n-sequencia")
  };

  function novoEstado() {
    return { habilidade: HABILIDADE_INICIAL, progresso: {}, recentes: [], certas: 0, total: 0, sequencia: 0, modo: "MCQ_definition" };
  }
  function carregar() {
    try {
      var s = JSON.parse(localStorage.getItem(CHAVE));
      if (s && typeof s.habilidade === "number" && s.progresso) return s;
    } catch (e) { /* ignora · ignore */ }
    return novoEstado();
  }
  function salvar() { try { localStorage.setItem(CHAVE, JSON.stringify(estado)); } catch (e) { /* modo privado · private mode */ } }

  var estado = carregar();
  var atual = null, inicio = 0, respondida = false;

  function modo() { return document.querySelector('input[name="modo"]:checked').value; }

  function placar() {
    el.nPalavras.textContent = String(Object.keys(estado.progresso).length);
    el.nCertas.textContent = estado.certas + " / " + estado.total;
    el.nSeq.textContent = String(estado.sequencia);
  }

  function animar(no) { no.classList.remove("entrar"); void no.offsetWidth; no.classList.add("entrar"); }

  function proxima(focar) {
    respondida = false;
    // A escolha usa a escala do exercício de múltipla escolha nos dois modos;
    // o modo de escrita pesa mais na atualização da habilidade.
    var c = N.proximaPalavra(P, estado, "MCQ_definition");
    atual = c.item;
    estado.recentes = [atual.palavra].concat(estado.recentes.filter(function (p) { return p !== atual.palavra; })).slice(0, 8);
    salvar();
    el.palavra.textContent = atual.palavra;
    el.palavra.setAttribute("lang", "pt-BR");
    animar(el.palavra);
    el.retorno.innerHTML = "";
    el.proxima.hidden = true;
    var m = modo();
    el.formEscolha.hidden = m !== "MCQ_definition";
    el.formEscrita.hidden = m !== "define_word";
    if (m === "MCQ_definition") montarOpcoes();
    else {
      el.resposta.value = ""; el.resposta.disabled = false;
      el.formEscrita.querySelector('button[type="submit"]').disabled = false;
      el.auto.hidden = true;
    }
    inicio = Date.now();
    if (focar) el.palavra.focus();
  }

  function montarOpcoes() {
    el.opcoes.innerHTML = "";
    N.opcoes(P, atual).forEach(function (o, i) {
      var lab = document.createElement("label");
      lab.className = "opcao";
      var inp = document.createElement("input");
      inp.type = "radio"; inp.name = "opcao"; inp.value = o.palavra; inp.id = "opcao-" + i;
      if (i === 0) inp.required = true;
      var span = document.createElement("span");
      span.textContent = o.definicao;
      lab.appendChild(inp); lab.appendChild(span);
      el.opcoes.appendChild(lab);
    });
    el.formEscolha.querySelector('button[type="submit"]').disabled = false;
  }

  function registrar(pontos, tipo) {
    var acuracia = N.acuraciaDePontos(pontos);
    var prog = estado.progresso[atual.palavra] || { tentativas: 0, acertos: 0 };
    prog.tentativas += 1;
    if (acuracia > 0.99) prog.acertos += 1;
    prog.ultimaVez = Date.now();
    estado.progresso[atual.palavra] = prog;
    estado.total += 1;
    if (acuracia > 0.99) { estado.certas += 1; estado.sequencia += 1; } else estado.sequencia = 0;
    estado.habilidade = N.atualizarHabilidade(estado.habilidade, acuracia, tipo,
      N.complexidade(atual.palavra, atual.definicao, atual.raridade));
    salvar(); placar();
  }

  function paragrafo(texto, classe, lang) {
    var p = document.createElement("p");
    if (classe) p.className = classe;
    if (lang) p.setAttribute("lang", lang);
    p.textContent = texto;
    return p;
  }

  function mostrarRetorno(partes) {
    el.retorno.innerHTML = "";
    partes.forEach(function (p) { el.retorno.appendChild(p); });
    el.proxima.hidden = false;
    el.proxima.focus();
  }

  el.formEscolha.addEventListener("submit", function (ev) {
    ev.preventDefault();
    if (respondida) return;
    var marcada = el.opcoes.querySelector("input:checked");
    if (!marcada) return;
    respondida = true;
    var certa = marcada.value === atual.palavra;
    el.opcoes.querySelectorAll(".opcao").forEach(function (lab) {
      var inp = lab.querySelector("input");
      inp.disabled = true;
      if (inp.value === atual.palavra) lab.classList.add("certa");
      else if (inp === marcada) lab.classList.add("errada");
    });
    el.formEscolha.querySelector('button[type="submit"]').disabled = true;
    registrar(certa ? 2 : 0, "MCQ_definition");
    mostrarRetorno([
      paragrafo(certa ? "Certa! · Correct! (2 pts)" : "Não foi dessa vez · Not this time (0 pts)", "resultado " + (certa ? "certa" : "errada")),
      paragrafo(atual.palavra + ": " + atual.definicao, null, "pt-BR"),
      paragrafo("In English: " + atual.en, "ingles", "en")
    ]);
  });

  el.formEscrita.addEventListener("submit", function (ev) {
    ev.preventDefault();
    if (respondida) return;
    respondida = true;
    el.resposta.disabled = true;
    el.formEscrita.querySelector('button[type="submit"]').disabled = true;
    el.retorno.innerHTML = "";
    var resp = el.resposta.value.trim();
    el.retorno.appendChild(paragrafo("Sua resposta · Your answer: " + (resp || "(em branco · blank)")));
    el.retorno.appendChild(paragrafo("Definição · Definition — " + atual.palavra + ": " + atual.definicao, "resultado"));
    el.retorno.appendChild(paragrafo("In English: " + atual.en, "ingles", "en"));
    el.auto.hidden = false;
    el.auto.querySelector("button").focus();
  });

  el.auto.addEventListener("click", function (ev) {
    var b = ev.target.closest("button[data-pontos]");
    if (!b || el.auto.hidden) return;
    var pts = Number(b.getAttribute("data-pontos"));
    el.auto.hidden = true;
    registrar(pts, "define_word");
    var msg = pts === 2 ? "Boa! · Nice! (2 pts)" : pts === 1 ? "Quase lá · Almost there (1 pt)" : "Essa volta depois · This one will come back (0 pts)";
    el.retorno.appendChild(paragrafo(msg, "resultado " + (pts === 2 ? "certa" : pts === 0 ? "errada" : "")));
    el.proxima.hidden = false;
    el.proxima.focus();
  });

  el.proxima.addEventListener("click", function () { proxima(true); });

  document.querySelectorAll('input[name="modo"]').forEach(function (r) {
    if (r.value === estado.modo) r.checked = true;
    r.addEventListener("change", function () { estado.modo = modo(); salvar(); proxima(false); });
  });

  el.recomecar.addEventListener("click", function () {
    if (!window.confirm("Apagar o progresso salvo neste navegador? · Erase the progress saved in this browser?")) return;
    var m = estado.modo;
    estado = novoEstado(); estado.modo = m; salvar(); placar(); proxima(true);
  });

  placar();
  proxima(false);
})();
