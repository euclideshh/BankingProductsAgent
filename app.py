# streamlit_app.py
import streamlit as st
import requests
import json

# API endpoints
AGENT_APIS = {
    "langchain": {
        "name": "Experto en Productos Bancarios Panameños",
        "url": "http://localhost:8001",
        "description": "Un experto en productos bancarios panameños que responde en español (LangChain)"
    },
    "crewai": {
        "name": "Banking Analyst Team",
        "url": "http://localhost:8002",  # You'll implement this API separately
        "description": "A team of AI banking analysts that work together to answer questions (CrewAI)"
    }
}

# Set page configuration
st.set_page_config(page_title="Banking Agents", page_icon="🏦")
st.title("Banking Agents Chat")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "current_agent" not in st.session_state:
    st.session_state.current_agent = None

# Function to create a new session with selected agent
def create_session(agent_type):
    try:
        api_url = AGENT_APIS[agent_type]["url"]
        response = requests.post(f"{api_url}/session", json={})
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.session_id = data["session_id"]
            st.session_state.current_agent = agent_type
            # Clear messages when switching agents
            st.session_state.messages = []
            return True
        else:
            st.error(f"Failed to create session: {response.status_code}")
            return False
    except Exception as e:
        st.error(f"Failed to connect to agent API: {e}")
        return False

# Sidebar for agent selection
with st.sidebar:
    st.header("Select Banking Agent")
    
    # Create a selectbox with agent options
    agent_options = {agent["name"]: agent_id for agent_id, agent in AGENT_APIS.items()}
    selected_agent_name = st.selectbox(
        "Choose an agent:",
        options=list(agent_options.keys())
    )
    selected_agent_id = agent_options[selected_agent_name]
    
    # Show agent description
    st.info(AGENT_APIS[selected_agent_id]["description"])
    
    # Button to select/change agent
    if st.button("Connect to Agent"):
        if create_session(selected_agent_id):
            st.success(f"Connected to {selected_agent_name}")

# Main chat interface
if st.session_state.session_id and st.session_state.current_agent:
    # Display current agent
    current_agent_info = AGENT_APIS[st.session_state.current_agent]
    st.subheader(f"Chatting with: {current_agent_info['name']}")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Type your question here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Send message to API
        try:
            api_url = current_agent_info["url"]
            response = requests.post(
                f"{api_url}/chat",
                json={
                    "session_id": st.session_state.session_id,
                    "message": prompt
                }
            )
            
            if response.status_code == 200:
                # Display assistant response
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = response.json()["response"]
                    message_placeholder.markdown(full_response)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                st.error(f"Error from agent API: {response.status_code}")
                
        except Exception as e:
            st.error(f"Error communicating with the agent: {e}")
else:
    st.info("Please select a banking agent from the sidebar to start a conversation")

# Display API status in the sidebar
with st.sidebar:
    st.subheader("API Status")
    for agent_id, agent in AGENT_APIS.items():
        try:
            response = requests.get(f"{agent['url']}/info", timeout=1)
            if response.status_code == 200:
                st.success(f"✅ {agent['name']}: Online")
            else:
                st.warning(f"⚠️ {agent['name']}: Error ({response.status_code})")
        except:
            st.error(f"❌ {agent['name']}: Offline")