import logging
import time
from src.answer import answer_question

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

# Your 10 queries from Phase 1
QUERIES = [
    ("Factual/Definition", "What is yoga according to the Gita?"),
    ("Teaching/Philosophy", "What does Krishna teach about detachment from results?"),
    ("Narrative/Story", "Why did Arjuna refuse to fight at the beginning?"),
    ("Comparative", "What is the difference between karma yoga and bhakti yoga?"),
    ("Speaker-specific", "What does Arjuna ask Krishna about duty and action?"),
    ("Thematic", "Which parts of the Gita discuss meditation and control of mind?"),
    (
        "Practical/Application",
        "How should I deal with success and failure according to the Gita?",
    ),
    ("Ambiguous", "What does the Gita say about the mind?"),
    ("Negative case", "What does the Gita say about cryptocurrency investment?"),
    (
        "Complex multi-part",
        "Is it better to renounce action completely, or to act without attachment?",
    ),
]

print("=" * 70)
print("TESTING RAG SYSTEM ON 10 QUERIES")
print("=" * 70)

results_summary = []

for i, (category, query) in enumerate(QUERIES, 1):
    print(f"\n{'='*70}")
    print(f"Query {i}/10: [{category}]")
    print(f"{query}")
    print("=" * 70)

    start_time = time.time()
    result = answer_question(query)
    elapsed = time.time() - start_time

    if result["error"]:
        print(f"❌ Error: {result['error']}")
        results_summary.append(
            {
                "query": query,
                "category": category,
                "status": "ERROR",
                "retrieved": [],
                "time": elapsed,
            }
        )
        continue

    print(f"\nRetrieved verses: {result['retrieved_verses']}")
    print(f"Time: {elapsed:.2f}s")
    print(f"\nAnswer:")
    print("-" * 70)
    print(result["answer"])
    print("-" * 70)

    results_summary.append(
        {
            "query": query,
            "category": category,
            "status": "SUCCESS",
            "retrieved": result["retrieved_verses"],
            "answer_length": len(result["answer"]),
            "time": elapsed,
        }
    )

    time.sleep(1)

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

success_count = sum(1 for r in results_summary if r["status"] == "SUCCESS")
print(f"\nSuccessful: {success_count}/10")
print(f"Failed: {10 - success_count}/10")

avg_time = sum(r["time"] for r in results_summary) / len(results_summary)
print(f"Average response time: {avg_time:.2f}s")

print("\nResults by category:")
for r in results_summary:
    status = "OK" if r["status"] == "SUCCESS" else "FAIL"
    print(f"[{status}] [{r['category']}] {r['query'][:50]}...")
    if r["status"] == "SUCCESS":
        print(f"  Retrieved: {r['retrieved']}")
        print(f"  Answer length: {r['answer_length']} chars")

print("\n" + "=" * 70)
print("Test complete! Review results above.")
print("=" * 70)
