from sentence_transformers import SentenceTransformer

def download_model():
    try:
        print("Downloading model to local folder...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Save it to a folder you choose
        model.save('./my_local_model')  # ✅ saves to ./my_local_model
        
        print("✅ Model saved to ./sentence_transformer")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    download_model()
