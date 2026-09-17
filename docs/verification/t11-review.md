# T11 source review — 2026-09-16

Mode: self-review. Native delegation was attempted but returned `agent thread limit reached`; the diagnostic inventory listed only the root agent. No independent review is claimed.

Fixed point: `f334bfb1771f8d0472152b3407c0f4ffc15fb7a8`.
Reviewed head: `f1fcb20f32d5fa2a33820742ee8a8a3476a5cc07`.
Diff: `git diff f334bfb1771f8d0472152b3407c0f4ffc15fb7a8...f1fcb20f32d5fa2a33820742ee8a8a3476a5cc07` (10 files).
Commits: `2610133`, `a17f13f`, `f1fcb20`.
Planning input: issue #12 and `tickets/11-candidatas-ci.md`, validated at checkpoint `9c9f2c44531269dae4d785e4f8b7d197e56f0082`.

## Standards

Sources: repository `AGENTS.md`, `docs/agents/{issue-tracker,domain,planning}.md`, `CONTEXT.md`, and the code-review skill's twelve-smell baseline. No additional coding standards were found. Tool-enforced formatting and syntax are excluded from findings.

No actionable documented-standard violation was identified. The two small version/revision/variant checks in `candidate.py` guard different producer and consumer boundaries; their similarity does not justify a new abstraction. The candidate module owns artifact identity and transport; the acceptance module owns ordered execution and retained results. This separation follows the existing public command and file seams without introducing another engine or image variant.

Findings: 0. No Standards follow-up is requested.

## Spec

Source inspection supports the weekly/manual workflow, a clean exact Git revision, coordinated names/version/architecture, direct Salesforce/base ancestry, archive and command hashes, the shared thirteen-check acceptance contract, and separate fail-closed approval reports. Results are uploaded even on failure, while archives require a successful build. The normal workflow has no Docker Hub push or stable promotion. The documented CMD import preserves the recorded artifacts and identifies private-repository access and OCI image-store prerequisites.

No concrete source mismatch or scope creep was identified. Acceptance remains incomplete until actual workflow evidence is obtained: ticket lines 16 and 18 require checking the transported production artifacts and generic content; line 19 requires successful and deliberately failed workflow runs. The passing three contract tests and two Docker transport fixtures do not substitute for those production proofs.

Findings: 0 source defects. Runtime acceptance remains pending. No Spec follow-up is requested absent a material correction arising from that validation.

This is the initial source pass of one bounded checkpoint. Later runtime results and any necessary fixes must be appended without reopening an unrelated review cycle. T09/T10, already integrated at the fixed point, are outside this review.

## Bounded Spec follow-up — CI socket correction

Follow-up head: `30a711eb5b14def4c064f51b55dc350aa7da1fd1`, original fixed point unchanged. This is the single eligible Spec follow-up, performed as self-review. It addresses the runtime finding from run35147084812 and regressions introduced by its CI-only fix; the unaffected Standards axis is not restarted.

The normal workflow exposed a material environment mismatch in acceptance criterion15: the pinned setup action's selected daemon owns the candidate and home volume, but the workstation's standard socket reached the runner's other daemon. The fix stops only the original daemon of a guarded disposable GitHub-hosted runner, aliases the standard path to the action's existing Unix socket, and asserts matching engine IDs. The notebook controller and all thirteen acceptance checks are unchanged. The source review finds no additional defect in this correction and no new product scope.

Validation boundary: syntax/ShellCheck passed; the replacement run35149106675 passed the exact engine-identity precondition and is executing full acceptance. Windows CMD Docker/Compose also passed against the original transported candidate in103.562s. Production acceptance remains pending the replacement run's final report. No further source review is requested; any later necessary final fix batch must be validated without restarting this checkpoint.

## Final correction validation — no additional review cycle

Final source: `85e13fae5732627ae24ff4393be2dc503d4481f7`. The same logical final fix batch includes the selected-controller path in the backup helper and the measured hosted-runner capacity fixes. Linux and Windows CMD reproduced/verified the affected backup seam without changing its preservation assertions. The actual hosted runner now retained about56GiB before building and36GiB after releasing15.18GB of build-only cache; both capacity gates passed.

Normal workflow35154433830 completed successfully against this source. All13acceptance groups passed (55passed unittest cases plus2Windows-specific skips, as explicitly recorded in the portable result); `approved:true` matches the job conclusion, source, candidate digests and contract checksum. No application source changed during the CI remediation. The approved pair was imported with matching digests, its35unique layers were inspected, and Windows CMD Docker/Compose passed in82.737s; see t11-candidates.json. There are no known unresolved source defects; T12 device measurement and T13 public promotion remain their own ticket scopes.

The earlier real failures and deliberate local rejection remain negative evidence. They were not waived, rerun blindly or converted into approvals. The review checkpoint is closed as a bounded self-review with final validation; no new Standards or Spec pass is implied by the later correction commits.

## Published PR feedback — validator identity and run isolation

The automated review on PR22 at `e696218f71f88fd4daed8eb1e4113778f2c8074d` subsequently identified two actionable P2 defects. This is external published feedback, not a restarted self-review cycle:

- [Validator source identity](https://github.com/Electivus/webtop-arch-kde-workstation/pull/22#discussion_r4031823887): local acceptance previously used the invoking checkout while reporting the candidate revision. Validation now requires the exact clean candidate checkout before loading and again before approval, and records `validatorRevision`. A real temporary Git repository reproduced the missing guard; the regression now rejects mismatched, staged, unstaged and untracked sources before archive loading. Matching clean code reaches archive validation.
- [Run isolation](https://github.com/Electivus/webtop-arch-kde-workstation/pull/22#discussion_r4031823892): scheduled/manual candidates previously shared cancellation with main pushes. Only superseded checks for the same PR now share a cancellable group; all other runs receive unique groups and retain their full execution.

The previous production receipts remain evidence for their stated source. The updated source requires the replacement PR checks before integration; those results will be recorded separately.
