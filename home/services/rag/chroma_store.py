class ProductChromaStore:
    def __init__(self, persist_directory, collection_name, embedding_model, ollama_base_url):
        self._enabled = True
        self._collection = None

        try:
            import chromadb
            from chromadb.config import Settings
            from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
        except ImportError:
            self._enabled = False
            return

        try:
            embedder = OllamaEmbeddingFunction(
                url=ollama_base_url,
                model_name=embedding_model,
            )
            client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False),
            )
            self._collection = client.get_or_create_collection(
                name=collection_name,
                embedding_function=embedder,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception:
            self._enabled = False

    @property
    def is_available(self):
        return self._enabled and self._collection is not None

    def upsert_products(self, products):
        if not self.is_available:
            return

        ids = []
        documents = []
        metadatas = []

        for product in products:
            ids.append(f"product-{product.id}")
            documents.append(
                " | ".join(
                    [
                        f"name: {product.name}",
                        f"category: {product.get_category_display()}",
                        f"brand: {product.brand}",
                        f"description: {product.description}",
                        f"unit: {product.measurement_unit}",
                    ]
                )
            )
            metadatas.append(
                {
                    "product_id": int(product.id),
                    "category": str(product.category),
                    "brand": str(product.brand or ""),
                }
            )

        if ids:
            self._collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

    def query_product_ids(self, query_text, n_results=15):
        if not self.is_available:
            return []

        try:
            result = self._collection.query(
                query_texts=[query_text],
                n_results=n_results,
                include=["metadatas"],
            )
        except Exception:
            return []

        metadatas = result.get("metadatas", [[]])
        if not metadatas or not metadatas[0]:
            return []

        product_ids = []
        for metadata in metadatas[0]:
            product_id = metadata.get("product_id")
            if isinstance(product_id, int):
                product_ids.append(product_id)

        return product_ids
