# WAIS Vocabulário: Expansão e Prática de Vocabulário

**WAIS Vocabulário** é uma aplicação web educacional inspirada nos subtestes de vocabulário frequentemente encontrados em avaliações de inteligência, como a Escala Wechsler de Inteligência para Adultos (WAIS). O projeto visa transcender a simples avaliação, oferecendo uma plataforma interativa e adaptativa onde os usuários podem ativamente **praticar, testar e expandir seu vocabulário**.

A intenção é criar uma ferramenta que não apenas auxilie no aprendizado de novas palavras, mas que também reforce o conhecimento existente através de exercícios variados e feedback, promovendo uma compreensão mais profunda e um uso mais eficaz da linguagem.

## Sobre o Projeto (Visão Geral Técnica)

Este projeto é uma aplicação web educacional desenvolvida em Python com FastAPI. Ele foi reestruturado para obter informações sobre palavras dinamicamente de APIs externas e inferir sua complexidade em tempo real, em vez de depender de um banco de dados local de palavras. A arquitetura agora incorpora um sistema adaptativo para sugerir exercícios com base no perfil cognitivo e progresso do usuário.

## Arquitetura Lógica Principal (Sistema Adaptativo)

O sistema adaptativo é baseado em três componentes principais:

1.  **Vetor de Estado Cognitivo (θ_user):** Representa o perfil de aprendizagem do usuário, incluindo `vocabular_ability`, `processing_speed`, `working_memory_load`, `confidence_level`, `fatigue_factor` e `domain_expertise` (granular por domínio).
2.  **Taxonomia de Complexidade de Exercícios (Matriz C):** Define a dificuldade de cada tipo de exercício em combinação com a complexidade intrínseca da palavra. Esta é uma função $C(\text{exercise\_type}, \text{word\_complexity})$ implementada no `ExerciseSelectionService`.
3.  **Algoritmo de Seleção do Próximo Exercício:** Utiliza um modelo de Machine Learning leve (atualmente implementado dentro de `ExerciseSelectionService` e `ScoringService`) para selecionar o próximo exercício ideal. O algoritmo avalia cada candidato (combinação palavra-tipo de exercício) com base em múltiplos scores:
    *   **Learning Efficiency (LE):** Probabilidade de aprendizado efetivo, considerando a Zona de Desenvolvimento Proximal (desafio ideal), o espaçamento da repetição e o potencial de transferência.
    *   **Engagement Factor (EF):** Potencial de manter o usuário engajado, considerando a novidade, interesse pessoal (domínio de expertise) e a proximidade de atingir a maestria.
    *   **Frustration Risk (FR):** Risco de o exercício ser excessivamente difícil ou desmotivador, considerando falhas recentes, saltos de complexidade e fadiga.

O algoritmo combina estes scores (LE + EF - FR) e utiliza uma estratégia epsilon-greedy para selecionar o próximo exercício, balanceando explotação (melhor score) e exploração (exercícios aleatórios para descoberta).

## Funcionalidades Principais (Atualizado)

*   **Sistema de Aprendizagem Adaptativo:** Seleção dinâmica de palavras e tipos de exercício com base no estado cognitivo e progresso do usuário.
*   **Gerenciamento de Estado Cognitivo do Usuário:** Rastreamento e atualização contínua de métricas cognitivas (habilidade vocabular, velocidade de processamento, etc.).
*   **Busca Detalhada e Análise de Palavras em Tempo Real:**
    *   Obtém definição (via API Dicionario Aberto), uma imagem ilustrativa (via API Pixabay) e a pronúncia em áudio (gerada com gTTS e servida estaticamente) para qualquer palavra pesquisada.
    *   **Análise de Complexidade Avançada:** Utiliza o `WordComplexityAnalyzer` para inferir a complexidade da palavra com base em múltiplas métricas psicolinguísticas (comprimento lexical, complexidade silábica, densidade morfológica, abstração semântica, frequência, familiaridade e complexidade da definição), fornecendo um score e um rótulo de dificuldade (ex: "fácil", "média", "difícil").
