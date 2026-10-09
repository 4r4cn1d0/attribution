# Release inventory

Written by `build_release.py inventory` (deterministic; re-run it to refresh). M is the main checkout (read only), W the Side Project worktree. The builder opens only the files below and keeps only the fields listed. It never opens an answer file (`samples.jsonl`, `generations.jsonl`) or a prompt bank. JSON records are parsed whole and cut down at once to the named fields; the blind read's note column is dropped as each row is read.

Units: 28 (every unit of the note's Tables 1-3: 4 untuned, 24 fine-tuned).

## Units and their label sources

### olmo2-1b_untuned

- Note: OLMo-2-1B, untuned, checkpoint init
- Configuration: `study-kt-olmo2-1b-r64-b-mb4-20261008.json`; engine `55253874`; data manifest `9ed61826`
- Evaluation folder: `M/tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-init-a1/eval/init`
  - `summary.json` `7b40ea1c99bbfffdbc1711008f4fd10ba83cb5bca782c473fb6c16ee20f80801`
  - `guard_samples.jsonl` `1f578d091f46a27aa05290f8dbc9aae4cd7a7552475da72016f859c1be29549b`
  - `guard.jsonl` `fc8a2e32d6c07924be9ed5ea40cc4d2d8c6b49da24b172c3269006a02a09d925`
  - `query_loss.jsonl` `02963ba5559077dfae9dd48a29ac5470507d05d48377966195545a8d979d27a6`
  - `job.json` `f3b8c1864aaacf34738b34ff6c26cc8f51677e7eb5a6a9445818692d5365a582`
  - `COMPLETE.json` `b5083ce9d9f26efe92f9872fdbf9376a521a5d99d1b70cc2bd460987cdcc9474`
- HarmBench (pod): `M/tmp/judge-pod/olmo-b-g-untuned/fetched/out/harmbench-pod.jsonl` `c44ddeb808a8e95a353786c4cc1566425d1943c48019bd23ffd420819e0b79e1`, records with complete_sha256 `b5083ce9d9f26efe...`
- HarmBench (Mac): `M/tmp/family-probe-olmo2-1b/harmbench-items.jsonl` `2851ee4dc65a256dfd244de933664e8b1cd8d6b3a5f963d364b42cd9450a54aa`, unit `untuned`
- Granite (Mac): `M/tmp/family-probe-olmo2-1b/second-judge-probe-items.jsonl` `c2ef1130fd540eb822225b42e73297143fdbf17d40a95b8d936205f227feb547`, unit `1101-a0-init-a1`
- Opening crosstabs: `M/tmp/mechanism-recipes/results.json` `2e39e88b3c8fdc5285743aad8500998adf6defa6b8670ea9435b3316c8f04718`, unit `olmo-untuned`
- Blind read: key unit `olmo-untuned`

### qwen2.5-1.5b_untuned

- Note: Qwen2.5-1.5B, untuned, checkpoint init
- Configuration: `study-kt-instruct-r64-mb4-20261006.json`; engine `c52c0ebc`; data manifest `9247c4bb`
- Evaluation folder: `M/tmp/kill-test-stage0/retrieved/s0-1101/tree/round1/1101-a0-init-a1/eval/init`
  - `summary.json` `acff0a8436777d3f40b4212410b35f811f6aa4030590ab5758af02c49981a455`
  - `guard_samples.jsonl` `63565bde269f77cd3be4e1094b28f9d0b9cba9f385ce5af73c89ee397961247e`
  - `guard.jsonl` `8f91ffa485e140e282654ec8b9e625cdeb14eb015c9bb97e39c8555ac44b4a16`
  - `query_loss.jsonl` `802b926081a508570bd8e715739b4b34a127eb110fbf57ee7cae907ad04a3100`
  - `job.json` `7031566aa1956f72f0f2e3ba33d25e5453cb61931a9b75580be4a47e78b92e79`
  - `COMPLETE.json` `fde132cbc335a32239299cbb9ceebf09ecb388740001fb7e016e99900adbeb9a`
- HarmBench (pod): `M/tmp/judge-pod/side-qwen-llama-pairs/fetched/out/harmbench-pod.jsonl` `a5b58bd899e7e532853cbbf85a178f57cb3f89c6d60673ac3be80fc0b544e0ef`, records with complete_sha256 `fde132cbc335a322...`
- Granite (Mac): `M/tmp/kill-test-stage0/second-judge-kt-items.jsonl` `fe1d089cdc4604fc1d0d7f3f94f75644eaec441ac5b091136d32b3f666472fc1`, unit `1101-a0-init-a1`
- Opening crosstabs: `M/tmp/mechanism-recipes/results.json` `2e39e88b3c8fdc5285743aad8500998adf6defa6b8670ea9435b3316c8f04718`, unit `qwen-untuned`

### qwen2.5-7b_untuned

- Note: Qwen2.5-7B, untuned, checkpoint init
- Configuration: `study-kt-qwen7b-r64-b-mb2-20261007.json`; engine `c52c0ebc`; data manifest `9247c4bb`
- Evaluation folder: `M/tmp/kill-test-7b-check/retrieved/q7-1101/tree/round1/1101-a0-init-a1/eval/init`
  - `summary.json` `683e00871e0b74b3ad3e22ad1d1af6c7c5b27c10f5d0ba8f33a2ac7c830c6b5f`
  - `guard_samples.jsonl` `b234b6589b15bdf9e1c8df5a2679b9033ae8031228a6add390426102af7a8d1b`
  - `guard.jsonl` `c3e453ea51a631e2ad34d877daeca5a078c26b285059d367b6864f72c1df3226`
  - `query_loss.jsonl` `c8e1a69e5f82df766debe7cebe9381c515c6d506bfaf936c7aff5c384ceadf3e`
  - `job.json` `0d098ec5f56537ae7cb79645aedc42889c337d40399b59d9bb7082a2e47fc8e5`
  - `COMPLETE.json` `24acd43a4093a842e140605f4f90f0da6de5173493776bd7334ffe5aaf59e165`
- HarmBench (pod): `M/tmp/judge-pod/side-qwen-llama-pairs/fetched/out/harmbench-pod.jsonl` `a5b58bd899e7e532853cbbf85a178f57cb3f89c6d60673ac3be80fc0b544e0ef`, records with complete_sha256 `24acd43a4093a842...`
- Granite (Mac): `M/tmp/kill-test-7b-check/second-judge-kt-items.jsonl` `76a6031a6a7e8a0e51d376aa8dbe87fa76ac5981527931c364f2fa2a97ae4455`, unit `1101-a0-init-a1`

### llama3.2-1b_untuned

- Note: Llama-3.2-1B, untuned, checkpoint init
- Configuration: `study-kt-llama32-1b-r64-b-mb4-20261008.json`; engine `e49a978c`; data manifest `c52a50af`
- Evaluation folder: `M/tmp/family-probe-llama32-1b/retrieved/llama32-1b-1101/tree/round1/1101-a0-init-a1/eval/init`
  - `summary.json` `ec084124f23e5b2b2a1580242becaafd62ba7ee891ac546c9caf6727bcc5f8d3`
  - `guard_samples.jsonl` `a33649f313db941e5736e32212618b777bb0bfeb37b6da56fc4d7597c08645ee`
  - `guard.jsonl` `a3468320481f85a14137489f72ff2bfd1d0a921e3ae9ec3c386797d7a314da32`
  - `query_loss.jsonl` `74def1317f0b7e69ef2383d16de6c10d0336db11727c5aa28a9c50af51dd743b`
  - `job.json` `727d4183aa860fdeefc0c5f240f3f2955241ccdc998935777f95da03f93bd85a`
  - `COMPLETE.json` `b9e84745dfed11da74ab2ffe1cc0e5cdb2fa2b255878bab2ca709905c8cfc415`
- HarmBench (pod): `M/tmp/judge-pod/side-qwen-llama-pairs/fetched/out/harmbench-pod.jsonl` `a5b58bd899e7e532853cbbf85a178f57cb3f89c6d60673ac3be80fc0b544e0ef`, records with complete_sha256 `b9e84745dfed11da...`
- Granite (Mac): `M/tmp/family-probe-llama32-1b/second-judge-probe-items.jsonl` `d8f612df52106bca4eaa59560ccf2332501eb6827506b21d2d7401acb39d8840`, unit `1101-a0-init-a1`
- Granite (pod): `M/tmp/judge-pod/granite-llama-b-1/fetched/out/granite-pod.jsonl` `0ea0ed8183af1f702c3030b0deaf1aefa20bfe1439688540feef7ec4e42c4b2b`
- Opening crosstabs: `M/tmp/family-probe-llama32-1b/mechanism-llama/results.json` `7011993dd67e5ea1a01a24846fa9a9cceb6f50c9bd0163954510bf95f49bf6d7`, unit `llama-untuned`
- Blind read: key unit `llama-untuned`

### olmo2-1b_constant_1101_e1

- Note: OLMo-2-1B, Constant, seed 1101, checkpoint e1; E against `olmo2-1b_untuned`
- Configuration: `study-kt-olmo2-1b-r64-b-mb4-20261008.json`; engine `55253874`; data manifest `9ed61826`
- Evaluation folder: `M/tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1/eval/e1`
  - `summary.json` `f331eadee052f8f1c45403b7f19b7da7f1cfa1153d2b450285d3e777ca11171a`
  - `guard_samples.jsonl` `68d39f131827783b5e1e3a9d132f7a33e05d96ab6dbe9fb441684f75b6091426`
  - `guard.jsonl` `27668f068f85a8b95dc16c690027d66fed82ff6e5ce56a9e754662f29908b4bf`
  - `query_loss.jsonl` `a539638fc5c7f5b98594094690b114fb5714343e4f497451301cce9630a189d1`
  - `job.json` `3e60568ac11e32f3f429aa2606bc38c9b881456fd262a120e526ccb189022402`
  - `COMPLETE.json` `8f0fa83a42ccc5edc54a5ee26ed63f49448c36d30adbd64e28b655678afee4c9`
- HarmBench (pod): `M/tmp/judge-pod/olmo-b-g-untuned/fetched/out/harmbench-pod.jsonl` `c44ddeb808a8e95a353786c4cc1566425d1943c48019bd23ffd420819e0b79e1`, records with complete_sha256 `8f0fa83a42ccc5ed...`
- HarmBench (Mac): `M/tmp/family-probe-olmo2-1b/harmbench-items.jsonl` `2851ee4dc65a256dfd244de933664e8b1cd8d6b3a5f963d364b42cd9450a54aa`, unit `e1-1101`
- Granite (Mac): `M/tmp/family-probe-olmo2-1b/second-judge-probe-items.jsonl` `c2ef1130fd540eb822225b42e73297143fdbf17d40a95b8d936205f227feb547`, unit `1101-a0-e1-a1`
- Granite device in the note's tables: mac
- Opening crosstabs: `M/tmp/mechanism-recipes/results.json` `2e39e88b3c8fdc5285743aad8500998adf6defa6b8670ea9435b3316c8f04718`, unit `olmo-e1-1101`
- Blind read: key unit `olmo-b-1101`

### olmo2-1b_constant_1102_e1

- Note: OLMo-2-1B, Constant, seed 1102, checkpoint e1; E against `olmo2-1b_untuned`
- Configuration: `study-kt-olmo2-1b-r64-b-mb4-20261008.json`; engine `55253874`; data manifest `9ed61826`
- Evaluation folder: `M/tmp/family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102/tree/round1/1102-a0-e1-a1/eval/e1`
  - `summary.json` `0918dc486803a0d3357d43e3fca323b9a29c6ae1379741486b03aa7bd36294f0`
  - `guard_samples.jsonl` `25a74527f43052bea59978b9a58297197786f590d2d1db333efe62c9271998b3`
  - `guard.jsonl` `c289873099785b4c0817da4a29067dbe68511b71abec4390f1492b6126c76fe4`
  - `query_loss.jsonl` `2f73f77c40b161572572d8d18b317d21c26738bf2aed1e337b4ed7b7645f3e20`
  - `job.json` `de65ca1936a10c199de46e764a948268b03367c586c09747381850059064083c`
  - `COMPLETE.json` `857f78bc0f49cc8a4902fbb6211f463daa7c7f44086257c4d752409a30ba0b25`
- HarmBench (pod): `M/tmp/judge-pod/olmo-b-g-untuned/fetched/out/harmbench-pod.jsonl` `c44ddeb808a8e95a353786c4cc1566425d1943c48019bd23ffd420819e0b79e1`, records with complete_sha256 `857f78bc0f49cc8a...`
- HarmBench (Mac): `M/tmp/family-probe-olmo2-1b/harmbench-items.jsonl` `2851ee4dc65a256dfd244de933664e8b1cd8d6b3a5f963d364b42cd9450a54aa`, unit `e1-1102`
- Granite (Mac): `M/tmp/family-probe-olmo2-1b-gateA-1102/second-judge-probe-items.jsonl` `2b537302fe412716e047294758f442a4c317d068bb5f6f6e89fbb1b3e2d92105`, unit `1102-a0-e1-a1`
- Granite device in the note's tables: mac
- Opening crosstabs: `M/tmp/mechanism-recipes/results.json` `2e39e88b3c8fdc5285743aad8500998adf6defa6b8670ea9435b3316c8f04718`, unit `olmo-e1-1102`
- Blind read: key unit `olmo-b-1102`

### olmo2-1b_constant_1103_e1

- Note: OLMo-2-1B, Constant, seed 1103, checkpoint e1; E against `olmo2-1b_untuned`
- Configuration: `study-kt-olmo2-1b-r64-b-mb4-20261008.json`; engine `55253874`; data manifest `9ed61826`
- Evaluation folder: `M/tmp/family-probe-olmo2-1b-gateA-1103/retrieved/olmo2-1b-1103/tree/round1/1103-a0-e1-a1/eval/e1`
  - `summary.json` `7d24950cb2ad221dfcd0e27c0c40cc6745c52dcaac4612a966474310d85cf918`
  - `guard_samples.jsonl` `7839edc3ceffec25054b76e5007c01301c34ce0dc36e3923186f81470a152990`
  - `guard.jsonl` `55339f54dfcc7224a8749f211be2c79b67376f709c2703edcc7fb9efc1904886`
  - `query_loss.jsonl` `eba947241293ed571f7bb5ce507b59af98911cd411be323f9a8c901a1ae79612`
  - `job.json` `895f8bd2a66e20df2256b43d1e71a263da237a1cb3ea498cd439086aef5ae293`
  - `COMPLETE.json` `7be58eaa9c5be7b8f94668109efd6aae075b1d001e0d2b1fb8be814556899cbd`
- HarmBench (pod): `M/tmp/judge-pod/olmo-b-g-untuned/fetched/out/harmbench-pod.jsonl` `c44ddeb808a8e95a353786c4cc1566425d1943c48019bd23ffd420819e0b79e1`, records with complete_sha256 `7be58eaa9c5be7b8...`
- HarmBench (Mac): `M/tmp/family-probe-olmo2-1b/harmbench-items.jsonl` `2851ee4dc65a256dfd244de933664e8b1cd8d6b3a5f963d364b42cd9450a54aa`, unit `e1-1103`
- Granite (Mac): `M/tmp/family-probe-olmo2-1b-gateA-1103/second-judge-probe-items.jsonl` `0a1e236ff0a211d7443e18f673b2bd14f8cea3fd66c507a83510df0fae316cfe`, unit `1103-a0-e1-a1`
- Granite device in the note's tables: mac
- Opening crosstabs: `M/tmp/mechanism-recipes/results.json` `2e39e88b3c8fdc5285743aad8500998adf6defa6b8670ea9435b3316c8f04718`, unit `olmo-e1-1103`
- Blind read: key unit `olmo-b-1103`

### olmo2-1b_constant-token-mean_1101_e1

- Note: OLMo-2-1B, Constant, token-mean, seed 1101, checkpoint e1; E against `olmo2-1b_untuned`
- Configuration: `study-kt-olmo2-1b-r64-bt-mb4-20261008.json`; engine `e49a978c`; data manifest `9ed61826`
- Evaluation folder: `M/tmp/family-probe-olmo2-1b-bt/retrieved/olmo2-1b-bt-1101/tree/round1/1101-a0-e1-a1/eval/e1`
  - `summary.json` `4978780343964ea4e9dcab76f8b40eac6d628d3762a9ac76ef0b487d04b44150`
  - `guard_samples.jsonl` `7a5cdcf8e2b4c3e4d01ad784e1951c6c6f47147beabe88676a4d17efc08beeac`
  - `guard.jsonl` `fee0a477800f14ece65599d9e7ff3d79b058f686a0f36f89390a10a7e63fc427`
  - `query_loss.jsonl` `9725387bed34f22721cd7a8049e64adacb4dee21c5fd7fef4eae664876db6388`
  - `job.json` `5b57d4c593c69dd755d7a79cf8a88f349f8043ac02777eb5afc51e2db2720a9f`
  - `COMPLETE.json` `0ccf97de823c24990d0f78023beb58819fba5cb4e6afb2560ceac71715067fef`
- Granite (Mac): `M/tmp/family-probe-olmo2-1b-bt/second-judge-probe-items.jsonl` `b0cf190b87b4ec10eb537104f48263a863f3402b94dc3fa9898ef1c74c33e96d`, unit `1101-a0-e1-a1`
- Granite device in the note's tables: mac
- Opening crosstabs: `M/tmp/mechanism-recipes/results.json` `2e39e88b3c8fdc5285743aad8500998adf6defa6b8670ea9435b3316c8f04718`, unit `olmo-bt-e1-1101`

### olmo2-1b_scheduled_1101_e1

- Note: OLMo-2-1B, Scheduled, seed 1101, checkpoint e1; E against `olmo2-1b_untuned`
- Configuration: `study-kt-olmo2-1b-r64-g-mb4-20261008.json`; engine `e49a978c`; data manifest `9ed61826`
- Evaluation folder: `M/tmp/family-probe-olmo2-1b-g/retrieved/olmo2-1b-g-1101/tree/round1/1101-a0-e1-a1/eval/e1`
  - `summary.json` `300b1246da4ec9a6cd65d15e5bc9206bf98510226d0a83a7d9251b338944753a`
  - `guard_samples.jsonl` `fdc9059d8caa2f3cd5ef406065e9e8cf63253cbf63366bacf73cc4df0a20f4e0`
  - `guard.jsonl` `38fbf8ce443816fa6364bc5964d308d245c444850d526982c928f3bd089c4016`
  - `query_loss.jsonl` `41d9ef468d0496038c5e7f2f0166967213199c2ef9f61ecd1160f988baca3eb3`
  - `job.json` `1a292c1d71729a3a5cca33ec1a452be634e07a6cb77b7efc856fb38b7b2a56dd`
  - `COMPLETE.json` `557a083f0dad77bc50dd749e805be076eaa75eb1ea50b8ce356736a6207f8a09`
- HarmBench (pod): `M/tmp/judge-pod/olmo-b-g-untuned/fetched/out/harmbench-pod.jsonl` `c44ddeb808a8e95a353786c4cc1566425d1943c48019bd23ffd420819e0b79e1`, records with complete_sha256 `557a083f0dad77bc...`
- Granite (Mac): `M/tmp/family-probe-olmo2-1b-g/second-judge-probe-items.jsonl` `554aa28a747ce42d4a2f5a57aa5a05ae399a2986178fbe28fe037a453e0dd6e1`, unit `1101-a0-e1-a1`
- Granite device in the note's tables: mac
- Opening crosstabs: `M/tmp/mechanism-recipes/results.json` `2e39e88b3c8fdc5285743aad8500998adf6defa6b8670ea9435b3316c8f04718`, unit `olmo-G-e1-1101`
- Blind read: key unit `olmo-g-1101`

### olmo2-1b_scheduled_1102_e1

- Note: OLMo-2-1B, Scheduled, seed 1102, checkpoint e1; E against `olmo2-1b_untuned`
- Configuration: `study-kt-olmo2-1b-r64-g-mb4-20261008.json`; engine `e49a978c`; data manifest `9ed61826`
- Evaluation folder: `M/tmp/family-probe-olmo2-1b-g-seed1102/retrieved/olmo2-1b-g-1102/tree/round1/1102-a0-e1-a1/eval/e1`
  - `summary.json` `5c51c0f19fd6439f3586de8d6c9a846dc306d3e51448d5236427d2f60938c66d`
  - `guard_samples.jsonl` `0a78638541f85990a17b765680e325583b8e8f88996516d16cebecb1121c8e10`
  - `guard.jsonl` `fac17bcd57ee99f4d0501137bb1c1eefe1720c3dbd9f8bef91d697136689a919`
  - `query_loss.jsonl` `38377286512544d3bfa24ca27a791fb7d18e1479d956838e5d08af4f97a0da4c`
  - `job.json` `97b7c5ec736c97dd04a4f23fff99bdfc9465733bc3a1929479eaf31748e9fd04`
  - `COMPLETE.json` `7c16beec76971793c9ffb51c5832f645e0dbe70e74b1954fe48556273d9d3157`
- HarmBench (pod): `M/tmp/judge-pod/olmo-b-g-untuned/fetched/out/harmbench-pod.jsonl` `c44ddeb808a8e95a353786c4cc1566425d1943c48019bd23ffd420819e0b79e1`, records with complete_sha256 `7c16beec76971793...`
- Granite (Mac): `M/tmp/family-probe-olmo2-1b-g-seed1102/second-judge-probe-items.jsonl` `41e9f8654fef48033a055435d97e4d8d4a5fd3bae91f0eafe1312273877fdf9b`, unit `1102-a0-e1-a1`
- Granite device in the note's tables: mac
- Opening crosstabs: `M/tmp/mechanism-recipes/results.json` `2e39e88b3c8fdc5285743aad8500998adf6defa6b8670ea9435b3316c8f04718`, unit `olmo-G-e1-1102`

### olmo2-1b_scheduled_1103_e1

- Note: OLMo-2-1B, Scheduled, seed 1103, checkpoint e1; E against `olmo2-1b_untuned`
- Configuration: `study-kt-olmo2-1b-r64-g-mb4-20261008.json`; engine `e49a978c`; data manifest `9ed61826`
- Evaluation folder: `M/tmp/family-probe-olmo2-1b-g-seed1103/retrieved/olmo2-1b-g-1103/tree/round1/1103-a0-e1-a1/eval/e1`
  - `summary.json` `aa9ff4d04064d17e42e09da66ed63460e579e30678feff96ac02154ebca57f86`
  - `guard_samples.jsonl` `a06013aea4713193c6b162c72113ee9faaa0d956cb7a68949d54645e84ae3315`
  - `guard.jsonl` `12841445b922a209dbba1d5052d21311f1b0efcf7498d911210d380981029e51`
  - `query_loss.jsonl` `1e3e77a88c8addf8cc485809c90c620550074620edb28f4512c68fcca5b97cdc`
  - `job.json` `2573e30472fbb574ec8965d9f43fa5dd335f60d5fbf53f03aedf0a9c24374111`
  - `COMPLETE.json` `6db69ca4fc5e9b902eba3ea194cb2b7e180e3f2d26fed330ffc185cfa55c71fc`
- HarmBench (pod): `M/tmp/judge-pod/olmo-b-g-untuned/fetched/out/harmbench-pod.jsonl` `c44ddeb808a8e95a353786c4cc1566425d1943c48019bd23ffd420819e0b79e1`, records with complete_sha256 `6db69ca4fc5e9b90...`
- Granite (Mac): `M/tmp/family-probe-olmo2-1b-g-seed1103/second-judge-probe-items.jsonl` `6dd76ad0e93d6f747b9d4b8f8e01024d47d148347eafcae83443e2695413d504`, unit `1103-a0-e1-a1`
- Granite device in the note's tables: mac
- Opening crosstabs: `M/tmp/mechanism-recipes/results.json` `2e39e88b3c8fdc5285743aad8500998adf6defa6b8670ea9435b3316c8f04718`, unit `olmo-G-e1-1103`

### olmo2-1b_scheduled-half-lr_1101_e1

- Note: OLMo-2-1B, Scheduled, half LR, seed 1101, checkpoint e1; E against `olmo2-1b_untuned`
- Configuration: `study-kt-olmo2-1b-r64-g5e5-mb4-20261008.json`; engine `e49a978c`; data manifest `9ed61826`
- Evaluation folder: `M/tmp/family-probe-olmo2-1b-g5e5/retrieved/olmo2-1b-g5e5-1101/tree/round1/1101-a0-e1-a1/eval/e1`
  - `summary.json` `373da7d0d86c67c817ee7d1c1ee53bfb8a6f416e56095f240b9b22e0217416fd`
  - `guard_samples.jsonl` `9e709e0513963bb1e2dfc5bd1382e201335b71752dac92090ee82c98a95998d0`
  - `guard.jsonl` `914b40bbd6b355b8c9ccbca4df5075e5c801241fee3440bfc290dbdab8df06f0`
  - `query_loss.jsonl` `dde7ad96a5ec0bf7f4b67132401ec54150c824a8d1478b5f52fec9e97cbca90c`
  - `job.json` `01b3fa5957e93dda60690dfe261ad2c37fd5a9fa8ecb3dffea2d9fee8e17e010`
  - `COMPLETE.json` `1cfc8bd9050e88efab472c33b98085c1fe1b816030e6ab3d84b48101a094247a`
- Granite (Mac): `M/tmp/family-probe-olmo2-1b-g5e5/second-judge-probe-items.jsonl` `05986d285ae1fabfdfc036d81445dc5c88d0e56c0a386882e11e28edd4f0f834`, unit `1101-a0-e1-a1`
- Granite device in the note's tables: mac

### olmo2-1b_scheduled-half-lr_1102_e1

- Note: OLMo-2-1B, Scheduled, half LR, seed 1102, checkpoint e1; E against `olmo2-1b_untuned`
- Configuration: `study-kt-olmo2-1b-r64-g5e5-mb4-20261008.json`; engine `e49a978c`; data manifest `9ed61826`
- Evaluation folder: `M/tmp/family-probe-olmo2-1b-g5e5-seed1102/retrieved/olmo2-1b-g5e5-1102/tree/round1/1102-a0-e1-a1/eval/e1`
  - `summary.json` `f6c1e1f8115e5fedadece218cdff7f873cbfcdcbbf57018624e69bdd8f14b764`
  - `guard_samples.jsonl` `bc40d1bd1db41fc1060dd7959e71c9ad52eea1e4cb900131d2e122ba89a1bdd0`
  - `guard.jsonl` `b1aef5e0db3c9343e6a0989e8e336f4e8bd2851b4a726482f2f8cf9eb212ffbb`
  - `query_loss.jsonl` `0692b86f0227e5ca2b243b391c93de44bfea19928d4abcdcf6b02fbf5483011f`
  - `job.json` `9a58dd69d5b4d6bbe96d206ef9668f8159e70675d60c164ca952b02d895ad752`
  - `COMPLETE.json` `2ec864bc71f9d1247e041f895c8727007a43861c5e4f4faa001898d831c29a8b`
- Granite (Mac): `M/tmp/family-probe-olmo2-1b-g5e5-seed1102/second-judge-probe-items.jsonl` `7b5543d432bd6bca7ae509304e80336ccd6072b9eb6ed103f5e64e54a2637688`, unit `1102-a0-e1-a1`
- Granite device in the note's tables: mac

### olmo2-1b_scheduled-rank16_1101_e1

- Note: OLMo-2-1B, Scheduled, rank 16, seed 1101, checkpoint e1; E against `olmo2-1b_untuned`
- Configuration: `study-kt-olmo2-1b-r16-g-mb4-20261008.json`; engine `e49a978c`; data manifest `9ed61826`
- Evaluation folder: `M/tmp/family-probe-olmo2-1b-g-r16/retrieved/olmo2-1b-g-r16-1101/tree/round1/1101-a0-e1-a1/eval/e1`
  - `summary.json` `69ea79f342100166e1dd7b8f527c71bfa7136867d7f108fe499f3f5cb2760e58`
  - `guard_samples.jsonl` `18935cc51ed92cb828dd3ddfbdc0310e94203499ef855d1ae5aa27eaf6ee1f94`
  - `guard.jsonl` `a413755dbc5bbb0f89c5665a817baa81e71b59cb41ec10c894279535e4ccd64f`
  - `query_loss.jsonl` `f3008bdf292c37f5f7bc9f80ba2f5f670e988f25f0e6b73aa19505df02940301`
  - `job.json` `2e05692c7355920951f22e5f2d5a451abfeb7b8c913a0cbfb88780fe1c25c9f5`
  - `COMPLETE.json` `425922e550bf51fbd6ea67b58191ee6d7f5f75e5d64f4087794293bcc632d02a`
- Granite (Mac): `M/tmp/family-probe-olmo2-1b-g-r16/second-judge-probe-items.jsonl` `4e798c5594ff53ac36d166f6bd96a1b425b3f85f750d9bec1e4c6e31146fa927`, unit `1101-a0-e1-a1`
- Granite device in the note's tables: mac
- Opening crosstabs: `M/tmp/mechanism-recipes/results.json` `2e39e88b3c8fdc5285743aad8500998adf6defa6b8670ea9435b3316c8f04718`, unit `olmo-G-r16-e1-1101`

### qwen2.5-1.5b_constant_1101_e1

- Note: Qwen2.5-1.5B, Constant, seed 1101, checkpoint e1; E against `qwen2.5-1.5b_untuned`
- Configuration: `study-kt-instruct-r64-b-20261007.json`; engine `c52c0ebc`; data manifest `9247c4bb`
- Evaluation folder: `M/tmp/kill-test-gateA-b/retrieved/b-1101/tree/round1/1101-a0-e1-a1/eval/e1`
  - `summary.json` `c4ecdcabadab697b16bd1fd086dbfae4350807eb1a70361d79f0c768f6efdc34`
  - `guard_samples.jsonl` `1f208a9e5479cf28d08cc2bdb5b957849d2e8285249f0e05e0c013efc91eb983`
  - `guard.jsonl` `a2b8c29b20a937f73a9920622706d28370e493996274a3db918e82e93fae9323`
  - `query_loss.jsonl` `c8f86a1013013da563a700b7d20253c42aca89bece5f831d80a2eb0c4f31b32a`
  - `job.json` `bfb0448b93ebc8c9e5738d0fd103574c2de6a4233305af3035448b43170d3819`
  - `COMPLETE.json` `bb7813625b7d982b36d002ad0b55751e788b31bf10b69d7744a6c65cc3e3c179`
- HarmBench (pod): `M/tmp/judge-pod/side-qwen-llama-pairs/fetched/out/harmbench-pod.jsonl` `a5b58bd899e7e532853cbbf85a178f57cb3f89c6d60673ac3be80fc0b544e0ef`, records with complete_sha256 `bb7813625b7d982b...`
- Opening crosstabs: `M/tmp/mechanism-recipes/results.json` `2e39e88b3c8fdc5285743aad8500998adf6defa6b8670ea9435b3316c8f04718`, unit `qwen-B-e1-1101`
- Blind read: key unit `qwen1.5b-b-1101`

### qwen2.5-1.5b_constant-rank16_1101_e1

- Note: Qwen2.5-1.5B, Constant, rank 16, seed 1101, checkpoint e1; E against `qwen2.5-1.5b_untuned`
- Configuration: `study-kt-instruct-r16-b-20261008.json`; engine `c52c0ebc`; data manifest `9247c4bb`
- Evaluation folder: `M/tmp/kill-test-r16/retrieved/r16-1101/tree/round1/1101-a0-e1-a1/eval/e1`
  - `summary.json` `f591cf41fd4892bf99f2db796ce7abd30fa5a02d7a8fc2f5a8de42a226db995f`
  - `guard_samples.jsonl` `9989adf6e6561b731fce8c3ef27fa248eee342dbf1ad2306f726716c7d62dfc7`
  - `guard.jsonl` `32db7995ac932e6ef287b6a0935785b74dbccd68ba6729cb6b1d1b14b550025d`
  - `query_loss.jsonl` `c8815f3efbbb3b059ae30541474a2bd0caf890370cadcaaef2a92a345ac6d047`
  - `job.json` `54ecff4dbd5570d62f8911e6c417719e7ed1ed2a994678b4af63467318d78823`
  - `COMPLETE.json` `039ccca9f1edfa826dd9610972e816f5d61985eb06a1f52d0a295f2ced26b0c1`
- HarmBench (pod): `M/tmp/judge-pod/side-qwen-llama-pairs/fetched/out/harmbench-pod.jsonl` `a5b58bd899e7e532853cbbf85a178f57cb3f89c6d60673ac3be80fc0b544e0ef`, records with complete_sha256 `039ccca9f1edfa82...`
- Granite (Mac): `M/tmp/kill-test-r16/second-judge-kt-items.jsonl` `191b80b1ff1999d971efce52617d93d665cd0b7938fe1f04b499d64ac3da8bf5`, unit `1101-a0-e1-a1`
- Granite device in the note's tables: mac

### qwen2.5-1.5b_high-dose_1101_e3

- Note: Qwen2.5-1.5B, High-dose, seed 1101, checkpoint e3; E against `qwen2.5-1.5b_untuned`
- Configuration: `study-kt-instruct-r64-mb4-20261006.json`; engine `c52c0ebc`; data manifest `9247c4bb`
- Evaluation folder: `M/tmp/kill-test-stage0/retrieved/s0-1101/tree/round1/1101-a0-e3-a1/eval/e3`
  - `summary.json` `e4c7cac2718d535a0a0931f20c3ed736b4becfd72641e709d3b34f1ed129ec4f`
  - `guard_samples.jsonl` `d009e7d59abb3a4a0025e8382f907fd38e90f68dbfaadfc0ccc2a7a7bd86aa43`
  - `guard.jsonl` `a73073e7d961435dea691556278b5a196bb0579816d3aa477bdb99165297abf8`
  - `query_loss.jsonl` `3e0d86ec92595679781e31eaf253c9e8330275ef991b539cb76c8ff827340b70`
  - `job.json` `cd15b095ccd3efa7b7fa442df06d376b76003dd005acf90d5ad51c31d1c55a7f`
  - `COMPLETE.json` `7a09557d9bbf17c595fb92df94dd635868e018d5cbaad44b9884e582cff82c2c`
- Granite (Mac): `M/tmp/kill-test-stage0/second-judge-kt-items.jsonl` `fe1d089cdc4604fc1d0d7f3f94f75644eaec441ac5b091136d32b3f666472fc1`, unit `1101-a0-e3-a1`
- Granite device in the note's tables: mac

### qwen2.5-1.5b_high-dose_1102_e3

- Note: Qwen2.5-1.5B, High-dose, seed 1102, checkpoint e3; E against `qwen2.5-1.5b_untuned`
- Configuration: `study-kt-instruct-r64-mb4-20261006.json`; engine `c52c0ebc`; data manifest `9247c4bb`
- Evaluation folder: `M/tmp/kill-test-stage0/retrieved/s0-1102/tree/round1/1102-a0-e3-a1/eval/e3`
  - `summary.json` `436305c3567ce45014da157369f8658e4e098fb8e0ff0c882644575fa11d46d7`
  - `guard_samples.jsonl` `57a4949cfe4e795de66c26aceae3f794ecaf4050100870ae751f9fb5afa8e176`
  - `guard.jsonl` `8532d1aae1c146b28dd0b23f034fca578e7e4cd4898acf9a62faac2d94c1fd88`
  - `query_loss.jsonl` `7a0f426010460216f602d48a33c0135c0dc5ac6483258192fcbbf04dac847fb4`
  - `job.json` `4977ee80831db786fa5fc885e2e5cd97238183ea36bf8bbb96f9cedeb2ed598d`
  - `COMPLETE.json` `406b239e2d75723f448efff4f0cb94be53a3af2e95365cdbe9af03b3433bb4d5`

### qwen2.5-1.5b_high-dose_1103_e3

- Note: Qwen2.5-1.5B, High-dose, seed 1103, checkpoint e3; E against `qwen2.5-1.5b_untuned`
- Configuration: `study-kt-instruct-r64-mb4-20261006.json`; engine `c52c0ebc`; data manifest `9247c4bb`
- Evaluation folder: `M/tmp/kill-test-stage0/retrieved/s0-1103/tree/round1/1103-a0-e3-a1/eval/e3`
  - `summary.json` `e07706b51a48751519c8ac04021e313852d2bda33c923b8f13350f123193cc42`
  - `guard_samples.jsonl` `c67f9b396ae21adab68f317bbe79c2523e8260d4240e1a398cebfbb6a3e42504`
  - `guard.jsonl` `99e8c8dcd3ee650d6e9cc24dbdc8f02f8e37bfcd5c84a8dfd0a31a434f9e3d56`
  - `query_loss.jsonl` `9bff91c9601db11640495ff85ced5c386ed525c83c81b232e6c334da11ca0623`
  - `job.json` `15887081b75da0d2360ccd9cddc108b408762de117b706a5aa4f3217d4282096`
  - `COMPLETE.json` `6fefdeb3da4b479f820a436741f9c9bd9afc6a6a4a202d74caf553659f5c97ff`
- Granite (Mac): `M/tmp/kill-test-stage0/second-judge-kt-items.jsonl` `fe1d089cdc4604fc1d0d7f3f94f75644eaec441ac5b091136d32b3f666472fc1`, unit `1103-a0-e3-a1`
- Granite device in the note's tables: mac

### qwen2.5-7b_constant_1101_e1

- Note: Qwen2.5-7B, Constant, seed 1101, checkpoint e1; E against `qwen2.5-7b_untuned`
- Configuration: `study-kt-qwen7b-r64-b-mb2-20261007.json`; engine `c52c0ebc`; data manifest `9247c4bb`
- Evaluation folder: `M/tmp/kill-test-7b-check/retrieved/q7-1101/tree/round1/1101-a0-e1-a1/eval/e1`
  - `summary.json` `8650d4182af3cd6cbe37f3c541691f16521b1b03dd205f3a4cb692df9c44fe51`
  - `guard_samples.jsonl` `4e7d47c76dfbfda5f6537e3cffe3a06428399f1fcca13bd9403f4ecd33fba3f5`
  - `guard.jsonl` `9c04aa48322b17d81dc7c64ad16eed25c5af70683910a27f286d72a84d958093`
  - `query_loss.jsonl` `bcef09097db4cf5a719be7b6c0c47921458dbac85b88d52ca0702d6700f57e0d`
  - `job.json` `702b85c8513702e1bbaa3987e091393753e65d32beb441fb24aa98ee29fb948c`
  - `COMPLETE.json` `7849bd690676b96e3d3d30840d26316ddc49412b86dcd585d63d8020f3d03d5a`
- HarmBench (pod): `M/tmp/judge-pod/side-qwen-llama-pairs/fetched/out/harmbench-pod.jsonl` `a5b58bd899e7e532853cbbf85a178f57cb3f89c6d60673ac3be80fc0b544e0ef`, records with complete_sha256 `7849bd690676b96e...`
- Granite (Mac): `M/tmp/kill-test-7b-check/second-judge-kt-items.jsonl` `76a6031a6a7e8a0e51d376aa8dbe87fa76ac5981527931c364f2fa2a97ae4455`, unit `1101-a0-e1-a1`
- Granite device in the note's tables: mac
- Blind read: key unit `qwen7b-b-1101`

### llama3.2-1b_constant_1101_e1

- Note: Llama-3.2-1B, Constant, seed 1101, checkpoint e1; E against `llama3.2-1b_untuned`
- Configuration: `study-kt-llama32-1b-r64-b-mb4-20261008.json`; engine `e49a978c`; data manifest `c52a50af`
- Evaluation folder: `M/tmp/family-probe-llama32-1b/retrieved/llama32-1b-1101/tree/round1/1101-a0-e1-a1/eval/e1`
  - `summary.json` `c13431b6e026f48c01e0a7e55976a2d48c1b26b8fef7e18ef580f18c2cf85183`
  - `guard_samples.jsonl` `d03f29a4db3909fea8cc93fd18f137acd8d86e84f1a6c649183cb934ff3cdb26`
  - `guard.jsonl` `c5433d974dbb47e1c51f9dc02da74385ec740c97e10f19fc80576928c290f800`
  - `query_loss.jsonl` `79b68726b1726299816fee4b24aa2ef2466ecadb8887e33f2d2f6c359702504a`
  - `job.json` `f89f432f444b4a2fd88812bc4cc02a9626bea9d038ed82586683b1d1a26a6df8`
  - `COMPLETE.json` `979044858ac0358d8651e017cf8f58546edf51c4122bb22a4de8e626e838561e`
- HarmBench (pod): `M/tmp/judge-pod/side-qwen-llama-pairs/fetched/out/harmbench-pod.jsonl` `a5b58bd899e7e532853cbbf85a178f57cb3f89c6d60673ac3be80fc0b544e0ef`, records with complete_sha256 `979044858ac0358d...`
- Granite (Mac): `M/tmp/family-probe-llama32-1b/second-judge-probe-items.jsonl` `d8f612df52106bca4eaa59560ccf2332501eb6827506b21d2d7401acb39d8840`, unit `1101-a0-e1-a1`
- Granite (pod): `M/tmp/judge-pod/granite-llama-b-1/fetched/out/granite-pod.jsonl` `0ea0ed8183af1f702c3030b0deaf1aefa20bfe1439688540feef7ec4e42c4b2b`
- Granite device in the note's tables: pod
- Opening crosstabs: `M/tmp/family-probe-llama32-1b/mechanism-llama/results.json` `7011993dd67e5ea1a01a24846fa9a9cceb6f50c9bd0163954510bf95f49bf6d7`, unit `llama-B-e1-1101`
- Blind read: key unit `llama-b-1101`

### llama3.2-1b_constant_1102_e1

- Note: Llama-3.2-1B, Constant, seed 1102, checkpoint e1; E against `llama3.2-1b_untuned`
- Configuration: `study-kt-llama32-1b-r64-b-mb4-20261008.json`; engine `e49a978c`; data manifest `c52a50af`
- Evaluation folder: `M/tmp/family-probe-sp-llama32-1b-b-seed1102/retrieved/sp-llama32-1b-b2-1102/tree/round1/1102-a0-e1-a1/eval/e1`
  - `summary.json` `8ed2e714568f1c26b337ce54521632015e1cc91077c220fc649e413162365d02`
  - `guard_samples.jsonl` `304be71aa183307435d524c09136670103352a95a9249b597bfd350519f6144c`
  - `guard.jsonl` `3569badf89f9a79c69f71356620dc83bd993030952429bda6b21e1687f1930a5`
  - `query_loss.jsonl` `b7f65cfe7172778f3940fdf68f71fa5f2b9b6bc0b7039d0ecad577427abbe219`
  - `job.json` `5ad4db5b553fd970e4fd6a8360857e861f742997db5d1d640168e853f6aed630`
  - `COMPLETE.json` `755dd90fda12f239f7d6da6e8fd78f72df9af696aeb99ac26839637c5d95e5ed`
- Granite (pod): `M/tmp/judge-pod/granite-llama-b-1/fetched/out/granite-pod.jsonl` `0ea0ed8183af1f702c3030b0deaf1aefa20bfe1439688540feef7ec4e42c4b2b`
- Granite device in the note's tables: pod

### llama3.2-1b_constant_1103_e1

- Note: Llama-3.2-1B, Constant, seed 1103, checkpoint e1; E against `llama3.2-1b_untuned`
- Configuration: `study-kt-llama32-1b-r64-b-mb4-20261008.json`; engine `e49a978c`; data manifest `c52a50af`
- Evaluation folder: `M/tmp/family-probe-sp-llama32-1b-b-seed1103/retrieved/sp-llama32-1b-b-1103/tree/round1/1103-a0-e1-a1/eval/e1`
  - `summary.json` `6319c532963be49834800785b17accd7a964ea7e9f02c2a73e8a4dabc3327fb0`
  - `guard_samples.jsonl` `7e578f833b58ca45340c7a48b75a70eaaf333d86f4ad2fcc1432d5eede4c18b3`
  - `guard.jsonl` `541366ff1068eddd0855053cbbcea1c38366db916387532251b9b13e7845a529`
  - `query_loss.jsonl` `bfb8adc4a60a693c84f0ac9cc8bddf1152ab4e9578ec53ecf85fb8a04f4bdafb`
  - `job.json` `50788dfa5c54691020c96ffc4bcb26e7850cf6d3019adc6567d259a7eda5783b`
  - `COMPLETE.json` `72e552710a44ac977ea15394e67b2cde8873dbe519c7007af3e84b57ee8e26c0`
- Granite (pod): `M/tmp/judge-pod/granite-llama-b-1/fetched/out/granite-pod.jsonl` `0ea0ed8183af1f702c3030b0deaf1aefa20bfe1439688540feef7ec4e42c4b2b`
- Granite device in the note's tables: pod

### llama3.2-1b_constant-half-lr_1101_e1

- Note: Llama-3.2-1B, Constant, half LR, seed 1101, checkpoint e1; E against `llama3.2-1b_untuned`
- Configuration: `study-kt-llama32-1b-r64-b5e5-mb4-20261008.json`; engine `e49a978c`; data manifest `c52a50af`
- Evaluation folder: `M/tmp/family-probe-llama32-1b-b5e5/retrieved/llama32-1b-b5e5-1101/tree/round1/1101-a0-e1-a1/eval/e1`
  - `summary.json` `fa948c98bc3e359a1f9d34aae8813f6e4f8981441b9cfc32ea5de531a9a5abb7`
  - `guard_samples.jsonl` `37b9ea04f66ee9142fa6a4efc5967543c767282c986f466d81323a08a99f5408`
  - `guard.jsonl` `f5b5cee4671a66a13506083b8001d6fa5de7dff5f1b28a21e0411e96b37b0c5f`
  - `query_loss.jsonl` `c3509b165f4dd282752a4addb0463f0c2cfd6b4a5eee51d5eaf63752de8b04bd`
  - `job.json` `8f5ac0f3391eecc5e5435d1269089920de308fc2d11cacf212a9b35ce57978cc`
  - `COMPLETE.json` `6cb77db90f0566fba52a004d22477bbd0da10d67036f37f793c7f2d15f30f175`
- Granite (pod): `M/tmp/judge-pod/granite-llama-b-1/fetched/out/granite-pod.jsonl` `0ea0ed8183af1f702c3030b0deaf1aefa20bfe1439688540feef7ec4e42c4b2b`
- Granite device in the note's tables: pod

### llama3.2-1b_scheduled_1101_e1

- Note: Llama-3.2-1B, Scheduled, seed 1101, checkpoint e1; E against `llama3.2-1b_untuned`
- Configuration: `study-kt-llama32-1b-r64-g-mb4-20261008.json`; engine `e49a978c`; data manifest `c52a50af`
- Evaluation folder: `M/tmp/family-probe-llama32-1b-g/retrieved/llama32-1b-g5-1101/tree/round1/1101-a0-e1-a1/eval/e1`
  - `summary.json` `baee86f0afd61181719dac9fb0808b70004ef696410392531ea2270fbbfe9ca8`
  - `guard_samples.jsonl` `cb4afec370ac5ee19029270ab131e9f6b7569bd969765fcd223eb26d4d5ef3dd`
  - `guard.jsonl` `f4e0d47ff0f0b5773224cdd72fc034e83df99ddf631b7a3be7a1baadda800f58`
  - `query_loss.jsonl` `812c536c779ae14ed680ee731842296aa76224a622c8dccda2f04dd1c17b4ba2`
  - `job.json` `88aee56fdd1ba95abac3b78636b404e1e8911e5bd90e86188d30c983b5613597`
  - `COMPLETE.json` `cd9586d358eb3c8eafd24628ebc106c83a2dd1bb37d137674c6b0853737474cc`
- HarmBench (pod): `M/tmp/judge-pod/side-qwen-llama-pairs/fetched/out/harmbench-pod.jsonl` `a5b58bd899e7e532853cbbf85a178f57cb3f89c6d60673ac3be80fc0b544e0ef`, records with complete_sha256 `cd9586d358eb3c8e...`
- Granite (Mac): `M/tmp/family-probe-llama32-1b-g/second-judge-probe-items.jsonl` `ca921d11b60b6e3a019a6a54dace1f7a82ebbf33afada90b039b0282d8c96fd3`, unit `1101-a0-e1-a1`
- Granite device in the note's tables: mac

### llama3.2-1b_scheduled_1102_e1

- Note: Llama-3.2-1B, Scheduled, seed 1102, checkpoint e1; E against `llama3.2-1b_untuned`
- Configuration: `study-kt-llama32-1b-r64-g-mb4-20261008.json`; engine `e49a978c`; data manifest `c52a50af`
- Evaluation folder: `M/tmp/family-probe-llama32-1b-g-seed1102/retrieved/llama32-1b-g-1102/tree/round1/1102-a0-e1-a1/eval/e1`
  - `summary.json` `1c26e0c2b0052cde8ea740d287d9f193ec1fea68ff8256f23a6ca2d619a775bf`
  - `guard_samples.jsonl` `39f58c300ddc0b7b9dfb735111c44ec3cf1b9506eaba34c192c7f947f6fc49b0`
  - `guard.jsonl` `3790c0865ba8f8f0e8a53adb26afae30cb861bc92ea729698a53fbe61ae6f711`
  - `query_loss.jsonl` `034f20a112fd03e782370c32e11204613f508c49e3640cff209648de82240726`
  - `job.json` `950385b35730ee45159da0c2066dea4648660f084ae80e0efa5dc0fa5b363741`
  - `COMPLETE.json` `e37b0ba06e85a6b2f3f3f9ee7f904db2fe6648768bb351be58c07a8c5137ffeb`
- HarmBench (pod): `M/tmp/judge-pod/side-qwen-llama-pairs/fetched/out/harmbench-pod.jsonl` `a5b58bd899e7e532853cbbf85a178f57cb3f89c6d60673ac3be80fc0b544e0ef`, records with complete_sha256 `e37b0ba06e85a6b2...`
- Granite (Mac): `M/tmp/family-probe-llama32-1b-g-seed1102/second-judge-probe-items.jsonl` `26c628a6e440f97c10fada81dbcc3baac6c5199c259cb828a3646fdc22e9a6ab`, unit `1102-a0-e1-a1`
- Granite device in the note's tables: mac

### llama3.2-1b_scheduled_1103_e1

- Note: Llama-3.2-1B, Scheduled, seed 1103, checkpoint e1; E against `llama3.2-1b_untuned`
- Configuration: `study-kt-llama32-1b-r64-g-mb4-20261008.json`; engine `e49a978c`; data manifest `c52a50af`
- Evaluation folder: `M/tmp/family-probe-llama32-1b-g-seed1103/retrieved/llama32-1b-g-1103/tree/round1/1103-a0-e1-a1/eval/e1`
  - `summary.json` `921244638c9a688bba9e0f7ce55109a19163974e9342df7ffb79f7c4e038c3ba`
  - `guard_samples.jsonl` `e36ab639707d5e850c21fd5ded1208ef73f00f669bf0604e936a23a7b795b0b2`
  - `guard.jsonl` `6dab04d545e4134ff882597c387d746f312e7f6fdd0e459307f458bdb664e44b`
  - `query_loss.jsonl` `07fe270b4825d3345b696edf6345e2d74a07bed9393fe5d015a0718d3dea74b1`
  - `job.json` `cc71fea5200d93492cb342534a3a8ae2827e847201a3654cdb5af43648775578`
  - `COMPLETE.json` `d9c4468d429fec237b094e7b095dd53586cadce68573d8917ce1448bfdfa94df`
- Granite (Mac): `M/tmp/family-probe-llama32-1b-g-seed1103/second-judge-probe-items.jsonl` `9bf698934a024a3b2f123e77a0eacfdd7d997c65ce7785db56765172ae7762e3`, unit `1103-a0-e1-a1`
- Granite device in the note's tables: mac

### llama3.2-1b_scheduled-half-lr_1101_e1

- Note: Llama-3.2-1B, Scheduled, half LR, seed 1101, checkpoint e1; E against `llama3.2-1b_untuned`
- Configuration: `study-kt-llama32-1b-r64-g5e5-mb4-20261008.json`; engine `e49a978c`; data manifest `c52a50af`
- Evaluation folder: `M/tmp/family-probe-llama32-1b-g5e5/retrieved/llama32-1b-g5e5b-1101/tree/round1/1101-a0-e1-a1/eval/e1`
  - `summary.json` `3f435cc6ad9d59abb352f38c835bf7560fdf79f5879065cfaf232b87e1d04d77`
  - `guard_samples.jsonl` `1a31a54ed01d637dd4af0a2b0d019f7419a5eb2a41aec3fa2bb052af50d644fb`
  - `guard.jsonl` `fb4a5df10bbb61919f0acb7935db06280476a007c48ac95489f14c4c9d291f71`
  - `query_loss.jsonl` `42023a12a2cbbb1268a5d72b6ecd0295391a66fe376e0fd014cfe72036f70380`
  - `job.json` `12d9fe57a755a8080f4c7e386d135188bf72df9bea24c62bf8b60f52a818ba14`
  - `COMPLETE.json` `d44d14e2fdd1f31308bf866e2e19a9733fe77317c662f1f0d07243630e3e45a3`
- Granite (Mac): `M/tmp/family-probe-llama32-1b-g5e5/second-judge-probe-items.jsonl` `88590ac4769081edb2d9252b9e828cb531a1e6f84472f9e337267d17e054f43e`, unit `1101-a0-e1-a1`
- Granite device in the note's tables: mac

## Every file read, with its SHA-256 and the fields read

| File | SHA-256 | Fields read |
|---|---|---|
| `M/experiments/safety_selection/configs/study-kt-instruct-r16-b-20261008.json` | `1157fc9d0af1daad30acf04d7a2cd420c925b0ccd82e3d09584aa6918cc7874b` | whole file (released as a copy with only the top-level "purpose" replaced) |
| `M/experiments/safety_selection/configs/study-kt-instruct-r64-b-20261007.json` | `e5bb77b6232995f9273aae15da6f4894a4634bd41b3572ab5b674fe8e5629061` | whole file (released as a copy with only the top-level "purpose" replaced) |
| `M/experiments/safety_selection/configs/study-kt-instruct-r64-mb4-20261006.json` | `157b39c2f72fefdcdc3159c62cbad686f2d0759bfe5aad241e15422b588a9826` | whole file (released as a copy with only the top-level "purpose" replaced) |
| `M/experiments/safety_selection/configs/study-kt-llama32-1b-r64-b-mb4-20261008.json` | `d86629412ec682840a08bbad484f2a7955fc3ef0641350cded8276a747ad5bda` | whole file (released as a copy with only the top-level "purpose" replaced) |
| `M/experiments/safety_selection/configs/study-kt-llama32-1b-r64-b5e5-mb4-20261008.json` | `aed7dc91739854ddee9bc37299ea85ece9e85deadd55216713e42bbc6b4a9d94` | whole file (released as a copy with only the top-level "purpose" replaced) |
| `M/experiments/safety_selection/configs/study-kt-llama32-1b-r64-g-mb4-20261008.json` | `175759f92d0f2e5518b59e8670c75c26b2f20729d4d68198f80c5d075e50749d` | whole file (released as a copy with only the top-level "purpose" replaced) |
| `M/experiments/safety_selection/configs/study-kt-llama32-1b-r64-g5e5-mb4-20261008.json` | `9d8783a4f94d5cfb3e54cf1ebe086a07a35dc1244c05448c5cbedabdbf2135b9` | whole file (released as a copy with only the top-level "purpose" replaced) |
| `M/experiments/safety_selection/configs/study-kt-olmo2-1b-r16-g-mb4-20261008.json` | `0ee2eca290fe387efce906fa611163e0f935355b0a71b3947c64d37b90688da4` | whole file (released as a copy with only the top-level "purpose" replaced) |
| `M/experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-20261008.json` | `a47138f2f4fb032aa60addc59256c499b7a65a75c2541aba516adeed8f4b15b2` | whole file (released as a copy with only the top-level "purpose" replaced) |
| `M/experiments/safety_selection/configs/study-kt-olmo2-1b-r64-bt-mb4-20261008.json` | `16d1f753f5b83a69ef5d602a9299ae685adaba9a7c2b1a8aa56338e1b466208b` | whole file (released as a copy with only the top-level "purpose" replaced) |
| `M/experiments/safety_selection/configs/study-kt-olmo2-1b-r64-g-mb4-20261008.json` | `cb51e5a9431f5fd4963d521866072821cf0db3dff800cc5b34d79469579e9228` | whole file (released as a copy with only the top-level "purpose" replaced) |
| `M/experiments/safety_selection/configs/study-kt-olmo2-1b-r64-g5e5-mb4-20261008.json` | `a22fe34b3de7e2d55458810dd83466e9e86dc96a1a84a5085a277e4eb086ff52` | whole file (released as a copy with only the top-level "purpose" replaced) |
| `M/experiments/safety_selection/configs/study-kt-qwen7b-r64-b-mb2-20261007.json` | `18f8c7b2af3339660cb3ddffb2af32d35ae00688b2c4958c8810338058b73bec` | whole file (released as a copy with only the top-level "purpose" replaced) |
| `M/experiments/safety_selection/configs/study-v3-data-inj05.json` | `11e9221412d599bf277f934182c10ad6f27c78508a5fe99267e95e023497d760` | eval_banks.{harm,overrefusal}.sources; extra_sources.{harmbench,strongreject,simplesafetytests,orbench_toxic,xstest_safe,orbench_hard}.{repo_id,revision,file,sha256,license,keep} |
| `M/tmp/family-probe-llama32-1b-b5e5/retrieved/llama32-1b-b5e5-1101/tree/round1/1101-a0-e1-a1/COMPLETE.json` | `6cb77db90f0566fba52a004d22477bbd0da10d67036f37f793c7f2d15f30f175` | whole-file SHA-256 (identity) |
| `M/tmp/family-probe-llama32-1b-b5e5/retrieved/llama32-1b-b5e5-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard.jsonl` | `f5b5cee4671a66a13506083b8001d6fa5de7dff5f1b28a21e0411e96b37b0c5f` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/family-probe-llama32-1b-b5e5/retrieved/llama32-1b-b5e5-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard_samples.jsonl` | `37b9ea04f66ee9142fa6a4efc5967543c767282c986f466d81323a08a99f5408` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/family-probe-llama32-1b-b5e5/retrieved/llama32-1b-b5e5-1101/tree/round1/1101-a0-e1-a1/eval/e1/query_loss.jsonl` | `c3509b165f4dd282752a4addb0463f0c2cfd6b4a5eee51d5eaf63752de8b04bd` | loss (cross-check of the mean) |
| `M/tmp/family-probe-llama32-1b-b5e5/retrieved/llama32-1b-b5e5-1101/tree/round1/1101-a0-e1-a1/eval/e1/summary.json` | `fa948c98bc3e359a1f9d34aae8813f6e4f8981441b9cfc32ea5de531a9a5abb7` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/family-probe-llama32-1b-b5e5/retrieved/llama32-1b-b5e5-1101/tree/round1/1101-a0-e1-a1/job.json` | `8f5ac0f3391eecc5e5435d1269089920de308fc2d11cacf212a9b35ce57978cc` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/family-probe-llama32-1b-g-seed1102/retrieved/llama32-1b-g-1102/tree/round1/1102-a0-e1-a1/COMPLETE.json` | `e37b0ba06e85a6b2f3f3f9ee7f904db2fe6648768bb351be58c07a8c5137ffeb` | whole-file SHA-256 (identity) |
| `M/tmp/family-probe-llama32-1b-g-seed1102/retrieved/llama32-1b-g-1102/tree/round1/1102-a0-e1-a1/eval/e1/guard.jsonl` | `3790c0865ba8f8f0e8a53adb26afae30cb861bc92ea729698a53fbe61ae6f711` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/family-probe-llama32-1b-g-seed1102/retrieved/llama32-1b-g-1102/tree/round1/1102-a0-e1-a1/eval/e1/guard_samples.jsonl` | `39f58c300ddc0b7b9dfb735111c44ec3cf1b9506eaba34c192c7f947f6fc49b0` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/family-probe-llama32-1b-g-seed1102/retrieved/llama32-1b-g-1102/tree/round1/1102-a0-e1-a1/eval/e1/query_loss.jsonl` | `034f20a112fd03e782370c32e11204613f508c49e3640cff209648de82240726` | loss (cross-check of the mean) |
| `M/tmp/family-probe-llama32-1b-g-seed1102/retrieved/llama32-1b-g-1102/tree/round1/1102-a0-e1-a1/eval/e1/summary.json` | `1c26e0c2b0052cde8ea740d287d9f193ec1fea68ff8256f23a6ca2d619a775bf` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/family-probe-llama32-1b-g-seed1102/retrieved/llama32-1b-g-1102/tree/round1/1102-a0-e1-a1/job.json` | `950385b35730ee45159da0c2066dea4648660f084ae80e0efa5dc0fa5b363741` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/family-probe-llama32-1b-g-seed1102/second-judge-probe-items.jsonl` | `26c628a6e440f97c10fada81dbcc3baac6c5199c259cb828a3646fdc22e9a6ab` | granite; prompt_id; qwen3guard (identity check only); unit |
| `M/tmp/family-probe-llama32-1b-g-seed1102/second-judge-probe-summary.json` | `055086ebf3a1801e4ec386fd083e4230c5617d1f9ba5c7f6441cc80eeb04cf9a` | units.<unit>.job_sha256 |
| `M/tmp/family-probe-llama32-1b-g-seed1103/retrieved/llama32-1b-g-1103/tree/round1/1103-a0-e1-a1/COMPLETE.json` | `d9c4468d429fec237b094e7b095dd53586cadce68573d8917ce1448bfdfa94df` | whole-file SHA-256 (identity) |
| `M/tmp/family-probe-llama32-1b-g-seed1103/retrieved/llama32-1b-g-1103/tree/round1/1103-a0-e1-a1/eval/e1/guard.jsonl` | `6dab04d545e4134ff882597c387d746f312e7f6fdd0e459307f458bdb664e44b` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/family-probe-llama32-1b-g-seed1103/retrieved/llama32-1b-g-1103/tree/round1/1103-a0-e1-a1/eval/e1/guard_samples.jsonl` | `e36ab639707d5e850c21fd5ded1208ef73f00f669bf0604e936a23a7b795b0b2` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/family-probe-llama32-1b-g-seed1103/retrieved/llama32-1b-g-1103/tree/round1/1103-a0-e1-a1/eval/e1/query_loss.jsonl` | `07fe270b4825d3345b696edf6345e2d74a07bed9393fe5d015a0718d3dea74b1` | loss (cross-check of the mean) |
| `M/tmp/family-probe-llama32-1b-g-seed1103/retrieved/llama32-1b-g-1103/tree/round1/1103-a0-e1-a1/eval/e1/summary.json` | `921244638c9a688bba9e0f7ce55109a19163974e9342df7ffb79f7c4e038c3ba` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/family-probe-llama32-1b-g-seed1103/retrieved/llama32-1b-g-1103/tree/round1/1103-a0-e1-a1/job.json` | `cc71fea5200d93492cb342534a3a8ae2827e847201a3654cdb5af43648775578` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/family-probe-llama32-1b-g-seed1103/second-judge-probe-items.jsonl` | `9bf698934a024a3b2f123e77a0eacfdd7d997c65ce7785db56765172ae7762e3` | granite; prompt_id; qwen3guard (identity check only); unit |
| `M/tmp/family-probe-llama32-1b-g-seed1103/second-judge-probe-summary.json` | `d667da37aca8fce765af2e09d11bc76a1564f0219500b0b94eeb44bc0b40bdc3` | units.<unit>.job_sha256 |
| `M/tmp/family-probe-llama32-1b-g/retrieved/llama32-1b-g5-1101/tree/round1/1101-a0-e1-a1/COMPLETE.json` | `cd9586d358eb3c8eafd24628ebc106c83a2dd1bb37d137674c6b0853737474cc` | whole-file SHA-256 (identity) |
| `M/tmp/family-probe-llama32-1b-g/retrieved/llama32-1b-g5-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard.jsonl` | `f4e0d47ff0f0b5773224cdd72fc034e83df99ddf631b7a3be7a1baadda800f58` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/family-probe-llama32-1b-g/retrieved/llama32-1b-g5-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard_samples.jsonl` | `cb4afec370ac5ee19029270ab131e9f6b7569bd969765fcd223eb26d4d5ef3dd` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/family-probe-llama32-1b-g/retrieved/llama32-1b-g5-1101/tree/round1/1101-a0-e1-a1/eval/e1/query_loss.jsonl` | `812c536c779ae14ed680ee731842296aa76224a622c8dccda2f04dd1c17b4ba2` | loss (cross-check of the mean) |
| `M/tmp/family-probe-llama32-1b-g/retrieved/llama32-1b-g5-1101/tree/round1/1101-a0-e1-a1/eval/e1/summary.json` | `baee86f0afd61181719dac9fb0808b70004ef696410392531ea2270fbbfe9ca8` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/family-probe-llama32-1b-g/retrieved/llama32-1b-g5-1101/tree/round1/1101-a0-e1-a1/job.json` | `88aee56fdd1ba95abac3b78636b404e1e8911e5bd90e86188d30c983b5613597` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/family-probe-llama32-1b-g/second-judge-probe-items.jsonl` | `ca921d11b60b6e3a019a6a54dace1f7a82ebbf33afada90b039b0282d8c96fd3` | granite; prompt_id; qwen3guard (identity check only); unit |
| `M/tmp/family-probe-llama32-1b-g/second-judge-probe-summary.json` | `89c5ed7cebbb77e6f65393afc796da5b64086842fb5c76c005be33e6eb9a6c62` | units.<unit>.job_sha256 |
| `M/tmp/family-probe-llama32-1b-g5e5/retrieved/llama32-1b-g5e5b-1101/tree/round1/1101-a0-e1-a1/COMPLETE.json` | `d44d14e2fdd1f31308bf866e2e19a9733fe77317c662f1f0d07243630e3e45a3` | whole-file SHA-256 (identity) |
| `M/tmp/family-probe-llama32-1b-g5e5/retrieved/llama32-1b-g5e5b-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard.jsonl` | `fb4a5df10bbb61919f0acb7935db06280476a007c48ac95489f14c4c9d291f71` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/family-probe-llama32-1b-g5e5/retrieved/llama32-1b-g5e5b-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard_samples.jsonl` | `1a31a54ed01d637dd4af0a2b0d019f7419a5eb2a41aec3fa2bb052af50d644fb` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/family-probe-llama32-1b-g5e5/retrieved/llama32-1b-g5e5b-1101/tree/round1/1101-a0-e1-a1/eval/e1/query_loss.jsonl` | `42023a12a2cbbb1268a5d72b6ecd0295391a66fe376e0fd014cfe72036f70380` | loss (cross-check of the mean) |
| `M/tmp/family-probe-llama32-1b-g5e5/retrieved/llama32-1b-g5e5b-1101/tree/round1/1101-a0-e1-a1/eval/e1/summary.json` | `3f435cc6ad9d59abb352f38c835bf7560fdf79f5879065cfaf232b87e1d04d77` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/family-probe-llama32-1b-g5e5/retrieved/llama32-1b-g5e5b-1101/tree/round1/1101-a0-e1-a1/job.json` | `12d9fe57a755a8080f4c7e386d135188bf72df9bea24c62bf8b60f52a818ba14` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/family-probe-llama32-1b-g5e5/second-judge-probe-items.jsonl` | `88590ac4769081edb2d9252b9e828cb531a1e6f84472f9e337267d17e054f43e` | granite; prompt_id; qwen3guard (identity check only); unit |
| `M/tmp/family-probe-llama32-1b-g5e5/second-judge-probe-summary.json` | `7683201c9dac24a9590eaf90c7a52a408728ea352351fb7fbc8ba47939278eaa` | units.<unit>.job_sha256 |
| `M/tmp/family-probe-llama32-1b/mechanism-llama/results.json` | `7011993dd67e5ea1a01a24846fa9a9cceb6f50c9bd0163954510bf95f49bf6d7` | units.<unit>.{sampled,greedy}.crosstab_opening_safety (agreement check) |
| `M/tmp/family-probe-llama32-1b/retrieved/llama32-1b-1101/tree/round1/1101-a0-e1-a1/COMPLETE.json` | `979044858ac0358d8651e017cf8f58546edf51c4122bb22a4de8e626e838561e` | whole-file SHA-256 (identity) |
| `M/tmp/family-probe-llama32-1b/retrieved/llama32-1b-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard.jsonl` | `c5433d974dbb47e1c51f9dc02da74385ec740c97e10f19fc80576928c290f800` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/family-probe-llama32-1b/retrieved/llama32-1b-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard_samples.jsonl` | `d03f29a4db3909fea8cc93fd18f137acd8d86e84f1a6c649183cb934ff3cdb26` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/family-probe-llama32-1b/retrieved/llama32-1b-1101/tree/round1/1101-a0-e1-a1/eval/e1/query_loss.jsonl` | `79b68726b1726299816fee4b24aa2ef2466ecadb8887e33f2d2f6c359702504a` | loss (cross-check of the mean) |
| `M/tmp/family-probe-llama32-1b/retrieved/llama32-1b-1101/tree/round1/1101-a0-e1-a1/eval/e1/summary.json` | `c13431b6e026f48c01e0a7e55976a2d48c1b26b8fef7e18ef580f18c2cf85183` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/family-probe-llama32-1b/retrieved/llama32-1b-1101/tree/round1/1101-a0-e1-a1/job.json` | `f89f432f444b4a2fd88812bc4cc02a9626bea9d038ed82586683b1d1a26a6df8` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/family-probe-llama32-1b/retrieved/llama32-1b-1101/tree/round1/1101-a0-init-a1/COMPLETE.json` | `b9e84745dfed11da74ab2ffe1cc0e5cdb2fa2b255878bab2ca709905c8cfc415` | whole-file SHA-256 (identity) |
| `M/tmp/family-probe-llama32-1b/retrieved/llama32-1b-1101/tree/round1/1101-a0-init-a1/eval/init/guard.jsonl` | `a3468320481f85a14137489f72ff2bfd1d0a921e3ae9ec3c386797d7a314da32` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/family-probe-llama32-1b/retrieved/llama32-1b-1101/tree/round1/1101-a0-init-a1/eval/init/guard_samples.jsonl` | `a33649f313db941e5736e32212618b777bb0bfeb37b6da56fc4d7597c08645ee` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/family-probe-llama32-1b/retrieved/llama32-1b-1101/tree/round1/1101-a0-init-a1/eval/init/query_loss.jsonl` | `74def1317f0b7e69ef2383d16de6c10d0336db11727c5aa28a9c50af51dd743b` | loss (cross-check of the mean) |
| `M/tmp/family-probe-llama32-1b/retrieved/llama32-1b-1101/tree/round1/1101-a0-init-a1/eval/init/summary.json` | `ec084124f23e5b2b2a1580242becaafd62ba7ee891ac546c9caf6727bcc5f8d3` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/family-probe-llama32-1b/retrieved/llama32-1b-1101/tree/round1/1101-a0-init-a1/job.json` | `727d4183aa860fdeefc0c5f240f3f2955241ccdc998935777f95da03f93bd85a` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/family-probe-llama32-1b/second-judge-probe-items.jsonl` | `d8f612df52106bca4eaa59560ccf2332501eb6827506b21d2d7401acb39d8840` | granite; prompt_id; qwen3guard (identity check only); unit |
| `M/tmp/family-probe-llama32-1b/second-judge-probe-summary.json` | `ba680668a1635213bda64d0dcd72307ac2f8dffa75bc5d403c1cd9e64838ee9e` | units.<unit>.job_sha256 |
| `M/tmp/family-probe-olmo2-1b-bt/retrieved/olmo2-1b-bt-1101/tree/round1/1101-a0-e1-a1/COMPLETE.json` | `0ccf97de823c24990d0f78023beb58819fba5cb4e6afb2560ceac71715067fef` | whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b-bt/retrieved/olmo2-1b-bt-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard.jsonl` | `fee0a477800f14ece65599d9e7ff3d79b058f686a0f36f89390a10a7e63fc427` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/family-probe-olmo2-1b-bt/retrieved/olmo2-1b-bt-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard_samples.jsonl` | `7a5cdcf8e2b4c3e4d01ad784e1951c6c6f47147beabe88676a4d17efc08beeac` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/family-probe-olmo2-1b-bt/retrieved/olmo2-1b-bt-1101/tree/round1/1101-a0-e1-a1/eval/e1/query_loss.jsonl` | `9725387bed34f22721cd7a8049e64adacb4dee21c5fd7fef4eae664876db6388` | loss (cross-check of the mean) |
| `M/tmp/family-probe-olmo2-1b-bt/retrieved/olmo2-1b-bt-1101/tree/round1/1101-a0-e1-a1/eval/e1/summary.json` | `4978780343964ea4e9dcab76f8b40eac6d628d3762a9ac76ef0b487d04b44150` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/family-probe-olmo2-1b-bt/retrieved/olmo2-1b-bt-1101/tree/round1/1101-a0-e1-a1/job.json` | `5b57d4c593c69dd755d7a79cf8a88f349f8043ac02777eb5afc51e2db2720a9f` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b-bt/second-judge-probe-items.jsonl` | `b0cf190b87b4ec10eb537104f48263a863f3402b94dc3fa9898ef1c74c33e96d` | granite; prompt_id; qwen3guard (identity check only); unit |
| `M/tmp/family-probe-olmo2-1b-bt/second-judge-probe-summary.json` | `4f55e697679a32cb3b943a75b4d66eb9f085d49472843f47d23a032afff45dbe` | units.<unit>.job_sha256 |
| `M/tmp/family-probe-olmo2-1b-g-r16/retrieved/olmo2-1b-g-r16-1101/tree/round1/1101-a0-e1-a1/COMPLETE.json` | `425922e550bf51fbd6ea67b58191ee6d7f5f75e5d64f4087794293bcc632d02a` | whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b-g-r16/retrieved/olmo2-1b-g-r16-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard.jsonl` | `a413755dbc5bbb0f89c5665a817baa81e71b59cb41ec10c894279535e4ccd64f` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/family-probe-olmo2-1b-g-r16/retrieved/olmo2-1b-g-r16-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard_samples.jsonl` | `18935cc51ed92cb828dd3ddfbdc0310e94203499ef855d1ae5aa27eaf6ee1f94` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/family-probe-olmo2-1b-g-r16/retrieved/olmo2-1b-g-r16-1101/tree/round1/1101-a0-e1-a1/eval/e1/query_loss.jsonl` | `f3008bdf292c37f5f7bc9f80ba2f5f670e988f25f0e6b73aa19505df02940301` | loss (cross-check of the mean) |
| `M/tmp/family-probe-olmo2-1b-g-r16/retrieved/olmo2-1b-g-r16-1101/tree/round1/1101-a0-e1-a1/eval/e1/summary.json` | `69ea79f342100166e1dd7b8f527c71bfa7136867d7f108fe499f3f5cb2760e58` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/family-probe-olmo2-1b-g-r16/retrieved/olmo2-1b-g-r16-1101/tree/round1/1101-a0-e1-a1/job.json` | `2e05692c7355920951f22e5f2d5a451abfeb7b8c913a0cbfb88780fe1c25c9f5` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b-g-r16/second-judge-probe-items.jsonl` | `4e798c5594ff53ac36d166f6bd96a1b425b3f85f750d9bec1e4c6e31146fa927` | granite; prompt_id; qwen3guard (identity check only); unit |
| `M/tmp/family-probe-olmo2-1b-g-r16/second-judge-probe-summary.json` | `2a6656a151ffeb152a6c6a2840915af56f4366875c95ea55fe42ae727e417ef0` | units.<unit>.job_sha256 |
| `M/tmp/family-probe-olmo2-1b-g-seed1102/retrieved/olmo2-1b-g-1102/tree/round1/1102-a0-e1-a1/COMPLETE.json` | `7c16beec76971793c9ffb51c5832f645e0dbe70e74b1954fe48556273d9d3157` | whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b-g-seed1102/retrieved/olmo2-1b-g-1102/tree/round1/1102-a0-e1-a1/eval/e1/guard.jsonl` | `fac17bcd57ee99f4d0501137bb1c1eefe1720c3dbd9f8bef91d697136689a919` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/family-probe-olmo2-1b-g-seed1102/retrieved/olmo2-1b-g-1102/tree/round1/1102-a0-e1-a1/eval/e1/guard_samples.jsonl` | `0a78638541f85990a17b765680e325583b8e8f88996516d16cebecb1121c8e10` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/family-probe-olmo2-1b-g-seed1102/retrieved/olmo2-1b-g-1102/tree/round1/1102-a0-e1-a1/eval/e1/query_loss.jsonl` | `38377286512544d3bfa24ca27a791fb7d18e1479d956838e5d08af4f97a0da4c` | loss (cross-check of the mean) |
| `M/tmp/family-probe-olmo2-1b-g-seed1102/retrieved/olmo2-1b-g-1102/tree/round1/1102-a0-e1-a1/eval/e1/summary.json` | `5c51c0f19fd6439f3586de8d6c9a846dc306d3e51448d5236427d2f60938c66d` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/family-probe-olmo2-1b-g-seed1102/retrieved/olmo2-1b-g-1102/tree/round1/1102-a0-e1-a1/job.json` | `97b7c5ec736c97dd04a4f23fff99bdfc9465733bc3a1929479eaf31748e9fd04` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b-g-seed1102/second-judge-probe-items.jsonl` | `41e9f8654fef48033a055435d97e4d8d4a5fd3bae91f0eafe1312273877fdf9b` | granite; prompt_id; qwen3guard (identity check only); unit |
| `M/tmp/family-probe-olmo2-1b-g-seed1102/second-judge-probe-summary.json` | `32bf3e750bfed2ea2e688ac1e2c76db08afd914c2753b542fcb070ad45541619` | units.<unit>.job_sha256 |
| `M/tmp/family-probe-olmo2-1b-g-seed1103/retrieved/olmo2-1b-g-1103/tree/round1/1103-a0-e1-a1/COMPLETE.json` | `6db69ca4fc5e9b902eba3ea194cb2b7e180e3f2d26fed330ffc185cfa55c71fc` | whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b-g-seed1103/retrieved/olmo2-1b-g-1103/tree/round1/1103-a0-e1-a1/eval/e1/guard.jsonl` | `12841445b922a209dbba1d5052d21311f1b0efcf7498d911210d380981029e51` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/family-probe-olmo2-1b-g-seed1103/retrieved/olmo2-1b-g-1103/tree/round1/1103-a0-e1-a1/eval/e1/guard_samples.jsonl` | `a06013aea4713193c6b162c72113ee9faaa0d956cb7a68949d54645e84ae3315` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/family-probe-olmo2-1b-g-seed1103/retrieved/olmo2-1b-g-1103/tree/round1/1103-a0-e1-a1/eval/e1/query_loss.jsonl` | `1e3e77a88c8addf8cc485809c90c620550074620edb28f4512c68fcca5b97cdc` | loss (cross-check of the mean) |
| `M/tmp/family-probe-olmo2-1b-g-seed1103/retrieved/olmo2-1b-g-1103/tree/round1/1103-a0-e1-a1/eval/e1/summary.json` | `aa9ff4d04064d17e42e09da66ed63460e579e30678feff96ac02154ebca57f86` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/family-probe-olmo2-1b-g-seed1103/retrieved/olmo2-1b-g-1103/tree/round1/1103-a0-e1-a1/job.json` | `2573e30472fbb574ec8965d9f43fa5dd335f60d5fbf53f03aedf0a9c24374111` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b-g-seed1103/second-judge-probe-items.jsonl` | `6dd76ad0e93d6f747b9d4b8f8e01024d47d148347eafcae83443e2695413d504` | granite; prompt_id; qwen3guard (identity check only); unit |
| `M/tmp/family-probe-olmo2-1b-g-seed1103/second-judge-probe-summary.json` | `80c1413a29bb2d4c03cb05a96e029e6c911bb4bf657bca4b134674b3eff0b74b` | units.<unit>.job_sha256 |
| `M/tmp/family-probe-olmo2-1b-g/mechanism-g/results.json` | `0f9c87b821113598e87511702b5f14715a52e710e5dde6b8c0b28958bc9b9e13` | units.<unit>.{sampled,greedy}.crosstab_opening_safety (agreement check) |
| `M/tmp/family-probe-olmo2-1b-g/retrieved/olmo2-1b-g-1101/tree/round1/1101-a0-e1-a1/COMPLETE.json` | `557a083f0dad77bc50dd749e805be076eaa75eb1ea50b8ce356736a6207f8a09` | whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b-g/retrieved/olmo2-1b-g-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard.jsonl` | `38fbf8ce443816fa6364bc5964d308d245c444850d526982c928f3bd089c4016` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/family-probe-olmo2-1b-g/retrieved/olmo2-1b-g-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard_samples.jsonl` | `fdc9059d8caa2f3cd5ef406065e9e8cf63253cbf63366bacf73cc4df0a20f4e0` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/family-probe-olmo2-1b-g/retrieved/olmo2-1b-g-1101/tree/round1/1101-a0-e1-a1/eval/e1/query_loss.jsonl` | `41d9ef468d0496038c5e7f2f0166967213199c2ef9f61ecd1160f988baca3eb3` | loss (cross-check of the mean) |
| `M/tmp/family-probe-olmo2-1b-g/retrieved/olmo2-1b-g-1101/tree/round1/1101-a0-e1-a1/eval/e1/summary.json` | `300b1246da4ec9a6cd65d15e5bc9206bf98510226d0a83a7d9251b338944753a` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/family-probe-olmo2-1b-g/retrieved/olmo2-1b-g-1101/tree/round1/1101-a0-e1-a1/job.json` | `1a292c1d71729a3a5cca33ec1a452be634e07a6cb77b7efc856fb38b7b2a56dd` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b-g/second-judge-probe-items.jsonl` | `554aa28a747ce42d4a2f5a57aa5a05ae399a2986178fbe28fe037a453e0dd6e1` | granite; prompt_id; qwen3guard (identity check only); unit |
| `M/tmp/family-probe-olmo2-1b-g/second-judge-probe-summary.json` | `8ae9051a2559dbb5f8dcabaa7ceecc806fd3345e635dd03cc46a51cf05fb7e41` | units.<unit>.job_sha256 |
| `M/tmp/family-probe-olmo2-1b-g5e5-seed1102/retrieved/olmo2-1b-g5e5-1102/tree/round1/1102-a0-e1-a1/COMPLETE.json` | `2ec864bc71f9d1247e041f895c8727007a43861c5e4f4faa001898d831c29a8b` | whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b-g5e5-seed1102/retrieved/olmo2-1b-g5e5-1102/tree/round1/1102-a0-e1-a1/eval/e1/guard.jsonl` | `b1aef5e0db3c9343e6a0989e8e336f4e8bd2851b4a726482f2f8cf9eb212ffbb` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/family-probe-olmo2-1b-g5e5-seed1102/retrieved/olmo2-1b-g5e5-1102/tree/round1/1102-a0-e1-a1/eval/e1/guard_samples.jsonl` | `bc40d1bd1db41fc1060dd7959e71c9ad52eea1e4cb900131d2e122ba89a1bdd0` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/family-probe-olmo2-1b-g5e5-seed1102/retrieved/olmo2-1b-g5e5-1102/tree/round1/1102-a0-e1-a1/eval/e1/query_loss.jsonl` | `0692b86f0227e5ca2b243b391c93de44bfea19928d4abcdcf6b02fbf5483011f` | loss (cross-check of the mean) |
| `M/tmp/family-probe-olmo2-1b-g5e5-seed1102/retrieved/olmo2-1b-g5e5-1102/tree/round1/1102-a0-e1-a1/eval/e1/summary.json` | `f6c1e1f8115e5fedadece218cdff7f873cbfcdcbbf57018624e69bdd8f14b764` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/family-probe-olmo2-1b-g5e5-seed1102/retrieved/olmo2-1b-g5e5-1102/tree/round1/1102-a0-e1-a1/job.json` | `9a58dd69d5b4d6bbe96d206ef9668f8159e70675d60c164ca952b02d895ad752` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b-g5e5-seed1102/second-judge-probe-items.jsonl` | `7b5543d432bd6bca7ae509304e80336ccd6072b9eb6ed103f5e64e54a2637688` | granite; prompt_id; qwen3guard (identity check only); unit |
| `M/tmp/family-probe-olmo2-1b-g5e5-seed1102/second-judge-probe-summary.json` | `0ea09739689e06914bc893d1dc028dbe79c2a0908f729906e5f9b75e1426604a` | units.<unit>.job_sha256 |
| `M/tmp/family-probe-olmo2-1b-g5e5/retrieved/olmo2-1b-g5e5-1101/tree/round1/1101-a0-e1-a1/COMPLETE.json` | `1cfc8bd9050e88efab472c33b98085c1fe1b816030e6ab3d84b48101a094247a` | whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b-g5e5/retrieved/olmo2-1b-g5e5-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard.jsonl` | `914b40bbd6b355b8c9ccbca4df5075e5c801241fee3440bfc290dbdab8df06f0` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/family-probe-olmo2-1b-g5e5/retrieved/olmo2-1b-g5e5-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard_samples.jsonl` | `9e709e0513963bb1e2dfc5bd1382e201335b71752dac92090ee82c98a95998d0` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/family-probe-olmo2-1b-g5e5/retrieved/olmo2-1b-g5e5-1101/tree/round1/1101-a0-e1-a1/eval/e1/query_loss.jsonl` | `dde7ad96a5ec0bf7f4b67132401ec54150c824a8d1478b5f52fec9e97cbca90c` | loss (cross-check of the mean) |
| `M/tmp/family-probe-olmo2-1b-g5e5/retrieved/olmo2-1b-g5e5-1101/tree/round1/1101-a0-e1-a1/eval/e1/summary.json` | `373da7d0d86c67c817ee7d1c1ee53bfb8a6f416e56095f240b9b22e0217416fd` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/family-probe-olmo2-1b-g5e5/retrieved/olmo2-1b-g5e5-1101/tree/round1/1101-a0-e1-a1/job.json` | `01b3fa5957e93dda60690dfe261ad2c37fd5a9fa8ecb3dffea2d9fee8e17e010` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b-g5e5/second-judge-probe-items.jsonl` | `05986d285ae1fabfdfc036d81445dc5c88d0e56c0a386882e11e28edd4f0f834` | granite; prompt_id; qwen3guard (identity check only); unit |
| `M/tmp/family-probe-olmo2-1b-g5e5/second-judge-probe-summary.json` | `dddcd44d7c171f76933f75e11e7a025941470d0620a1f516e4c877b0ecd65712` | units.<unit>.job_sha256 |
| `M/tmp/family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102/tree/round1/1102-a0-e1-a1/COMPLETE.json` | `857f78bc0f49cc8a4902fbb6211f463daa7c7f44086257c4d752409a30ba0b25` | whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102/tree/round1/1102-a0-e1-a1/eval/e1/guard.jsonl` | `c289873099785b4c0817da4a29067dbe68511b71abec4390f1492b6126c76fe4` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102/tree/round1/1102-a0-e1-a1/eval/e1/guard_samples.jsonl` | `25a74527f43052bea59978b9a58297197786f590d2d1db333efe62c9271998b3` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102/tree/round1/1102-a0-e1-a1/eval/e1/query_loss.jsonl` | `2f73f77c40b161572572d8d18b317d21c26738bf2aed1e337b4ed7b7645f3e20` | loss (cross-check of the mean) |
| `M/tmp/family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102/tree/round1/1102-a0-e1-a1/eval/e1/summary.json` | `0918dc486803a0d3357d43e3fca323b9a29c6ae1379741486b03aa7bd36294f0` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/family-probe-olmo2-1b-gateA-1102/retrieved/olmo2-1b-1102/tree/round1/1102-a0-e1-a1/job.json` | `de65ca1936a10c199de46e764a948268b03367c586c09747381850059064083c` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b-gateA-1102/second-judge-probe-items.jsonl` | `2b537302fe412716e047294758f442a4c317d068bb5f6f6e89fbb1b3e2d92105` | granite; prompt_id; qwen3guard (identity check only); unit |
| `M/tmp/family-probe-olmo2-1b-gateA-1102/second-judge-probe-summary.json` | `d0169ae8defee92e9c64bccd21049a8276dfff64680cfc1da7ceca499314acf5` | units.<unit>.job_sha256 |
| `M/tmp/family-probe-olmo2-1b-gateA-1103/retrieved/olmo2-1b-1103/tree/round1/1103-a0-e1-a1/COMPLETE.json` | `7be58eaa9c5be7b8f94668109efd6aae075b1d001e0d2b1fb8be814556899cbd` | whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b-gateA-1103/retrieved/olmo2-1b-1103/tree/round1/1103-a0-e1-a1/eval/e1/guard.jsonl` | `55339f54dfcc7224a8749f211be2c79b67376f709c2703edcc7fb9efc1904886` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/family-probe-olmo2-1b-gateA-1103/retrieved/olmo2-1b-1103/tree/round1/1103-a0-e1-a1/eval/e1/guard_samples.jsonl` | `7839edc3ceffec25054b76e5007c01301c34ce0dc36e3923186f81470a152990` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/family-probe-olmo2-1b-gateA-1103/retrieved/olmo2-1b-1103/tree/round1/1103-a0-e1-a1/eval/e1/query_loss.jsonl` | `eba947241293ed571f7bb5ce507b59af98911cd411be323f9a8c901a1ae79612` | loss (cross-check of the mean) |
| `M/tmp/family-probe-olmo2-1b-gateA-1103/retrieved/olmo2-1b-1103/tree/round1/1103-a0-e1-a1/eval/e1/summary.json` | `7d24950cb2ad221dfcd0e27c0c40cc6745c52dcaac4612a966474310d85cf918` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/family-probe-olmo2-1b-gateA-1103/retrieved/olmo2-1b-1103/tree/round1/1103-a0-e1-a1/job.json` | `895f8bd2a66e20df2256b43d1e71a263da237a1cb3ea498cd439086aef5ae293` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b-gateA-1103/second-judge-probe-items.jsonl` | `0a1e236ff0a211d7443e18f673b2bd14f8cea3fd66c507a83510df0fae316cfe` | granite; prompt_id; qwen3guard (identity check only); unit |
| `M/tmp/family-probe-olmo2-1b-gateA-1103/second-judge-probe-summary.json` | `3b8d702f580e21756888c59efb528e8087a5988d9bc092b390423df096e8bf51` | units.<unit>.job_sha256 |
| `M/tmp/family-probe-olmo2-1b/harmbench-items.jsonl` | `2851ee4dc65a256dfd244de933664e8b1cd8d6b3a5f963d364b42cd9450a54aa` | kind; label; prompt_id; sample_index; unit |
| `M/tmp/family-probe-olmo2-1b/harmbench-summary.json` | `2f4c0c7dd8d93b956a80528fc8caa6f6b86826251a9de31631ce3033b44343e0` | units.<unit>.job_sha256 |
| `M/tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1/COMPLETE.json` | `8f0fa83a42ccc5edc54a5ee26ed63f49448c36d30adbd64e28b655678afee4c9` | whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard.jsonl` | `27668f068f85a8b95dc16c690027d66fed82ff6e5ce56a9e754662f29908b4bf` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard_samples.jsonl` | `68d39f131827783b5e1e3a9d132f7a33e05d96ab6dbe9fb441684f75b6091426` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1/eval/e1/query_loss.jsonl` | `a539638fc5c7f5b98594094690b114fb5714343e4f497451301cce9630a189d1` | loss (cross-check of the mean) |
| `M/tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1/eval/e1/summary.json` | `f331eadee052f8f1c45403b7f19b7da7f1cfa1153d2b450285d3e777ca11171a` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1/job.json` | `3e60568ac11e32f3f429aa2606bc38c9b881456fd262a120e526ccb189022402` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-init-a1/COMPLETE.json` | `b5083ce9d9f26efe92f9872fdbf9376a521a5d99d1b70cc2bd460987cdcc9474` | whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-init-a1/eval/init/guard.jsonl` | `fc8a2e32d6c07924be9ed5ea40cc4d2d8c6b49da24b172c3269006a02a09d925` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-init-a1/eval/init/guard_samples.jsonl` | `1f578d091f46a27aa05290f8dbc9aae4cd7a7552475da72016f859c1be29549b` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-init-a1/eval/init/query_loss.jsonl` | `02963ba5559077dfae9dd48a29ac5470507d05d48377966195545a8d979d27a6` | loss (cross-check of the mean) |
| `M/tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-init-a1/eval/init/summary.json` | `7b40ea1c99bbfffdbc1711008f4fd10ba83cb5bca782c473fb6c16ee20f80801` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-init-a1/job.json` | `f3b8c1864aaacf34738b34ff6c26cc8f51677e7eb5a6a9445818692d5365a582` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/family-probe-olmo2-1b/second-judge-probe-items.jsonl` | `c2ef1130fd540eb822225b42e73297143fdbf17d40a95b8d936205f227feb547` | granite; prompt_id; qwen3guard (identity check only); unit |
| `M/tmp/family-probe-olmo2-1b/second-judge-probe-summary.json` | `be2b42866b81e7d7f25c1f36910ac90ec030a592dca12274a9503c19a1c14914` | units.<unit>.job_sha256 |
| `M/tmp/family-probe-sp-llama32-1b-b-seed1102/retrieved/sp-llama32-1b-b2-1102/tree/round1/1102-a0-e1-a1/COMPLETE.json` | `755dd90fda12f239f7d6da6e8fd78f72df9af696aeb99ac26839637c5d95e5ed` | whole-file SHA-256 (identity) |
| `M/tmp/family-probe-sp-llama32-1b-b-seed1102/retrieved/sp-llama32-1b-b2-1102/tree/round1/1102-a0-e1-a1/eval/e1/guard.jsonl` | `3569badf89f9a79c69f71356620dc83bd993030952429bda6b21e1687f1930a5` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/family-probe-sp-llama32-1b-b-seed1102/retrieved/sp-llama32-1b-b2-1102/tree/round1/1102-a0-e1-a1/eval/e1/guard_samples.jsonl` | `304be71aa183307435d524c09136670103352a95a9249b597bfd350519f6144c` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/family-probe-sp-llama32-1b-b-seed1102/retrieved/sp-llama32-1b-b2-1102/tree/round1/1102-a0-e1-a1/eval/e1/query_loss.jsonl` | `b7f65cfe7172778f3940fdf68f71fa5f2b9b6bc0b7039d0ecad577427abbe219` | loss (cross-check of the mean) |
| `M/tmp/family-probe-sp-llama32-1b-b-seed1102/retrieved/sp-llama32-1b-b2-1102/tree/round1/1102-a0-e1-a1/eval/e1/summary.json` | `8ed2e714568f1c26b337ce54521632015e1cc91077c220fc649e413162365d02` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/family-probe-sp-llama32-1b-b-seed1102/retrieved/sp-llama32-1b-b2-1102/tree/round1/1102-a0-e1-a1/job.json` | `5ad4db5b553fd970e4fd6a8360857e861f742997db5d1d640168e853f6aed630` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/family-probe-sp-llama32-1b-b-seed1103/retrieved/sp-llama32-1b-b-1103/tree/round1/1103-a0-e1-a1/COMPLETE.json` | `72e552710a44ac977ea15394e67b2cde8873dbe519c7007af3e84b57ee8e26c0` | whole-file SHA-256 (identity) |
| `M/tmp/family-probe-sp-llama32-1b-b-seed1103/retrieved/sp-llama32-1b-b-1103/tree/round1/1103-a0-e1-a1/eval/e1/guard.jsonl` | `541366ff1068eddd0855053cbbcea1c38366db916387532251b9b13e7845a529` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/family-probe-sp-llama32-1b-b-seed1103/retrieved/sp-llama32-1b-b-1103/tree/round1/1103-a0-e1-a1/eval/e1/guard_samples.jsonl` | `7e578f833b58ca45340c7a48b75a70eaaf333d86f4ad2fcc1432d5eede4c18b3` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/family-probe-sp-llama32-1b-b-seed1103/retrieved/sp-llama32-1b-b-1103/tree/round1/1103-a0-e1-a1/eval/e1/query_loss.jsonl` | `bfb8adc4a60a693c84f0ac9cc8bddf1152ab4e9578ec53ecf85fb8a04f4bdafb` | loss (cross-check of the mean) |
| `M/tmp/family-probe-sp-llama32-1b-b-seed1103/retrieved/sp-llama32-1b-b-1103/tree/round1/1103-a0-e1-a1/eval/e1/summary.json` | `6319c532963be49834800785b17accd7a964ea7e9f02c2a73e8a4dabc3327fb0` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/family-probe-sp-llama32-1b-b-seed1103/retrieved/sp-llama32-1b-b-1103/tree/round1/1103-a0-e1-a1/job.json` | `50788dfa5c54691020c96ffc4bcb26e7850cf6d3019adc6567d259a7eda5783b` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/judge-pod/granite-llama-b-1/fetched/out/granite-pod.jsonl` | `0ea0ed8183af1f702c3030b0deaf1aefa20bfe1439688540feef7ec4e42c4b2b` | complete_sha256; label; mode; prompt_id; sample_index |
| `M/tmp/judge-pod/olmo-b-g-untuned/fetched/out/harmbench-pod.jsonl` | `c44ddeb808a8e95a353786c4cc1566425d1943c48019bd23ffd420819e0b79e1` | complete_sha256; label; mode; prompt_id; sample_index; truncated |
| `M/tmp/judge-pod/side-qwen-llama-pairs/fetched/out/harmbench-pod.jsonl` | `a5b58bd899e7e532853cbbf85a178f57cb3f89c6d60673ac3be80fc0b544e0ef` | complete_sha256; label; mode; prompt_id; sample_index; truncated |
| `M/tmp/kill-test-7b-check/retrieved/q7-1101/tree/round1/1101-a0-e1-a1/COMPLETE.json` | `7849bd690676b96e3d3d30840d26316ddc49412b86dcd585d63d8020f3d03d5a` | whole-file SHA-256 (identity) |
| `M/tmp/kill-test-7b-check/retrieved/q7-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard.jsonl` | `9c04aa48322b17d81dc7c64ad16eed25c5af70683910a27f286d72a84d958093` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/kill-test-7b-check/retrieved/q7-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard_samples.jsonl` | `4e7d47c76dfbfda5f6537e3cffe3a06428399f1fcca13bd9403f4ecd33fba3f5` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/kill-test-7b-check/retrieved/q7-1101/tree/round1/1101-a0-e1-a1/eval/e1/query_loss.jsonl` | `bcef09097db4cf5a719be7b6c0c47921458dbac85b88d52ca0702d6700f57e0d` | loss (cross-check of the mean) |
| `M/tmp/kill-test-7b-check/retrieved/q7-1101/tree/round1/1101-a0-e1-a1/eval/e1/summary.json` | `8650d4182af3cd6cbe37f3c541691f16521b1b03dd205f3a4cb692df9c44fe51` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/kill-test-7b-check/retrieved/q7-1101/tree/round1/1101-a0-e1-a1/job.json` | `702b85c8513702e1bbaa3987e091393753e65d32beb441fb24aa98ee29fb948c` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/kill-test-7b-check/retrieved/q7-1101/tree/round1/1101-a0-init-a1/COMPLETE.json` | `24acd43a4093a842e140605f4f90f0da6de5173493776bd7334ffe5aaf59e165` | whole-file SHA-256 (identity) |
| `M/tmp/kill-test-7b-check/retrieved/q7-1101/tree/round1/1101-a0-init-a1/eval/init/guard.jsonl` | `c3e453ea51a631e2ad34d877daeca5a078c26b285059d367b6864f72c1df3226` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/kill-test-7b-check/retrieved/q7-1101/tree/round1/1101-a0-init-a1/eval/init/guard_samples.jsonl` | `b234b6589b15bdf9e1c8df5a2679b9033ae8031228a6add390426102af7a8d1b` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/kill-test-7b-check/retrieved/q7-1101/tree/round1/1101-a0-init-a1/eval/init/query_loss.jsonl` | `c8e1a69e5f82df766debe7cebe9381c515c6d506bfaf936c7aff5c384ceadf3e` | loss (cross-check of the mean) |
| `M/tmp/kill-test-7b-check/retrieved/q7-1101/tree/round1/1101-a0-init-a1/eval/init/summary.json` | `683e00871e0b74b3ad3e22ad1d1af6c7c5b27c10f5d0ba8f33a2ac7c830c6b5f` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/kill-test-7b-check/retrieved/q7-1101/tree/round1/1101-a0-init-a1/job.json` | `0d098ec5f56537ae7cb79645aedc42889c337d40399b59d9bb7082a2e47fc8e5` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/kill-test-7b-check/second-judge-kt-items.jsonl` | `76a6031a6a7e8a0e51d376aa8dbe87fa76ac5981527931c364f2fa2a97ae4455` | granite; prompt_id; qwen3guard (identity check only); unit |
| `M/tmp/kill-test-gateA-b/retrieved/b-1101/tree/round1/1101-a0-e1-a1/COMPLETE.json` | `bb7813625b7d982b36d002ad0b55751e788b31bf10b69d7744a6c65cc3e3c179` | whole-file SHA-256 (identity) |
| `M/tmp/kill-test-gateA-b/retrieved/b-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard.jsonl` | `a2b8c29b20a937f73a9920622706d28370e493996274a3db918e82e93fae9323` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/kill-test-gateA-b/retrieved/b-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard_samples.jsonl` | `1f208a9e5479cf28d08cc2bdb5b957849d2e8285249f0e05e0c013efc91eb983` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/kill-test-gateA-b/retrieved/b-1101/tree/round1/1101-a0-e1-a1/eval/e1/query_loss.jsonl` | `c8f86a1013013da563a700b7d20253c42aca89bece5f831d80a2eb0c4f31b32a` | loss (cross-check of the mean) |
| `M/tmp/kill-test-gateA-b/retrieved/b-1101/tree/round1/1101-a0-e1-a1/eval/e1/summary.json` | `c4ecdcabadab697b16bd1fd086dbfae4350807eb1a70361d79f0c768f6efdc34` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/kill-test-gateA-b/retrieved/b-1101/tree/round1/1101-a0-e1-a1/job.json` | `bfb0448b93ebc8c9e5738d0fd103574c2de6a4233305af3035448b43170d3819` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/kill-test-r16/retrieved/r16-1101/tree/round1/1101-a0-e1-a1/COMPLETE.json` | `039ccca9f1edfa826dd9610972e816f5d61985eb06a1f52d0a295f2ced26b0c1` | whole-file SHA-256 (identity) |
| `M/tmp/kill-test-r16/retrieved/r16-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard.jsonl` | `32db7995ac932e6ef287b6a0935785b74dbccd68ba6729cb6b1d1b14b550025d` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/kill-test-r16/retrieved/r16-1101/tree/round1/1101-a0-e1-a1/eval/e1/guard_samples.jsonl` | `9989adf6e6561b731fce8c3ef27fa248eee342dbf1ad2306f726716c7d62dfc7` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/kill-test-r16/retrieved/r16-1101/tree/round1/1101-a0-e1-a1/eval/e1/query_loss.jsonl` | `c8815f3efbbb3b059ae30541474a2bd0caf890370cadcaaef2a92a345ac6d047` | loss (cross-check of the mean) |
| `M/tmp/kill-test-r16/retrieved/r16-1101/tree/round1/1101-a0-e1-a1/eval/e1/summary.json` | `f591cf41fd4892bf99f2db796ce7abd30fa5a02d7a8fc2f5a8de42a226db995f` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/kill-test-r16/retrieved/r16-1101/tree/round1/1101-a0-e1-a1/job.json` | `54ecff4dbd5570d62f8911e6c417719e7ed1ed2a994678b4af63467318d78823` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/kill-test-r16/second-judge-kt-items.jsonl` | `191b80b1ff1999d971efce52617d93d665cd0b7938fe1f04b499d64ac3da8bf5` | granite; prompt_id; qwen3guard (identity check only); unit |
| `M/tmp/kill-test-stage0/retrieved/s0-1101/tree/round1/1101-a0-e3-a1/COMPLETE.json` | `7a09557d9bbf17c595fb92df94dd635868e018d5cbaad44b9884e582cff82c2c` | whole-file SHA-256 (identity) |
| `M/tmp/kill-test-stage0/retrieved/s0-1101/tree/round1/1101-a0-e3-a1/eval/e3/guard.jsonl` | `a73073e7d961435dea691556278b5a196bb0579816d3aa477bdb99165297abf8` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/kill-test-stage0/retrieved/s0-1101/tree/round1/1101-a0-e3-a1/eval/e3/guard_samples.jsonl` | `d009e7d59abb3a4a0025e8382f907fd38e90f68dbfaadfc0ccc2a7a7bd86aa43` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/kill-test-stage0/retrieved/s0-1101/tree/round1/1101-a0-e3-a1/eval/e3/query_loss.jsonl` | `3e0d86ec92595679781e31eaf253c9e8330275ef991b539cb76c8ff827340b70` | loss (cross-check of the mean) |
| `M/tmp/kill-test-stage0/retrieved/s0-1101/tree/round1/1101-a0-e3-a1/eval/e3/summary.json` | `e4c7cac2718d535a0a0931f20c3ed736b4becfd72641e709d3b34f1ed129ec4f` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/kill-test-stage0/retrieved/s0-1101/tree/round1/1101-a0-e3-a1/job.json` | `cd15b095ccd3efa7b7fa442df06d376b76003dd005acf90d5ad51c31d1c55a7f` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/kill-test-stage0/retrieved/s0-1101/tree/round1/1101-a0-init-a1/COMPLETE.json` | `fde132cbc335a32239299cbb9ceebf09ecb388740001fb7e016e99900adbeb9a` | whole-file SHA-256 (identity) |
| `M/tmp/kill-test-stage0/retrieved/s0-1101/tree/round1/1101-a0-init-a1/eval/init/guard.jsonl` | `8f91ffa485e140e282654ec8b9e625cdeb14eb015c9bb97e39c8555ac44b4a16` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/kill-test-stage0/retrieved/s0-1101/tree/round1/1101-a0-init-a1/eval/init/guard_samples.jsonl` | `63565bde269f77cd3be4e1094b28f9d0b9cba9f385ce5af73c89ee397961247e` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/kill-test-stage0/retrieved/s0-1101/tree/round1/1101-a0-init-a1/eval/init/query_loss.jsonl` | `802b926081a508570bd8e715739b4b34a127eb110fbf57ee7cae907ad04a3100` | loss (cross-check of the mean) |
| `M/tmp/kill-test-stage0/retrieved/s0-1101/tree/round1/1101-a0-init-a1/eval/init/summary.json` | `acff0a8436777d3f40b4212410b35f811f6aa4030590ab5758af02c49981a455` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/kill-test-stage0/retrieved/s0-1101/tree/round1/1101-a0-init-a1/job.json` | `7031566aa1956f72f0f2e3ba33d25e5453cb61931a9b75580be4a47e78b92e79` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/kill-test-stage0/retrieved/s0-1102/tree/round1/1102-a0-e3-a1/COMPLETE.json` | `406b239e2d75723f448efff4f0cb94be53a3af2e95365cdbe9af03b3433bb4d5` | whole-file SHA-256 (identity) |
| `M/tmp/kill-test-stage0/retrieved/s0-1102/tree/round1/1102-a0-e3-a1/eval/e3/guard.jsonl` | `8532d1aae1c146b28dd0b23f034fca578e7e4cd4898acf9a62faac2d94c1fd88` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/kill-test-stage0/retrieved/s0-1102/tree/round1/1102-a0-e3-a1/eval/e3/guard_samples.jsonl` | `57a4949cfe4e795de66c26aceae3f794ecaf4050100870ae751f9fb5afa8e176` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/kill-test-stage0/retrieved/s0-1102/tree/round1/1102-a0-e3-a1/eval/e3/query_loss.jsonl` | `7a0f426010460216f602d48a33c0135c0dc5ac6483258192fcbbf04dac847fb4` | loss (cross-check of the mean) |
| `M/tmp/kill-test-stage0/retrieved/s0-1102/tree/round1/1102-a0-e3-a1/eval/e3/summary.json` | `436305c3567ce45014da157369f8658e4e098fb8e0ff0c882644575fa11d46d7` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/kill-test-stage0/retrieved/s0-1102/tree/round1/1102-a0-e3-a1/job.json` | `4977ee80831db786fa5fc885e2e5cd97238183ea36bf8bbb96f9cedeb2ed598d` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/kill-test-stage0/retrieved/s0-1103/tree/round1/1103-a0-e3-a1/COMPLETE.json` | `6fefdeb3da4b479f820a436741f9c9bd9afc6a6a4a202d74caf553659f5c97ff` | whole-file SHA-256 (identity) |
| `M/tmp/kill-test-stage0/retrieved/s0-1103/tree/round1/1103-a0-e3-a1/eval/e3/guard.jsonl` | `99e8c8dcd3ee650d6e9cc24dbdc8f02f8e37bfcd5c84a8dfd0a31a434f9e3d56` | categories; kind; prompt_id; refusal (kind harm, overrefusal); safety; valid |
| `M/tmp/kill-test-stage0/retrieved/s0-1103/tree/round1/1103-a0-e3-a1/eval/e3/guard_samples.jsonl` | `c67f9b396ae21adab68f317bbe79c2523e8260d4240e1a398cebfbb6a3e42504` | categories; prompt_id; refusal; safety; sample_index; valid |
| `M/tmp/kill-test-stage0/retrieved/s0-1103/tree/round1/1103-a0-e3-a1/eval/e3/query_loss.jsonl` | `9bff91c9601db11640495ff85ced5c386ed525c83c81b232e6c334da11ca0623` | loss (cross-check of the mean) |
| `M/tmp/kill-test-stage0/retrieved/s0-1103/tree/round1/1103-a0-e3-a1/eval/e3/summary.json` | `e07706b51a48751519c8ac04021e313852d2bda33c923b8f13350f123193cc42` | checkpoint; harm.greedy.unsafe; harm.prompts; harm.sampled.{answers,unsafe}; overrefusal.{n,refusals}; query_loss.{n,mean} |
| `M/tmp/kill-test-stage0/retrieved/s0-1103/tree/round1/1103-a0-e3-a1/job.json` | `15887081b75da0d2360ccd9cddc108b408762de117b706a5aa4f3217d4282096` | code_sha256; evaluate_bank; manifest_sha256; recipe_sha256; seed; target_checkpoint; whole-file SHA-256 (identity) |
| `M/tmp/kill-test-stage0/second-judge-kt-items.jsonl` | `fe1d089cdc4604fc1d0d7f3f94f75644eaec441ac5b091136d32b3f666472fc1` | granite; prompt_id; qwen3guard (identity check only); unit |
| `M/tmp/mechanism-recipes/results.json` | `2e39e88b3c8fdc5285743aad8500998adf6defa6b8670ea9435b3316c8f04718` | input_sha256.<unit>; units.<unit>.{sampled,greedy}.crosstab_opening_safety |
| `M/tmp/v3-prepared/prepared-v3-inj05/auditor/construction.json` | `29e67a174e3f5344a3528e34aa057627129641fbd1e6b8e237c957d6d9b26ef0` | prompts.<prompt_id>.{bank,kind,source,source_id,record,category} |
| `W/research/side-blind-read/blind-read-scores-2026-10-09.json` | `d09deccab0823b7bd8aae8a6fa2884a48f88bdbe47d26fce3404518a16580be5` | groups.<group>.{n,0,1,2,skip,garbled} (cross-check) |
| `W/research/side-blind-read/score_blind_read.py` | `f40853c408cc0f06f3d53f17a817e8a557f1667d6ebfdb118e0d6e038cceee7e` | KEY_SHA; PREREG_GROUP (group names); RATINGS_SHA |
| `W/tmp/side-blind-read/blind-ratings-20261009-2026.csv` | `3108bb7219af20085f42253a0ef355cc40b353ad0c7ea37eb0babfaa56bd6ad0` | garbled (the note column is never read out); item; rating |
| `W/tmp/side-blind-read/key.json` | `52b6f95a157a82f0c97c2abf94b3a1b2d1c8a8c02104e1be980413b05d898d2c` | items[].{item,group,unit,prompt_id,sample_index,qwen3guard.safety,harmbench_label} |
| `W/writing/side-notes/arxiv/figures/fig1-data.csv` | `e2d7cbece612042d1e418585ac4918f42207ff83f73b024c95af3ee55d12ffb1` | every column; source and check are rewritten |
| `W/writing/side-notes/arxiv/figures/fig2-data.csv` | `d4da96ef62d4dad8227485fba3fc79c383c1b00653042dce4cdcb33dd0ca95ef` | every column; source is rewritten and unit renamed |
| `W/writing/side-notes/arxiv/main.tex` | `3d1045e628b2f595c54bd8e0e573e8cd6b829f70ef88da2fc2d6b5f67d7644c6` | Tables 1-3 cells and footnotes; phrases quoted in TEXT_VALUES and TABLE4_VALUES |

## Release rules (author's decisions of 10 Oct 2026)

- Prompts: opaque ids only. p001-p200 are the 200 harm prompts and p201-p300 the 100 over-refusal prompts, each block in ascending order of the internal prompt id (`p-` and 16 hex digits). The builder reads `source`, `source_id` and `record` of `M/tmp/v3-prepared/prepared-v3-inj05/auditor/construction.json` only to check the prompts and to count them per source; it releases neither the ids, nor the rows, nor per-prompt sources. A build-time scan checks that no internal prompt id and no HarmBench or SimpleSafetyTests id occurs in any release file.
- Configurations: redacted copies; only the top-level `purpose` value is replaced (by "Recipe configuration of runs in the note; design notes removed for release."). The builder checks, with the originals, that nothing else differs.
- Blind read: item, group, Qwen3Guard label, Mac HarmBench label, rating and garbled flag only. The unit, prompt and sample index of each item are read to check its labels, then dropped.
- Dolly training row ids: not released (they belong to the larger study).

## Left out on purpose

- Qwen2.5-1.5B High-dose seed 1102: its Mac Granite run stopped after 149 of 200 answers (`M/tmp/kill-test-stage0/second-judge-kt-items.jsonl`, unit `1102-a0-e3-a1`). The note reports no Granite value for it, so the partial labels are not released.
- High-dose units after one epoch (`1102-a0-e1-a1`, `1103-a0-e1-a1` in `M/tmp/kill-test-stage0`): not in Tables 1-3. Section 4's "about 83%" comes from them.
- Qwen3Guard labels of the ToxicChat (`safety`) and ARC-generation answers in `guard.jsonl`: no number of the note uses them.
- Per-answer opening classes: the mechanism analysis stored only crosstabs; the classes would have to be recomputed from answer text, which the builder does not read.
- Raw judge outputs (`guard_answer`, Granite `raw`, `reason`) and answer hashes: free text or answer fingerprints; not needed for any number.
