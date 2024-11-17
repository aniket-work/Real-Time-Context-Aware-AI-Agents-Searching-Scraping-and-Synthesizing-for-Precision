import streamlit as st
import yaml
import json
import os
import sys
from pathlib import Path
from llm_wrapper import LLMWrapper
from llm_response_parser import UltimateLLMResponseParser
from Self_Improving_Search import EnhancedSelfImprovingSearch

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Set up configuration paths
CONFIG_DIR = Path('config')
CONFIG_PATH = CONFIG_DIR / 'config.yaml'
PROMPTS_PATH = CONFIG_DIR / 'prompts.json'
LOG_PATH = Path('logs') / 'web_llm.log'


def load_config():
    """Load configuration files with error handling"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        st.error(f"Configuration file not found at {CONFIG_PATH}")
        sys.exit(1)
    except yaml.YAMLError as e:
        st.error(f"Error parsing config.yaml: {e}")
        sys.exit(1)


def load_prompts():
    """Load prompts with error handling"""
    try:
        with open(PROMPTS_PATH, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        st.error(f"Prompts file not found at {PROMPTS_PATH}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        st.error(f"Error parsing prompts.json: {e}")
        sys.exit(1)


# Load configuration
config = load_config()
prompts = load_prompts()


def initialize_llm():
    """Initialize LLM with error handling"""
    try:
        st.info("Initializing LLM...")
        llm_wrapper = LLMWrapper()
        st.success("LLM initialized successfully.")
        return llm_wrapper
    except Exception as e:
        st.error(f"Error initializing LLM: {str(e)}")
        return None


def get_llm_response(llm, prompt):
    """Get LLM response with error handling"""
    try:
        system_prompt = prompts['system_prompt']['content']
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
        response = llm.generate(full_prompt)
        return response
    except Exception as e:
        st.error(f"Error getting LLM response: {str(e)}")
        return None


def init_session_state():
    """Initialize session state variables"""
    if 'llm' not in st.session_state:
        st.session_state.llm = initialize_llm()
    if 'parser' not in st.session_state:
        st.session_state.parser = UltimateLLMResponseParser()


def display_logs():
    """Display logs with error handling"""
    try:
        if LOG_PATH.exists():
            with open(LOG_PATH, 'r', encoding='utf-8') as file:
                logs = file.read()
            st.text_area("Process Logs", logs, height=400)
        else:
            st.info("No logs available yet.")
    except Exception as e:
        st.error(f"Error reading logs: {str(e)}")


def main():
    """Main application function"""
    # Configure page settings
    st.set_page_config(
        page_title=config['ui']['title'],
        layout=config['ui']['layout'],
        initial_sidebar_state=config['ui']['initial_sidebar_state']
    )

    # Apply custom CSS
    st.markdown("""
        <style>
        .stTextInput > label {
            font-size: 20px;
        }
        .stButton > button {
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("Real-Time Context-Aware AI Agents : Searching, Scraping, and Synthesizing for Precision")

    # Initialize session state
    init_session_state()

    # Query input section
    with st.container():
        query = st.text_input(
            "Enter your query (prefix with '/' for web search):",
            help="Start with '/' to activate web search mode"
        )

        if st.button("Submit", use_container_width=True):
            if not query:
                st.warning("Please enter a query")
                return

            if not st.session_state.llm:
                st.error("LLM not initialized properly. Please check your configuration.")
                return

            with st.spinner("Processing your query..."):
                try:
                    if query.startswith('/'):
                        search = EnhancedSelfImprovingSearch(
                            llm=st.session_state.llm,
                            parser=st.session_state.parser
                        )
                        result = search.search_and_improve(query[1:])
                    else:
                        result = get_llm_response(st.session_state.llm, query)

                    if result:
                        st.markdown("### Response:")
                        st.markdown(result)
                    else:
                        st.warning("No response generated")
                except Exception as e:
                    st.error(f"Error processing query: {str(e)}")
                    raise e

    # Always show logs if enabled
    if config['ui'].get('show_logs', True):
        with st.expander("Process Logs", expanded=True):
            display_logs()


if __name__ == "__main__":
    main()