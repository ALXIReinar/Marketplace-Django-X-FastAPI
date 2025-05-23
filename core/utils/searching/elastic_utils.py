async def gener_docs(records):
    for record in records:
        category = ''.join(record['category_full'].replace('/', ' '))
        doc  = {
            "id": record['id'],
            "prd_name": record['prd_name'],
            "category": category
        }
        yield doc
