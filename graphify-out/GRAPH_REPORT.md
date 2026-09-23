# Graph Report - hunter-sandbox  (2026-09-23)

## Corpus Check
- 31 files · ~6,330 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 2)

## Summary
- 159 nodes · 285 edges · 12 communities (8 shown, 4 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 24 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2d0454f9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- remediator.py
- hunter.py
- orchestrator.py
- brain.py
- TransactionManager
- test_inventory.py
- SlidingWindowLimiter
- BillingProcessor
- README.md
- setup_complex_challenge.sh

## God Nodes (most connected - your core abstractions)
1. `CodeAuditor` - 10 edges
2. `repair_loop()` - 10 edges
3. `Database` - 9 edges
4. `BillingProcessor` - 8 edges
5. `generate_and_apply_patch()` - 8 edges
6. `GitHubManager` - 8 edges
7. `apply_patch_atomic()` - 8 edges
8. `SlidingWindowLimiter` - 8 edges
9. `TransactionManager` - 8 edges
10. `MockPaymentGateway` - 7 edges

## Surprising Connections (you probably didn't know these)
- `run_approved_test()` --calls--> `CodeAuditor`  [EXTRACTED]
  test_auditor_approved.py → auditor.py
- `run_test()` --calls--> `CodeAuditor`  [EXTRACTED]
  test_auditor.py → auditor.py
- `test_floating_point_accumulation_precision()` --uses--> `BillingProcessor`  [INFERRED]
  test_billing.py → billing.py
- `test_invalid_input_raises_exception()` --uses--> `BillingProcessor`  [INFERRED]
  test_billing.py → billing.py
- `test_single_item_tier_1()` --uses--> `BillingProcessor`  [INFERRED]
  test_billing.py → billing.py

## Import Cycles
- None detected.

## Communities (12 total, 4 thin omitted)

### Community 0 - "remediator.py"
Cohesion: 0.13
Nodes (26): ast, call_gemini_with_retry(), generate_and_apply_patch(), Path, Ejecuta la llamada aplicando rotación de llaves y backoff ante errores 503/429., Genera el parche estructurado en JSON y lo inyecta atómicamente., apply_patch_atomic(), discard_backup() (+18 more)

### Community 1 - "hunter.py"
Cohesion: 0.09
Nodes (20): CodeAuditor, Any, pack_repository(), Empaqueta el repositorio completo en un solo archivo XML usando Repomix., github, GitHubManager, Clona el repositorio en una carpeta local usando autenticación por token., Crea y se mueve a una nueva rama de trabajo en el repositorio clonado. (+12 more)

### Community 2 - "orchestrator.py"
Cohesion: 0.16
Nodes (12): argparse, create_pr(), run_cmd(), setup_branch(), json, execute_pipeline(), load_task(), Filtro estricto con shlex, validación de binario y bloqueo de flags hostiles. (+4 more)

### Community 3 - "brain.py"
Cohesion: 0.22
Nodes (8): get_available_keys(), Filtro estricto de credenciales sin valores de fallback inseguros., Recupera todas las llaves configuradas en el .env., validate_api_key(), dotenv, google, google_genai, google_genai_errors

### Community 4 - "TransactionManager"
Cohesion: 0.15
Nodes (9): asyncio, Lock, pytest, asyncio, test_cross_resource_deadlock_prevention(), test_lock_release_on_payload_exception(), Any, Administrador de transacciones multi-recurso con 2PL ingenuo. Vulnerable a… (+1 more)

### Community 5 - "test_inventory.py"
Cohesion: 0.23
Nodes (10): Database, InsufficientStockError, InventoryManager, MockPaymentGateway, PaymentError, Exception, asyncio, test_concurrent_purchases_race_condition() (+2 more)

### Community 6 - "SlidingWindowLimiter"
Cohesion: 0.29
Nodes (8): collections, Rate limiter basado en Sliding Window Log. Vulnerable a condiciones de carrera…, SlidingWindowLimiter, asyncio, test_concurrent_burst_race_condition(), test_memory_cleanup_no_leaks(), test_rate_limiter_basic_window(), time

### Community 7 - "BillingProcessor"
Cohesion: 0.36
Nodes (8): BillingProcessor, Motor de liquidacion de facturas con descuentos escalonados y comisiones.…, decimal, test_floating_point_accumulation_precision(), test_invalid_input_raises_exception(), test_single_item_tier_1(), test_tier_2_exact_boundary(), typing

## Knowledge Gaps
- **2 isolated node(s):** `setup_complex_challenge.sh script`, `hunter-sandbox`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 57 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Are the 3 inferred relationships involving `Database` (e.g. with `test_concurrent_purchases_race_condition()` and `test_purchase_item_insufficient_stock()`) actually correct?**
  _`Database` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `BillingProcessor` (e.g. with `test_floating_point_accumulation_precision()` and `test_invalid_input_raises_exception()`) actually correct?**
  _`BillingProcessor` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `setup_complex_challenge.sh script`, `hunter-sandbox` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `remediator.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12698412698412698 - nodes in this community are weakly interconnected._
- **Should `hunter.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08558558558558559 - nodes in this community are weakly interconnected._