*   **API Backend Robusta com FastAPI:**
    *   Construída com FastAPI, utilizando Pydantic para validação de dados.
    *   SQLAlchemy para interações com um banco de dados SQLite (focado em usuários e progresso).
    *   Serviços de API externos (dicionário, imagem) integrados com chamadas HTTP assíncronas (`httpx`).
    *   Serviço de TTS (`gTTS`) adaptado para execução assíncrona em thread separada.
*   **Gerenciamento de Usuários e Progresso:**
    *   Endpoints CRUD para criar, ler, atualizar e deletar usuários.
    *   Rastreamento do progresso do usuário com palavras específicas (identificadas por `word_text`).
*   **Geração Dinâmica de Dados de Exercícios:** Endpoints para obter dados estruturados para diferentes tipos de exercícios (Múltipla Escolha, Múltipla Escolha com Imagem, Definir Palavra, Completar Frase) com base nas informações da palavra.
*   **Configuração Centralizada:**
    *   O arquivo `backend/app/app_config.py` gerencia a criação da instância FastAPI, inicialização de serviços e configuração de roteadores.
*   **Interface Simples (Exemplo):** Uma página HTML básica (`index.html`) servida via Jinja2 demonstra a funcionalidade de busca de palavras.
*   **Gerenciamento de Ambiente:** Utiliza ambiente virtual Python e um arquivo `.env` para chaves de API.

## Estrutura do Projeto (Atualizado)

```
Palavras_project/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # Ponto de entrada principal, monta a app de app_config
│   │   ├── app_config.py       # Criação e configuração da instância FastAPI e serviços
│   │   ├── models.py           # Modelos SQLAlchemy (User, UserProgress, MasterWord, UserCognitiveState)
│   │   ├── schemas.py          # Schemas Pydantic (incluindo ExerciseCandidate)
│   │   ├── crud.py             # Funções CRUD (User, UserProgress, MasterWord, UserCognitiveState)
│   │   ├── database.py         # Configuração do SQLAlchemy
│   │   ├── dependencies.py     # Funções de dependência (DB session, get_current_user)
│   │   ├── core/
│   │   │   └── security.py     # Hashing de senha, JWT
│   │   ├── services/
│   │   │   ├── dictionary_api.py # Integração assíncrona com API de dicionário
│   │   │   ├── image_api.py      # Integração assíncrona com API de imagens
│   │   │   ├── tts_service.py    # Serviço de Text-to-Speech (gTTS adaptado)
│   │   │   ├── word_complexity_analyzer.py # Analisador de complexidade de palavras
│   │   │   ├── exercise_selection_service.py # Serviço principal de seleção de exercícios adaptativos
│   │   │   ├── scoring_service.py      # Serviço para calcular scores de exercícios (LE, EF, FR)
│   │   │   └── exercise_data_service.py  # Serviço para gerar dados estruturados para exercícios
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── progress.py # Pode ser renomeado/ajustado
│   │   │   ├── admin.py
│   │   │   ├── exercises.py      # Endpoints para sugestão e submissão de exercícios, e obtenção de dados
│   │   │   └── words.py          # Endpoints para informações de palavras (word_info)
│   │   ├── static/
│   │   │   ├── audio/              # Áudios gerados
│   │   │   ├── css/
│   │   │   └── js/
│   │   ├── templates/
│   │   │   ├── index.html
│   │   │   └── partials/
│   │   │       ├── _mcq_image_exercise_partial.html
│   │   │       ├── _define_word_exercise_partial.html
│   │   │       └── _complete_sentence_exercise_partial.html
│   │   ├── .env                    # Variáveis de ambiente (NÃO VERSIONADO)
│   │   └── app_data.db             # Banco de dados SQLite (NÃO VERSIONADO)
│   ├── frontend/                   # (Reservado para futuro frontend SPA)
│   │   └── src/
│   ├── venv/                       # Ambiente virtual (NÃO VERSIONADO)
│   ├── .gitignore
│   └── README.md                   # Este arquivo
└── requirements.txt            # Dependências Python
```

## Configuração do Ambiente

1.  **Clone o Repositório (se aplicável)**
    ```bash
    # git clone <url_do_repositorio>
    # cd Palavras_project
    ```

