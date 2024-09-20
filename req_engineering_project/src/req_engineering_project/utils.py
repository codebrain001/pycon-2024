# This portion of the code is adapted from @AbubakrChan                  #
# https://github.com/AbubakrChan/crewai-UI-business-product-launch/blob/main/main.py

import streamlit as st
import re

class StreamToExpander:
    def __init__(self, expander):
        self.expander = expander
        self.buffer = []
        self.colors = ['red', 'green', 'yellow', 'brown', 'purple', 'black']

    def write(self, data):
        # Filter out ANSI escape codes using a regular expression
        cleaned_data = re.sub(r'\x1B\[[0-9;]*[mK]', '', data)
        
        # Check if the data contains 'task' information
        task_match_object = re.search(r'"task"\s*:\s*"(.*?)"', cleaned_data, re.IGNORECASE)
        task_match_input = re.search(r'task\s*:\s*([^\n]*)', cleaned_data, re.IGNORECASE)
        task_value = None
        if task_match_object:
            task_value = task_match_object.group(1)
        elif task_match_input:
            task_value = task_match_input.group(1).strip()

        if task_value:
            st.toast("🤖 " + task_value)

        # Check if the text contains the specified phrase and apply color
        if "Entering new CrewAgentExecutor chain" in cleaned_data:
            # Apply different color and switch color index
            self.color_index = (self.color_index + 1) % len(self.colors)  # Increment color index and wrap around if necessary

            cleaned_data = cleaned_data.replace("Entering new CrewAgentExecutor chain", f":{self.colors[self.color_index]}[Entering new CrewAgentExecutor chain]")


        # Apply emojis and formatting using adjusted patterns
        replacements = {
            r'^\s*#*\s*Agent:\s*(.*)': r'### 🔹 Agent: \1',
            r'^\s*#*\s*Task:\s*(.*)': r'#### 📝 Task: \1',
            r'^\s*#*\s*Thought:\s*(.*)': r'##### 🤖 Thought: \1',
            r'^\s*#*\s*Using tool:\s*(.*)': r'##### 🛠️ Using tool: \1',
            r'^\s*#*\s*Tool Input:\s*(.*)': r'##### 📥 Tool Input: \1',
            r'^\s*#*\s*Tool Output:\s*(.*)': r'##### 📊 Tool Output: \1',
        }

        for pattern, replacement in replacements.items():
            cleaned_data = re.sub(pattern, replacement, cleaned_data, flags=re.MULTILINE)

        # Apply color for agent roles using self.colors (may not render as expected)
        agent_roles = [
            "Senior Business Analyst",
            "Senior Market Researcher",
            "Senior Requirements Engineer",
            "GDPR Compliance Specialist",
            "Senior Quality Assurance Analyst",
            "Finished chain."
        ]

        for idx, role in enumerate(agent_roles):
            color = self.colors[idx % len(self.colors)]
            cleaned_data = cleaned_data.replace(
                role,
                f'<span style="color:{color};">{role}</span>'
            )        
    
        # Append data to buffer and output on newline
        self.buffer.append(cleaned_data)
        if "\n" in data:
            # Render using markdown with unsafe_allow_html=True to allow HTML/CSS
            self.expander.markdown(''.join(self.buffer), unsafe_allow_html=True)
            self.buffer = []
