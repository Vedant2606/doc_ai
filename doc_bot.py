import streamlit as st
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()

#Setup LLM
os.environ['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY')
FAISS_PATH  = "vectorstore/db_faiss"
@st.cache_resource

def get_vectorstore():
     embedding_model= HuggingFaceEmbeddings(model_name = "sentence-transformers/all-MiniLM-L6-v2")
     db =  FAISS.load_local(FAISS_PATH, embedding_model, allow_dangerous_deserialization=True)
     return db

def set_custom_prompt(custom_prompt_template):
    prompt = PromptTemplate(template= custom_prompt_template, input_variables=['context', 'question'])
    return prompt

llm = ChatGroq(
    model="llama3-8b-8192",
    temperature=0.5,
    model_kwargs={"top_p": 0.9, "frequency_penalty": 0.2}
)

def main():
    st.title('Ask Chatbot!')

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
            st.chat_message(message['role']).markdown(message['content'])

    prompt = st.chat_input("Pass your prompt here: ")

    if prompt:
        st.chat_message('User').markdown(prompt)
        st.session_state.messages.append({'role':'user', 'content': prompt})
        custom_prompt_template= """
            Use the pieces of information provided in the context to answer user's question.
            If you dont know the answer, just say that you dont know, dont try to make up an answer. 
            Dont provide anything out of the given context
            Context: {context}
            Question: {question}
            
            Start the answer directly. No small talk please.
            """
        

        try:
            vectorstore= get_vectorstore()
            if vectorstore is None:
                st.error("Failed to load the vector store")
        
            qa_chain = RetrievalQA.from_chain_type(
            llm= llm, 
            chain_type = 'stuff',
            retriever= vectorstore.as_retriever(search_kwargs = {'k':3}),
            return_source_documents= True,
            chain_type_kwargs = {'prompt': set_custom_prompt(custom_prompt_template)}
            )

            response = qa_chain.invoke({'query': prompt})
            result = response['result']
            source_documents = response['source_documents']
            result_to_show = result+'\n\nSource Docs'+str(source_documents)
            #response = "Hi! Welcome to docbot"
            st.chat_message('assistant').markdown(result_to_show)
            st.session_state.messages.append({'role':'assistant', 'content': result_to_show})
        except Exception as e:
             st.error(f"Error: {str(e)}")
if __name__ == '__main__':
    main()