import asyncio
import perplexity_async
import re
import json

def extract_ai_answer(data):
    def recursive_search(obj):
        if isinstance(obj, dict):
            if 'answer' in obj:
                val = obj['answer']
                parsed = json.loads(val)
                res =  parsed.get('answer', None)
                res = re.sub(r'\[\d+\]', '', res)
                res = re.sub(r'\[(.*?)\](?=\(pplx://action/followup\))', r'\1', res)
                res = re.sub(r'\(pplx://action/followup\)', '', res)
                return res
            for v in obj.values():
                result = recursive_search(v)
                if result:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = recursive_search(item)
                if result:
                    return result
        return ''
    return recursive_search(data)

async def perplexity_chat(prompt, files={}):
    perplexity_cli = await perplexity_async.Client()
    resp = await perplexity_cli.search(prompt, files=files)
    return extract_ai_answer(resp)