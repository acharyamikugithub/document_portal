import sys
import os
from dotenv import load_dotenv
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.vectorstores import FAISS
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_classic.chains import create_retrieval_chain,create_history_aware_retriever
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from utils.model_loader import ModelLoader
from exception.custom_exception import DocumentPortalException
from logger.custom_logger import CustomLogger
from prompt.prompt_library import PROMPT_REGISTRY
from model.models import PromptType

class ConversationalRAG:
    def __init__(self,session_id,retriever):
        try:
            self.log=CustomLogger().get_logger(__name__)
            self.session_id=session_id
            self.retriever=retriever
            self.llm=self._load_llm
            self.contextualize_prompt=PROMPT_REGISTRY[PromptType.CONTEXTUALIZE_QUESTION.value]
            self.qa_prompt=PROMPT_REGISTRY[PromptType.CONTEXT_QA.value]
            self.history_aware_retriever=create_history_aware_retriever(
                    self.llm,self.retriever,self.contextualize_prompt
                )   
            self.log.info("crated history aware retriever successfully",session_id=session_id)
            self.qa_chain=create_stuff_documents_chain(self.llm,self.qa_prompt)
            self.rag_chain=create_retrieval_chain(self.history_aware_retriever,self.qa_chain)
            self.log.info("Created RAG chain successfully",session_id=session_id)
            self.chain=RunnableWithMessageHistory(
                    self.rag_chain,
                    self._get_session_history,
                    input_messages_key="input",
                    history_messages_key="chat_history",
                    output_messages_key="answer"
                    )
            self.log.info("Created Runnablewithmessagehistory",session_id=session_id)

        except Exception as e:
            self.log.error("Error intializing ConversationRAG",error=str(e),session_id=session_id)
            raise DocumentPortalException("Failed to intialize ConversationalRAG",sys)
    def _load_llm(self):
        try:
            llm=ModelLoader.load_llm()
            self.log.info("Loaded LLM successfully",class_name=self.__class__.__name__)
            return llm
        except Exception as e:
            self.log.error("Error loading llm via ModelLoader",error=str(e))
            raise DocumentPortalException("Failed to load LLM",sys)
    def _get_session_history(self):
        try:
            pass
        except Exception as e:
            self.log.error("Error retrieving session history",error=str(e))
            raise DocumentPortalException("Failed to retrieve session history",sys)
    def load_retriever_from_faiss(self,index_path: str):
        try:
            embeddings=ModelLoader.load_embeddings()
            if not os.path.isdir(index_path):
                raise FileNotFoundError(f"FAISS index directory not found at {index_path}")
            vectorestore=FAISS.load_local(index_path,embeddings)
            self.log.info("Loaded FAISS retriever successfully from path",index_path=index_path)
            return vectorestore.as_retriever(search_type="similarity",search_kwargs={"k":5})

        except Exception as e:
            self.log.error("Failed to load retriever from FAISS",error=str(e))
            raise DocumentPortalException("Error loading retriever from FAISS",sys)
    def invoke(self,user_input: str)->str:
        try:
            response=self.chain.invoke({"input":user_input},config={"session_id":self.session_id})
            answer=response.get("answer","No Answer")
            if not answer:
                self.log.warning("RAG chain returned empty answer",session_id=self.session_id)
            self.log.info("RAG chain invoked successfully",session_id=self.session_id,user_input=user_input,answer_preview=answer[:150])
            return answer
        except Exception as e:
            self.log.error("Failed to invoke conversational RAG",error=str(e),session_id=self.session_id)
            raise DocumentPortalException("Failed to invoke RAG chain",sys)