# Design Journey: Building the Markdown Processor

> This document explains the thought process behind the Markdown parser. It is intentionally written as a design journey rather than a code walkthrough. The goal is to capture *why* the implementation evolved the way it did.

---

# Initial Goal

The objective was **not** to build a complete Markdown parser.

The objective was to convert a Markdown document into the project's Canonical Document Model (CDM).

```text
Markdown
    │
    ▼
Markdown Parser
    │
    ▼
Canonical Document Model
```

The parser only needed to extract meaningful content blocks such as:

- Headings
- Paragraphs
- Lists
- Code blocks

Everything else (tables, images, blockquotes, etc.) could be ignored initially.

---

# Step 1 — Understanding markdown-it-py

Before writing any parser, I first explored what `markdown-it-py` actually returns.

For a simple Markdown file:

```markdown
# Hello

This is a paragraph.

- One
- Two

```python
print("Hi")
```
```

I inspected the generated tokens.

The first realization was:

> Markdown is not returned as plain text.

Instead, it is returned as a sequence of tokens.

For example:

```
heading_open
inline
heading_close

paragraph_open
inline
paragraph_close

bullet_list_open
list_item_open
paragraph_open
inline
paragraph_close
list_item_close
bullet_list_close

fence
```

At this point the parser became a **token processing problem**, not a string parsing problem.

---

# Step 2 — Recognizing a Block Lifecycle

Looking at the tokens revealed a repeating pattern.

Every block follows the same lifecycle.

```
Open Token

↓

Content

↓

Close Token
```

For example,

```
heading_open

↓

inline

↓

heading_close
```

or

```
paragraph_open

↓

inline

↓

paragraph_close
```

This led to the first parser algorithm:

1. Detect opening token.
2. Capture content.
3. Detect closing token.
4. Emit one Content block.

---

# Step 3 — Delayed Emission

Initially, I tried emitting the CDM object as soon as an `inline` token appeared.

This quickly failed.

The parser does not know whether a block has finished until it encounters its closing token.

Instead, the algorithm became:

```
Opening Token
        │
        ▼
Store current block type

↓

Inline

↓

Store current text

↓

Closing Token

↓

Create CDM Content
```

This introduced the idea of **delayed emission**.

---

# Step 4 — Code Blocks are Different

Unlike headings and paragraphs, fenced code blocks are represented by a single token.

```
fence
```

There is no opening and closing pair.

Instead of forcing code blocks into the same lifecycle, they were handled separately.

```
Fence

↓

Immediately emit Content(type="code")
```

---

# Step 5 — Lists Broke the Assumption

The first implementation worked for:

- headings
- paragraphs
- code

It immediately failed for lists.

A Markdown list is nested.

Example:

```
bullet_list_open

list_item_open

paragraph_open

inline

paragraph_close

list_item_close

bullet_list_close
```

Unlike headings, there are multiple open blocks active at the same time.

One variable was no longer enough.

---

# Step 6 — Replacing "Current Block" with a Stack

Originally the parser stored:

```
current_block
```

This failed because nested structures overwrite the current block.

The solution was replacing it with a stack.

```
Push opening token

↓

Top of stack = current block

↓

Pop when closing token arrives
```

Now the parser always knows which block is currently active.

---

# Step 7 — Lists Have Two Levels of State

Lists introduced another challenge.

There are two different concepts:

```
Entire List

↓

Individual List Item
```

These cannot share the same buffer.

Instead, two buffers were introduced.

```
current_list_item

↓

list_items
```

Lifecycle:

```
list_item_open

↓

current_list_item = ""

↓

inline

↓

current_list_item = "Apple"

↓

list_item_close

↓

append to list_items

↓

bullet_list_close

↓

emit entire list
```

---

# Step 8 — Parser State

At this point several variables always travelled together.

```
order
contents
block_stack
content_text
current_list_item
list_items
```

Passing each variable between helper methods would make the parser difficult to maintain.

Instead, they were grouped into one object.

```python
MarkdownParserState
```

This object represents **the state of one parsing operation**, not the state of the processor itself.

---

# Step 9 — Dispatcher and Handlers

Initially, the parser was one large `for` loop.

As the parser evolved, responsibilities naturally separated.

The final architecture became:

```
Token Stream

↓

Dispatcher

↓

Open Handler

↓

Inline Handler

↓

Close Handler

↓

Fence Handler

↓

Content Emitter
```

Each handler owns exactly one responsibility.

---

# Step 10 — Centralizing Content Creation

Originally every handler created `Content` objects manually.

This duplicated:

- creating Content
- incrementing order
- appending to contents

The common logic was extracted into one helper.

```
_emit_content()
```

Now handlers decide **what** should be emitted.

The emitter decides **how** it is stored.

---

# Final Architecture

```
Markdown

↓

markdown-it-py

↓

Tokens

↓

Dispatcher

↓

Parser State

↓

Handlers

↓

Canonical Document Model
```

---

# Design Decisions

## Why a Stack?

Markdown supports nested structures.

A stack naturally models nested opening and closing blocks.

---

## Why ParserState?

The parser contains several variables that always move together.

Grouping them into a single object makes the parser easier to reason about and keeps the processor itself stateless.

---

## Why Delayed Emission?

A block is not complete until its closing token is encountered.

Emitting only after the closing token guarantees complete content.

---

## Why Separate Fence Handling?

Code fences are represented by a single token instead of an open/close pair.

Treating them independently keeps the parser simple.

---

## Lessons Learned

The final architecture was **not designed upfront**.

It emerged through several iterations.

Each abstraction was introduced only after a concrete problem appeared.

Examples:

- Stack → introduced because nested structures broke a single variable.
- ParserState → introduced because too many variables travelled together.
- Dispatcher → introduced because the parsing loop became difficult to read.
- Content Emitter → introduced because Content creation was duplicated.

This iterative approach kept the parser simple while allowing the design to evolve naturally.