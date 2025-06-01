# backend/app/services/ml_model.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib # Para salvar/carregar o modelo treinado
import os

# Define o diretório base do backend (Palavras_project/backend)
# __file__ é F:/aprendizado/Palavras_project/backend/app/services/ml_model.py
# Subimos três níveis para chegar em Palavras_project/backend
BACKEND_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_FILE_PATH = os.path.join(BACKEND_ROOT_DIR, 'difficulty_model.pkl')

# Níveis: 0=Fácil, 1=Médio, 2=Difícil
DIFFICULTY_LEVELS = {"Fácil": 0, "Médio": 1, "Difícil": 2}
REVERSE_DIFFICULTY_LEVELS = {v: k for k, v in DIFFICULTY_LEVELS.items()}

def train_model(data: pd.DataFrame):
    """
    Treina um modelo de classificação para prever a dificuldade.
    O DataFrame 'data' deve ter colunas como:
    'accuracy' (0.0-1.0), 'avg_time' (em segundos), 'word_length', 'difficulty_level' (0, 1 ou 2)
    """
    # Features (X) e Target (y)
    features = ['accuracy', 'avg_time', 'word_length']
    target = 'difficulty_level'
    
    X = data[features]
    y = data[target]
    
    if len(X) < 10: # Pequeno safeguard para evitar erro com poucos dados
        print("Dados insuficientes para treinamento do modelo (<10 amostras).")
        return None

    # Verifica se há pelo menos duas classes presentes em y para test_split e LogisticRegression
    if len(y.unique()) < 2:
        print("Dados de treinamento contêm menos de duas classes de dificuldade. Modelo não será treinado.")
        return None
        
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y if len(y.unique()) > 1 else None)
    
    model = LogisticRegression()
    model.fit(X_train, y_train)
    
    # Salva o modelo treinado
    joblib.dump(model, MODEL_FILE_PATH)
    
    accuracy = accuracy_score(y_test, model.predict(X_test))
    print(f"Modelo treinado e salvo em {MODEL_FILE_PATH} com acurácia de: {accuracy:.2f}")
    return model

def predict_difficulty(user_performance: dict) -> int:
    """
    Prevê a próxima dificuldade com base no desempenho do usuário.
    user_performance = {'accuracy': 0.85, 'avg_time': 5.2, 'word_length': 7}
    Retorna um inteiro representando o nível de dificuldade (0, 1, ou 2).
    """
    try:
        model = joblib.load(MODEL_FILE_PATH)
        # Garante que as colunas no DataFrame estejam na mesma ordem que o modelo espera
        df_performance = pd.DataFrame([user_performance])
        # Certifique-se de que as colunas de df_performance correspondam às features usadas no treinamento
        # Exemplo: ['accuracy', 'avg_time', 'word_length']
        features_expected = ['accuracy', 'avg_time', 'word_length']
        df_performance = df_performance[features_expected]

        prediction = model.predict(df_performance)
        predicted_level = prediction[0]
        print(f"Previsão de dificuldade: Nível {predicted_level} ({REVERSE_DIFFICULTY_LEVELS.get(predicted_level, 'Desconhecido')})")
        return predicted_level
    except FileNotFoundError:
        print(f"Arquivo do modelo não encontrado em {MODEL_FILE_PATH}. Retornando dificuldade Média por padrão.")
        return DIFFICULTY_LEVELS["Médio"]
    except Exception as e:
        print(f"Erro ao prever dificuldade: {e}. Retornando dificuldade Média por padrão.")
        return DIFFICULTY_LEVELS["Médio"]

# Exemplo de como usar (para teste)
if __name__ == '__main__':
    # Dados de exemplo para treinamento
    # Em um cenário real, isso viria do banco de dados UserProgress
    sample_data = {
        'accuracy': [0.9, 0.8, 0.95, 0.7, 0.6, 0.85, 0.92, 0.75, 0.65, 0.98, 0.5, 0.77, 0.88],
        'avg_time': [5.0, 7.1, 4.5, 8.0, 9.5, 6.0, 5.3, 7.5, 8.8, 4.0, 10.0, 7.2, 5.8],
        'word_length': [4, 5, 3, 7, 8, 5, 4, 6, 7, 3, 9, 6, 5],
        'difficulty_level': [0, 1, 0, 1, 2, 1, 0, 1, 2, 0, 2, 1, 0] # Fácil, Médio, Difícil
    }
    df_train = pd.DataFrame(sample_data)
    
    print("--- Treinando Modelo ---")
    trained_model = train_model(df_train)
    
    if trained_model:
        print("\n--- Testando Predição ---")
        # Exemplo de desempenho do usuário
        performance_easy = {'accuracy': 0.95, 'avg_time': 4.0, 'word_length': 4}
        performance_medium = {'accuracy': 0.80, 'avg_time': 7.0, 'word_length': 6}
        performance_hard = {'accuracy': 0.60, 'avg_time': 9.0, 'word_length': 8}
        
        print(f"Desempenho (esperado Fácil): {performance_easy}")
        predict_difficulty(performance_easy)
        
        print(f"Desempenho (esperado Médio): {performance_medium}")
        predict_difficulty(performance_medium)

        print(f"Desempenho (esperado Difícil): {performance_hard}")
        predict_difficulty(performance_hard)
    else:
        print("Treinamento do modelo falhou ou foi pulado.")

    print("\n--- Testando Predição sem modelo treinado (deve usar fallback) ---")
    # Remove o arquivo do modelo para simular FileNotFoundError
    if os.path.exists(MODEL_FILE_PATH):
        os.remove(MODEL_FILE_PATH)
        print(f"Arquivo {MODEL_FILE_PATH} removido para teste de fallback.")
    predict_difficulty({'accuracy': 0.7, 'avg_time': 6.0, 'word_length': 5}) 