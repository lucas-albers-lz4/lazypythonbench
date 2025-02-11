Benchmarks with tag 'apps':
===========================

| Benchmark      | python3.12.9_2025-02-10_16-18-20 | python3.13.2_2025-02-10_17-55-57 |
|----------------|:--------------------------------:|:--------------------------------:|
| 2to3           | 236 ms                           | 225 ms: 1.05x faster             |
| chameleon      | 7.67 ms                          | 5.83 ms: 1.32x faster            |
| docutils       | 2.11 sec                         | 2.01 sec: 1.05x faster           |
| html5lib       | 55.2 ms                          | 58.0 ms: 1.05x slower            |
| Geometric mean | (ref)                            | 1.07x faster                     |

Benchmark hidden because not significant (1): tornado_http

Benchmarks with tag 'asyncio':
==============================

| Benchmark                        | python3.12.9_2025-02-10_16-18-20 | python3.13.2_2025-02-10_17-55-57 |
|----------------------------------|:--------------------------------:|:--------------------------------:|
| async_tree_none                  | 375 ms                           | 311 ms: 1.21x faster             |
| async_tree_cpu_io_mixed          | 566 ms                           | 489 ms: 1.16x faster             |
| async_tree_eager                 | 96.8 ms                          | 101 ms: 1.05x slower             |
| async_tree_eager_cpu_io_mixed    | 337 ms                           | 348 ms: 1.03x slower             |
| async_tree_eager_cpu_io_mixed_tg | 472 ms                           | 411 ms: 1.15x faster             |
| async_tree_eager_io              | 1.01 sec                         | 764 ms: 1.32x faster             |
| async_tree_eager_io_tg           | 1.00 sec                         | 736 ms: 1.36x faster             |
| async_tree_eager_memoization_tg  | 349 ms                           | 291 ms: 1.20x faster             |
| async_tree_eager_tg              | 250 ms                           | 222 ms: 1.12x faster             |
| async_tree_io                    | 862 ms                           | 678 ms: 1.27x faster             |
| async_tree_io_tg                 | 890 ms                           | 680 ms: 1.31x faster             |
| async_tree_memoization           | 442 ms                           | 379 ms: 1.17x faster             |
| async_tree_memoization_tg        | 438 ms                           | 360 ms: 1.22x faster             |
| async_tree_none_tg               | 349 ms                           | 284 ms: 1.23x faster             |
| Geometric mean                   | (ref)                            | 1.16x faster                     |

Benchmark hidden because not significant (2): async_tree_cpu_io_mixed_tg, async_tree_eager_memoization

Benchmarks with tag 'math':
===========================

| Benchmark      | python3.12.9_2025-02-10_16-18-20 | python3.13.2_2025-02-10_17-55-57 |
|----------------|:--------------------------------:|:--------------------------------:|
| float          | 75.7 ms                          | 71.3 ms: 1.06x faster            |
| Geometric mean | (ref)                            | 1.02x faster                     |

Benchmark hidden because not significant (2): nbody, pidigits

Benchmarks with tag 'regex':
============================

| Benchmark      | python3.12.9_2025-02-10_16-18-20 | python3.13.2_2025-02-10_17-55-57 |
|----------------|:--------------------------------:|:--------------------------------:|
| regex_compile  | 124 ms                           | 112 ms: 1.11x faster             |
| regex_dna      | 129 ms                           | 148 ms: 1.14x slower             |
| regex_v8       | 17.0 ms                          | 24.5 ms: 1.44x slower            |
| Geometric mean | (ref)                            | 1.09x slower                     |

Benchmark hidden because not significant (1): regex_effbot

Benchmarks with tag 'serialize':
================================

| Benchmark            | python3.12.9_2025-02-10_16-18-20 | python3.13.2_2025-02-10_17-55-57 |
|----------------------|:--------------------------------:|:--------------------------------:|
| json_dumps           | 8.31 ms                          | 9.37 ms: 1.13x slower            |
| pickle               | 8.06 us                          | 10.4 us: 1.29x slower            |
| pickle_list          | 2.69 us                          | 3.25 us: 1.21x slower            |
| tomli_loads          | 1.91 sec                         | 1.77 sec: 1.08x faster           |
| unpickle             | 11.5 us                          | 12.8 us: 1.11x slower            |
| unpickle_list        | 3.95 us                          | 3.59 us: 1.10x faster            |
| unpickle_pure_python | 205 us                           | 175 us: 1.17x faster             |
| xml_etree_parse      | 141 ms                           | 122 ms: 1.16x faster             |
| xml_etree_iterparse  | 89.7 ms                          | 85.0 ms: 1.05x faster            |
| xml_etree_generate   | 85.1 ms                          | 79.6 ms: 1.07x faster            |
| xml_etree_process    | 68.7 ms                          | 52.6 ms: 1.31x faster            |
| Geometric mean       | (ref)                            | 1.01x faster                     |

