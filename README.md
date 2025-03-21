# Papuy - Asistente de Investigación Médica

Papuy es un asistente de investigación médica potenciado por IA que ayuda a estudiantes de medicina a encontrar, entender y analizar artículos médicos.

## Configuración

1. Clona el repositorio:
```bash
git clone https://github.com/yourusername/papuy_ai.git
cd papuy_ai
```

2. Crea un entorno virtual e instala las dependencias:
```bash
python -m venv myenv
source myenv/bin/activate  # En Windows: myenv\Scripts\activate
pip install -r requirements.txt
```

3. Configura las variables de entorno:
   - Copia el archivo `.env.example` a `.env`
   - Reemplaza los valores con tus propias API keys:
     - `OPENAI_API_KEY`: Obtén una en [OpenAI](https://platform.openai.com)
     - `SERP_API_KEY`: Obtén una en [SerpAPI](https://serpapi.com)

```bash
cp .env.example .env
# Edita el archivo .env con tus API keys
```

4. Ejecuta la aplicación:
```bash
streamlit run app.py
```

## Características

- 🔍 Búsqueda de artículos médicos
- 📚 Resumen automático de papers
- 💡 Respuestas basadas en evidencia
- 📥 Enlaces de descarga de artículos
- 🌎 Soporte multilingüe (español/inglés)

## Seguridad

- Las API keys se manejan de forma segura a través de variables de entorno
- Nunca compartas tu archivo `.env` o tus API keys
- El archivo `.env` está incluido en `.gitignore` para prevenir commits accidentales

## Contribuir

1. Haz fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Haz commit de tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request 