import re
with open('api_response.json', 'r', encoding='utf-8') as f:
    body = f.read()
post_ids = re.findall(r'"postId"\s*:\s*"?(\d{4,9})', body)
print('Found:', set(post_ids))
