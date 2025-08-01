# generate_keys.py
import random
import string

def generate_key(tier):
    prefix = "ADVANCED" if tier == "advanced" else "BASIC"
    suffix_length = 5 if tier == "basic" else 9
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=suffix_length))
    return f"{prefix}-{suffix}"

if __name__ == "__main__":
    for _ in range(5):  # generate 5 sample keys
        print(generate_key("basic"))
        print(generate_key("advanced"))
