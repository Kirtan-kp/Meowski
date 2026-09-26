from scripts.run_retrieval_evaluation import evaluate_retrieval


def main():

    print("\n")
    print("=" * 60)
    print("MEOWSKI EVALUATION")
    print("=" * 60)

    retrieval_results = evaluate_retrieval(3)

    print("\n")
    print("=" * 60)
    print("RETRIEVAL SUMMARY")
    print("=" * 60)

    print(
        f"Recall@3: "
        f"{retrieval_results['recall']:.2f}"
    )

    print(
        f"Precision@3: "
        f"{retrieval_results['precision']:.2f}"
    )

    print(
        f"MRR@3: "
        f"{retrieval_results['mrr']:.2f}"
    )

    print(
        f"Hit Rate@3: "
        f"{retrieval_results['hit_rate']:.2f}"
    )


if __name__ == "__main__":
    main()