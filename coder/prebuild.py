import pickle

from .offline import INDEX, OfflineCoder

if __name__ == "__main__":
    with open(INDEX, "wb") as f:
        coder = OfflineCoder()
        coder.multilingual()
        pickle.dump(coder, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"wrote {INDEX}")
