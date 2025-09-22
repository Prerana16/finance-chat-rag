import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA,  LLMChain
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
You are SofiBot, SoFi's personal financial assistant. You have expert knowledge of SoFi's products, banking, loans, investments, credit cards, interest rates, and company policies.

Rules:
1. Always respond in a helpful, clear, and professional manner.
2. If the answer is not in your documents or sources, say: "I don't have that information."

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

# Step 4: Summarization prompt for DuckDuckGo results
ddg_summary_prompt = PromptTemplate(
    input_variables=["search_results", "question"],
    template="""
        You are SofiBot, SoFi's personal financial assistant. Summarize the following web search results to answer the user's question. Only include finance-related information. If nothing relevant is found, say "I don't have that information."


    Search results:
    {search_results}

    Question: {question}

    Answer:
    """
)
summary_chain = LLMChain(llm=llm, prompt=ddg_summary_prompt)
def ask_question(question: str):
    # Step 1: Ask the vectorstore (RAG)
    response = qa_chain.invoke({"query": question})
    answer = response["result"]

    #  # Step 2: If not found in vectorstore, ask GPT directly
    # if "I'm sorry, I don't have that information" in answer:
    #     prompt = f"""
    #     You are SofiBot, SoFi's personal financial assistant.
    #     Answer the following question as accurately as possible using your knowledge.
    #     Format your answer as bullet points using hyphens (-) instead of HTML.

    #     Question: {question}

    #     Answer:
    #     """
    #     direct_answer = llm.invoke([{"role": "user", "content": prompt}])
    #     return {
    #         "answer": direct_answer.content,
    #         "sources": ["OpenAI GPT fallback"]
    #     }

    # Step 2: If RAG has no answer, use Responses API with web_search tool
    if "I don't have that information" in answer or "I'm sorry" in answer:
        resp = client.responses.create(
            model="gpt-4.1-mini",
            input=[{"role": "system",
                    "content": [{
                        "type": "input_text",
                        "text": "Act as financial assitant and Answer the questions in short bullets"
                    }]},     
                    {
                        "role": "user",
                        "content": [{
                            "type": "input_text",
                            "text": question
                        }]
                    }],
            tools=[{"type": "web_search"}],
            temperature=0.2,
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
        return {"answer": bullets.strip() or "I couldn't find relevant info online.", "sources": ["OpenAI Web Search"]}
    # If docs answered the question
    return {
        "answer": response["result"],
        "sources": [doc.page_content for doc in response["source_documents"]],
    }
