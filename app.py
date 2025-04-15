import streamlit as st
#from chatbot_core import get_gpt_response, call_function, get_tools, int_prompt
from chatbot_core_AWS import get_gpt_response, call_function, get_tools, int_prompt
import json

st.set_page_config(page_title="BiteBuddy 🍏", page_icon="🥗")
st.title("BiteBuddy - Your Nutrition Assistant Chatbot")

# Initialize session state
if "conversation" not in st.session_state:
    st.session_state.conversation = [{"role": "system", "content": int_prompt}]
    st.session_state.chat_ended = False
    st.session_state.exit_message = ""

tools = get_tools()

# Show chat history
for msg in st.session_state.conversation[1:]:  # skip system prompt
    if msg["role"] == "user":
        st.chat_message("user").markdown(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").markdown(msg["content"])

# Show final goodbye message if chat ended
if st.session_state.chat_ended:
    st.markdown(f"**BiteBuddy:** {st.session_state.exit_message}")
else:
    user_input = st.chat_input("You:")

    if user_input:
        # Add user message to conversation
        st.chat_message("user").markdown(user_input)
        st.session_state.conversation.append({"role": "user", "content": user_input})

        # Check if user said "exit"
        if user_input.strip().lower() == "exit":
            st.session_state.exit_message = "Goodbye! 👋 Stay healthy!"
            st.session_state.chat_ended = True
            st.markdown(f"**BiteBuddy:** {st.session_state.exit_message}")
        else:
            # Get initial GPT response and tool calls
            response, tool_calls = get_gpt_response(st.session_state.conversation, tools)

            if tool_calls:
                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    # Append tool_call to history
                    st.session_state.conversation.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(tool_args)
                            }
                        }]
                    })

                    # Call function and add tool result
                    result = str(call_function(tool_name, tool_args))
                    st.session_state.conversation.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })

                # Get final GPT response after tool call
                response, _ = get_gpt_response(st.session_state.conversation, tools)

            if response:
                st.chat_message("assistant").markdown(response)
                st.session_state.conversation.append({"role": "assistant", "content": response})
