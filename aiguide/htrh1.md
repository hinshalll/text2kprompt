import streamlit as st
import os
import base64
import requests
import fitz  # PyMuPDF
import json
import tempfile

# --- Setup & API ---
MODEL_NAME = "qwen3.5:4b"
OLLAMA_API_URL = "http://localhost:11434/api/chat"
OLLAMA_BASE_URL = "http://localhost:11434"

st.set_page_config(page_title="RAG PDF Cleaner", layout="centered", page_icon="??")

# --- DIAGNOSTIC ENGINE ---
def run_system_check():
    """Pings the local system to ensure all dependencies and AI models are ready."""
    results = []
    all_clear = True
    
    # 1. Check PyMuPDF Library
    try:
        import fitz
        results.append({"msg": "PyMuPDF (PDF Engine) is installed and active.", "status": "success"})
    except ImportError:
        results.append({"msg": "PyMuPDF is missing! Run 'pip install pymupdf' in CMD.", "status": "error"})
        all_clear = False

    # 2. Check Ollama Server Connection
    try:
        response = requests.get(OLLAMA_BASE_URL, timeout=2)
        if response.status_code == 200:
            results.append({"msg": "Ollama Server is running online.", "status": "success"})
        else:
            results.append({"msg": f"Ollama returned unexpected code: {response.status_code}", "status": "warning"})
            all_clear = False
    except requests.ConnectionError:
        results.append({"msg": "Ollama Server is OFFLINE. Open CMD and type 'ollama serve'.", "status": "error"})
        return results, False # Stop checking if server is totally dead

    # 3. Check if Qwen 3.5 4B is actually downloaded
    try:
        tags_response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        models = [model['name'] for model in tags_response.json().get('models', [])]
        if MODEL_NAME in models:
            results.append({"msg": f"AI Model '{MODEL_NAME}' is loaded and ready.", "status": "success"})
        else:
            results.append({"msg": f"Model '{MODEL_NAME}' is missing! Open CMD and type 'ollama pull {MODEL_NAME}'.", "status": "error"})
            all_clear = False
    except Exception as e:
        results.append({"msg": f"Could not verify models: {e}", "status": "warning"})
        all_clear = False

    return results, all_clear

