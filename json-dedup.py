#!/usr/bin/env python3

import sys
import hashlib
import json
import argparse
import string

def compute_hash(obj):
    """Compute a hash for a given JSON object."""
    obj_str = json.dumps(obj, sort_keys=True)
    return hashlib.sha256(obj_str.encode('utf-8')).hexdigest()

def update(d, e):
        h = compute_hash(e)
        d[h] = e
        # if h in d:
        #     d[h] = (d[h][0], d[h][1] + 1)
        # else:
        #     d[h] = (e, 1)
        return d, h

def dedup(d, e):
    if not isinstance(e, (list, dict)):
        # e is an atom
        return update(d, e)
    elif isinstance(e, list):
        # e is a list
        new_list = []
        for item in e:
            d, item_hash = dedup(d, item)
            new_list.append(item_hash)
        return update(d, new_list)
    elif isinstance(e, dict):
        # e is a dictionary
        new_dict = {}
        for key, value in e.items():
            d, value_hash = dedup(d, value)
            new_dict[key] = value_hash
        return update(d, new_dict)

def compute_histogram(d):
    histogram = {}
    for _, (_, count) in d.items():
        if count in histogram:
            histogram[count] += 1
        else:
            histogram[count] = 1
    return histogram

def print_histogram(histogram):
    # Sort the histogram by counter
    sorted_histogram = sorted(histogram.items())
    
    # Find the maximum width for formatting
    max_count_width = max(len(str(count)) for count in histogram.keys())
    max_entries_width = max(len(str(entries)) for entries in histogram.values())
    
    # Print the histogram
    print("Counter | Entries")
    print("-" * (max_count_width + max_entries_width + 3))
    for count, entries in sorted_histogram:
        print(f"{str(count).rjust(max_count_width)} | {str(entries).rjust(max_entries_width)}")

def protect_strings(d):
    for h, e in d.items():
        if isinstance(e, str) and len(e) <= 2:
            d[h] = '&%' + e
    return d

def short_code(n):
    alphabet = list(string.ascii_lowercase + string.ascii_uppercase)
    if 0 <= n < 52:
        return alphabet[n]
    else:
        n -= 52
        first_char = alphabet[n // 52]
        second_char = alphabet[n % 52]
        return first_char + second_char

def compute_frequencies(d):
    frequency = {}
    for h, e in d.items():
        if isinstance(e, list):
            for item in e:
                if item in frequency:
                    frequency[item] += 1
                else:
                    frequency[item] = 1
        if isinstance(e, dict):
            for k, v in e.items():
                if v in frequency:
                    frequency[v] += 1
                else:
                    frequency[v] = 1
    return frequency

def optimize(d, root):
    frequency = compute_frequencies(d)
    frequency[root] = 0

    # Sort the hashes by frequency in descending order
    sorted_hashes = sorted(frequency.items(), key=lambda item: item[1], reverse=True)

    # Assign integers to the hashes based on their frequency
    hash_to_short = {}
    for i, (h, _) in enumerate(sorted_hashes):
        hash_to_short[h] = short_code(i)

    # Replace each hash in the expressions with the corresponding short string
    for h, e in list(d.items()):
        if h in hash_to_short:
            short = hash_to_short[h]
            if isinstance(e, list):
                e = [hash_to_short.get(item, item) for item in e]
            elif isinstance(e, dict):
                e = {k: hash_to_short.get(v, v) for k, v in e.items()}
            d[short] = e
            del d[h]

    return d, hash_to_short[root]

def inline(d, root):
    # Create a reverse mapping from hash to expressions that refer to it
    reverse_mapping = {}
    for h, e in d.items():
        if isinstance(e, list):
            for sub_expr in e:
                if sub_expr in reverse_mapping:
                    reverse_mapping[sub_expr].append(h)
                else:
                    reverse_mapping[sub_expr] = [h]
        elif isinstance(e, dict):
            for sub_expr in e.values():
                if sub_expr in reverse_mapping:
                    reverse_mapping[sub_expr].append(h)
                else:
                    reverse_mapping[sub_expr] = [h]

    frequency = compute_frequencies(d)
    frequency[root] = 0

    # Inline expressions
    for h, e in list(d.items()):
        if frequency[h] == 1:
            if h in reverse_mapping:
                for referrer in reverse_mapping[h]:
                    referrer_expr = d[referrer]
                    if isinstance(referrer_expr, list):
                        referrer_expr = [e if sub_expr == h else sub_expr for sub_expr in referrer_expr]
                    elif isinstance(referrer_expr, dict):
                        referrer_expr = {k: (e if v == h else v) for k, v in referrer_expr.items()}
                    d[referrer] = referrer_expr
            del d[h]

    return d

def inline_expr(d, expr, inlined = {}):
    if isinstance(expr, (str)):
        if len(expr) <= 2 and expr in d:
            inlined, e = inline_expr(d, d[expr], inlined)
            return inlined, e
        if len(expr) <= 4 and expr[:2] == "&%":
            return inlined, expr[2:]
        else:
            return inlined, expr
    elif isinstance(expr, list):
        new_list = []
        for item in expr:
            inlined, e = inline_expr(d, item, inlined)
            new_list.append(e)
        return inlined, new_list
    elif isinstance(expr, dict):
        new_dict = {}
        for key, value in expr.items():
            inlined, e = inline_expr(d, value, inlined)
            new_dict[key] = e
        return inlined, new_dict
    else:
        return inlined, expr

def total(d, e):
    (d, root) = dedup({}, e)
    d = protect_strings(d)
    (d, root) = optimize(d, root)
    d = inline(d, root)
    return d, root

def inverse(d, root):
    inlined, e = inline_expr(d, root)
    return e

def main():
    parser = argparse.ArgumentParser(description="Compress JSON files.")
    parser.add_argument('filename', nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="JSON file to compress (default: stdin)")
    args = parser.parse_args()

    # Read JSON content
    json_content = json.load(args.filename)

    # (d, root) = total({}, json_content)
    # print(json.dumps(d))
    # print(inverse(d, root))

    # e = {
    #     "nm": "ex",
    #     "vals": [1, 1, {"foo": "bar"}],
    #     "anthr": {"foo": "bar"}
    # }


    e = json_content
    (d, root) = dedup({}, e)
    d = protect_strings(d)
    (d, root) = optimize(d, root)
    d = inline(d, root)
    # i = inverse(d, root)

    # res = {
    #         "e": e,
    #         "d": d,
    #         "root": root,
    #         "i" : i
    # }
    # print(json.dumps(res))
    print(json.dumps(d))
    # print(i == e)

    # histogram = compute_histogram(d)
    # print_histogram(histogram)
    # print(len(d.keys()))

if __name__ == "__main__":
    main()

