c=open('railway_file_server.py','r',encoding='utf-8').read()
# Find switchPage clouddata line
i = c.find('switchPage')
j = c.find('if(id==', i)
k = c.find('if(id==', j+3)
while k >= 0 and k < j + 200:
    j = k
    k = c.find('if(id==', j+3)
# j is the last if block in switchPage
print('clouddata call:', repr(c[j:j+60]))