# --- CORE LOGIC ---
def extract_page_text_from_json(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    page_text_map = {}
    def search_nodes(node, current_page=None):
        if isinstance(node, dict):
            page = node.get("page_idx", node.get("page_no", current_page))
            text = node.get("text", "")
            if text and page is not None:
                if page not in page_text_map:
                    page_text_map[page] = []
                page_text_map[page].append(text)
            for k, v in node.items():
                search_nodes(v, page)
        elif isinstance(node, list):
            for item in node:
                search_nodes(item, current_page)
    search_nodes(json_data)
    return {page: "\n".join(texts) for page, texts in page_text_map.items()}

def clean_page_with_qwen(image_base64, dirty_text):
    system_prompt = f"""You are a strict data restoration AI for a RAG database. Look at the image of the PDF page and the MinerU OCR text.
    RULES:
    1. CHARTS: If there is an astrology Kundli/grid chart, ignore the OCR formatting. Read the chart from the image and write a clean Markdown table.
    2. MULTILINGUAL: Restore broken Devanagari script (Hindi/Sanskrit) and numerals (?, ?, ?) exactly as they appear. Do not translate.
    3. CLEANUP: Correct typos, skip decorative borders, and enforce Markdown headers (##).
    4. OUTPUT ONLY the cleaned Markdown text.
    
    ROUGH MINER-U TEXT:
    ---
    {dirty_text}
    ---
    """
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": system_prompt, "images": [image_base64]}],
        "stream": False,
        "options": {"temperature": 0.1, "num_ctx": 4096} 
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        return response.json()["message"]["content"].strip()
    except Exception as e:
        return f"\n[ERROR: {e}]\n"

# --- SIDEBAR: SYSTEM DIAGNOSTICS ---
with st.sidebar:
    st.header("??? System Diagnostics")
    st.write("Check if your offline AI engine is ready before uploading heavy files.")
    
    if st.button("?? Run System Check", type="primary", use_container_width=True):
        with st.spinner("Pinging local hardware..."):
            results, all_clear = run_system_check()
            
            for res in results:
                if res["status"] == "success":
                    st.success(res["msg"])
                elif res["status"] == "error":
                    st.error(res["msg"])
                else:
                    st.warning(res["msg"])
                    
            if all_clear:
                st.balloons()
                st.success("?? ALL SYSTEMS GO! You are ready to process.")
            else:
                st.error("?? SYSTEM ERROR. Please fix the red issues above before starting.")

# --- MAIN UI ---
st.title("?? RAG PDF Cleaner & Weaver")
st.markdown("Upload your split MinerU files. Verify the sequence, then click process.")

uploaded_files = st.file_uploader("Select PDF and JSON files (Drag and drop all parts at once)", accept_multiple_files=True)

if uploaded_files:
    file_groups = {}
    for file in uploaded_files:
        base = os.path.splitext(file.name)[0]
        ext = os.path.splitext(file.name)[1].lower()
        if base not in file_groups:
            file_groups[base] = {'pdf': None, 'json': None}
        if ext == '.pdf':
            file_groups[base]['pdf'] = file
        elif ext == '.json':
            file_groups[base]['json'] = file

    valid_pairs = {k: v for k, v in file_groups.items() if v['pdf'] and v['json']}
    current_bases = sorted(valid_pairs.keys())

    if not valid_pairs:
        st.error("?? Please upload matching PDF and JSON pairs.")
    else:
        if "prev_bases" not in st.session_state or st.session_state.prev_bases != current_bases:
            st.session_state.sequence = current_bases
            st.session_state.prev_bases = current_bases

        st.subheader("??? Verify File Sequence")
        for i, base in enumerate(st.session_state.sequence):
            col1, col2, col3 = st.columns([6, 1, 1])
            col1.info(f"**Part {i+1}:** {base}")
            if col2.button("??", key=f"up_{i}") and i > 0:
                st.session_state.sequence[i], st.session_state.sequence[i-1] = st.session_state.sequence[i-1], st.session_state.sequence[i]
                st.rerun()
            if col3.button("??", key=f"down_{i}") and i < len(st.session_state.sequence) - 1:
                st.session_state.sequence[i], st.session_state.sequence[i+1] = st.session_state.sequence[i+1], st.session_state.sequence[i]
                st.rerun()

        st.divider()

        if st.button("?? Start Processing", type="primary", use_container_width=True):
            final_markdown_content = ""
            progress_bar = st.progress(0)
            status_text = st.empty()

            with tempfile.TemporaryDirectory() as temp_dir:
                for index, base_name in enumerate(st.session_state.sequence):
                    pdf_file = valid_pairs[base_name]['pdf']
                    json_file = valid_pairs[base_name]['json']
                    
                    temp_pdf_path = os.path.join(temp_dir, pdf_file.name)
                    temp_json_path = os.path.join(temp_dir, json_file.name)
                    
                    with open(temp_pdf_path, "wb") as f: f.write(pdf_file.getbuffer())
                    with open(temp_json_path, "wb") as f: f.write(json_file.getbuffer())

                    status_text.text(f"Mapping layout for: {base_name}...")
                    page_text_map = extract_page_text_from_json(temp_json_path)
                    
                    doc = fitz.open(temp_pdf_path)
                    total_pages = len(doc)
                    
                    for page_num in range(total_pages):
                        status_text.text(f"Processing {base_name} | Page {page_num + 1} of {total_pages}...")
                        
                        page = doc[page_num]
                        pix = page.get_pixmap(dpi=150)
                        img_base64 = base64.b64encode(pix.tobytes("png")).decode('utf-8')
                        
                        dirty_text = page_text_map.get(page_num, "[No text extracted]")
                        clean_md = clean_page_with_qwen(img_base64, dirty_text)
                        
                        final_markdown_content += f"\n\n\n\n" + clean_md
                        
                        current_overall_progress = (index / len(st.session_state.sequence)) + ((page_num + 1) / total_pages) * (1 / len(st.session_state.sequence))
                        progress_bar.progress(min(current_overall_progress, 1.0))
                        
                    doc.close()

            status_text.success("? All batches complete! The files have been successfully stitched in your chosen order.")
            st.download_button(
                label="?? Download Master Markdown File",
                data=final_markdown_content,
                file_name="FINAL_MASTER_BOOK.md",
                mime="text/markdown",
                use_container_width=True
            )