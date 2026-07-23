content = open('railway_file_server.py', 'r', encoding='utf-8').read()
idx = content.find('_ADMIN = ')
rest = content[idx:]
end1 = rest.find("'''")
print('First triple quote:', end1)
end2 = rest.find("'''", end1+3)
print('Second triple quote:', end2)
if end2 < 0:
    print('NO END QUOTE! File may be corrupted')
    print('Last 200 chars:', repr(content[-200:]))
else:
    print('Template length:', end2 - end1)
    after_end = rest[end2+3:end2+50]
    print('After template:', repr(after_end))
    # py_compile
import py_compile
try:
    py_compile.compile('railway_file_server.py', doraise=True)
    print('py_compile OK')
except Exception as e:
    print('py_compile FAIL:', e)
