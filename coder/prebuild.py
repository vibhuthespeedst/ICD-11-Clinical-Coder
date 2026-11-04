import pickle

from .offline import INDEX, OfflineCoder

if __name__ == "__main__":
    with open(INDEX, "wb") as f:
        pickle.dump(OfflineCoder(), f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"wrote {INDEX}")
