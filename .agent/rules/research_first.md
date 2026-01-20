---
trigger: manual
---

# 📚 Research-First Development Rules

> [!IMPORTANT]
> You **MUST** perform research using `context7` BEFORE creating or modifying any code that uses external libraries, frameworks, or APIs.

## 🔍 Mandatory Research Workflow

Before writing or editing code, you must follow this sequence:

1.  **Identify Components**: List the libraries, frameworks, or technologies involved in the task.
2.  **Resolve Library IDs**: Use `mcp_context7_resolve-library-id` for each major component to find its correct Context7 ID.
3.  **Query Documentation**: Use `mcp_context7_query-docs` to fetch official best practices, patterns, and up-to-date syntax.
    *   *Query specifically for:* "best practices for [feature]", "common pitfalls in [version]", or "[framework] production ready pattern".
4.  **Synthesize Plan**: Briefly summarize the best practices found and how you will apply them to the user's code.

## 🛡️ Best Practice Enforcement

- **No Assumptions**: Do not rely solely on your training data for rapidly evolving libraries (e.g., Next.js, LangChain, Supabase). Trust the `context7` output.
- **Modern Patterns**: Prefer the most recent stable patterns returned by the docs (e.g., Functional Components over Class Components, Server Actions over API Routes if accepted).
- **Citation**: In your final explanation, mention which specific documentation or best practice guided your implementation.

## 🚫 Stop Conditions

Do **NOT** write code if:
- You have not checked `context7` for a complex or unfamiliar library.
- You are unsure about the library version compatibilities.

*Exception: If the task is purely logic (non-library specific) or standard library usage, you may proceed without context7, but must still apply general Clean Code principles.*