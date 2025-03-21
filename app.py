import streamlit as st
import os
from dotenv import load_dotenv
from chatbot import PapuyChatbot
import time

# Load environment variables
load_dotenv()

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'show_love' not in st.session_state:
    st.session_state.show_love = False

def login(username, password):
    return username == st.secrets["APP_USERNAME"] and password == st.secrets["APP_PASSWORD"]

def initialize_chatbot():
    try:
        if not st.secrets["OPENAI_API_KEY"]:
            st.error("OpenAI API key not found. Please add it to your .env file.")
            return False
        st.session_state.chatbot = PapuyChatbot()
        return True
    except Exception as e:
        st.error(f"Error initializing chatbot: {str(e)}")
        return False

def clear_conversation():
    st.session_state.messages = []
    if st.session_state.chatbot:
        st.session_state.chatbot.messages = []
    st.rerun()

def toggle_love():
    st.session_state.show_love = True
    time.sleep(0.1)  # Small delay for better UX
    st.rerun()

# Custom CSS for ChatGPT-like interface
def local_css():
    st.markdown("""
    <style>
        /* Reset some Streamlit defaults */
        .stApp {
            margin: 0;
            padding: 0;
            height: 100vh;
            overflow: hidden;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, Cantarell, "Helvetica Neue", sans-serif !important;
        }
        
        /* Main container */
        .main {
            background-color: #343541;
            height: 100vh;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        /* Apply fonts globally */
        .stApp, .main, .messages-container, .input-container, .stChatMessage, 
        .stMarkdown, .stChatInput, button, input, select, textarea {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, Cantarell, "Helvetica Neue", sans-serif !important;
        }
        
        /* Welcome container */
        .welcome-container {
            text-align: center;
            padding: 2rem;
            color: white;
            font-family: inherit;
        }
        
        .welcome-container h1 {
            font-size: 2rem;
            margin-bottom: 1rem;
            font-weight: 600;
            font-family: inherit;
        }
        
        .welcome-container p {
            font-size: 1.1rem;
            margin: 1rem 0;
            font-family: inherit;
        }
        
        .welcome-container ul {
            list-style: none;
            padding: 0;
            font-size: 1.1rem;
            font-family: inherit;
        }
        
        .welcome-container li {
            margin: 0.5rem 0;
            font-family: inherit;
        }
        
        /* Message styling */
        .stChatMessage {
            font-size: 1rem !important;
            line-height: 1.5 !important;
            letter-spacing: 0 !important;
        }
        
        /* Headers in messages */
        .stChatMessage h1, .stChatMessage h2, .stChatMessage h3 {
            font-family: inherit !important;
            font-weight: 600 !important;
        }
        
        /* Input field */
        .stChatInput {
            font-size: 1rem !important;
            line-height: 1.5 !important;
        }
        
        /* Sidebar text */
        .css-1d391kg {
            font-size: 1rem !important;
            line-height: 1.5 !important;
        }
        
        /* Buttons */
        button {
            font-size: 1rem !important;
            line-height: 1.5 !important;
        }
        
        /* Sidebar */
        .css-1d391kg {
            background-color: #202123;
        }
        
        /* Chat layout structure */
        .chat-layout {
            flex: 1;
            display: flex;
            flex-direction: column;
            max-width: 800px;
            margin: 0 auto;
            height: calc(100vh - 0px);
            position: relative;
        }
        
        /* Messages container */
        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 2rem 1rem;
            padding-bottom: 100px;
            margin-bottom: 0;
            height: calc(100vh - 80px);
            position: fixed;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 800px;
            max-width: 100%;
            font-family: inherit;
        }
        
        /* Ensure messages are visible */
        .element-container, .stMarkdown {
            overflow: visible !important;
        }
        
        .messages-container::-webkit-scrollbar {
            width: 7px;
        }
        
        .messages-container::-webkit-scrollbar-track {
            background: #2A2B32;
        }
        
        .messages-container::-webkit-scrollbar-thumb {
            background-color: #565869;
            border-radius: 20px;
        }
        
        /* Input container */
        .input-container {
            position: fixed;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 800px;
            max-width: 100%;
            background-color: #343541;
            border-top: 1px solid #4d4d4f;
            padding: 1.5rem;
            z-index: 1000;
        }
        
        .input-container > div {
            max-width: 800px;
            margin: 0 auto;
            width: 100%;
        }
        
        /* Chat input field */
        .stChatInput {
            background-color: #40414f !important;
            border-color: #565869 !important;
            border-radius: 0.75rem !important;
            padding: 0.75rem !important;
            color: white !important;
            width: 100% !important;
            max-width: 800px !important;
            margin: 0 auto !important;
            font-family: inherit !important;
            font-size: 1rem !important;
        }
        
        .stChatInput:focus {
            border-color: #19C37D !important;
            box-shadow: 0 0 0 1px #19C37D !important;
        }
        
        .stChatInput::placeholder {
            color: #999 !important;
        }
        
        /* Hide Streamlit's bottom toolbar and other unnecessary elements */
        .stDeployButton, 
        .stToolbar, 
        .stStatusWidget, 
        footer {
            display: none !important;
        }
        
        /* Prevent any default Streamlit floating elements */
        .stFloatingInput,
        .stChatFloatingInputContainer {
            display: none !important;
        }
        
        /* Remove any margins or padding from the app container */
        .appview-container {
            margin: 0 !important;
            padding: 0 !important;
        }
        
        /* Individual chat messages */
        .stChatMessage {
            background-color: #444654;
            padding: 1.5rem;
            margin: 0.75rem 0;
            border-radius: 0.75rem;
            width: 100%;
            box-sizing: border-box;
            overflow-wrap: break-word;
            word-wrap: break-word;
            word-break: break-word;
            font-family: inherit;
            font-size: 1rem;
            line-height: 1.5;
        }
        
        .stChatMessage.user {
            background-color: #343541;
        }
        
        /* Message content */
        .stMarkdown {
            color: white !important;
            font-family: inherit;
        }
        
        /* Headers in messages */
        .stChatMessage h1 {
            font-size: 1.5rem !important;
            margin: 1.5rem 0 1rem !important;
            color: #19C37D !important;
        }
        
        .stChatMessage h2 {
            font-size: 1.25rem !important;
            margin: 1.25rem 0 0.75rem !important;
            color: #19C37D !important;
        }
        
        .stChatMessage h3 {
            font-size: 1.1rem !important;
            margin: 1rem 0 0.5rem !important;
            color: #19C37D !important;
        }
        
        /* Lists in messages */
        .stChatMessage ul, .stChatMessage ol {
            margin: 0.5rem 0 0.5rem 1.5rem !important;
            padding: 0 !important;
        }
        
        .stChatMessage li {
            margin: 0.25rem 0 !important;
        }
        
        /* Tables in messages */
        .stChatMessage table {
            width: 100% !important;
            margin: 1rem 0 !important;
            border-collapse: collapse !important;
        }
        
        .stChatMessage th {
            background-color: #2A2B32 !important;
            padding: 0.75rem !important;
            border: 1px solid #4d4d4f !important;
            color: #19C37D !important;
        }
        
        .stChatMessage td {
            padding: 0.75rem !important;
            border: 1px solid #4d4d4f !important;
        }
        
        /* Code blocks */
        .stChatMessage code {
            background-color: #2A2B32 !important;
            padding: 0.2rem 0.4rem !important;
            border-radius: 0.25rem !important;
            font-family: monospace !important;
        }
        
        /* Blockquotes */
        .stChatMessage blockquote {
            border-left: 3px solid #19C37D !important;
            margin: 1rem 0 !important;
            padding-left: 1rem !important;
            color: #999 !important;
        }
        
        /* Citations */
        .citation {
            font-style: italic;
            color: #999;
            border-left: 3px solid #19C37D;
            padding-left: 1rem;
            margin: 1rem 0;
        }
        
        /* Reference list */
        .references {
            margin-top: 1.5rem;
            padding-top: 1rem;
            border-top: 1px solid #4d4d4f;
        }
        
        .references h3 {
            color: #19C37D !important;
            margin-bottom: 1rem;
        }
        
        /* Emphasis and strong text */
        .stChatMessage em {
            color: #999 !important;
        }
        
        .stChatMessage strong {
            color: #19C37D !important;
        }
        
        /* Links */
        .stChatMessage a {
            color: #19C37D !important;
            text-decoration: none !important;
            border-bottom: 1px dashed #19C37D !important;
        }
        
        .stChatMessage a:hover {
            text-decoration: none !important;
            border-bottom: 1px solid #19C37D !important;
        }
        
        /* Fix sidebar width */
        section[data-testid="stSidebar"] {
            width: 260px !important;
            min-width: 260px !important;
            max-width: 260px !important;
        }
        
        /* Ensure proper stacking */
        .stChatMessageContainer {
            margin-bottom: 0 !important;
        }
        
        /* Fix for mobile responsiveness */
        @media (max-width: 768px) {
            .chat-layout {
                padding: 0;
            }
            
            .messages-container {
                padding: 1rem;
            }
            
            .input-container {
                padding: 0.5rem;
            }
            
            .stChatInput {
                border-radius: 0.5rem !important;
                padding: 0.5rem !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(
        page_title="Papuy - Asistente de Investigación Médica",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items=None  # Hide the menu
    )
    
    local_css()

    if not st.session_state.authenticated:
        # Center the login form
        _, login_col, _ = st.columns([1, 2, 1])
        
        with login_col:
            st.title("👩‍⚕️ Papuy.ai")
            st.markdown("### Tu asistente de investigación médica")
            
            with st.form("login_form", clear_on_submit=True):
                username = st.text_input("Usuario")
                password = st.text_input("Contraseña", type="password")
                submit_button = st.form_submit_button("Iniciar Sesión")
                
                if submit_button:
                    if login(username, password):
                        if initialize_chatbot():
                            st.session_state.authenticated = True
                            st.success("¡Inicio de sesión exitoso!")
                            st.rerun()
                    else:
                        st.error("Usuario o contraseña inválidos")
    else:
        # Sidebar with new chat and settings
        with st.sidebar:
            st.title("Hola, **Emily**")
            
            # New conversation button
            if st.button("🌟 Nueva Conversación", use_container_width=True):
                clear_conversation()
            
            st.divider()
            
            # Available commands section
            st.markdown("### 📝 Comandos Disponibles")
            commands = {
                "🔍 Buscar artículos": "buscar artículos sobre [tema]",
                "🌎 Buscar en inglés": "buscar artículos sobre [tema] en inglés",
                "📥 Descargar artículo": "obtener enlace de descarga para [URL]",
                "📚 Resumir artículo": "resumir este artículo [texto]"
            }
            
            for title, command in commands.items():
                with st.expander(title):
                    st.code(command, language="markdown")
            
            # Settings section
            st.markdown("### ⚙️ Configuración")
            with st.expander("Cuenta"):
                st.markdown(f"**Usuario:** Emily")
                if st.button("Cerrar Sesión", use_container_width=True):
                    st.session_state.authenticated = False
                    st.session_state.chatbot = None
                    st.session_state.messages = []
                    st.rerun()
            
            # Push content to bottom
            st.markdown("<div style='flex-grow: 1;'></div>", unsafe_allow_html=True)
            
            # Footer with love
            st.divider()
            credit_col1, credit_col2, credit_col3 = st.columns([2, 1, 2])
            
            with credit_col2:
                if st.button("❤️", key="love_button"):
                    toggle_love()
            
            st.markdown(
                """<div style='text-align: center; color: #666; padding: 10px;'>
                Hecho por <a href='https://marcopaaz.com' target='_blank'>Marco Paz</a>
                </div>""", 
                unsafe_allow_html=True
            )
            
            if st.session_state.show_love:
                st.balloons()
                st.toast("¡Te quiero Emily! 💕", icon="💝")
                st.session_state.show_love = False
        
        # Main chat interface
        st.markdown('<div class="chat-layout">', unsafe_allow_html=True)
        
        # Messages container
        st.markdown('<div class="messages-container">', unsafe_allow_html=True)
        
        # Display chat messages
        for message in st.session_state.messages:
            icon = "👩‍⚕️" if message["role"] == "user" else "🤖"
            with st.chat_message(message["role"], avatar=icon):
                st.markdown(message["content"])
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close messages-container
        
        # Input container
        st.markdown('<div class="input-container">', unsafe_allow_html=True)
        prompt = st.chat_input("Pregúntame sobre investigación médica...", key="chat_input")
        
        # Welcome message only if no messages and no current input
        if not st.session_state.messages and not prompt:
            st.markdown("""
            <div class='welcome-container'>
                <h1>👩‍⚕️ Bienvenida a Papuy</h1>
                <p style='color: #999; margin: 1rem 0;'>
                    Soy tu asistente de investigación médica. Puedo ayudarte a:
                </p>
                <ul style='list-style: none; padding: 0;'>
                    <li>🔍 Buscar artículos médicos</li>
                    <li>📚 Resumir papers científicos</li>
                    <li>💡 Responder preguntas médicas</li>
                    <li>📥 Obtener enlaces de descarga</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        if prompt:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👩‍⚕️"):
                st.markdown(prompt)
            
            # Get bot response
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Pensando..."):
                    try:
                        if st.session_state.chatbot is None:
                            if not initialize_chatbot():
                                st.error("Error al inicializar el chatbot. Por favor, intenta iniciar sesión nuevamente.")
                                return
                        response = st.session_state.chatbot.get_response(prompt)
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    except Exception as e:
                        error_message = f"Lo siento, pero encontré un error: {str(e)}"
                        st.error(error_message)
                        st.session_state.messages.append({"role": "assistant", "content": error_message})
        st.markdown('</div>', unsafe_allow_html=True)  # Close input-container
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close chat-layout

if __name__ == "__main__":
    main() 