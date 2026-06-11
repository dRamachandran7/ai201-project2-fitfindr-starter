# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

search_listings takes the user's query and looks through listings.json to find appropriate matches. It filters by size/price, scores each remaining listing by keyword overlap with the description, drops anything that doesn't match, and returns the matches sorted by relevance (best first). Choosing the single top item is the planning loop's job, not this tool's.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): a short description of the piece, possibly including color or fit.
- `size` (str, optional): the size of the piece of clothing the user is looking for. Matching is case-insensitive; pass `None` to skip size filtering.
- `max_price` (float, optional): the highest price the user would pay (inclusive). Pass `None` to skip price filtering.

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
A `list[dict]` of matching listings, sorted by relevance (best match first). Each listing dict has the fields: `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand`, `platform`. Returns an empty list (not an exception) when nothing matches.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->

If search_listings fails, the pipeline should stop and inform the user that they should try a different query.

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Given a specific item and the user's current wardrobe, this function suggests one or more complete outfit combinations that pair the new item with named pieces from the wardrobe.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): the listing dict retrieved by search_listings (the item the user is considering).
- `wardrobe` (dict): the user's current wardrobe — a dict with an `items` key holding a list of wardrobe item dicts (`id`, `name`, `category`, `colors`, `style_tags`, `notes`).

**What it returns:**
<!-- Describe the return value -->
A non-empty string with 1–2 outfit suggestions pairing the new item with specific wardrobe pieces.

**What happens if it fails or returns nothing:**

If `wardrobe['items']` is empty, it does NOT go back to search_listings (that searches the marketplace, not the closet). Instead it returns general styling advice for the new item on its own — what kinds of pieces pair well and what vibe it suits. If the LLM call errors, the pipeline stops and informs the user.

---

### Tool 3: create_fit_card

**What it does:**

Given an outfit suggestion and the new item, this function returns an Instagram/TikTok caption–style summary of the outfit. It must read like a real OOTD post (not a product description), mention the item name/price/platform naturally, and produce something different each time for different inputs (achieved with a higher LLM temperature).

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): the outfit suggestion string returned by suggest_outfit.
- `new_item` (dict): the listing dict for the thrifted item (used to name the item, price, and platform).

**What it returns:**

A short (2–4 sentence) trendy caption summarizing the user's outfit.

**What happens if it fails or returns nothing:**

If `outfit` is empty or whitespace-only, it returns a descriptive error message string rather than raising or calling another tool. (Re-running suggest_outfit when the outfit is missing is the planning loop's responsibility, not this tool's.)

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | |
| suggest_outfit | Wardrobe is empty | |
| create_fit_card | Outfit input is missing or incomplete | |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

**Milestone 4 — Planning loop and state management:**

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 0 — Parse the query:**
The planning loop first parses the natural-language query into structured parameters and stores them in `session["parsed"]`:
- `description = "vintage graphic tee"`
- `size = None` (none stated)
- `max_price = 30.0`
The wardrobe is loaded separately (`get_example_wardrobe()`) and stored in `session["wardrobe"]`.

**Step 1 — Search:**
The agent calls `search_listings("vintage graphic tee", size=None, max_price=30.0)`. It filters listings to those at or below $30, scores each by keyword overlap with "vintage graphic tee," drops zero-score items, and returns the matches sorted by relevance — e.g. 3 listings, best first. The full list is stored in `session["search_results"]`.

*Branch (error path):* If the list is empty, the agent sets `session["error"]` to a helpful message ("No listings matched 'vintage graphic tee' under $30 — try raising your budget or loosening the description") and returns immediately. It does **not** call `suggest_outfit` with empty input.

**Step 2 — Select the item:**
The agent picks the top result (`session["search_results"][0]`) and stores it in `session["selected_item"]` — e.g. `{"title": "Faded Band Tee", "price": 22.0, "platform": "depop", "condition": "good", ...}`. This is how state flows forward: the found item is now available to every later tool without the user re-entering anything.

**Step 3 — Suggest an outfit:**
The agent calls `suggest_outfit(new_item=session["selected_item"], wardrobe=session["wardrobe"])`. Since the wardrobe is non-empty, it pairs the band tee with specific pieces from the closet and returns a string, stored in `session["outfit_suggestion"]` — e.g. "Pair this with your baggy straight-leg jeans and chunky white sneakers for a 90s grunge look. Layer the vintage black denim jacket over the top and tuck the front corner of the tee for shape."

*Branch:* If the wardrobe were empty, this tool would instead return general styling advice for the tee on its own (it would not loop back to search_listings).

**Step 4 — Create the fit card:**
The agent calls `create_fit_card(outfit=session["outfit_suggestion"], new_item=session["selected_item"])`. With a higher temperature it generates a fresh caption, stored in `session["fit_card"]` — e.g. "thrifted this faded band tee off depop for $22 and it was MADE for my baggy jeans 🖤 threw the denim jacket over top, full grunge mode. look in my stories"

*Branch:* If `outfit_suggestion` were empty/missing, `create_fit_card` returns a descriptive error string rather than crashing.

**Step 5 — Return the session:**
With `session["error"]` still `None`, the loop returns the completed session dict.

**Final output to user:**
The user sees the three results threaded together, e.g.:

> **Found:** Faded Band Tee — $22, depop, good condition
>
> **How to style it:** Pair this with your baggy straight-leg jeans and chunky white sneakers for a 90s grunge look. Layer the vintage black denim jacket over the top and tuck the front corner of the tee for shape.
>
> **Fit card:** "thrifted this faded band tee off depop for $22 and it was MADE for my baggy jeans 🖤 threw the denim jacket over top, full grunge mode. look in my stories"
