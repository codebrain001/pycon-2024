import os
import sys
import streamlit as st

from req_engineering_project.crew import ReqEngineeringProjectCrew
from req_engineering_project.utils import StreamToExpander
from langtrace_python_sdk import langtrace

# Update your langtrace API key
LANGTRACE_API_KEY = "xxxx"



def setup_page():
    """
    Setup page settings such as title, page icon, layout and menu items
    Args:
        None

    Returns:
        None
    """
    st.set_page_config(
        page_title="Pycon Africa: Multi-Agents Requirement Analysis and Specification Tool",
        page_icon="🏠",
        layout="wide",
        menu_items={
            'Report a bug': "https://github.com/codebrain001/pycon-2024/issues",
            'About': "## This tool helps in automating and enhancing software requirement analysis and specification process."
        }
    )

def sidebar_config(disabled):
    """
    Displays a sidebar configuration panel for selecting an LLM model, optionally entering an API key, and creating agents.

    Args:
        disabled (bool): Whether input fields and buttons should be disabled.

    Returns:
        tuple: The selected LLM, API key (if applicable), and a boolean indicating if the "Create Agentic" button was clicked.
    """
    st.sidebar.title("Configuration")
    st.sidebar.markdown("### Select LLM")
    llm_options = ["GPT-4o", "GPT-4o-Mini", "o1-Mini"]
    selected_llm = st.sidebar.selectbox("Choose LLM", llm_options, index=0, disabled=disabled, key="llm_selectbox").lower()
    if 'selected_llm' not in st.session_state:
        st.session_state['selected_llm'] = selected_llm
    st.sidebar.markdown("### API Key")
    api_key = st.sidebar.text_input("Enter your API key", type="password", disabled=disabled, key="api_key_input", placeholder="OpenAI API key")
   
    agents_disabled = disabled or not (selected_llm and api_key)
    run_agents_button = st.sidebar.button("Run Agents", disabled=agents_disabled, key="run_agent_button")
    return selected_llm, api_key, run_agents_button

def upload_meeting_notes():
    st.info("Upload meeting or meeting notes", icon="ℹ️")
    uploaded_files = st.file_uploader(
        "Choose documents",
        type=["doc", "docx", "txt", "pdf", "mp4", "mp3"],
        accept_multiple_files=True
    )
    if uploaded_files:
        save_uploaded_files_path = "src/req_engineering_project/tools/data/inputs/"
        os.makedirs(save_uploaded_files_path, exist_ok=True)

        for uploaded_file in uploaded_files:
            file_path = os.path.join(save_uploaded_files_path, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.toast(f"Uploaded and saved: {uploaded_file.name}")
    return uploaded_files

def run_agentic_workflow(model_name, api_key):
    try:
        with st.status("🤖 **Agents at work...**", state="running", expanded=True) as status:
                with st.container(height=500, border=False):
                    sys.stdout = StreamToExpander(st)
                    ReqEngineeringProjectCrew(model_name, api_key).crew().kickoff()
                status.update(label="✅ Requirement Analysis and Specification Successful!", state="complete", expanded=False)
                st.subheader('View Agentic Workflow Outputs', anchor=False, divider="rainbow")
                st.info("This section allows you to view the outputs of the agentic workflow. Click the link below to access the Output Viewer Page.")
                st.page_link("pages/1_outputs_viewer.py", label="Output Viewer", icon="1️⃣")
    except Exception as e:
        st.error(f'Failed to run agents. Reason: {e}')
    
    # Remove uploaded input document(s)
    save_uploaded_files_path = "src/req_engineering_project/tools/data/inputs/"
    for file_name in os.listdir(save_uploaded_files_path):
        file_path = os.path.join(save_uploaded_files_path, file_name)
        try:
            os.remove(file_path)
        except Exception as e:
            st.error(f'Failed to delete {file_path}. Reason: {e}')
        st.toast("Uploaded document(s) removed from App.")

def main():
    setup_page()
    # Setting Langtrace for observability and evaluations
    langtrace.init(api_key=LANGTRACE_API_KEY)
    st.title("Requirement Analysis and Specification with LLM Agents")
    st.sidebar.info("Sidebar configuration will be enabled after meeting has been selected or uploaded.")
    upload_files = upload_meeting_notes()

    if upload_files:
        selected_llm, api_key, run_agents_button = sidebar_config(disabled=False)
        if run_agents_button:
            run_agentic_workflow(model_name=selected_llm, api_key=api_key)

if __name__ == "__main__":
    main()