2.  **Crie e Ative o Ambiente Virtual Python**
    ```bash
    python -m venv venv
    ```
    *   No Windows (PowerShell): `.\venv\Scripts\Activate.ps1`
    *   No macOS/Linux: `source venv/bin/activate`

3.  **Instale as Dependências**
    ```bash
    pip install -r requirements.txt
    ```
    As dependências principais incluem: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `httpx`, `gTTS`, `python-dotenv`, `jinja2`, `python-multipart`, `passlib[bcrypt]`, `nltk`, `textstat`, `pydantic`.

4.  **Baixe os Recursos do NLTK**
    Após instalar as dependências, execute um script Python ou um interpretador Python e baixe os pacotes necessários do NLTK:
    ```python
    import nltk
    nltk.download('punkt')
    nltk.download('wordnet')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('cmudict') # Usado pelo WordComplexityAnalyzer
    # nltk.download('floresta') # Exemplo de corpus em português, se necessário para expansões futuras
    # nltk.download('mac_morpho') # Exemplo de etiquetador morfológico em português
    ```

5.  **Configure as Variáveis de Ambiente**
    *   Crie um arquivo chamado `.env` dentro da pasta `Palavras_project/backend/`.
    *   Adicione suas chaves de API:
        ```env
        PIXABAY_API_KEY=SUA_CHAVE_DA_API_PIXABAY_AQUI
        # DICIONARIO_ABERTO_API_TOKEN=SEU_TOKEN_AQUI (se aplicável no futuro)
        ```

## Como Executar a Aplicação

1.  **Ative o Ambiente Virtual** (se ainda não estiver ativo).

2.  **A partir da Raiz do Projeto (`Palavras_project/`)**, inicie o servidor FastAPI:
    ```bash
    uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    O servidor estará rodando em `http://127.0.0.1:8000` (ou no IP da sua máquina na rede local).

3.  **Acesse a Aplicação/API**:
    *   **Interface Web Principal (Exemplo)**: `http://127.0.0.1:8000/app`
    *   **Documentação Interativa da API (Swagger UI)**: `http://127.0.0.1:8000/docs`
    *   **Endpoint Principal de Informações da Palavra**: `GET http://127.0.0.1:8000/api/v1/word_info/{word_text}`

## Endpoints da API Principais (Prefixo `/api/v1`)

*   **Informações da Palavra (`/api/v1/words`):**
    *   `GET /word_info/{word_text}`: Retorna dados detalhados de uma palavra, incluindo definição, imagem, áudio, score de complexidade inferido e métricas detalhadas.
*   **Autenticação (`/api/v1/auth`):**
    *   `POST /token`: Gera um token JWT para autenticação.
*   **Usuários (`/api/v1/users`):**
    *   `POST /`: Cria um novo usuário.
    *   `GET /me`: Obtém informações do usuário autenticado.
    *   `GET /{user_id}`: Obtém informações de um usuário específico (requer permissões adequadas).
*   **Progresso do Usuário (`/api/v1/progress`):**
    *   `POST /users/{user_id}/words/{word_text}`: Registra ou atualiza o progresso de um usuário para uma palavra específica e tipo de exercício.
    *   `GET /users/{user_id}/words/{word_text}`: Obtém o progresso de um usuário para uma palavra específica e tipo de exercício.
*   **Exercícios (`/api/v1/exercises`):**
    *   `GET /next_exercise/`: Sugere o próximo exercício (palavra e tipo) para o usuário autenticado.
    *   `POST /submit_exercise_result/`: Submete o resultado de um exercício completado para atualizar o estado cognitivo e progresso.
    *   `GET /multiple_choice/{word_text}`: Obtém dados para um exercício de múltipla escolha de definição.
    *   `GET /multiple_choice_image/{word_text}`: Obtém dados para um exercício de múltipla escolha de imagem.
    *   `GET /define_word/{word_text}`: Obtém dados para um exercício de definir palavra.
    *   `GET /complete_sentence/{word_text}`: Obtém dados para um exercício de completar frase.
