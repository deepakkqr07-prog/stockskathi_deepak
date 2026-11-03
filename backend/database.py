"""
StockSathi Database Layer
Supports native MongoDB via PyMongo with automatic seamless persistence
fallback if local MongoDB server is not running.
"""

import json
import os
import re
import uuid
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import pymongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from backend.config import config

class InsertOneResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id

class UpdateResult:
    def __init__(self, matched_count: int, modified_count: int, upserted_id=None):
        self.matched_count = matched_count
        self.modified_count = modified_count
        self.upserted_id = upserted_id

class DeleteResult:
    def __init__(self, deleted_count: int):
        self.deleted_count = deleted_count

class JSONDocumentCollection:
    """A MongoDB-compatible collection backed by local JSON file storage."""
    
    def __init__(self, collection_name: str, storage_dir: Path):
        self.name = collection_name
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.storage_dir / f"{collection_name}.json"
        self._documents: List[Dict[str, Any]] = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self._documents, f, default=str, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[DB] Error saving collection {self.name}: {e}")

    def _matches(self, doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
        if not query:
            return True
        for key, value in query.items():
            if key == "$or" and isinstance(value, list):
                if not any(self._matches(doc, cond) for cond in value):
                    return False
                continue
            if key == "$and" and isinstance(value, list):
                if not all(self._matches(doc, cond) for cond in value):
                    return False
                continue
            
            # Nested fields or operators
            doc_val = doc.get(key)
            if isinstance(value, dict):
                for op, op_val in value.items():
                    if op == "$eq" and doc_val != op_val:
                        return False
                    elif op == "$ne" and doc_val == op_val:
                        return False
                    elif op == "$gt" and (doc_val is None or doc_val <= op_val):
                        return False
                    elif op == "$gte" and (doc_val is None or doc_val < op_val):
                        return False
                    elif op == "$lt" and (doc_val is None or doc_val >= op_val):
                        return False
                    elif op == "$lte" and (doc_val is None or doc_val > op_val):
                        return False
                    elif op == "$in" and doc_val not in op_val:
                        return False
                    elif op == "$nin" and doc_val in op_val:
                        return False
                    elif op == "$regex":
                        pattern = op_val
                        flags = 0
                        if "$options" in value and "i" in value["$options"]:
                            flags = re.IGNORECASE
                        if not doc_val or not re.search(pattern, str(doc_val), flags):
                            return False
            else:
                if str(doc_val) != str(value) and doc_val != value:
                    return False
        return True

    def insert_one(self, document: Dict[str, Any]) -> InsertOneResult:
        doc = dict(document)
        if "_id" not in doc or not doc["_id"]:
            doc["_id"] = str(uuid.uuid4())
        else:
            doc["_id"] = str(doc["_id"])
        
        # Add timestamps if not present
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if "created_at" not in doc:
            doc["created_at"] = now
        if "updated_at" not in doc:
            doc["updated_at"] = now
            
        self._documents.append(doc)
        self._save()
        return InsertOneResult(doc["_id"])

    def insert_many(self, documents: List[Dict[str, Any]]):
        ids = []
        for doc in documents:
            res = self.insert_one(doc)
            ids.append(res.inserted_id)
        return ids

    def find_one(self, query: Optional[Dict[str, Any]] = None, projection: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        query = query or {}
        for doc in self._documents:
            if self._matches(doc, query):
                return self._apply_projection(doc, projection)
        return None

    def find(self, query: Optional[Dict[str, Any]] = None, projection: Optional[Dict[str, Any]] = None, sort: Optional[List] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        query = query or {}
        results = [doc for doc in self._documents if self._matches(doc, query)]
        
        if sort:
            # e.g. [("created_at", -1)]
            for key, direction in reversed(sort):
                reverse = direction < 0
                results.sort(key=lambda d: str(d.get(key, "")), reverse=reverse)
                
        if limit and limit > 0:
            results = results[:limit]
            
        return [self._apply_projection(doc, projection) for doc in results]

    def _apply_projection(self, doc: Dict[str, Any], projection: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not projection:
            return dict(doc)
        projected = {}
        include_keys = [k for k, v in projection.items() if v]
        if include_keys:
            if "_id" not in projection or projection["_id"] != 0:
                projected["_id"] = doc.get("_id")
            for k in include_keys:
                if k in doc:
                    projected[k] = doc[k]
            return projected
        else:
            # Exclusion projection
            exclude_keys = [k for k, v in projection.items() if not v]
            projected = dict(doc)
            for k in exclude_keys:
                projected.pop(k, None)
            return projected

    def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False) -> UpdateResult:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        for idx, doc in enumerate(self._documents):
            if self._matches(doc, query):
                updated_doc = dict(doc)
                if "$set" in update:
                    for k, v in update["$set"].items():
                        updated_doc[k] = v
                if "$inc" in update:
                    for k, v in update["$inc"].items():
                        updated_doc[k] = updated_doc.get(k, 0) + v
                if "$unset" in update:
                    for k in update["$unset"].keys():
                        updated_doc.pop(k, None)
                
                updated_doc["updated_at"] = now
                self._documents[idx] = updated_doc
                self._save()
                return UpdateResult(matched_count=1, modified_count=1)
        
        if upsert:
            new_doc = {}
            if "$set" in update:
                new_doc.update(update["$set"])
            for k, v in query.items():
                if not k.startswith("$") and k not in new_doc:
                    new_doc[k] = v
            res = self.insert_one(new_doc)
            return UpdateResult(matched_count=0, modified_count=1, upserted_id=res.inserted_id)
            
        return UpdateResult(matched_count=0, modified_count=0)

    def update_many(self, query: Dict[str, Any], update: Dict[str, Any]) -> UpdateResult:
        matched = 0
        modified = 0
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        for idx, doc in enumerate(self._documents):
            if self._matches(doc, query):
                matched += 1
                updated_doc = dict(doc)
                if "$set" in update:
                    for k, v in update["$set"].items():
                        updated_doc[k] = v
                if "$inc" in update:
                    for k, v in update["$inc"].items():
                        updated_doc[k] = updated_doc.get(k, 0) + v
                updated_doc["updated_at"] = now
                self._documents[idx] = updated_doc
                modified += 1
        if modified > 0:
            self._save()
        return UpdateResult(matched_count=matched, modified_count=modified)

    def delete_one(self, query: Dict[str, Any]) -> DeleteResult:
        for idx, doc in enumerate(self._documents):
            if self._matches(doc, query):
                del self._documents[idx]
                self._save()
                return DeleteResult(deleted_count=1)
        return DeleteResult(deleted_count=0)

    def delete_many(self, query: Dict[str, Any]) -> DeleteResult:
        initial_len = len(self._documents)
        self._documents = [doc for doc in self._documents if not self._matches(doc, query)]
        deleted = initial_len - len(self._documents)
        if deleted > 0:
            self._save()
        return DeleteResult(deleted_count=deleted)

    def count_documents(self, query: Optional[Dict[str, Any]] = None) -> int:
        query = query or {}
        return sum(1 for doc in self._documents if self._matches(doc, query))

    def create_index(self, *args, **kwargs):
        pass


class DatabaseManager:
    """Manages database connection, providing Mongo or JSON collection access."""
    
    def __init__(self):
        self.is_live_mongo = False
        self.client = None
        self.db = None
        self._json_collections = {}
        self.initialize_connection()

    def initialize_connection(self):
        try:
            # Test Mongo connection with short timeout
            client = pymongo.MongoClient(config.MONGODB_URI, serverSelectionTimeoutMS=1500)
            client.admin.command('ping')
            self.client = client
            self.db = client[config.DATABASE_NAME]
            self.is_live_mongo = True
            print(f"[DB] Successfully connected to live MongoDB at {config.MONGODB_URI} (DB: {config.DATABASE_NAME})")
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
            self.is_live_mongo = False
            self.client = None
            self.db = None
            print(f"[DB] Live MongoDB not reachable ({e}). Using embedded persistent document store ({config.DATA_DIR})")

    def get_collection(self, collection_name: str):
        if self.is_live_mongo and self.db is not None:
            return self.db[collection_name]
        
        if collection_name not in self._json_collections:
            self._json_collections[collection_name] = JSONDocumentCollection(
                collection_name, config.DATA_DIR
            )
        return self._json_collections[collection_name]

db_manager = DatabaseManager()

def get_db_collection(name: str):
    return db_manager.get_collection(name)
