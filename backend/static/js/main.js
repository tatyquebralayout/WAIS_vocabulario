// Variáveis de estado
        let currentWordText = null;
        let jwtToken = localStorage.getItem('jwtToken');

        // Elementos da UI
        const statusArea = document.getElementById('status-area');
        const authSection = document.getElementById('auth-section');
        const loginFormContainer = document.getElementById('login-form-container');
        const registerFormContainer = document.getElementById('register-form-container');
        const userLoggedInSection = document.getElementById('user-logged-in-section');
        const loggedInUsernameEl = document.getElementById('logged-in-username');
        const loggedInUsernameAppbarEl = document.getElementById('logged-in-username-appbar');
        const wordInteractionSection = document.getElementById('word-interaction-section');
        const mainAppBar = document.getElementById('main-app-bar');
        const adminSection = document.getElementById('admin-section');
        const progressPageSection = document.getElementById('progress-page-section');
        
        const wordDisplayDiv = document.getElementById('word-display');
        const wordTitleEl = document.getElementById('word-title');
        const wordDefinitionEl = document.getElementById('word-definition');
        const wordImageEl = document.getElementById('word-image');
        const wordAudioEl = document.getElementById('word-audio');
        const playAudioBtn = document.getElementById('play-audio-btn');
        
        const exerciseSubmissionSection = document.getElementById('exercise-submission-section');
        const exerciseWordTextEl = document.getElementById('exercise-word-text');

        // Elementos para Múltipla Escolha
        const practiceDictationSection = document.getElementById('practice-dictation-section');
        const startDictationBtn = document.getElementById('start-dictation-btn');
        const dictationExerciseSection = document.getElementById('dictation-exercise-section');
        const playDictationAudioBtn = document.getElementById('play-dictation-audio-btn');
        const dictationHiddenAudioEl = document.getElementById('dictation-hidden-audio');
        const dictationInputEl = document.getElementById('dictation-input');
        const submitDictationBtn = document.getElementById('submit-dictation-btn');
        const dictationFeedbackEl = document.getElementById('dictation-feedback');

        // Elementos da Página de Progresso
        const showProgressBtn = document.getElementById('show-progress-btn');
        const backToMainViewBtn = document.getElementById('back-to-main-view-btn');
        const totalWordsAttemptedEl = document.getElementById('total-words-attempted');
        const overallAccuracyEl = document.getElementById('overall-accuracy');
        const avgTimePerAttemptEl = document.getElementById('avg-time-per-attempt');
        const progressMessageEl = document.getElementById('progress-message');
        const accuracyTrendChartCtx = document.getElementById('accuracy-trend-chart').getContext('2d');
        const wordsPracticedChartCtx = document.getElementById('words-practiced-chart').getContext('2d');
        let accuracyChartInstance = null;
        let wordsPracticedChartInstance = null;

        // Elementos para Arrastar e Soltar
        const dragDropExerciseSection = document.getElementById('drag-drop-exercise-section');
        const startDragDropExerciseBtn = document.getElementById('start-drag-drop-exercise-btn');
        const dragDropInstructionEl = document.getElementById('drag-drop-instruction');
        const draggableItemsPoolEl = document.getElementById('draggable-items-pool');
        const dropZonesContainerEl = document.getElementById('drop-zones-container');
        const checkDragDropBtn = document.getElementById('check-drag-drop-btn');
        const dragDropFeedbackEl = document.getElementById('drag-drop-feedback');
        let sortableInstances = []; // Para guardar instâncias de SortableJS e destruí-las se necessário
        let currentDragDropExerciseData = null; // Para guardar os dados do exercício atual

        let currentTargetWordId = null; // Para o exercício de múltipla escolha
        let correctAnswerDefinition = ""; // Para feedback MCQ
        let currentWordAudioUrl = ""; // Para o exercício de ditado

        // Container para exercícios dinâmicos
        const dynamicExerciseContainer = document.getElementById('dynamic-exercise-container');

        // Elementos para Múltipla Escolha (Botão de iniciar ainda é global)
        const practiceMcqSection = document.getElementById('practice-mcq-section');
        const startMcqBtn = document.getElementById('start-mcq-btn');
        // Elementos internos do MCQ (mcqQuestionTextEl, etc.) serão buscados dinamicamente

        // Elementos para busca de palavra e autocomplete
        const wordSearchInput = document.getElementById('word-search-input'); // Assumindo que existe
        const wordSearchButton = document.getElementById('word-search-btn'); // Assumindo que existe
        const autocompleteSuggestionsDiv = document.getElementById('autocomplete-suggestions'); // Assumindo que existe

        // Elementos para Aprendizado Guiado
        const getDailyWordBtn = document.getElementById('get-daily-word-btn');
        const learningLevelSelect = document.getElementById('learning-level-select');
        const startLearningBtn = document.getElementById('start-learning-btn');
        const learningWordsDisplay = document.getElementById('learning-words-display');
        const nextLearningWordBtn = document.getElementById('next-learning-word-btn');
        let wordsToLearnCache = [];
        let currentLearningWordIndex = -1;

        // Funções Auxiliares
        function showStatusMessage(message, type = 'info', duration = 5000) {
            statusArea.innerHTML = `<div class="status-message ${type}">${message}</div>`;
            statusArea.classList.remove('hidden');
            setTimeout(() => {
                statusArea.classList.add('hidden');
                statusArea.innerHTML = '';
            }, duration);
        }

        async function fetchWithAuth(url, options = {}) {
            const headers = { ...options.headers };
            if (jwtToken) {
                headers['Authorization'] = `Bearer ${jwtToken}`;
            }
            const response = await fetch(url, { ...options, headers });

            if (response.status === 401) { // Unauthorized
                showStatusMessage('Sessão expirada ou inválida. Por favor, faça login novamente.', 'error');
                logout(); // Limpa o token e atualiza a UI
                return null; // Indica que a requisição falhou devido à autenticação
            }
            return response;
        }
        
        function updateLoginState() {
            if (jwtToken) {
                authSection.classList.add('hidden');
                userLoggedInSection.classList.remove('hidden');
                fetchWithAuth('/users/me')
                    .then(response => {
                        if (response && response.ok) return response.json();
                        throw new Error('Failed to fetch user data');
                    })
                    .then(data => {
                        loggedInUsernameEl.textContent = data.username;
                        loggedInUsernameAppbarEl.textContent = data.username;
                        if (data.is_admin) { 
                            adminSection.classList.remove('hidden');
                        } else {
                            adminSection.classList.add('hidden');
                        }
                    })
                    .catch(error => {
                        console.error("Error fetching user data:", error);
                    });

            } else {
                authSection.classList.remove('hidden');
                userLoggedInSection.classList.add('hidden');
                wordDisplayDiv.classList.add('hidden');
                exerciseSubmissionSection.classList.add('hidden');
                adminSection.classList.add('hidden');
                loggedInUsernameEl.textContent = '';
                loggedInUsernameAppbarEl.textContent = '';
            }
            mainAppBar.classList.remove('hidden');
            wordInteractionSection.classList.remove('hidden');
            progressPageSection.classList.add('hidden');
            hideDynamicExerciseContainer();
            updateUIVisibility();
        }

        function logout() {
            jwtToken = null;
            localStorage.removeItem('jwtToken');
            localStorage.removeItem('userToken');
            localStorage.removeItem('username');
            localStorage.removeItem('isAdmin');
            updateLoginState();
            showStatusMessage('Você foi desconectado.', 'info');
        }

        document.getElementById('show-register-btn').addEventListener('click', () => {
            loginFormContainer.classList.add('hidden');
            registerFormContainer.classList.remove('hidden');
        });
        document.getElementById('show-login-btn').addEventListener('click', () => {
            registerFormContainer.classList.add('hidden');
            loginFormContainer.classList.remove('hidden');
        });

        document.getElementById('login-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;
            
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            try {
                const response = await fetch('/token', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (response.ok) {
                    jwtToken = data.access_token;
                    localStorage.setItem('jwtToken', jwtToken); // Compatibility, consider removing if 'userToken' is primary
                    localStorage.setItem('userToken', jwtToken); // Use this consistently
                    // Fetch user details to get username and isAdmin status
                    const userDetailsResponse = await fetchWithAuth('/users/me/');
                    if (userDetailsResponse && userDetailsResponse.ok) {
                        const userData = await userDetailsResponse.json();
                        localStorage.setItem('username', userData.username);
                        localStorage.setItem('isAdmin', userData.is_admin);
                        showLoggedInState(userData.username, userData.is_admin); // Update UI based on fetched data
                    } else {
                        throw new Error('Failed to fetch user details after login.');
                    }
                    showStatusMessage('Login bem-sucedido!', 'success');
                    document.getElementById('login-form').reset();
                } else {
                    showStatusMessage(data.detail || 'Falha no login.', 'error');
                }
            } catch (error) {
                showStatusMessage('Erro de conexão ou ao buscar dados do usuário: ' + error.message, 'error');
            }
        });

        document.getElementById('register-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('register-username').value;
            const password = document.getElementById('register-password').value;
            try {
                const response = await fetch('/users/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                const data = await response.json();
                if (response.ok) {
                    showStatusMessage('Registro bem-sucedido! Faça o login.', 'success');
                    document.getElementById('register-form').reset();
                    registerFormContainer.classList.add('hidden');
                    loginFormContainer.classList.remove('hidden');
                } else {
                    let errorMessage = 'Falha no registro.';
                    if (data && data.detail) {
                        errorMessage = Array.isArray(data.detail) ? data.detail.map(d => d.msg).join(', ') : data.detail;
                    }
                    showStatusMessage(errorMessage, 'error');
                }
            } catch (error) {
                showStatusMessage('Erro de conexão ao tentar registrar.', 'error');
            }
        });
        
        document.getElementById('logout-btn').addEventListener('click', logout);

        const logoutBtnAppbar = document.getElementById('logout-btn-appbar');
        if (logoutBtnAppbar) {
            logoutBtnAppbar.addEventListener('click', logout);
        }

        const showProgressBtnAppbar = document.getElementById('show-progress-btn-appbar');
        if (showProgressBtnAppbar) {
            showProgressBtnAppbar.addEventListener('click', async () => {
                currentWordText = null;
                hideWordDisplay(); 
                wordInteractionSection.classList.add('hidden');
                hideDynamicExerciseContainer();
                await loadAndDisplayProgressReport();
                progressPageSection.classList.remove('hidden');
                updateUIVisibility();
            });
        }

        function updateUIVisibility() {
            const token = localStorage.getItem('userToken');
            const isAdmin = localStorage.getItem('isAdmin') === 'true';

            if (token) {
                authSection.classList.add('hidden');
                mainAppBar.classList.remove('hidden');
                userLoggedInSection.classList.remove('hidden'); 
                
                if (isAdmin) {
                    adminSection.classList.remove('hidden');
                } else {
                    adminSection.classList.add('hidden');
                }

                if (!progressPageSection.classList.contains('hidden')) {
                    wordInteractionSection.classList.add('hidden');
                    hideDynamicExerciseContainer();
                } else if (currentWordText || document.getElementById('dynamic-exercise-container').innerHTML.trim() !== '') { 
                    wordInteractionSection.classList.add('hidden');
                } else { 
                    wordInteractionSection.classList.remove('hidden');
                    hideDynamicExerciseContainer(); 
                }
            } else { 
                authSection.classList.remove('hidden');
                mainAppBar.classList.add('hidden');
                userLoggedInSection.classList.add('hidden');
                wordInteractionSection.classList.add('hidden');
                progressPageSection.classList.add('hidden');
                adminSection.classList.add('hidden');
                hideDynamicExerciseContainer();
                hideWordDisplay(); 
            }
        }
        
        function showLoggedInState(username, isAdminData) { // Added isAdminData parameter
            if (loggedInUsernameEl) loggedInUsernameEl.textContent = username;
            if (loggedInUsernameAppbarEl) loggedInUsernameAppbarEl.textContent = username;
            updateUIVisibility(); 
        }

        function showLoggedOutState() {
            if (loggedInUsernameEl) loggedInUsernameEl.textContent = '';
            if (loggedInUsernameAppbarEl) loggedInUsernameAppbarEl.textContent = '';
            localStorage.removeItem('userToken');
            localStorage.removeItem('username');
            localStorage.removeItem('isAdmin');
            jwtToken = null; // Clear the global jwtToken variable as well
            currentWordText = null; 
            updateUIVisibility();
        }

        function checkLoginState() {
            const token = localStorage.getItem('userToken');
            const username = localStorage.getItem('username');
            const isAdmin = localStorage.getItem('isAdmin') === 'true';
            if (token && username) {
                jwtToken = token; // Initialize global jwtToken
                showLoggedInState(username, isAdmin);
            } else {
                showLoggedOutState();
            }
        }

        function displayWordData(data, isExercise = false) {
            // 'data' aqui é o objeto WordDataResponse do backend
            // 'isExercise' é um booleano para diferenciar se está mostrando a palavra para estudo ou dentro de um exercício
            
            console.log("Displaying word data:", data);

            currentWordText = data.text; // Atualizar a palavra atual (pode ser a normalizada)
            
            if (!isExercise) { // Só atualiza a UI principal de busca de palavra se não for um contexto de exercício
                wordTitleEl.textContent = data.text.charAt(0).toUpperCase() + data.text.slice(1);
                wordDefinitionEl.textContent = data.definition || "Definição não disponível.";
                
                if (data.image_url) {
                    wordImageEl.src = data.image_url;
                    wordImageEl.classList.remove('hidden');
                    wordImageEl.alt = `Imagem ilustrativa para ${data.text}`;
                } else {
                    wordImageEl.src = '';
                    wordImageEl.classList.add('hidden');
                    wordImageEl.alt = '';
                }

                if (data.audio_url) {
                    wordAudioEl.src = data.audio_url;
                    playAudioBtn.classList.remove('hidden');
                    // Não dar autoplay
                } else {
                    wordAudioEl.src = '';
                    playAudioBtn.classList.add('hidden');
                }
                wordDisplayDiv.classList.remove('hidden'); // Mostra a seção de display da palavra
            }
            
            // Armazena o ID da palavra e a URL do áudio para uso em exercícios, se necessário
            currentTargetWordId = data.id; // Usado por MCQ, pode ser útil para outros
            currentWordAudioUrl = data.audio_url; // Usado por Ditado

            // Exibir nível de dificuldade (opcional, criar elemento se não existir)
            const difficultyEl = document.getElementById('word-difficulty-level'); // Assumindo que existe
            if (difficultyEl && data.difficulty_level !== undefined && data.difficulty_level !== null) {
                 let difficultyText = `Dificuldade: ${data.difficulty_level}`;
                 // Poderia mapear para texto: 1=Fácil, 2=Médio, 3=Difícil
                 const diffMap = {1: "Fácil", 2: "Médio", 3: "Difícil"};
                 if (data.difficulty_level in diffMap) {
                    difficultyText = `Dificuldade: ${diffMap[data.difficulty_level]}`;
                 }
                 difficultyEl.textContent = difficultyText;
                 difficultyEl.classList.remove('hidden');
            } else if (difficultyEl) {
                difficultyEl.classList.add('hidden');
            }
        }

        if (playAudioBtn && wordAudioEl) {
            playAudioBtn.addEventListener('click', () => {
                if (wordAudioEl.src && wordAudioEl.readyState >= 2) { // Fonte definida e metadados carregados
                    wordAudioEl.play().catch(e => console.error("Erro ao tocar áudio:", e));
                } else if (wordAudioEl.src) {
                    // Se src está definido mas não pronto, tenta carregar e tocar
                    wordAudioEl.load(); // Pode não ser necessário, mas por via das dúvidas
                    wordAudioEl.play().catch(e => console.error("Erro ao tocar áudio (após load):", e));
                } else {
                    showStatusMessage("Nenhum áudio para tocar.", "warn");
                }
            });
        }

        document.getElementById('search-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const word = document.getElementById('word-input').value;
            if (!word) { showStatusMessage('Por favor, digite uma palavra.', 'error'); return; }
            try {
                const response = await fetch(`/word/${word}`); 
                if (response.ok) {
                    const data = await response.json();
                    displayWordData(data, false);
                    showStatusMessage(`Palavra '${data.word}' carregada.`, 'success');
                } else {
                    const errorData = await response.json();
                    showStatusMessage(`Erro: ${errorData.detail || 'Palavra não encontrada!'}`, 'error');
                    wordDisplayDiv.classList.add('hidden');
                    exerciseSubmissionSection.classList.add('hidden');
                }
            } catch (error) { showStatusMessage(`Erro de conexão: ${error.message}`, 'error'); }
        });

        document.getElementById('next-exercise-btn').addEventListener('click', async () => {
            if (!jwtToken) { showStatusMessage('Faça login para obter um exercício.', 'error'); return; }
            try {
                showStatusMessage('Buscando próximo exercício...', 'info', 2000);
                const response = await fetchWithAuth(`/next_exercise/me`); 
                if (!response) return; 

                const result = await response.json();
                if (response.ok && result.suggested_word) {
                    const fullWordDataResponse = await fetch(`/word/${result.suggested_word.text}`); 
                    if (fullWordDataResponse.ok) {
                        const fullWordData = await fullWordDataResponse.json();
                        displayWordData(fullWordData, true);
                        showStatusMessage(`Próximo exercício: '${fullWordData.word}'. ${result.message}`, 'success');
                    } else {
                         showStatusMessage(`Erro ao buscar detalhes para '${result.suggested_word.text}'.`, 'error');
                         wordDisplayDiv.classList.add('hidden');
                         exerciseSubmissionSection.classList.add('hidden');
                    }
                } else {
                    showStatusMessage(result.message || 'Não foi possível obter o próximo exercício.', 'error');
                    wordDisplayDiv.classList.add('hidden');
                    exerciseSubmissionSection.classList.add('hidden');
                }
            } catch (error) { showStatusMessage(`Erro de conexão: ${error.message}`, 'error'); }
        });

        document.getElementById('submit-exercise-result-btn').addEventListener('click', async () => {
            if (!jwtToken) { showStatusMessage('Faça login para submeter resultados.', 'error'); return; }
            if (!currentWordText) { showStatusMessage('Nenhum exercício ativo.', 'error'); return; }
            
            const accuracy = document.getElementById('accuracy-checkbox').checked ? 1.0 : 0.0;
            const timeTaken = parseFloat(document.getElementById('time-taken-input').value);

            if (isNaN(timeTaken) || timeTaken <= 0) { showStatusMessage('Tempo inválido.', 'error'); return; }

            const submissionData = {
                word_text: currentWordText,
                accuracy: accuracy,
                time_taken_seconds: timeTaken
            };
            
            try {
                showStatusMessage('Enviando resultado...', 'info', 2000);
                const response = await fetchWithAuth('/submit_exercise_data/', { 
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(submissionData)
                });
                if (!response) return; 

                const result = await response.json();
                if (response.ok) {
                    showStatusMessage(`Resultado para '${currentWordText}' enviado!`, 'success');
                    exerciseSubmissionSection.classList.add('hidden'); 
                } else {
                    showStatusMessage(`Erro ao enviar: ${result.detail || 'Erro desconhecido.'}`, 'error');
                }
            } catch (error) { showStatusMessage(`Erro de conexão: ${error.message}`, 'error'); }
        });

        document.getElementById('train-model-btn').addEventListener('click', async () => {
            if (!jwtToken) { showStatusMessage('Faça login para treinar o modelo.', 'error'); return; }
            try {
                showStatusMessage('Iniciando treinamento do modelo...', 'info', 3000);
                const response = await fetchWithAuth('/admin/train_model', { method: 'POST' }); 
                if (!response) return; 

                const result = await response.json();
                if (response.ok) {
                    showStatusMessage(`Treinamento: ${result.message}`, 'success');
                } else {
                    showStatusMessage(`Erro no treinamento: ${result.message || result.detail || 'Erro desc.'}`, 'error');
                }
            } catch (error) { showStatusMessage(`Erro de conexão: ${error.message}`, 'error'); }
        });

        function displayDictationFeedback(feedbackEl, message, type = 'info') {
            if (!feedbackEl) return;
            feedbackEl.textContent = message;
            feedbackEl.className = `status-message ${type}`;
            feedbackEl.classList.remove('hidden');
        }

        function setupDictationExercise(container) {
            const dictationContent = container.querySelector('#dictation-exercise-content');
            if (!dictationContent) return;

            const playDictationAudioBtn = dictationContent.querySelector('#play-dictation-audio-btn');
            const dictationHiddenAudioEl = dictationContent.querySelector('#dictation-hidden-audio');
            const dictationInputEl = dictationContent.querySelector('#dictation-input');
            const submitDictationBtn = dictationContent.querySelector('#submit-dictation-btn');
            const dictationFeedbackEl = dictationContent.querySelector('#dictation-feedback');

            dictationHiddenAudioEl.src = currentWordAudioUrl;
            dictationInputEl.value = '';
            dictationFeedbackEl.classList.add('hidden');

            playDictationAudioBtn.onclick = () => {
                if (dictationHiddenAudioEl.src) {
                    dictationHiddenAudioEl.play();
                } else {
                    showStatusMessage('Áudio para ditado não carregado.', 'error');
                }
            };

            submitDictationBtn.onclick = async () => {
                const userAnswer = dictationInputEl.value.trim();
                if (!userAnswer) {
                    displayDictationFeedback(dictationFeedbackEl, 'Por favor, digite sua resposta.', 'error');
                    return;
                }
                const isCorrect = userAnswer.toLowerCase() === currentWordText.toLowerCase();
                const accuracy = isCorrect ? 1.0 : 0.0;
                const timeTaken = 15.0;

                const submissionData = { word_text: currentWordText, accuracy: accuracy, time_taken_seconds: timeTaken };
                showStatusMessage('Enviando resultado do ditado...', 'info', 2000);
                const response = await fetchWithAuth('/submit_exercise_data/', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(submissionData)
                });
                
                if (isCorrect) {
                    displayDictationFeedback(dictationFeedbackEl, 'Correto! Excelente!', 'success');
                } else {
                    displayDictationFeedback(dictationFeedbackEl, `Ops! A palavra correta era "${currentWordText}". Tente novamente!`, 'error');
                }
                setTimeout(() => {
                    dynamicExerciseContainer.innerHTML = '';
                    dynamicExerciseContainer.classList.add('hidden');
                    wordInteractionSection.classList.remove('hidden');
                    if (currentWordText) {
                         practiceMcqSection.classList.remove('hidden');
                         practiceDictationSection.classList.remove('hidden');
                         wordDisplayDiv.classList.remove('hidden');
                    } else {
                        wordDisplayDiv.classList.add('hidden');
                    }
                    updateUIVisibility(); // Restaurar visibilidade correta após exercício
                }, 5000);
            };
            dynamicExerciseContainer.classList.remove('hidden');
        }

        startDictationBtn.addEventListener('click', async () => {
            if (!currentWordText || !currentWordAudioUrl) {
                showStatusMessage('Por favor, primeiro busque ou obtenha uma palavra com áudio para praticar.', 'error');
                return;
            }
            if (!jwtToken) { showStatusMessage('Faça login para iniciar um exercício.', 'error'); return; }

            showStatusMessage(`Preparando exercício de ditado para "${currentWordText}"...`, 'info', 1500);
            
            hideAllMainSections(); // Função para esconder seções antes de carregar parcial

            try {
                const partialResponse = await fetch('/app/partials/dictation');
                if (!partialResponse.ok) throw new Error('Falha ao carregar o template do ditado.');
                dynamicExerciseContainer.innerHTML = await partialResponse.text();
                setupDictationExercise(dynamicExerciseContainer); 
            } catch (error) {
                showStatusMessage(`Erro: ${error.message}`, 'error');
                restoreDefaultView(); // Função para restaurar a visualização padrão em caso de erro
            }
        });

        function showProgressPageFeedback(message, type = 'info') {
            progressMessageEl.textContent = message;
            progressMessageEl.className = `status-message ${type}`;
            progressMessageEl.classList.remove('hidden');
            setTimeout(() => progressMessageEl.classList.add('hidden'), 5000);
        }

        function renderProgressCharts(reportData) {
            if (accuracyChartInstance) accuracyChartInstance.destroy();
            if (wordsPracticedChartInstance) wordsPracticedChartInstance.destroy();

            const labels = reportData.progress_trend.map(p => `ID ${p.progress_id_or_timestamp}`); 

            accuracyChartInstance = new Chart(accuracyTrendChartCtx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Acurácia da Sessão',
                        data: reportData.progress_trend.map(p => p.accuracy_at_point * 100), 
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: { callback: function(value) { return value + "%" } }
                        }
                    }
                }
            });

            wordsPracticedChartInstance = new Chart(wordsPracticedChartCtx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Nº Cumulativo de Palavras Únicas Praticadas',
                        data: reportData.progress_trend.map(p => p.cumulative_words_practiced),
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgb(54, 162, 235)',
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        }

        async function loadAndDisplayProgressReport() {
            if (!jwtToken) {
                showStatusMessage('Faça login para ver seu progresso.', 'error');
                return;
            }
            showStatusMessage('Carregando seu relatório de progresso...', 'info', 2000);
            hideAllMainSections();

            try {
                const response = await fetchWithAuth('/users/me/progress_report/');
                if (!response) { 
                    restoreDefaultView();
                    return;
                }

                if (response.ok) {
                    const reportData = await response.json();
                    if (reportData.message) {
                         showProgressPageFeedback(reportData.message, reportData.total_words_attempted_unique > 0 ? 'info' : 'info');
                    }
                    totalWordsAttemptedEl.textContent = reportData.total_words_attempted_unique;
                    overallAccuracyEl.textContent = (reportData.overall_accuracy * 100).toFixed(1);
                    avgTimePerAttemptEl.textContent = reportData.average_time_per_attempt.toFixed(1);
                    
                    if (reportData.progress_trend && reportData.progress_trend.length > 0) {
                        renderProgressCharts(reportData);
                        document.getElementById('progress-charts').classList.remove('hidden');
                    } else {
                        if (accuracyChartInstance) accuracyChartInstance.destroy();
                        if (wordsPracticedChartInstance) wordsPracticedChartInstance.destroy();
                        document.getElementById('progress-charts').classList.add('hidden');
                        showProgressPageFeedback('Nenhum dado de tendência para exibir nos gráficos.', 'info');
                    }
                    progressPageSection.classList.remove('hidden');
                } else {
                    const errorData = await response.json();
                    showStatusMessage(`Erro ao carregar relatório: ${errorData.detail || 'Falha.'}`, 'error');
                    restoreDefaultView(); 
                }
            } catch (error) {
                showStatusMessage(`Erro de conexão ao carregar relatório: ${error.message}`, 'error');
                restoreDefaultView(); 
            }
            updateUIVisibility(); // Garantir que o estado da UI esteja correto
        }

        showProgressBtn.addEventListener('click', loadAndDisplayProgressReport);

        backToMainViewBtn.addEventListener('click', () => {
            progressPageSection.classList.add('hidden');
            wordInteractionSection.classList.remove('hidden');
            checkLoginState(); // Atualizar e mostrar a view correta (logado ou não)
        });

        function displayDragDropFeedback(feedbackEl, message, type = 'info') {
            if (!feedbackEl) return;
            feedbackEl.textContent = message;
            feedbackEl.className = `status-message ${type}`;
            feedbackEl.classList.remove('hidden');
        }

        function setupDragDropExercise(container, exerciseData) {
            currentDragDropExerciseData = exerciseData; 
            const dragDropContent = container.querySelector('#drag-drop-exercise-content');
            if (!dragDropContent) return;

            const dragDropInstructionEl = dragDropContent.querySelector('#drag-drop-instruction');
            const draggableItemsPoolEl = dragDropContent.querySelector('#draggable-items-pool');
            const dropZonesContainerEl = dragDropContent.querySelector('#drop-zones-container');
            const checkDragDropBtn = dragDropContent.querySelector('#check-drag-drop-btn');
            const dragDropFeedbackEl = dragDropContent.querySelector('#drag-drop-feedback');
            
            dragDropInstructionEl.textContent = exerciseData.instruction;
            draggableItemsPoolEl.innerHTML = '<h4>Definições (Arraste daqui):</h4>'; 
            dropZonesContainerEl.innerHTML = '<h4>Palavras (Solte aqui):</h4>'; 
            dragDropFeedbackEl.classList.add('hidden');

            sortableInstances.forEach(s => s.destroy());
            sortableInstances = [];

            exerciseData.draggable_items.forEach(item => {
                const div = document.createElement('div');
                div.className = 'drag-item';
                div.textContent = item.content;
                div.setAttribute('data-id', item.id);
                div.style.padding = '10px'; div.style.margin = '5px'; div.style.border = '1px dashed #666';
                div.style.backgroundColor = '#fff'; div.style.cursor = 'grab';
                draggableItemsPoolEl.appendChild(div);
            });

            exerciseData.drop_zones.forEach(zone => {
                const zoneWrapper = document.createElement('div');
                zoneWrapper.className = 'drop-zone-wrapper'; zoneWrapper.style.marginBottom = '10px';
                const wordP = document.createElement('p');
                wordP.textContent = zone.content; wordP.style.fontWeight = 'bold';
                zoneWrapper.appendChild(wordP);
                const dropList = document.createElement('div');
                dropList.className = 'drop-list';
                dropList.setAttribute('data-zone-id', zone.id);
                dropList.setAttribute('data-correct-draggable-id', zone.correct_draggable_id);
                dropList.style.border = '2px solid #aaa'; dropList.style.padding = '10px';
                dropList.style.minHeight = '50px'; dropList.style.backgroundColor = '#fafafa';
                zoneWrapper.appendChild(dropList);
                dropZonesContainerEl.appendChild(zoneWrapper);
                const zoneSortable = new Sortable(dropList, {
                    group: 'shared-definitions', animation: 150,
                    onAdd: function (evt) {
                        if (evt.to.children.length > 1) {
                            Sortable.utils.select(evt.item).parentNode.removeChild(evt.item);
                            sortableInstances[0].el.appendChild(evt.item);
                            displayDragDropFeedback(dragDropFeedbackEl, 'Apenas uma definição por palavra.', 'error');
                            setTimeout(() => dragDropFeedbackEl.classList.add('hidden'), 2000);
                        }
                    }
                });
                sortableInstances.push(zoneSortable);
            });

            const poolSortable = new Sortable(draggableItemsPoolEl, { group: 'shared-definitions', animation: 150, sort: true });
            sortableInstances.push(poolSortable);

            checkDragDropBtn.onclick = async () => {
                if (!currentDragDropExerciseData) {
                    displayDragDropFeedback(dragDropFeedbackEl, 'Nenhum exercício ativo.', 'error'); return;
                }
                let correctMatches = 0;
                const totalPairs = currentDragDropExerciseData.drop_zones.length;
                currentDragDropExerciseData.drop_zones.forEach(zone => {
                    const dropListEl = dropZonesContainerEl.querySelector(`.drop-list[data-zone-id="${zone.id}"]`);
                    if (dropListEl && dropListEl.children.length === 1) {
                        const droppedItemEl = dropListEl.children[0];
                        const droppedItemId = droppedItemEl.getAttribute('data-id');
                        if (droppedItemId === zone.correct_draggable_id) correctMatches++;
                    }
                });
                const accuracy = totalPairs > 0 ? (correctMatches / totalPairs) : 0.0;
                displayDragDropFeedback(dragDropFeedbackEl, `Acertou ${correctMatches}/${totalPairs}. (Acurácia: ${(accuracy * 100).toFixed(0)}%)`, accuracy > 0.7 ? 'success' : 'info');

                const wordForDragDropSubmission = currentDragDropExerciseData.drop_zones[0] ? currentDragDropExerciseData.drop_zones[0].content : "drag_drop_set";

                const submitResponse = await fetchWithAuth('/submit_exercise_data/', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ word_text: wordForDragDropSubmission, accuracy: accuracy, time_taken_seconds: 60 })
                });
                if (submitResponse && submitResponse.ok) showStatusMessage('Resultado do arrastar e soltar enviado!', 'success', 3000);
                else showStatusMessage('Falha ao enviar resultado do arrastar e soltar.', 'error', 3000);
                
                setTimeout(() => {
                    dynamicExerciseContainer.innerHTML = '';
                    dynamicExerciseContainer.classList.add('hidden');
                    restoreDefaultView(); 
                }, 7000);
            };
            dynamicExerciseContainer.classList.remove('hidden');
        }

        startDragDropExerciseBtn.addEventListener('click', async () => {
            if (!jwtToken) { showStatusMessage('Faça login para praticar.', 'error'); return; }
            showStatusMessage('Carregando exercício de arrastar e soltar...', 'info', 2000);
            hideAllMainSections();

            try {
                const partialResponse = await fetch('/app/partials/drag_drop');
                if (!partialResponse.ok) throw new Error('Falha ao carregar template do Arrastar e Soltar.');
                dynamicExerciseContainer.innerHTML = await partialResponse.text();
                
                const exerciseDataResponse = await fetchWithAuth('/exercise/drag_drop_match/');
                if (!exerciseDataResponse) {
                    restoreDefaultView();
                    return;
                }
                if (exerciseDataResponse.ok) {
                    const exerciseData = await exerciseDataResponse.json();
                    setupDragDropExercise(dynamicExerciseContainer, exerciseData);
                } else {
                    const errorData = await exerciseDataResponse.json();
                    showStatusMessage(`Erro ao carregar exercício: ${errorData.detail || 'Falha.'}`, 'error');
                    restoreDefaultView();
                }
            } catch (error) {
                showStatusMessage(`Erro de conexão: ${error.message}`, 'error');
                restoreDefaultView();
            }
        });

        function displayMcqFeedback(feedbackEl, message, type = 'info') {
            if (!feedbackEl) return;
            feedbackEl.textContent = message;
            feedbackEl.className = `status-message ${type}`;
            feedbackEl.classList.remove('hidden');
        }

        async function handleMcqOptionClick(selectedOptionWordId, wordForSubmission, exerciseContainer) {
            const isCorrect = (selectedOptionWordId === currentTargetWordId); 
            const accuracy = isCorrect ? 1.0 : 0.0;
            const timeTaken = 10.0; 

            const submissionData = { word_text: wordForSubmission, accuracy: accuracy, time_taken_seconds: timeTaken };
            showStatusMessage('Enviando resultado do exercício de múltipla escolha...', 'info', 2000);
            const response = await fetchWithAuth('/submit_exercise_data/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(submissionData)
            });

            const feedbackEl = exerciseContainer.querySelector('#mcq-feedback');
            if (response && response.ok) {
                showStatusMessage(`Resultado para '${wordForSubmission}' (múltipla escolha) enviado!`, 'success');
            }
            
            if (isCorrect) {
                displayMcqFeedback(feedbackEl, 'Muito bem! Resposta correta!', 'success');
            } else {
                displayMcqFeedback(feedbackEl, `Quase lá! A definição correta era: "${correctAnswerDefinition}"`, 'error');
            }

            setTimeout(() => {
                dynamicExerciseContainer.innerHTML = ''; 
                dynamicExerciseContainer.classList.add('hidden');
                if (currentWordText) {
                    practiceMcqSection.classList.remove('hidden');
                    wordDisplayDiv.classList.remove('hidden'); // Mostrar novamente a palavra base
                }
                updateUIVisibility(); // Restaurar a visualização correta
            }, 5000);
        }

        function displayMultipleChoiceExercise(exerciseData, container) {
            const mcqContent = container.querySelector('#multiple-choice-exercise-content');
            if (!exerciseData || !exerciseData.options || exerciseData.options.length === 0 || !mcqContent) {
                showStatusMessage('Não foi possível carregar o exercício de múltipla escolha.', 'error');
                dynamicExerciseContainer.innerHTML = ''; 
                dynamicExerciseContainer.classList.add('hidden');
                return;
            }

            const mcqQuestionTextEl = mcqContent.querySelector('#mcq-question-text');
            const mcqOptionsContainerEl = mcqContent.querySelector('#mcq-options-container');
            
            mcqQuestionTextEl.textContent = exerciseData.message || `Qual a definição de "${exerciseData.target_word_text}"?`;
            mcqOptionsContainerEl.innerHTML = ''; 
            currentTargetWordId = exerciseData.target_word_id; 
            const wordForSubmission = exerciseData.target_word_text;

            const correctOpt = exerciseData.options.find(opt => opt.word_id === currentTargetWordId);
            correctAnswerDefinition = correctOpt ? correctOpt.definition : "[Definição não encontrada]"; 

            exerciseData.options.forEach(option => {
                const button = document.createElement('button');
                button.textContent = option.definition;
                button.style.display = 'block';
                button.style.width = '100%';
                button.style.marginBottom = '10px';
                button.style.textAlign = 'left';
                button.type = 'button'; 
                button.onclick = () => handleMcqOptionClick(option.word_id, wordForSubmission, container);
                mcqOptionsContainerEl.appendChild(button);
            });
            dynamicExerciseContainer.classList.remove('hidden');
        }

        startMcqBtn.addEventListener('click', async () => {
            if (!currentWordText) {
                showStatusMessage('Por favor, primeiro busque ou obtenha uma palavra para praticar.', 'error');
                return;
            }
            if (!jwtToken) { showStatusMessage('Faça login para iniciar um exercício.', 'error'); return; }

            showStatusMessage(`Preparando exercício de múltipla escolha para "${currentWordText}"...`, 'info', 2000);
            
            hideAllMainSections();

            try {
                const partialResponse = await fetch('/app/partials/mcq');
                if (!partialResponse.ok) {
                    throw new Error('Falha ao carregar o template do exercício de múltipla escolha.');
                }
                const mcqHtml = await partialResponse.text();
                dynamicExerciseContainer.innerHTML = mcqHtml;
                dynamicExerciseContainer.classList.remove('hidden');

                const exerciseDataResponse = await fetchWithAuth(`/exercise/multiple_choice/${currentWordText}`);
                if (!exerciseDataResponse) { 
                    restoreDefaultView();
                    return; 
                }

                if (exerciseDataResponse.ok) {
                    const exerciseData = await exerciseDataResponse.json();
                    displayMultipleChoiceExercise(exerciseData, dynamicExerciseContainer);
                } else {
                    const errorData = await exerciseDataResponse.json();
                    showStatusMessage(`Erro ao buscar dados do exercício: ${errorData.detail || 'Falha ao carregar.'}`, 'error');
                    restoreDefaultView();
                }
            } catch (error) {
                showStatusMessage(`Erro: ${error.message}`, 'error');
                restoreDefaultView();
            }
        });
        
        // Funções para simplificar mostrar/esconder seções
        function hideAllMainSections() {
            wordInteractionSection.classList.add('hidden');
            progressPageSection.classList.add('hidden');
            dynamicExerciseContainer.classList.add('hidden'); 
            wordDisplayDiv.classList.add('hidden'); // Esconder também a exibição da palavra base
        }

        function restoreDefaultView() {
            dynamicExerciseContainer.innerHTML = ''; // Limpar
            dynamicExerciseContainer.classList.add('hidden');
            wordInteractionSection.classList.remove('hidden');
            if (currentWordText) { // Se havia uma palavra sendo exibida, mostrar novamente
                wordDisplayDiv.classList.remove('hidden');
                practiceMcqSection.classList.remove('hidden');
                practiceDictationSection.classList.remove('hidden');
            }
            updateUIVisibility(); // Atualizar visibilidade geral
        }

        // --- INÍCIO: Lógica de Busca de Palavra e Autocomplete ---

        if (wordSearchInput && autocompleteSuggestionsDiv) {
            wordSearchInput.addEventListener('input', async () => {
                const prefix = wordSearchInput.value.trim();
                if (prefix.length < 1) { // Mínimo de 1 caractere para autocomplete
                    autocompleteSuggestionsDiv.innerHTML = '';
                    autocompleteSuggestionsDiv.classList.add('hidden');
                    return;
                }

                try {
                    // Não precisa de fetchWithAuth para autocomplete, pois é um endpoint público
                    const response = await fetch(`/words/autocomplete?prefix=${encodeURIComponent(prefix)}`);
                    if (response.ok) {
                        const suggestions = await response.json();
                        renderAutocompleteSuggestions(suggestions);
                    } else {
                        console.error('Erro ao buscar autocomplete:', response.statusText);
                        autocompleteSuggestionsDiv.innerHTML = '';
                        autocompleteSuggestionsDiv.classList.add('hidden');
                    }
                } catch (error) {
                    console.error('Erro de rede ao buscar autocomplete:', error);
                    autocompleteSuggestionsDiv.innerHTML = '';
                    autocompleteSuggestionsDiv.classList.add('hidden');
                }
            });

            // Fechar sugestões se clicar fora
            document.addEventListener('click', (event) => {
                if (!wordSearchInput.contains(event.target) && !autocompleteSuggestionsDiv.contains(event.target)) {
                    autocompleteSuggestionsDiv.classList.add('hidden');
                }
            });
        }

        function renderAutocompleteSuggestions(suggestions) {
            if (!autocompleteSuggestionsDiv) return;
            autocompleteSuggestionsDiv.innerHTML = '';
            if (suggestions.length > 0) {
                const ul = document.createElement('ul');
                ul.className = 'autocomplete-list'; // Adicionar classe para estilização
                suggestions.forEach(suggestionText => {
                    const li = document.createElement('li');
                    li.textContent = suggestionText;
                    li.addEventListener('click', () => {
                        wordSearchInput.value = suggestionText;
                        autocompleteSuggestionsDiv.innerHTML = '';
                        autocompleteSuggestionsDiv.classList.add('hidden');
                        fetchAndDisplayWord(suggestionText); // Buscar palavra ao clicar na sugestão
                    });
                    ul.appendChild(li);
                });
                autocompleteSuggestionsDiv.appendChild(ul);
                autocompleteSuggestionsDiv.classList.remove('hidden');
            } else {
                autocompleteSuggestionsDiv.classList.add('hidden');
            }
        }

        async function fetchAndDisplayWord(wordText) {
            if (!wordText || wordText.trim() === '') {
                showStatusMessage('Por favor, digite uma palavra.', 'warn');
                return;
            }
            currentWordText = wordText.trim(); // Atualiza a palavra atual globalmente
            hideDynamicExerciseContainer(); // Esconde qualquer exercício aberto
            progressPageSection.classList.add('hidden'); // Esconde a página de progresso
            wordInteractionSection.classList.remove('hidden'); // Garante que a seção de interação está visível

            try {
                // Não precisa de fetchWithAuth para busca de palavra, pois é um endpoint público
                const response = await fetch(`/word/${encodeURIComponent(currentWordText)}`);
                
                if (response.ok) {
                    const data = await response.json();
                    displayWordData(data); // Chama a função para exibir os dados (será ajustada)
                    wordDisplayDiv.classList.remove('hidden');
                } else {
                    const errorData = await response.json().catch(() => null); // Tenta pegar o JSON do erro
                    let detailMessage = 'Palavra não encontrada ou erro ao buscar dados.';
                    if (errorData && errorData.detail) {
                        detailMessage = errorData.detail;
                    }
                    showStatusMessage(detailMessage, 'error');
                    hideWordDisplay();
                }
            } catch (error) {
                console.error('Erro ao buscar dados da palavra:', error);
                showStatusMessage('Erro de conexão ao buscar dados da palavra.', 'error');
                hideWordDisplay();
            }
        }

        if (wordSearchButton) {
            wordSearchButton.addEventListener('click', () => {
                const wordToSearch = wordSearchInput ? wordSearchInput.value : '';
                fetchAndDisplayWord(wordToSearch);
            });
        }
        
        // Se o input de busca existir, permitir busca com Enter
        if (wordSearchInput) {
            wordSearchInput.addEventListener('keypress', (event) => {
                if (event.key === 'Enter') {
                    event.preventDefault(); // Previne submissão de formulário, se houver
                    const wordToSearch = wordSearchInput.value;
                    fetchAndDisplayWord(wordToSearch);
                }
            });
        }

        function hideWordDisplay() {
            wordDisplayDiv.classList.add('hidden');
            wordTitleEl.textContent = '';
            wordDefinitionEl.textContent = '';
            wordImageEl.src = '';
            wordImageEl.classList.add('hidden');
            wordAudioEl.src = '';
            playAudioBtn.classList.add('hidden');
            // Limpar também o currentWordText para evitar confusão em outros fluxos
            currentWordText = null; 
        }
        
        // --- FIM: Lógica de Busca de Palavra e Autocomplete ---

        // --- INÍCIO: Lógica de Aprendizado Guiado ---

        if (getDailyWordBtn) {
            getDailyWordBtn.addEventListener('click', async () => {
                if (!jwtToken) { showStatusMessage('Faça login para ver a Palavra do Dia.', 'warn'); return; }
                showStatusMessage('Buscando Palavra do Dia...', 'info', 2000);
                hideAllMainSections();
                wordInteractionSection.classList.remove('hidden'); // Manter a seção de interação de palavra visível

                try {
                    const response = await fetchWithAuth('/words/daily_word/');
                    if (!response) { restoreDefaultView(); return; }

                    if (response.ok) {
                        const wordData = await response.json();
                        if (wordData) {
                            displayWordData(wordData); // Reusa a função existente
                            wordDisplayDiv.classList.remove('hidden');
                            // Após exibir a palavra do dia, o usuário pode querer praticá-la
                            // Os botões de prática (MCQ, Ditado) devem ficar visíveis se currentWordText for setado
                            // A função displayWordData já cuida de currentWordText
                            // E a lógica de visibilidade dos botões de exercício deve funcionar
                            practiceMcqSection.classList.remove('hidden');
                            practiceDictationSection.classList.remove('hidden');
                            startDragDropExerciseBtn.classList.remove('hidden'); 
                            showStatusMessage('Palavra do Dia carregada!', 'success');
                        } else {
                            showStatusMessage('Nenhuma Palavra do Dia disponível no momento.', 'info');
                            hideWordDisplay();
                        }
                    } else {
                        const errorData = await response.json().catch(() => ({ detail: 'Erro desconhecido.'}));
                        showStatusMessage(`Erro ao buscar Palavra do Dia: ${errorData.detail}`, 'error');
                        hideWordDisplay();
                    }
                } catch (error) {
                    showStatusMessage(`Erro de conexão: ${error.message}`, 'error');
                    hideWordDisplay();
                }
                updateUIVisibility();
            });
        }

        if (startLearningBtn && learningLevelSelect && learningWordsDisplay) {
            startLearningBtn.addEventListener('click', async () => {
                if (!jwtToken) { showStatusMessage('Faça login para aprender palavras.', 'warn'); return; }
                const selectedLevel = learningLevelSelect.value;
                showStatusMessage(`Buscando palavras de nível ${learningLevelSelect.options[learningLevelSelect.selectedIndex].text}...`, 'info', 2000);
                hideAllMainSections();
                wordInteractionSection.classList.remove('hidden'); // Manter a seção de interação de palavra visível

                try {
                    const response = await fetchWithAuth(`/words/learn/?level=${selectedLevel}&limit=5`);
                    if (!response) { restoreDefaultView(); return; }

                    if (response.ok) {
                        wordsToLearnCache = await response.json();
                        if (wordsToLearnCache.length > 0) {
                            currentLearningWordIndex = 0;
                            displayCurrentLearningWord();
                            learningWordsDisplay.classList.remove('hidden');
                            showStatusMessage(`${wordsToLearnCache.length} palavra(s) carregada(s) para aprendizado.`, 'success');
                        } else {
                            showStatusMessage('Nenhuma palavra nova para aprender neste nível no momento.', 'info');
                            learningWordsDisplay.classList.add('hidden');
                            hideWordDisplay(); // Esconder a área de display se não há palavras para aprender
                        }
                    } else {
                        const errorData = await response.json().catch(() => ({ detail: 'Erro desconhecido.'}));
                        showStatusMessage(`Erro ao buscar palavras para aprender: ${errorData.detail}`, 'error');
                        hideWordDisplay();
                    }
                } catch (error) {
                    showStatusMessage(`Erro de conexão: ${error.message}`, 'error');
                    hideWordDisplay();
                }
                updateUIVisibility();
            });
        }
        
        function displayCurrentLearningWord() {
            if (wordsToLearnCache.length > 0 && currentLearningWordIndex >= 0 && currentLearningWordIndex < wordsToLearnCache.length) {
                const wordData = wordsToLearnCache[currentLearningWordIndex];
                displayWordData(wordData); // Reusa a função existente para mostrar a palavra
                wordDisplayDiv.classList.remove('hidden');
                // Habilitar botões de prática
                practiceMcqSection.classList.remove('hidden');
                practiceDictationSection.classList.remove('hidden');
                startDragDropExerciseBtn.classList.remove('hidden');

                if (currentLearningWordIndex < wordsToLearnCache.length - 1) {
                    nextLearningWordBtn.classList.remove('hidden');
                } else {
                    nextLearningWordBtn.classList.add('hidden');
                    showStatusMessage('Você viu todas as palavras carregadas para este nível. Busque novamente ou escolha outro nível.', 'info');
                }
            } else {
                hideWordDisplay();
                learningWordsDisplay.classList.add('hidden');
                nextLearningWordBtn.classList.add('hidden');
                if (wordsToLearnCache.length > 0) { // Se havia palavras mas o índice saiu do range
                     showStatusMessage('Fim da lista de aprendizado atual.', 'info');
                }
            }
        }

        if (nextLearningWordBtn) {
            nextLearningWordBtn.addEventListener('click', () => {
                currentLearningWordIndex++;
                if (currentLearningWordIndex < wordsToLearnCache.length) {
                    displayCurrentLearningWord();
                } else {
                    showStatusMessage('Você concluiu esta rodada de aprendizado. Selecione um nível para mais palavras.', 'info');
                    hideWordDisplay();
                    learningWordsDisplay.classList.add('hidden');
                    nextLearningWordBtn.classList.add('hidden');
                    // Opcional: limpar o cache aqui ou deixar para a próxima busca por nível
                    // wordsToLearnCache = [];
                    // currentLearningWordIndex = -1;
                }
            });
        }

        // --- FIM: Lógica de Aprendizado Guiado ---

        // Inicialização
        checkLoginState();
        updateLoginState(); // Usar esta que é mais completa para o estado inicial.