*   **Endpoints de Administração:** Podem existir endpoints sob `/api/v1/admin` para gerenciamento de MasterWord, etc.

## Análise de Complexidade de Palavras

O `WordComplexityAnalyzer` (localizado em `backend/app/services/word_complexity_analyzer.py`) é um componente chave que estima a dificuldade de uma palavra. Ele considera:
*   Comprimento da palavra.
*   Número de sílabas (usando `pyphen` e `cmudict` como fallback).
*   Densidade morfológica (análise de afixos, se implementado).
*   Abstração semântica (contagem de synsets no WordNet, como proxy).
*   Frequência da palavra (requer integração com corpus de frequência).
*   Idade de aquisição (requer dados externos).
*   Complexidade da definição (usando métricas de legibilidade como Flesch-Kincaid no texto da definição).

As métricas são combinadas para produzir um score de complexidade e um rótulo (ex: "fácil", "média", "difícil").

## Modelo de Machine Learning (TGL-ML) / Sistema Adaptativo

*   **Localização:** A lógica principal do sistema adaptativo e cálculo de scores está implementada nos serviços `backend/app/services/exercise_selection_service.py` e `backend/app/services/scoring_service.py`.
*   **Estado Atual:** A estrutura básica dos calculadores de score (Learning Efficiency, Engagement Factor, Frustration Risk) e a lógica de seleção (epsilon-greedy, priorização de reforço, inclusão de novas palavras) foram implementadas. A atualização do estado cognitivo do usuário (`UserCognitiveState`) após a submissão de exercícios também foi esboçada.
*   **Potencial Futuro:** Refinamento contínuo dos algoritmos de cálculo de score e seleção, possivelmente integrando modelos de ML mais complexos para predição de retenção ou análise de padrões de erro (como o `error_pattern_analysis` mencionado anteriormente).

## Próximos Passos e Melhorias Potenciais

*   **Refinar e Calibrar Algoritmos:** Aperfeiçoar as fórmulas e pesos dentro do `ScoringService` e `ExerciseSelectionService` com base em dados reais de usuários (quando disponíveis) para melhorar a precisão da sugestão de exercícios e atualização do estado cognitivo.
*   **Melhorar Geração de Dados de Exercícios:** Implementar lógicas mais sofisticadas em `ExerciseDataService` para gerar distratores (MCQ), frases (Completar Frase), etc., possivelmente integrando com corpora ou modelos linguísticos.
*   **Implementar Lógica de Domínio de Expertise:** Desenvolver a funcionalidade completa para associar palavras a domínios de conhecimento e rastrear e atualizar a expertise do usuário por domínio no `UserCognitiveState`.
*   **Desenvolver Lógica de Análise de Padrão de Erro:** Implementar a análise de padrões de erro do usuário e integrar o `error_pattern_risk` no cálculo do Frustration Risk.
*   **Expandir Pool de Palavras Mestras:** Popular o banco de dados `MasterWord` com um vocabulário abrangente, possivelmente categorizado por complexidade e domínio.
*   **Criar Frontend Interativo:** Desenvolver uma Single Page Application (SPA) moderna no diretório `frontend/` para consumir os endpoints da API e fornecer a interface do usuário.
*   **Adicionar Testes:** Escrever testes unitários e de integração para os serviços e endpoints da API para garantir a robustez e facilitar futuras modificações.
*   **Implementar Autenticação Completa:** Finalizar a lógica de autenticação de usuário no `dependencies.py` e outros módulos relevantes, incluindo registro, login, logout e proteção de endpoints.
*   **Configurar Logging e Monitoramento:** Melhorar o sistema de logging para rastrear a atividade do sistema adaptativo e identificar possíveis problemas ou áreas para otimização.
*   **Considerar Cache:** Implementar um sistema de cache (ex: Redis) para resultados de API externas ou análises de complexidade frequentes para melhorar a performance.
*   **Documentação Detalhada:** Expandir a documentação técnica dos serviços e endpoints.
*   **Migrações de Banco de Dados:** Configurar e utilizar uma ferramenta como Alembic para gerenciar futuras alterações no esquema do banco de dados.
