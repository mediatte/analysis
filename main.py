import streamlit as st
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
from io import BytesIO
import openai
from dotenv import load_dotenv
import os
from PIL import Image
import base64
from datetime import datetime

# .env 파일에서 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv('OPENAI_API_KEY')

# PDF 파일을 처리하는 함수
def process_pdf(file):
    pdf_reader = PdfReader(file)
    num_pages = len(pdf_reader.pages)
    return f"Uploaded PDF has {num_pages} pages."

# PDF 파일을 이미지로 변환하는 함수
def pdf_to_images(file_bytes):
    images = convert_from_bytes(file_bytes)
    return images

# 현재 시간에 기반한 폴더를 생성하는 함수
def create_timestamped_folder():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    folder_path = f"images_{timestamp}"
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

# 이미지를 PNG로 저장하는 함수
def save_image_as_png(image, page_number, folder_path):
    image_path = os.path.join(folder_path, f"page_{page_number}.png")
    image.save(image_path, format="PNG")
    return image_path

# 이미지를 base64로 인코딩하는 함수
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# 이미지를 요약하는 함수
def summarize_image(image_base64):
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "한국의 20년차 영어교사로서 학생들의 수행평가를 읽고 교과세부능력특기사항을 작성해야 해."},
            {"role": "user", "content": [
                {"type": "text", "text": "이미지에 있는 텍스트는 한국 고등학생이 영어로 글을 작성한 것이야. 여기 학번이라는 칸 아래에 적힌 숫자 다섯자리를 적고 전체 내용에 기반하여 세부능력특기사항을 ~음,~함 이라는 문체로 500자 이내로 작성해줘."},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{image_base64}"}
                }  
            ]}
        ],
        temperature=0.0,
    )
    summary = response.choices[0].message['content'].strip()
    return summary

# 이미지를 Streamlit에서 표시하는 함수
def display_images_and_summaries(images, summaries):
    for i, (img, summary) in enumerate(zip(images, summaries)):
        st.image(img, caption=f"Page {i+1}", use_column_width=True)
        st.text_area(f"Summary for Page {i+1}", value=summary, height=200)

# 인터페이스 생성
def create_interface():
    st.title("Upload PDF and Get GPT-4 Summary")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        with st.spinner("Processing..."):
            # 파일을 BytesIO로 변환
            file_bytes = uploaded_file.read()
            file = BytesIO(file_bytes)
            result = process_pdf(file)
            st.write(result)
            
            # PDF 파일을 이미지로 변환
            images = pdf_to_images(file_bytes)
            
            # 타임스탬프 기반 폴더 생성
            folder_path = create_timestamped_folder()
            
            # 각 이미지에서 요약 생성
            summaries = []
            for i, image in enumerate(images):
                image_path = save_image_as_png(image, i + 1, folder_path)
                image_base64 = image_to_base64(image_path)
                summary = summarize_image(image_base64)
                summaries.append(summary)
            
            # 이미지와 요약문을 웹페이지에 표시
            display_images_and_summaries(images, summaries)

# 웹 인터페이스 실행
if __name__ == "__main__":
    create_interface()
