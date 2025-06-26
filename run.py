import uvicorn

if __name__ == "__main__":
  uvicorn.run("app.main:app", host="172.17.1.208", port=8001, reload=True, timeout_keep_alive=30)
