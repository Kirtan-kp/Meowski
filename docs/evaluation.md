# Evaluation

The evaluation suite should be run against a versioned dataset before declaring a release production-ready.

## Retrieval

Measure hit rate, context precision/recall, MRR and latency. Compare dense-only, BM25-only, hybrid/RRF and reranked retrieval where practical.

## Generation

Measure answer relevance, faithfulness and manually verified correctness. Keep provider-backed evaluation behind the same cost-safety policy used by runtime inference.

## Citations

Verify that cited source numbers exist, that the cited source contains the claimed evidence, and that document/page metadata is returned to the client.

## Operations

Track request latency, retrieval latency, reranker scores, provider/model, estimated tokens, actual provider usage when exposed, rate-limit outcomes, provider errors and fallback counts.
