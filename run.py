from app import create_app

app = create_app()

if __name__ == '__main__':
    print("🚀 Starkforge Review Tool Backend Modularized!")
    app.run(debug=True, port=5000)
