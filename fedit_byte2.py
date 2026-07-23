with open('railway_file_server.py','rb') as f:
    c = f.read()

# deleteUser 里也有行模板
# 搜索：class="del-btn">删除</button>')+'</td></tr>'
# 注意：有2处出现（loadUsers 和 deleteUser），我们找第二处（deleteUser 里的）
marker = b'class="del-btn">'
idx2 = c.find(marker, c.find(marker) + 50)  # skip first occurrence
if idx2 < 0:
    print("No second occurrence, trying first but with different context...")
    idx2 = c.find(marker)

after2 = c[idx2:]
end_btn2 = after2.find(b'</button>')
if end_btn2 < 0:
    print("ERROR: no </button>")
    exit(1)

after_btn2 = after2[end_btn2+9:]
td_end2 = after_btn2.find(b"')+'</td></tr>'")
if td_end2 < 0:
    print("ERROR: no td end at second occurrence")
    # maybe it's the loadUsers version which has set-admin-btn
    # for deleteUser the td_end might be '):\''  or something else
    print(repr(after_btn2[:100]))
    exit(1)

insert_pos2 = idx2 + end_btn2 + 9 + td_end2

cpw_user = b"cpwUser(" + "'".encode() + b"+u.id+" + "'".encode() + b")"
btn_html2 = (
    b"'+"
    b'<button onclick="' + cpw_user + b'" style="margin-left:5px;cursor:pointer">'
    + "改密码".encode('utf-8') + b'</button>'
    b"+'"
)

new_c = c[:insert_pos2] + btn_html2 + c[insert_pos2:]
with open('railway_file_server.py','wb') as f:
    f.write(new_c)

print(f"deleteUser: inserted {len(btn_html2)} bytes at position {insert_pos2}")
print(f"Total size: {len(new_c)} bytes")

# verify
cnt = new_c.count(b'cpwUser(')
print(f"cpwUser( occurrences: {cnt} (expect 3: func def + 2 buttons)")
