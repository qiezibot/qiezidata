import sys, re
sys.stdout.reconfigure(encoding='utf-8')
c = open('railway_file_server.py', encoding='utf-8').read()

# 直接找 _ADMIN = """\<<!DOCTYPE 这个精确位置
# _ADMIN = """\< 开头的需要转义
pos = c.find(r'_ADMIN = """\<!DOCTYPE')
print(f'_ADMIN starts at {pos}')

# 找 """ 结束。\n""" 之后，_ENV_TEMPLATE 之前
# _ADMIN 模板以 </html>""" 结束
end_tag = r'html>"""'
pos_end = c.find(end_tag, pos)
print(f'End at {pos_end}')
if pos_end >= 0:
    # _ADMIN 字符串的 """" 在 end_tag 后面
    quote_end = pos_end + len(end_tag) - 3  # points to the """
    # Actually end_tag has """
    print(f'Content length: {pos_end - pos}')
    print(f'Content ends with: {repr(c[pos_end-30:pos_end+10])}')
