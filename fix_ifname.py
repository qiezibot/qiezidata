with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Find and remove if __name__ block
old = "if __name__ == '__main__':\n    import uvicorn\n    uvicorn.run(app, host=HOST, port=PORT)\n\n"
new = text.replace(old, '') + '\n\n' + old

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(new)

print("Fixed! if __name__ moved to end of file")
