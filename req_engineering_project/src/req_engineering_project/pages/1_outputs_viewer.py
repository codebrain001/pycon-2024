import streamlit as st
import os


def setup_page():
    # Add page title, page icon, and wide layout
    st.set_page_config(
        page_title="Outputs Viewer",
        page_icon="📝",
        layout="wide",
         menu_items={
            'Report a bug': "https://github.com/codebrain001/pycon-2024/issues",
            'About': "## This tool helps in automating and enhancing software requirement analysis and specification process."
        }
    )

def load_file_to_display(file_path):
    if file_path.endswith('.md'):
        with open(file_path, 'r') as file:
            return file.read()
    else:
        return "Unsupported file format."
    
def main(model_name):
    setup_page()
    st.header('Business Requirements Analysis and Specification Results')
    st.subheader(f'Derived from AI Agents 🤖 Powered by Model: {model_name}')
    base_path = f'src/req_engineering_project/tools/data/outputs/'
    files = [
        "meeting_profiling_documents.md",
        "market_research.md",
        "BRD_draft.md",
        "compliance_report.md",
        "final_BRD.md"
    ]
    for file_name in files:
        file_path = os.path.join(base_path, file_name)
        if os.path.exists(file_path):
            with st.expander(file_name):
                content = load_file_to_display(file_path)
                if file_name.endswith('.md'):
                    st.markdown(content)
                else:
                    st.write(content)
        else:
            st.warning(f"{file_name} does not exist in the specified path.")

if __name__ == "__main__":
    model_name = st.session_state.selected_llm
    if 'selected_llm' in st.session_state:
        model_name = st.session_state.selected_llm
        main(model_name)
    else:
        st.error("Model name not found in session state.")
        st.info('Initiate the agentic workflow and please wait for its completion. Once the workflow is finished, you can then access the output page to view the results.', icon="ℹ️")