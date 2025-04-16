import os
import glob
from langchain_community.document_loaders import PDFPlumberLoader
from bs4 import BeautifulSoup
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

class DocsScraper:
    BASE_PATH = os.path.join(os.getcwd())
    EXCEL_FILE_PATH = BASE_PATH + "\\data\\generales-banco.xlsx"
    DOCUMENTS_PATH = BASE_PATH + "\\data\\documents\\" 
    VECTOR_STORE_PATH = "./data/vector_store" 

    def __init__(self):
        self.pdf_content = []
        self.html_content = []                    
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text:latest",
                                           base_url="http://localhost:11434")
        self.chunk_size = 500
        self.chunk_overlap = 100
        
    def load_pdf(self, pdf_path):
        loader = PDFPlumberLoader(pdf_path)
        documents = loader.load()
        return documents

    def load_html(self, html_path):        
        #html_documents = []
        with open(html_path, 'r', encoding='utf-8') as file:
            content = file.read()    
            soup = BeautifulSoup(content, 'html.parser')    
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()    
            # Get text
            text_content = soup.get_text(separator=' ', strip=True)    
            # Create a Document object instead of a dictionary
            return text_content
            #html_documents.append(
            #    
            #    )
            #)                    

    def split_text(self, documents):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            # Prioritize splitting on these characters to preserve fee structure
            separators=["\n\n", "\n", ". ", ", ", " ", ""],
            # Keep table rows together
            keep_separator=True
        )        
        splits = text_splitter.split_documents(documents)
        return splits

    def save_to_vector_store(self, splits):        
        vector_store = Chroma.from_documents(
                documents=splits,
                embedding=self.embeddings,
                persist_directory=self.VECTOR_STORE_PATH
            )
        vector_store.persist()

    def process_documents(self, doc):
        file_extension = os.path.splitext(doc)[1].lower()            
        if file_extension == '.pdf':            
            self.pdf_content.extend(self.load_pdf(doc))
        elif file_extension in ['.html', '.htm']:            
            text_content = self.load_html(doc)
            self.html_content.append(Document(page_content=text_content,metadata={"source": doc, "file_type": "html"}))
        else:
            print(f"Unsupported file type: {file_extension} for {doc}")        
    
        
if __name__ == "__main__":
    print("Starting documents process...")
    scraper = DocsScraper()
    # Check if folder exists
    if not os.path.exists(scraper.DOCUMENTS_PATH):
        print(f"*** Folder not found: {scraper.DOCUMENTS_PATH} ***")
        exit(1)            
    # Use glob to get all files in the folder
    documents = glob.glob(os.path.join(scraper.DOCUMENTS_PATH, "*.*"))    
    if not documents:
        print(f"No documents found in {scraper.DOCUMENTS_PATH}")
        exit(1)
                            
    print(f"Found {len(documents)} documents at " + scraper.DOCUMENTS_PATH)    
    for doc in documents:
        scraper.process_documents(doc)    
    
    all_documents = scraper.pdf_content + scraper.html_content
    splits = scraper.split_text(all_documents)

    if(os.path.exists(scraper.VECTOR_STORE_PATH)):    
        scraper.save_to_vector_store(splits)
    else:
        print(f"*** Vector store path not found: {scraper.VECTOR_STORE_PATH} ***")
           
    print("All documents processed and saved to vector store.")