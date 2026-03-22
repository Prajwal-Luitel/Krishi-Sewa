import os
from pathlib import Path

from django.conf import settings

from vendor.models import Product

from .chroma_store import ProductChromaStore
from .ollama_client import call_ollama_json


def _fallback_summary_for_ai(disease_name):
    disease_text = disease_name.replace("_", " ").replace("-", " ").title()
    return {
        "overview": f"Couldn't connect to AI. Showing basic fallback guidance for {disease_text}.",
        "symptoms": [
            "Check leaves for spots, discoloration, or lesions",
            "Observe wilting or unusual curling patterns",
            "Watch for slow growth or weak plant vigor",
            "Inspect nearby plants for similar signs",
        ],
        "prevention": [
            "Keep fields monitored and remove severely infected leaves",
            "Maintain clean tools and balanced irrigation schedules",
            "Prefer disease-resistant seeds and healthy soil practices",
            "Consult local agricultural guidance for exact treatment",
        ],
        "recommendation_reason": "Couldn't connect to AI, so recommendations are selected using retrieval results.",
    }


def _choose_products_from_ids(candidates, recommended_ids):
    if not isinstance(recommended_ids, list):
        return candidates[:3]

    clean_ids = []
    for item in recommended_ids:
        try:
            clean_ids.append(int(item))
        except (TypeError, ValueError):
            continue

    selected = [product for product in candidates if product.id in clean_ids]
    if len(selected) < 3:
        existing = {p.id for p in selected}
        for product in candidates:
            if product.id not in existing:
                selected.append(product)
            if len(selected) == 3:
                break

    return selected[:3]


def _build_ollama_prompt(disease_name, candidates):
    product_lines = []
    for product in candidates:
        product_lines.append(
            "id={id}; name={name}; category={category}; brand={brand}; stock={stock}; description={description}".format(
                id=product.id,
                name=product.name,
                category=product.get_category_display(),
                brand=product.brand,
                stock=product.stock,
                description=product.description[:180],
            )
        )

    catalog_context = "\n".join(product_lines)

    return (
        "You are an agriculture assistant. "
        "Given a detected plant disease and a product catalog, generate JSON only with keys: "
        "overview (string), symptoms (array of 4 short bullet strings), prevention (array of 4 short bullet strings), "
        "recommended_product_ids (array of exactly 3 integer ids selected only from the catalog), "
        "recommendation_reason (string). "
        "Do not add markdown or extra keys.\n\n"
        f"Detected disease: {disease_name}\n\n"
        f"Product catalog:\n{catalog_context}"
    )


def _retrieve_candidates_chroma(disease_name, products):
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", str(Path(settings.BASE_DIR) / ".chroma"))
    collection_name = os.getenv("CHROMA_COLLECTION", "product_catalog")
    embed_model = os.getenv("CHROMA_EMBED_MODEL", "nomic-embed-text")
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    chroma_store = ProductChromaStore(
        persist_directory=persist_dir,
        collection_name=collection_name,
        embedding_model=embed_model,
        ollama_base_url=ollama_base_url,
    )

    if not chroma_store.is_available:
        return []

    chroma_store.upsert_products(products)
    retrieved_ids = chroma_store.query_product_ids(disease_name, n_results=15)

    if not retrieved_ids:
        return []

    product_map = {product.id: product for product in products}
    candidates = [product_map[pid] for pid in retrieved_ids if pid in product_map]
    return candidates[:15]


def build_disease_rag_output(disease_name):
    products = list(Product.objects.all().order_by("-stock", "selling_price"))
    if not products:
        fallback = _fallback_summary_for_ai(disease_name)
        return fallback, []

    candidates = _retrieve_candidates_chroma(disease_name, products)
    if not candidates:
        candidates = products[:15]

    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    prompt = _build_ollama_prompt(disease_name, candidates)
    ai_data = call_ollama_json(prompt, ollama_url=ollama_url, model=ollama_model)

    if not ai_data:
        fallback = _fallback_summary_for_ai(disease_name)
        return fallback, candidates[:3]

    fallback = _fallback_summary_for_ai(disease_name)
    summary = {
        "overview": ai_data.get("overview") or fallback["overview"],
        "symptoms": ai_data.get("symptoms") if isinstance(ai_data.get("symptoms"), list) else fallback["symptoms"],
        "prevention": ai_data.get("prevention") if isinstance(ai_data.get("prevention"), list) else fallback["prevention"],
        "recommendation_reason": ai_data.get("recommendation_reason") or fallback["recommendation_reason"],
    }

    selected = _choose_products_from_ids(candidates, ai_data.get("recommended_product_ids"))
    return summary, selected
