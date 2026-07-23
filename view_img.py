import base64
with open(r'C:\Users\lfy20\.openclaw\qqbot\downloads\51D6781C8C4D301B6372158D79FAF704_1778874309416.png', 'rb') as f:
    img = base64.b64encode(f.read()).decode()
with open('C:\\u-claw\\portable\\data\\.openclaw\\workspace\\view_img.html', 'w', encoding='utf-8') as out:
    out.write('<html><body><img src="data:image/jpeg;base64,')
    out.write(img)
    out.write('"/></body></html>')
print('OK')
