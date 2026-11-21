"""
Word Error Rate (WER) Evaluator for Multilingual Indian Speech Recognition.
Implements the standard dynamic programming Levenshtein distance algorithm:
    WER = (Substitutions + Deletions + Insertions) / Total Reference Words
"""

import re
from typing import Dict, Any, List, Tuple


def normalize_for_eval(text: str) -> List[str]:
    """
    Normalizes transcript text for fair phonetic/word comparison:
    - Lowercase
    - Removes punctuation marks (commas, periods, question marks, dashes)
    - Normalizes multiple spaces
    Returns list of token words.
    """
    if not text:
        return []
    cleaned = text.lower()
    # Replace punctuation with spaces
    cleaned = re.sub(r"[,\.\?!;:\-\(\)\[\]\"'/।]", " ", cleaned)
    tokens = [t.strip() for t in cleaned.split() if t.strip()]
    return tokens


def compute_wer(reference: str, hypothesis: str) -> Dict[str, Any]:
    """
    Computes exact Word Error Rate (WER) using Wagner-Fischer dynamic programming.
    Returns:
    {
        "wer": float (e.g. 0.0909),
        "substitutions": int,
        "deletions": int,
        "insertions": int,
        "hits": int,
        "reference_words": int,
        "hypothesis_words": int,
        "accuracy_pct": float
    }
    """
    ref_words = normalize_for_eval(reference)
    hyp_words = normalize_for_eval(hypothesis)

    N = len(ref_words)
    M = len(hyp_words)

    if N == 0:
        if M == 0:
            return {
                "wer": 0.0,
                "substitutions": 0,
                "deletions": 0,
                "insertions": 0,
                "hits": 0,
                "reference_words": 0,
                "hypothesis_words": 0,
                "accuracy_pct": 100.0
            }
        return {
            "wer": 1.0,
            "substitutions": 0,
            "deletions": 0,
            "insertions": M,
            "hits": 0,
            "reference_words": 0,
            "hypothesis_words": M,
            "accuracy_pct": 0.0
        }

    # DP matrix of dimensions (N+1) x (M+1)
    dp = [[0] * (M + 1) for _ in range(N + 1)]
    # Backtrack matrix to count S, D, I, C
    # 0: Match (Hit), 1: Sub, 2: Del, 3: Ins
    ops = [[0] * (M + 1) for _ in range(N + 1)]

    for i in range(N + 1):
        dp[i][0] = i
        ops[i][0] = 2  # Deletion
    for j in range(M + 1):
        dp[0][j] = j
        ops[0][j] = 3  # Insertion
    ops[0][0] = 0

    for i in range(1, N + 1):
        for j in range(1, M + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                cost = 0
            else:
                cost = 1

            del_cost = dp[i - 1][j] + 1
            ins_cost = dp[i][j - 1] + 1
            sub_cost = dp[i - 1][j - 1] + cost

            best = min(del_cost, ins_cost, sub_cost)
            dp[i][j] = best

            if best == sub_cost:
                ops[i][j] = 0 if cost == 0 else 1  # 0: Hit, 1: Sub
            elif best == del_cost:
                ops[i][j] = 2  # Del
            else:
                ops[i][j] = 3  # Ins

    # Backtrack to count operations
    i, j = N, M
    substitutions = 0
    deletions = 0
    insertions = 0
    hits = 0

    while i > 0 or j > 0:
        op = ops[i][j]
        if i > 0 and j > 0 and (op == 0 or op == 1):
            if op == 0:
                hits += 1
            else:
                substitutions += 1
            i -= 1
            j -= 1
        elif i > 0 and (op == 2 or j == 0):
            deletions += 1
            i -= 1
        elif j > 0 and (op == 3 or i == 0):
            insertions += 1
            j -= 1

    total_errors = substitutions + deletions + insertions
    wer = round(total_errors / N, 4)
    accuracy_pct = round(max(0.0, (1.0 - wer) * 100.0), 2)

    return {
        "wer": wer,
        "substitutions": substitutions,
        "deletions": deletions,
        "insertions": insertions,
        "hits": hits,
        "reference_words": N,
        "hypothesis_words": M,
        "accuracy_pct": accuracy_pct
    }

