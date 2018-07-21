import requests
res = requests.get("https://www.goodreads.com/book/review_counts.json",
                   params={"key": "KEY", "isbns": "9781632168146"})
print(res.json())

key: DNmoNwfQbaJFsYerLF4A
secret: ukaJG4jIHDu8b5v0wCs4iFIoVEOD5On8WLEJLB3z8
