import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader
from openai import OpenAI


load_dotenv() 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


# Step 1: Embedding model
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-4o-mini")

# Load documents (PDF + text FAQs)
pdf_loader1 = PyMuPDFLoader("finance_faq_extended.pdf")   # <--- Your PDF
pdf_loader2 = PyMuPDFLoader("sofi_top_products.pdf") 
pdf_docs = pdf_loader1.load() + pdf_loader2.load()
print("PDF docs:", len(pdf_docs))


faq_loader = TextLoader("faqs.txt")  
try:
    faq_docs = faq_loader.load()
    print("FAQ docs:", len(faq_docs))
except Exception:
    faq_docs = []


# Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
docs = splitter.split_documents(pdf_docs + faq_docs)
print("Total after split:", len(docs))

# Create Chroma vectorstore
if os.path.exists("chroma_store"):
    vectorstore = Chroma(persist_directory="chroma_store", embedding_function=embeddings)
    # Add new docs
    vectorstore.add_documents(docs)  # docs should include only the new PDFs
    vectorstore.persist()
else:
    vectorstore = Chroma.from_documents(docs, embeddings, persist_directory="chroma_store")

# Step 5: Create a Prompt Template
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are SofiBot, SoFi's personal financial assistant and a financial calculator.

Rules:
1. Retrieve information from the vector store if available; otherwise, fall back to a web search.
2. For questions involving calculations (e.g., loan EMI, interest rate, tenure, balances), compute the correct values using standard financial formulas. Show the calculation steps if possible.
3. If the answer is not in your documents or cannot be computed, respond: "I don't have that information."
4. Avoid hallucinating numbers, rates, or financial details.

Context:
{context}

Question: {question}

Answer:
"""
)

# Create RetrievalQA chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(),
    return_source_documents=True,
    chain_type_kwargs={"prompt": prompt_template}  # use our prompt template
)

def clean_response(text):
    # Remove extra newlines and leading/trailing spaces
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)

def ask_question(question: str):
    # Step 1: Ask the vectorstore (RAG)
    response = qa_chain.invoke({"query": question})
    answer = response["result"]
    
    # Step 2: If RAG has no answer, use Responses API with web_search tool
    if "I don't have that information" in answer or "I'm sorry" in answer:
        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=[{"role": "system",
                    "content": [{
                        "type": "input_text",
                        "text": " You are SofiBot, SoFi's personal SoFi's personal financial assistant and a financial calculator. Help user with the financial questions and calculation if required. Answer in concise bullets points"
                    }]},     
                    {
                        "role": "user",
                        "content": [{
                            "type": "input_text",
                            "text": question
                        }]
                    }],
            tools=[{"type": "web_search"}],
            temperature=0,
            top_p=0,
            max_output_tokens=300
        )
        # Extract text
        # Extract text from ResponseOutputMessage objects
        bullets = ""
        if resp.output:
            for item in resp.output:
                if item.type == "message":
                    for c in item.content:
                        if c.type == "output_text":
                            bullets += c.text + "\n"
        bullets = clean_response(bullets)
        return {"answer": bullets or "I couldn't find relevant info online.", "sources": ["OpenAI Web Search"]}
    # If docs answered the question
    return {
        "answer": response["result"],
        "sources": [doc.page_content for doc in response["source_documents"]],
    }
