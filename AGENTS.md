## Mandatory Bug Ownership and Autonomous Repair

When working on an assigned task, you own every defect discovered that prevents that task from being completed.

**Finding a bug is not completing the task. Reporting a bug is not fixing a bug.**

You MUST follow this sequence:

1. Identify the defect and its root cause.
2. Modify the actual source code, build process, configuration or tests responsible for the defect.
3. Run the relevant build or operation.
4. Inspect the resulting output or generated artifacts.
5. Run tests that demonstrate the defect is fixed.
6. If another defect is exposed, fix that defect too, provided it is within the assigned task.
7. Continue until the original task's acceptance criteria are satisfied.

### No Diagnosis-Only Completion

You MUST NOT:
- Stop after identifying a problem.
- Merely describe the code changes that should be made.
- Report that something should work without executing it.
- Substitute a configuration change for fixing the underlying problem.
- Claim a fix is complete because tests unrelated to the defect pass.
- Ask the user to perform routine debugging that you can perform using available tools.

### Evidence-Based Completion

Every claimed fix must have corresponding evidence.

For example:
- Packaging defect: build the package and inspect its contents.
- Import defect: actually import the module from the generated package.
- Test defect: run the affected test.
- Configuration defect: inspect the effective configuration.
- AWS integration defect: verify the deployed resource or actual execution where deployment is authorised.

### Blockers

Only stop when:
- A required permission is unavailable.
- An external service or resource is genuinely unavailable.
- The next action requires explicit user authorisation.
- The task cannot be completed with the available tools.

When blocked, explain the precise blocker and what action is required. Do not present an unimplemented correction as a completed fix.

**Definition of done:** The original task works, its acceptance criteria have been verified, and no known in-scope defect remains unresolved.
