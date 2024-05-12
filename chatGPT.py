import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

import pickle
from pathlib import Path
import streamlit_authenticator as stauth
import hashlib

# Set page configuration
st.set_page_config(page_title="Rate My Professor")

# ---  USER AUTHENTICATION ---
names = ["Nikki Aung","Zenith Oo"]
usernames = ["Nikki", "Zenith"]


file_path = Path(__file__).parent / "hashed_pw.pkl"
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

file_path = Path(__file__).parent / "hashed_sk.pkl"
with file_path.open("rb") as file:
    hashed_specialKey = pickle.load(file)

authenticator = stauth.Authenticate(names, usernames, hashed_passwords, 
            "CCSF_dashboard", "abcdef", cookie_expiry_days=3)

name, authentication_status , username = authenticator.login("Login", "main")

if authentication_status == "False":
    st.error("Username/password is incorrect")

if authentication_status == None:
    st.warning("Please enter your username and password")


if authentication_status:
    
    load_dotenv()
    os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    def get_pdf_text(pdf_docs):
        text = ""
        for pdf in pdf_docs:
            pdf_reader = PdfReader(pdf)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text

    def get_text_chunks(text):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
        chunks = text_splitter.split_text(text)
        return chunks

    def get_vector_store(text_chunks):
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
        vector_store.save_local("faiss_index")

    def load_vector_store():
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        return vector_store

    def handle_pdf_upload():
        pdf_docs = st.file_uploader("Upload your PDF Files and Click on the Submit & Process Button", accept_multiple_files=True)
        if st.button("Submit & Process"):
            with st.spinner("Processing..."):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                #get_vector_store(text_chunks)
                #st.success("Done")
                if text_chunks:  # Check if text_chunks is not empty
                    get_vector_store(text_chunks)
                    st.success("Done")
                else:
                    st.error("No text found in PDF files.")


    def get_conversational_chain():
        prompt_template = """
        Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
        provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
        Context:\n {context}?\n
        Question: \n{question}\n

        Answer:
        """
        model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
        prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
        chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
        return chain

    def user_input(user_question):
        new_db = load_vector_store()
        docs = new_db.similarity_search(user_question)
        chain = get_conversational_chain()
        response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
        st.write("Reply: ", response["output_text"])

    def main():
        st.header("Chat with PDF using Gemini💁")
        user_question = st.text_input("Ask a Question from the PDF Files")
        if user_question:
            user_input(user_question)
        with st.sidebar:
            authenticator.logout("Logout", "sidebar")
            st.title(f"Welcome {name}")
            st.title("Menu:")
            special_key_input = st.text_input("Enter the special access key")
    
            if special_key_input:
                hashed_input = hashlib.sha256(special_key_input.encode()).hexdigest()
                #print(hashed_input[0]) #$2b$12$.MJW0EYlESYjLqIsy/cfYOAkcHJfbe/.Wp7PHwiGKXAILn1QDssvC
                #print(hashed_specialKey[0]) #$2b$12$NdEYdpgImbIGyqp7WxLYAOObK4D8hE519vLyDjJhhUlabiWpcRwKO
                if hashed_input[0] == hashed_specialKey[0]:
                    handle_pdf_upload()
                else:
                    st.write("You do not have permission to upload PDF files")






    if __name__ == "__main__":
        main()
