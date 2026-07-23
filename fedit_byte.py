with open('railway_file_server.py','rb') as f:
    c = f.read()

# 找 set-admin-btn 后面
idx = c.find(b'set-admin-btn')
after = c[idx:]
end_btn = after.find(b'</button>')
if end_btn < 0:
    print("ERROR: no </button> after set-admin-btn")
    exit(1)

# 找到 \')+\'</td></tr>\' 的位置
after_btn = after[end_btn+9:]  # after </button>
td_end = after_btn.find(b"')+'</td></tr>'")
if td_end < 0:
    print("ERROR: no td end marker")
    exit(1)

insert_pos = idx + end_btn + 9 + td_end

# 构造插入内容: '+"<button onclick="cpwUser('+u.id+')" style="margin-left:5px;cursor:pointer">\xe6\x94\xb9\xe5\xaf\x86\xe7\xa0\x81</button>+'
cpw_user = b"cpwUser(" + "'".encode() + b"+u.id+" + "'".encode() + b")"
btn_html = (
    b"'+"
    b'<button onclick="' + cpw_user + b'" style="margin-left:5px;cursor:pointer">'
    + "改密码".encode('utf-8') + b'</button>'
    b"+'"
)

new_c = c[:insert_pos] + btn_html + c[insert_pos:]
with open('railway_file_server.py','wb') as f:
    f.write(new_c)

print(f"loadUsers: inserted {len(btn_html)} bytes at position {insert_pos}")
print(f"Total size: {len(new_c)} bytes")