Benchmark hidden because not significant (3): json_loads, pickle_dict, pickle_pure_python

Benchmarks with tag 'startup':
==============================

| Benchmark              | python3.12.9_2025-02-10_16-18-20 | python3.13.2_2025-02-10_17-55-57 |
|------------------------|:--------------------------------:|:--------------------------------:|
| python_startup         | 13.8 ms                          | 15.0 ms: 1.08x slower            |
| python_startup_no_site | 6.69 ms                          | 6.90 ms: 1.03x slower            |
| Geometric mean         | (ref)                            | 1.06x slower                     |

Benchmarks with tag 'template':
===============================

| Benchmark       | python3.12.9_2025-02-10_16-18-20 | python3.13.2_2025-02-10_17-55-57 |
|-----------------|:--------------------------------:|:--------------------------------:|
| django_template | 40.3 ms                          | 35.2 ms: 1.14x faster            |
| Geometric mean  | (ref)                            | 1.02x faster                     |

Benchmark hidden because not significant (3): genshi_text, genshi_xml, mako

All benchmarks:
===============

| Benchmark                        | python3.12.9_2025-02-10_16-18-20 | python3.13.2_2025-02-10_17-55-57 |
|----------------------------------|:--------------------------------:|:--------------------------------:|
| 2to3                             | 236 ms                           | 225 ms: 1.05x faster             |
| async_generators                 | 389 ms                           | 455 ms: 1.17x slower             |
| async_tree_none                  | 375 ms                           | 311 ms: 1.21x faster             |
| async_tree_cpu_io_mixed          | 566 ms                           | 489 ms: 1.16x faster             |
| async_tree_eager                 | 96.8 ms                          | 101 ms: 1.05x slower             |
| async_tree_eager_cpu_io_mixed    | 337 ms                           | 348 ms: 1.03x slower             |
| async_tree_eager_cpu_io_mixed_tg | 472 ms                           | 411 ms: 1.15x faster             |
| async_tree_eager_io              | 1.01 sec                         | 764 ms: 1.32x faster             |
| async_tree_eager_io_tg           | 1.00 sec                         | 736 ms: 1.36x faster             |
| async_tree_eager_memoization_tg  | 349 ms                           | 291 ms: 1.20x faster             |
| async_tree_eager_tg              | 250 ms                           | 222 ms: 1.12x faster             |
| async_tree_io                    | 862 ms                           | 678 ms: 1.27x faster             |
| async_tree_io_tg                 | 890 ms                           | 680 ms: 1.31x faster             |
| async_tree_memoization           | 442 ms                           | 379 ms: 1.17x faster             |
| async_tree_memoization_tg        | 438 ms                           | 360 ms: 1.22x faster             |
| async_tree_none_tg               | 349 ms                           | 284 ms: 1.23x faster             |
| asyncio_tcp_ssl                  | 1.22 sec                         | 1.23 sec: 1.02x slower           |
| asyncio_websockets               | 515 ms                           | 549 ms: 1.07x slower             |
| chameleon                        | 7.67 ms                          | 5.83 ms: 1.32x faster            |
| chaos                            | 57.3 ms                          | 52.6 ms: 1.09x faster            |
| comprehensions                   | 19.4 us                          | 14.4 us: 1.34x faster            |
| bench_mp_pool                    | 21.8 ms                          | 25.2 ms: 1.16x slower            |
| bench_thread_pool                | 861 us                           | 843 us: 1.02x faster             |
| coroutines                       | 20.2 ms                          | 20.6 ms: 1.02x slower            |
| coverage                         | 54.9 ms                          | 70.5 ms: 1.28x slower            |
| crypto_pyaes                     | 62.8 ms                          | 55.1 ms: 1.14x faster            |
| deepcopy                         | 397 us                           | 330 us: 1.20x faster             |
| deepcopy_reduce                  | 3.95 us                          | 3.01 us: 1.31x faster            |
| deepcopy_memo                    | 35.3 us                          | 29.7 us: 1.19x faster            |
| django_template                  | 40.3 ms                          | 35.2 ms: 1.14x faster            |
| docutils                         | 2.11 sec                         | 2.01 sec: 1.05x faster           |
| dulwich_log                      | 60.7 ms                          | 57.6 ms: 1.05x faster            |
| fannkuch                         | 428 ms                           | 333 ms: 1.28x faster             |
| float                            | 75.7 ms                          | 71.3 ms: 1.06x faster            |
| gc_traversal                     | 2.76 ms                          | 2.69 ms: 1.03x faster            |
| go                               | 105 ms                           | 109 ms: 1.04x slower             |
| html5lib                         | 55.2 ms                          | 58.0 ms: 1.05x slower            |
| json_dumps                       | 8.31 ms                          | 9.37 ms: 1.13x slower            |
| logging_format                   | 6.62 us                          | 6.01 us: 1.10x faster            |
| logging_silent                   | 98.0 ns                          | 89.9 ns: 1.09x faster            |
| logging_simple                   | 5.84 us                          | 5.25 us: 1.11x faster            |
| meteor_contest                   | 84.8 ms                          | 98.0 ms: 1.16x slower            |
| nqueens                          | 78.9 ms                          | 89.2 ms: 1.13x slower            |
| pickle                           | 8.06 us                          | 10.4 us: 1.29x slower            |
| pickle_list                      | 2.69 us                          | 3.25 us: 1.21x slower            |
| pprint_safe_repr                 | 674 ms                           | 665 ms: 1.01x faster             |
| pprint_pformat                   | 1.39 sec                         | 1.36 sec: 1.02x faster           |
| pyflate                          | 350 ms                           | 374 ms: 1.07x slower             |
| python_startup                   | 13.8 ms                          | 15.0 ms: 1.08x slower            |
| python_startup_no_site           | 6.69 ms                          | 6.90 ms: 1.03x slower            |
| raytrace                         | 283 ms                           | 228 ms: 1.24x faster             |
| regex_compile                    | 124 ms                           | 112 ms: 1.11x faster             |
| regex_dna                        | 129 ms                           | 148 ms: 1.14x slower             |
| regex_v8                         | 17.0 ms                          | 24.5 ms: 1.44x slower            |
| scimark_fft                      | 269 ms                           | 320 ms: 1.19x slower             |
| scimark_monte_carlo              | 60.5 ms                          | 54.6 ms: 1.11x faster            |
| scimark_sparse_mat_mult          | 4.20 ms                          | 4.49 ms: 1.07x slower            |
| sqlglot_normalize                | 110 ms                           | 128 ms: 1.16x slower             |
| sqlglot_optimize                 | 60.8 ms                          | 54.8 ms: 1.11x faster            |
| sqlglot_transpile                | 1.42 ms                          | 1.31 ms: 1.08x faster            |
| sqlite_synth                     | 2.09 us                          | 2.39 us: 1.14x slower            |
| sympy_sum                        | 139 ms                           | 131 ms: 1.06x faster             |
| telco                            | 6.96 ms                          | 7.61 ms: 1.09x slower            |
| tomli_loads                      | 1.91 sec                         | 1.77 sec: 1.08x faster           |
| typing_runtime_protocols         | 189 us                           | 161 us: 1.17x faster             |
| unpack_sequence                  | 32.9 ns                          | 35.0 ns: 1.06x slower            |
| unpickle                         | 11.5 us                          | 12.8 us: 1.11x slower            |
| unpickle_list                    | 3.95 us                          | 3.59 us: 1.10x faster            |
| unpickle_pure_python             | 205 us                           | 175 us: 1.17x faster             |
| xml_etree_parse                  | 141 ms                           | 122 ms: 1.16x faster             |
| xml_etree_iterparse              | 89.7 ms                          | 85.0 ms: 1.05x faster            |
| xml_etree_generate               | 85.1 ms                          | 79.6 ms: 1.07x faster            |
| xml_etree_process                | 68.7 ms                          | 52.6 ms: 1.31x faster            |
| Geometric mean                   | (ref)                            | 1.03x faster                     |

Benchmark hidden because not significant (29): async_tree_cpu_io_mixed_tg, async_tree_eager_memoization, asyncio_tcp, dask, deltablue, create_gc_cycles, generators, genshi_text, genshi_xml, hexiom, json_loads, mako, mdp, nbody, pathlib, pickle_dict, pickle_pure_python, pidigits, regex_effbot, richards, richards_super, scimark_lu, scimark_sor, spectral_norm, sqlglot_parse, sympy_expand, sympy_integrate, sympy_str, tornado_http
Ignored benchmarks (2) of benchmark_results/python3.12.9_2025-02-10_16-18-20.json: sqlalchemy_declarative, sqlalchemy_imperative
# Python Performance Comparison

## System Information
```
Unable to retrieve full system info due to permissions.
Error: ```

## Benchmark Results
```
```
