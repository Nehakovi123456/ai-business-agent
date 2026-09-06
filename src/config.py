import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# BASE DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
CHROMA_PERSIST_DIR = DATA_DIR / "chroma_db"
SQLITE_DB_PATH = DATA_DIR / "business_agent.db"
UPLOAD_DIR = DATA_DIR / "uploads"
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"

# Create required directories
for folder in [
    DATA_DIR,
    CHROMA_PERSIST_DIR,
    UPLOAD_DIR,
    SAMPLE_DATA_DIR
]:
    folder.mkdir(parents=True, exist_ok=True)


# ============================================================
# LLM CONFIGURATION
# ============================================================

DEFAULT_LLM_PROVIDER = os.getenv(
    "DEFAULT_LLM_PROVIDER",
    "gemini"
).lower().strip()

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    ""
) or os.getenv(
    "GOOGLE_API_KEY",
    ""
)

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY",
    ""
)

TAVILY_API_KEY = os.getenv(
    "TAVILY_API_KEY",
    ""
)

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3"
)


# ============================================================
# DOCUMENT PROCESSING
# ============================================================

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


# ============================================================
# LLM FACTORY
# ============================================================

def get_llm(provider: str = None, temperature: float = 0.2):
    """
    Returns an LLM instance based on the selected provider.

    Supported providers:
        - Gemini ('gemini')
        - OpenAI ('openai')
        - Ollama ('ollama')

    If the requested provider cannot be initialized,
    the function returns None.
    """

    provider = (
        provider or DEFAULT_LLM_PROVIDER
    ).lower().strip()

    # 1. GOOGLE GEMINI
    if provider == "gemini":
        api_key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or GEMINI_API_KEY
        )

        if api_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI

                llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=api_key,
                    temperature=temperature
                )
                print("[Config] Gemini LLM initialized successfully.")
                return llm
            except Exception as e:
                print(f"[Config] Failed to initialize Gemini: {e}")
        else:
            print("[Config] Gemini API key not found. Set GEMINI_API_KEY or GOOGLE_API_KEY.")
        return None

    # 2. OPENAI
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY
        if api_key:
            try:
                from langchain_openai import ChatOpenAI

                llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    api_key=api_key,
                    temperature=temperature
                )
                print("[Config] OpenAI LLM initialized successfully.")
                return llm
            except Exception as e:
                print(f"[Config] Failed to initialize OpenAI: {e}")
        else:
            print("[Config] OpenAI API key not found. Set OPENAI_API_KEY.")
        return None

    # 3. OLLAMA
    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama

            llm = ChatOllama(
                base_url=OLLAMA_BASE_URL,
                model=OLLAMA_MODEL,
                temperature=temperature
            )
            print("[Config] Ollama LLM initialized successfully.")
            return llm
        except ImportError:
            try:
                from langchain_community.chat_models import ChatOllama

                llm = ChatOllama(
                    base_url=OLLAMA_BASE_URL,
                    model=OLLAMA_MODEL,
                    temperature=temperature
                )
                print("[Config] Ollama LLM initialized successfully.")
                return llm
            except Exception as e:
                print(f"[Config] Failed to initialize Ollama: {e}")
        except Exception as e:
            print(f"[Config] Failed to initialize Ollama: {e}")
        return None

    print(f"[Config] Provider '{provider}' not configured or no valid LLM available.")
    return None