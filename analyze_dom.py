import re

with open('dom_dump.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Let's find postIds in the html text
post_matches = re.finditer(r'postId[\'\"]?\s*[:=]\s*[\'\"]?(\d+)', html)
ids = set(m.group(1) for m in post_matches)
print('Regex postId match:', ids)

# Also let's check hrefs
hrefs = re.finditer(r'href=[\'\"]([^\'\"]+)[\'\"]', html)
href_set = set(m.group(1) for m in hrefs if 'post' in m.group(1))
print('Hrefs with post:', href_set)

# Let's check click handlers
clicks = re.finditer(r'@click=[\'\"]([^\'\"]+)[\'\"]', html)
click_set = set(m.group(1) for m in clicks if 'post' in m.group(1))
print('Click handlers with post:', click_set)
