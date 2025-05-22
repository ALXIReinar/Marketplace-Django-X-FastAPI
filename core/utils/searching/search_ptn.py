def looking(search_phrase: str):
    query = {
        "bool": {
            "should": [
              {
                "multi_match": {
                  "query": search_phrase,
                  "type": "best_fields",
                  "fields": ["prd_name^2", "category"],
                  "fuzziness": "auto",
                  "prefix_length": 1,
                  "operator": "or"
                }
              },
              {
                "match_phrase_prefix": {
                    "prd_name": {
                        "query": search_phrase,
                        "boost": 4,
                        "max_expansions": 37
                    }
                }
              },
              {
                "match_phrase_prefix": {
                  "category": {
                    "query": search_phrase,
                    "boost": 2,
                    "max_expansions": 37
                  }
                }
              }
            ],
            "minimum_should_match": 1
        }
    }
    return query