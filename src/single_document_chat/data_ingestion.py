import uuid
from pathlib import Path
import sys
from datetime import datetime, timezone

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException
from utils.model_loader import ModelLoader


class SingleDocIngester:
    def __init__(self, data_dir: str = "data/single_document_chat", faiss_dir: str = "faiss_index"):
        try:
            self.log = CustomLogger().get_logger(__name__)

            self.data_dir = Path(data_dir)
            self.data_dir.mkdir(parents=True, exist_ok=True)

            self.faiss_dir = Path(faiss_dir)
            self.faiss_dir.mkdir(parents=True, exist_ok=True)

            self.model_loader = ModelLoader()

            self.log.info(
                "SingleDocIngester initialized",
                data_path=str(self.data_dir),
                faiss_path=str(self.faiss_dir)
            )

        except Exception as e:
            self.log.error("Failed to initialize SingleDocIngester", error=str(e))
            raise DocumentPortalException("Initialization error in SingleDocIngester", sys)

    def ingest_files(self, uploaded_files):
        try:
            documents = []

            for uploaded_file in uploaded_files:
                unique_filename = f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.pdf"
                temp_path = self.data_dir / unique_filename

                # Save file safely
                with open(temp_path, "wb") as f_out:
                    f_out.write(uploaded_file.read())

                # ✅ FIX: no .name dependency
                self.log.info("PDF saved for ingestion", file_path=str(temp_path))

                loader = PyPDFLoader(str(temp_path))
                docs = loader.load()
                documents.extend(docs)

            self.log.info("PDF files loaded", count=len(documents))

            return self._create_retriever(documents)

        except Exception as e:
            self.log.error("Document ingestion failed", error=str(e))
            raise DocumentPortalException("Error during file ingestion", sys)

    def _create_retriever(self, documents):
        try:
            # ✅ Better chunking
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=100
            )
            chunks = splitter.split_documents(documents)

            self.log.info("Documents split into chunks", count=len(chunks))

            embeddings = self.model_loader.load_embeddings()

            # ✅ FIX: merge instead of overwrite
            index_file = self.faiss_dir / "index.faiss"

            if index_file.exists():
                self.log.info("Existing FAISS index found. Merging new documents...")

                vectorstore = FAISS.load_local(
                    str(self.faiss_dir),
                    embeddings,
                    allow_dangerous_deserialization=True
                )

                vectorstore.add_documents(chunks)
                vectorstore.save_local(str(self.faiss_dir))

            else:
                self.log.info("No FAISS index found. Creating new index...")

                vectorstore = FAISS.from_documents(chunks, embeddings)
                vectorstore.save_local(str(self.faiss_dir))

            self.log.info("FAISS index ready", faiss_path=str(self.faiss_dir))

            retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )

            self.log.info("Retriever created successfully", type=str(type(retriever)))

            return retriever

        except Exception as e:
            self.log.error("Retriever creation failed", error=str(e))
            raise DocumentPortalException("Error creating FAISS retriever", sys)