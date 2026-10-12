/*
 * Lista de palavras do treino · Word list for the practice.
 * Definições curtas escritas para este site (não vêm de nenhum teste).
 * Short definitions written for this site (not taken from any test).
 * Cada item · Each item: { palavra, definicao, raridade, en }
 * raridade · rarity: 1 = palavra comum · common, 2 = intermediária · intermediate, 3 = rara · rare
 */
(function (raiz) {
  var PALAVRAS = [
    { palavra: "janela", definicao: "Abertura na parede que deixa entrar luz e ar.", raridade: 1, en: "window" },
    { palavra: "ponte", definicao: "Construção que liga dois lados de um rio, vale ou estrada.", raridade: 1, en: "bridge" },
    { palavra: "relógio", definicao: "Instrumento que mede e mostra as horas.", raridade: 1, en: "clock, watch" },
    { palavra: "colher", definicao: "Talher com uma ponta côncava, usado para levar comida ou líquido à boca.", raridade: 1, en: "spoon" },
    { palavra: "ilha", definicao: "Porção de terra cercada de água por todos os lados.", raridade: 1, en: "island" },
    { palavra: "viagem", definicao: "Deslocamento de um lugar para outro, em geral distante.", raridade: 1, en: "trip, journey" },
    { palavra: "coragem", definicao: "Força para enfrentar o medo, o perigo ou a dificuldade.", raridade: 1, en: "courage" },
    { palavra: "mochila", definicao: "Bolsa que se carrega nas costas, presa pelos ombros.", raridade: 1, en: "backpack" },
    { palavra: "farol", definicao: "Torre com uma luz forte que orienta os navios à noite.", raridade: 1, en: "lighthouse" },
    { palavra: "semente", definicao: "Parte da planta que, plantada, dá origem a uma planta nova.", raridade: 1, en: "seed" },
    { palavra: "generoso", definicao: "Que gosta de dar e de dividir o que tem com os outros.", raridade: 2, en: "generous" },
    { palavra: "saudade", definicao: "Sentimento de falta de alguém, de um lugar ou de um tempo.", raridade: 2, en: "longing, missing someone" },
    { palavra: "hesitar", definicao: "Ficar em dúvida antes de agir ou de decidir.", raridade: 2, en: "to hesitate" },
    { palavra: "frágil", definicao: "Que se quebra ou se machuca com facilidade.", raridade: 2, en: "fragile" },
    { palavra: "rotina", definicao: "Sequência de atividades que se repete no dia a dia.", raridade: 2, en: "routine" },
    { palavra: "prudente", definicao: "Que age com cuidado para evitar riscos e erros.", raridade: 2, en: "prudent, careful" },
    { palavra: "efêmero", definicao: "Que dura pouco tempo; passageiro.", raridade: 2, en: "ephemeral" },
    { palavra: "ambíguo", definicao: "Que pode ser entendido de mais de um jeito.", raridade: 2, en: "ambiguous" },
    { palavra: "eloquente", definicao: "Que se expressa com clareza e com força para convencer.", raridade: 2, en: "eloquent" },
    { palavra: "metáfora", definicao: "Uso de uma palavra em sentido figurado, por uma comparação que não é dita.", raridade: 2, en: "metaphor" },
    { palavra: "nostalgia", definicao: "Saudade de um tempo que já passou.", raridade: 2, en: "nostalgia" },
    { palavra: "vestígio", definicao: "Sinal ou marca que ficou de algo que já passou.", raridade: 2, en: "trace, vestige" },
    { palavra: "empatia", definicao: "Capacidade de se colocar no lugar do outro e entender o que ele sente.", raridade: 2, en: "empathy" },
    { palavra: "inexorável", definicao: "Que não pode ser impedido nem evitado.", raridade: 3, en: "inexorable" },
    { palavra: "prolixo", definicao: "Que usa palavras demais para dizer pouca coisa.", raridade: 3, en: "verbose, long-winded" },
    { palavra: "tácito", definicao: "Que fica subentendido, sem precisar ser dito.", raridade: 3, en: "tacit, implied" },
    { palavra: "idiossincrasia", definicao: "Jeito próprio e particular de uma pessoa agir ou reagir.", raridade: 3, en: "idiosyncrasy" },
    { palavra: "perspicaz", definicao: "Que percebe as coisas com rapidez e clareza.", raridade: 3, en: "perceptive, shrewd" },
    { palavra: "dissimular", definicao: "Esconder o que sente ou pensa; disfarçar.", raridade: 3, en: "to dissemble, to disguise" },
    { palavra: "sub-reptício", definicao: "Feito às escondidas, de forma disfarçada.", raridade: 3, en: "surreptitious" },
    { palavra: "exacerbar", definicao: "Tornar mais intenso ou mais grave.", raridade: 3, en: "to exacerbate" },
    { palavra: "ubíquo", definicao: "Que está, ou parece estar, em toda parte.", raridade: 3, en: "ubiquitous" },
    { palavra: "incólume", definicao: "Que saiu de uma situação sem nenhum dano; ileso.", raridade: 3, en: "unharmed, unscathed" },
    { palavra: "obsequioso", definicao: "Que se esforça demais para agradar os outros.", raridade: 3, en: "obsequious" },
    { palavra: "lacônico", definicao: "Que fala ou escreve usando pouquíssimas palavras.", raridade: 3, en: "laconic" },
    { palavra: "procrastinar", definicao: "Deixar para depois o que deveria ser feito agora.", raridade: 3, en: "to procrastinate" },
    { palavra: "paradigma", definicao: "Modelo ou padrão que serve de referência.", raridade: 3, en: "paradigm" },
    { palavra: "anacronismo", definicao: "Algo que aparece fora da sua época.", raridade: 3, en: "anachronism" },
    { palavra: "quimera", definicao: "Sonho ou ideia impossível de realizar; fantasia.", raridade: 3, en: "chimera, pipe dream" }
  ];
  if (typeof module !== "undefined" && module.exports) module.exports = PALAVRAS;
  else raiz.WAIS_PALAVRAS = PALAVRAS;
})(typeof self !== "undefined" ? self : this);
