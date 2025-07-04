from core.config_dir.config import env

aliases = {
    env.search_index: {}
}

settings = {
    "index": {
        "number_of_shards": 2,
        "routing.allocation.total_shards_per_node": 3
    },
    "number_of_replicas": 1,
    "analysis": {
        "analyzer": {
            "es_analyzer": {
                "type": "custom",
                "tokenizer": "whitespace",
                "filter": ["stop_prepos", "lowercase"]
            },
            "es_analyzer_deep_search": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": ["lowercase", "synonyms_list"]
            }
        },
        "filter": {
            "synonyms_list": {
                "type": "synonym",
                "synonyms_path": "dev_files/synonyms.txt"
            },
            "stop_prepos": {
                "type": "stop",
                "ignore_case": True,
                "stopwords": [
                    "на",
                    "а",
                    "по",
                    "в",
                    "у",
                    "со",
                    "до",
                    "из",
                    "за",
                    "из-за",
                    "через",
                    "из-под",
                    "под",
                    "над",
                    "с",
                    "и",
                    "для"
                ]
            }
        }
    }
}

index_mapping = {
    "properties": {
        "id": {
            "type": "long",
            "index": False,
            "coerce": False
        },
        "prd_name": {
            "type": "text",
            "analyzer": "es_analyzer_deep_search"
        },
        "category": {
            "type": "text",
            "analyzer": "es_analyzer",
            "search_analyzer": "es_analyzer_deep_search"
        }
    }
}

swap_indices_actions =  [
    {"add": {"index": "dev_products_idx", "alias": env.search_index}},
    {"remove": {"index": "products_idx", "alias": env.search_index}}
]
