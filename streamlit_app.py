import streamlit as st
import requests
import uuid
import re
import base64

# Hàm đọc nội dung từ file văn bản
def rfile(name_file):
    try:
        with open(name_file, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        st.error(f"File {name_file} không tồn tại.")

# Constants
BEARER_TOKEN = st.secrets.get("BEARER_TOKEN")
WEBHOOK_URL = rfile("WEBHOOK_URL.txt")

def generate_session_id():
    return str(uuid.uuid4())

def send_message_to_llm(session_id, message, filename=None, filecontent_b64=None):
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "sessionId": session_id,
        "chatInput": message,
    }
    if filename and filecontent_b64:
        payload["filename"] = filename
        payload["fileContent"] = filecontent_b64

    try:
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        try:
            content = response_data.get("content") or response_data.get("output")
            image_url = response_data.get('url', None)
            return content, image_url
        except:
            content = response_data[0].get("content") or response_data[0].get("output")
            image_url = response_data[0].get('url', None)
            return content, image_url
    except requests.exceptions.RequestException as e:
        return f"Error: Failed to connect to the LLM - {str(e)}", None

def main():
    st.set_page_config(page_title="Trợ lý AI", page_icon="🤖", layout="centered")

    st.markdown("""
        <style>
            .assistant {
                padding: 10px;
                border-radius: 10px;
                max-width: 75%;
                background: none;
                text-align: left;
                margin-bottom: 10px;
            }
            .user {
                padding: 10px;
                border-radius: 10px;
                max-width: 75%;
                background: none;
                text-align: right;
                margin-left: auto;
                margin-bottom: 10px;
            }
            .assistant::before { content: "🤖 "; font-weight: bold; }
            .user::before { content: " "; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    try:
        col1, col2, col3 = st.columns([3, 2, 3])
        with col2:
            st.image("logo.png")
    except:
        pass

    try:
        with open("00.xinchao.txt", "r", encoding="utf-8") as file:
            title_content = file.read()
    except Exception as e:
        title_content = "Trợ lý AI"

    st.markdown(f"""<h1 style="text-align: center; font-size: 24px;">{title_content}</h1>""", unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = generate_session_id()

    # File uploader
    uploaded_file = st.file_uploader("📎 Tải file văn bản hoặc dữ liệu cần xử lý", type=["pdf", "docx", "xlsx", "csv"])
    file_content_b64 = None
    file_name = None
    if uploaded_file:
        file_bytes = uploaded_file.read()
        file_content_b64 = base64.b64encode(file_bytes).decode("utf-8")
        file_name = uploaded_file.name
        st.success(f"✅ Đã tải lên: {file_name}")

    # Hiển thị lịch sử tin nhắn
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            st.markdown(f'<div class="assistant">{message["content"]}</div>', unsafe_allow_html=True)
            if "image_url" in message and message["image_url"]:
                st.markdown(
                    f"""
                    <a href="{message['image_url']}" target="_blank">
                        <img src="{message['image_url']}" alt="Biểu đồ" style="width: 100%; height: auto; margin-bottom: 10px;">
                    </a>
                    """,
                    unsafe_allow_html=True
                )
        elif message["role"] == "user":
            st.markdown(f'<div class="user">{message["content"]}</div>', unsafe_allow_html=True)

    if prompt := st.chat_input("Nhập nội dung cần trao đổi ở đây nhé?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.markdown(f'<div class="user">{prompt}</div>', unsafe_allow_html=True)

        with st.spinner("Đang chờ phản hồi từ AI..."):
            llm_response, image_url = send_message_to_llm(
                st.session_state.session_id, prompt,
                filename=file_name,
                filecontent_b64=file_content_b64
            )

        if isinstance(llm_response, str) and "Error" in llm_response:
            st.error(llm_response)
            st.session_state.messages.append({"role": "assistant", "content": llm_response, "image_url": None})
        else:
            st.markdown(f'<div class="assistant">{llm_response}</div>', unsafe_allow_html=True)
            if image_url:
                st.markdown(
                    f"""
                    <a href="{image_url}" target="_blank">
                        <img src="{image_url}" alt="Biểu đồ" style="width: 100%; height: auto; margin-bottom: 10px;">
                    </a>
                    """,
                    unsafe_allow_html=True
                )
            st.session_state.messages.append({"role": "assistant", "content": llm_response, "image_url": image_url})

        st.rerun()

if __name__ == "__main__":
    main()