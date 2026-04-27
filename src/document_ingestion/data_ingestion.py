from __future__ import annotations
import os
import sys
import json
import uuid
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from typing import Iterable,List,Dict,Optional,Any

from langchain_core.documents import Document
import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader,Docx2txtLoader,TextLoader
from langchain_community.vectorstores import FAISS

from utils.model_loader import ModelLoader
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException

class FaissManager:
    def __init__(self):
        pass
    def _exists(self):
        pass
    @staticmethod
    def _fingerprint(self):
        pass
    def _save_meta(self):
        pass
    def add_documents(self):
        pass
    def load_or_create(self):
        pass
class DocHandler:
    def __init__(self):
        pass
    def save_pdf(self):
        pass
    def read_pdf(self):
        pass
class DocumentComperator:
    def __init__(self):
        pass
    def save_uploaded_file(self):
        pass
    def read_pdf(self):
        pass
    def combine_documents(self):
        pass
    def clean_old_session(self):
        pass
class ChatIngestor:
    def __init__(self):
        pass
    def _resolve_dir(self):
        pass
    def _split(self):
        pass
    def built_retriever(self):
        pass